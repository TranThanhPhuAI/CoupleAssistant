"""Cấu hình. Mọi đường dẫn đổi được bằng biến môi trường để chạy độc lập với Couple Assistant."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent           # social/
REPO = ROOT.parent                                       # thư mục dự án Couple Assistant
DATA_DIR = Path(os.environ.get("LOVESPOT_SOCIAL_DATA", str(ROOT / "data")))
DB_PATH = DATA_DIR / "social.db"
SECRET_FILE = DATA_DIR / "jwt_secret"
# Danh sách quán: chỉ ĐỌC từ dữ liệu của Couple Assistant (không ghi, không phụ thuộc mã nguồn bên đó)
PLACES_CSV = Path(os.environ.get("LOVESPOT_PLACES_CSV", str(REPO / "data" / "clean" / "restaurants_clean.csv")))

TOKEN_DAYS = 7
MIN_PASSWORD = 8
MAX_FAILS, LOCK_MINUTES = 5, 15
ALLOW_REGISTER = os.environ.get("LOVESPOT_SOCIAL_REGISTER", "on") != "off"

USERNAME = r"^[a-z0-9_]{3,30}$"          # @tên: chữ thường không dấu, số, _
MAX_POST, MAX_COMMENT, MAX_BIO = 2000, 600, 600
UPLOAD_DIR = DATA_DIR / "uploads"          # ảnh người dùng đăng (tên ngẫu nhiên 32 ký tự hex, không đoán được)
MAX_IMAGES, MAX_IMAGE_BYTES = 4, 4 * 1024 * 1024
FEED_PAGE = 20
SUGGEST_PEOPLE, SUGGEST_PLACES = 6, 5
