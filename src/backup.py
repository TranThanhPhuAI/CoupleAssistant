"""Sao lưu dữ liệu ra một file .zip có ngày giờ; giữ BACKUP_KEEP bản gần nhất.

Gồm: tài khoản, hồ sơ, nhật ký AI, phản hồi, dữ liệu đã xử lý, nhãn, đánh giá, bản index đang dùng
và dữ liệu tab Cộng đồng (social/data).
Không gồm: model, môi trường Python (cài lại được).
Nơi lưu: biến môi trường LOVESPOT_BACKUP_DIR (nên trỏ sang ổ ngoài hoặc thư mục OneDrive / Google Drive),
mặc định data/backups.     Chạy:  python run.py saoluu
"""
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import config as cfg

FOLDERS = ["auth", "profiles", "ai_log", "feedback", "clean", "absa", "eval", "raw", "place_media"]


def _social(z):
    """Dữ liệu tab Cộng đồng (social/data): chụp CSDL SQLite bằng API backup (an toàn khi server đang chạy)."""
    import sqlite3
    import tempfile
    sdir = cfg.BASE / "social" / "data"
    added = []
    if (sdir / "social.db").exists():
        with tempfile.TemporaryDirectory() as td:
            snap = Path(td) / "social.db"
            src, dst = sqlite3.connect(sdir / "social.db"), sqlite3.connect(snap)
            with dst:
                src.backup(dst)
            src.close(); dst.close()
            z.write(snap, "social/data/social.db")
        added.append(sdir / "social.db")
    if (sdir / "jwt_secret").exists():
        z.write(sdir / "jwt_secret", "social/data/jwt_secret")
        added.append(sdir / "jwt_secret")
    for p in sorted((sdir / "uploads").glob("*")) if (sdir / "uploads").is_dir() else []:   # ảnh người dùng đăng
        z.write(p, f"social/data/uploads/{p.name}")
        added.append(p)
    return added


def backup(dest=None, keep=cfg.BACKUP_KEEP):
    dest = dest or cfg.BACKUP_DIR
    dest.mkdir(parents=True, exist_ok=True)
    data = cfg.BASE / "data"
    out = dest / f"couple_assistant_{datetime.now():%Y%m%d_%H%M%S}.zip"
    files = [p for f in FOLDERS if (data / f).exists() for p in (data / f).rglob("*") if p.is_file()]
    cur = (cfg.INDEX_DIR / "CURRENT").read_text(encoding="utf-8").strip() if (cfg.INDEX_DIR / "CURRENT").exists() else None
    if cur:  # chỉ bản index đang dùng
        files += [cfg.INDEX_DIR / "CURRENT", *[p for p in (cfg.INDEX_DIR / cur).rglob("*") if p.is_file()]]
    tmp = out.with_suffix(".zip.tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, p.relative_to(cfg.BASE))
        files += _social(z)
    tmp.replace(out)
    old = sorted(dest.glob("couple_assistant_*.zip"))[:-keep]
    for p in old:
        p.unlink()
    return out, len(files), len(old)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    out, n, removed = backup()
    print(f"Đã sao lưu {n} file -> {out} ({out.stat().st_size / 1e6:.1f} MB); xóa {removed} bản cũ")
