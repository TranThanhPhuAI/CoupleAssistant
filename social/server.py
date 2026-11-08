"""Lovespot Social — mạng xã hội ẩm thực hẹn hò.   Chạy:  python social/server.py   -> http://127.0.0.1:8100

Độc lập với Couple Assistant (cổng, CSDL, tài khoản riêng); chỉ đọc danh sách quán ở data/clean/restaurants_clean.csv.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from lovespot.media import router as media  # noqa: E402
from lovespot.routes_people import router as people  # noqa: E402
from lovespot.routes_posts import router as posts  # noqa: E402

WEB = ROOT / "web"
app = FastAPI(title="Lovespot Social API", version="0.1",
              description="Mạng xã hội ẩm thực hẹn hò: hồ sơ gu ăn uống, kết nối, review quán thật, gợi ý người cùng gu.")
app.include_router(people)
app.include_router(posts)
app.include_router(media)
app.mount("/static", StaticFiles(directory=WEB), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(WEB / "index.html")


if __name__ == "__main__":
    import uvicorn
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Chạy Lovespot Social")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8100)
    a = ap.parse_args()
    print(f"Lovespot Social: http://{a.host}:{a.port}   (tài liệu API: /docs)   Ctrl+C để dừng")
    uvicorn.run(app, host=a.host, port=a.port, log_level="warning")
