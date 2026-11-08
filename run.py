"""Couple Assistant — lệnh chạy duy nhất.  Gõ:  python run.py   để xem hướng dẫn."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src" if (ROOT / "src").is_dir() else ROOT

# lệnh -> (mô tả, [các script chạy lần lượt])
COMMANDS = {
    "web":      ("Mở giao diện web + API         -> http://127.0.0.1:8000  (tài liệu API: /docs)", ["api.py"]),
    "taikhoan": ("Tài khoản đăng nhập web       vd: python run.py taikhoan tao admin --admin", ["auth.py"]),
    "saoluu":   ("Sao lưu dữ liệu ra file .zip (nơi lưu: biến LOVESPOT_BACKUP_DIR)", ["backup.py"]),
    "hoso":     ("Tạo / sửa hồ sơ sở thích cá nhân   vd: python run.py hoso tao minh", ["profile_cli.py"]),
    "hoi":      ("Hỏi gợi ý quán hẹn hò        vd: python run.py hoi \"cafe yên tĩnh Quận 1\" --nguoi-a minh",
                 ["app_cli.py"]),
    "plan":     ("Lập plan hẹn hò nhiều chặng  vd: python run.py plan \"yên tĩnh\" --luc 19:00 --nguoi-a minh",
                 ["app_cli.py", "--plan"]),
    "thongke":  ("Chỉ số AI: tỷ lệ chọn quán, quán bịa bị chặn, độ trễ...", ["ai_service.py", "thongke"]),
    "anhfoody": ("Lấy link ảnh quán từ Foody để thẻ gợi ý hiện ảnh (~20 phút lần đầu)", ["foody_photos.py"]),
    "kiemtra":  ("Kiểm tra toàn bộ hệ thống   thêm --quick / --no-llm", ["smoke_test.py"]),
    "nhap":     ("Nhập quán/review mới         vd: python run.py nhap data/staging/dot1 [--dry-run]", ["ingest.py"]),
    "tinhlai":  ("Tính lại tham số chấm điểm (chạy định kỳ, vd hằng tuần)", ["ingest.py", "--recompute"]),
    "danhgia":  ("Đánh giá chất lượng (Recall@10, NDCG@10)   thêm --no-judge", ["evaluate.py"]),
    "demo":     ("Xem demo từng phần: xếp hạng hai người, tính cách, LLM",
                 ["stage4_rank.py", "|", "stage5_personality.py", "|", "stage6_demo.py"]),
    "xaylai":   ("Xây lại dữ liệu từ đầu (không gồm gán nhãn LLM ~2 giờ)",
                 ["stage1_clean.py", "|", "stage2_embed.py", "|", "stage3_scores.py", "|", "stage5_personality.py",
                  "|", "interests.py"]),
    "gannhan":  ("Gán nhãn ABSA bằng LLM (cần Ollama, ~2 giờ)", ["stage3_label.py", "|", "stage3_label.py", "--expand"]),
}
ALIASES = {"ask": "hoi", "test": "kiemtra", "ingest": "nhap", "recompute": "tinhlai", "eval": "danhgia",
           "rebuild": "xaylai", "label": "gannhan", "profile": "hoso", "stats": "thongke"}


def usage():
    print("Couple Assistant — gợi ý quán hẹn hò TP.HCM\n\nCách dùng:  python run.py <lệnh> [tham số]\n")
    for k, (desc, _) in COMMANDS.items():
        print(f"  {k:9s} {desc}")
    print("\nVí dụ:\n  python run.py web                          (dùng trên trình duyệt — dễ nhất)\n"
          "  python run.py hoso tao minh                (nhập sở thích, hỏi từng bước)\n"
          "  python run.py hoi \"ăn tối lãng mạn Quận 3 lúc 19h\" --nguoi-a minh --nguoi-b lan\n"
          "  python run.py plan \"yên tĩnh\" --luc 19:00 --ngan-sach 300000 --nguoi-a minh --nguoi-b lan\n"
          "  python run.py kiemtra --quick\n\nChi tiết: README.md và thư mục docs/")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help", "help"}:
        usage()
        return 0
    cmd = ALIASES.get(sys.argv[1], sys.argv[1])
    if cmd not in COMMANDS:
        print(f"Không có lệnh '{sys.argv[1]}'.\n")
        usage()
        return 2
    extra = sys.argv[2:]
    steps, cur = [], []
    for tok in COMMANDS[cmd][1]:  # tách các bước bằng "|"
        if tok == "|":
            steps.append(cur)
            cur = []
        else:
            cur.append(tok)
    steps.append(cur)
    for i, step in enumerate(steps):
        args = step + (extra if len(steps) == 1 else [])
        if len(steps) > 1:
            print(f"\n===== Bước {i + 1}/{len(steps)}: {' '.join(step)} =====", flush=True)
        # đường dẫn tương đối người dùng gõ (vd data/staging/dot1) tính từ thư mục gốc
        args = [str((ROOT / a).resolve()) if (ROOT / a).exists() and not a.startswith("-") else a for a in args]
        code = subprocess.call([sys.executable, str(SRC / args[0]), *args[1:]], cwd=SRC)
        if code != 0:
            print(f"\nLỗi ở bước '{' '.join(step)}' (mã {code}).")
            return code
    return 0


if __name__ == "__main__":
    sys.exit(main())
