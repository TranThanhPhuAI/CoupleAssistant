"""Đóng gói GIAO DIỆN để đưa lên Vercel. Backend (AI, model, dữ liệu) vẫn chạy trên máy nhà qua Cloudflare Tunnel.

    python tools/vercel_build.py https://hen.tenmien.com        -> thư mục dist/vercel/ (kéo thả lên Vercel)

Vercel chỉ phục vụ file tĩnh; mọi yêu cầu /api/*, /social/api/*, /docs được Vercel chuyển tiếp (rewrite) về backend,
nên trình duyệt thấy một tên miền duy nhất: không cần CORS, đăng nhập và tab Cộng đồng chạy như cũ.
Chỉ chép những file giao diện cần thiết: không có dữ liệu, tài khoản, khóa, file zip, cấu hình máy.
"""
import json
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dist" / "vercel"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        sys.exit("Cách dùng: python tools/vercel_build.py https://<tên miền backend>   (vd https://hen.tenmien.com)")
    backend = sys.argv[1].rstrip("/")
    u = urlparse(backend)
    if u.scheme != "https" or not u.netloc or u.path or u.query:
        sys.exit("Địa chỉ backend phải dạng https://ten-mien (không có đường dẫn phía sau). "
                 "Đây là tên miền Cloudflare Tunnel trỏ về máy chạy 'python run.py web'.")

    # Xóa bản cũ nhưng GIỮ .vercel/ (liên kết project sau lần 'vercel link') để đưa lên lại không phải chọn project
    OUT.mkdir(parents=True, exist_ok=True)
    for p in OUT.iterdir():
        if p.name != ".vercel":
            shutil.rmtree(p) if p.is_dir() else p.unlink()
    web, social = ROOT / "src" / "web", ROOT / "social" / "web"
    # Couple Assistant: index.html ở gốc, phần còn lại ở /static (giống khi server phục vụ); bỏ thư mục dev/ (chỉ dùng khi phát triển)
    shutil.copy2(web / "index.html", OUT / "index.html")
    shutil.copytree(web, OUT / "static", ignore=shutil.ignore_patterns("index.html", "dev", "__pycache__"))
    # Cộng đồng Lovespot: /social/ (index.html dùng đường dẫn tương đối static/...)
    if social.is_dir():
        (OUT / "social").mkdir()
        shutil.copy2(social / "index.html", OUT / "social" / "index.html")
        shutil.copytree(social, OUT / "social" / "static", ignore=shutil.ignore_patterns("index.html"))

    proxy = ["/api/:path*", "/social/api/:path*", "/docs", "/openapi.json"]
    vercel = {
        "$schema": "https://openapi.vercel.sh/vercel.json",
        "framework": None,          # trang tĩnh: không để Vercel tự đoán (từng nhận nhầm là FastAPI)
        "buildCommand": "",
        "installCommand": "",
        "cleanUrls": False,
        "rewrites": [{"source": s, "destination": backend + s} for s in proxy],
        "headers": [
            {"source": "/static/media/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=604800"}]},
            {"source": "/(.*)", "headers": [{"key": "X-Content-Type-Options", "value": "nosniff"},
                                            {"key": "Referrer-Policy", "value": "strict-origin-when-cross-origin"}]},
        ],
    }
    (OUT / "vercel.json").write_text(json.dumps(vercel, ensure_ascii=False, indent=2), encoding="utf-8")
    # 'vercel link' tạo .env.local chứa token -> không bao giờ đưa lên
    (OUT / ".vercelignore").write_text(".env*\n.vercel\n", encoding="utf-8")

    files = [p for p in OUT.rglob("*") if p.is_file()]
    mb = sum(p.stat().st_size for p in files) / 1e6
    print(f"Đã tạo {OUT.relative_to(ROOT)}  ({len(files)} file, {mb:.1f} MB), backend: {backend}")
    print("Tiếp theo (chạy TRONG thư mục dist\\vercel, KHÔNG chạy ở thư mục gốc dự án):")
    print("    cd dist\\vercel")
    print("    npx vercel --prod          (hoặc vercel.com -> Add New -> Project -> kéo thả thư mục dist\\vercel, Framework: Other)")


if __name__ == "__main__":
    main()
