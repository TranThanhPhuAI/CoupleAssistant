"""Vector store nhẹ bằng numpy, có phiên bản + tráo atomic.

Cấu trúc:  data/index/<version>/{emb.npy, meta.csv, manifest.json}
           data/index/CURRENT   <- tên version đang phục vụ
build(): nhận TOÀN BỘ tập doc hiện tại, dùng lại embedding cũ theo text_hash
(chỉ embed doc mới/đổi nội dung), ghi bản mới rồi mới tráo con trỏ.
Web đang đọc bản cũ không bị ảnh hưởng nếu build lỗi giữa chừng.
"""
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


def text_hash(model_name, text):
    return hashlib.sha1(f"{model_name}\x00{text}".encode("utf-8")).hexdigest()


class VectorStore:
    def __init__(self, root):
        self.root = Path(root)
        self.pointer = self.root / "CURRENT"

    def current_dir(self):
        if not self.pointer.exists():
            return None
        d = self.root / self.pointer.read_text(encoding="utf-8").strip()
        return d if d.exists() else None

    def load(self):
        """Trả về (meta DataFrame, emb float32 [N, dim], manifest) hoặc None nếu chưa có index."""
        d = self.current_dir()
        if d is None:
            return None
        meta = pd.read_csv(d / "meta.csv", encoding="utf-8-sig", dtype=str)
        emb = np.load(d / "emb.npy").astype(np.float32)
        manifest = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        assert len(meta) == len(emb), "Index hỏng: meta và emb lệch số dòng"
        return meta, emb, manifest

    def build(self, docs, embed_fn, model_name, keep=2):
        """docs: DataFrame có cột doc_id (duy nhất), text, + cột metadata tùy ý.
        embed_fn(list[str]) -> np.ndarray đã chuẩn hóa L2."""
        assert docs["doc_id"].is_unique, "doc_id trùng"
        docs = docs.reset_index(drop=True).copy()
        docs["text_hash"] = [text_hash(model_name, t) for t in docs["text"]]

        # Dùng lại embedding của bản hiện tại nếu cùng model + cùng nội dung
        old = self.load()
        reuse = {}
        if old is not None and old[2].get("model") == model_name:
            reuse = dict(zip(old[0]["text_hash"], range(len(old[0]))))
        idx_old = docs["text_hash"].map(reuse)
        need = idx_old.isna().to_numpy()

        new_emb = embed_fn(docs.loc[need, "text"].tolist()) if need.any() else None
        dim = new_emb.shape[1] if new_emb is not None else old[1].shape[1]
        emb = np.zeros((len(docs), dim), dtype=np.float16)
        if (~need).any():
            emb[~need] = old[1][idx_old[~need].astype(int).to_numpy()].astype(np.float16)
        if new_emb is not None:
            emb[need] = new_emb.astype(np.float16)

        # Ghi bản mới vào thư mục riêng, xong hết mới tráo con trỏ
        version = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        d = self.root / version
        d.mkdir(parents=True)
        np.save(d / "emb.npy", emb)
        docs.to_csv(d / "meta.csv", index=False, encoding="utf-8-sig")
        stats = {"model": model_name, "dim": int(dim), "n_docs": int(len(docs)),
                 "n_embedded_new": int(need.sum()), "n_reused": int((~need).sum()),
                 "n_removed": len(set(reuse) - set(docs["text_hash"])),  # doc cũ không còn trong tập mới
                 "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        (d / "manifest.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
        tmp = self.root / "CURRENT.tmp"
        tmp.write_text(version, encoding="utf-8")
        os.replace(tmp, self.pointer)  # atomic

        # Dọn bản cũ, giữ lại `keep` bản gần nhất để rollback
        versions = sorted(p for p in self.root.iterdir() if p.is_dir())
        for p in versions[:-keep]:
            shutil.rmtree(p, ignore_errors=True)
        return stats
