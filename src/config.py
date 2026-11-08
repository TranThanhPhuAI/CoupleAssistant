"""Cấu hình chung: đường dẫn + tham số. Mọi script import từ đây."""
import os
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent         # thư mục chứa code
BASE = SRC_DIR.parent if SRC_DIR.name == "src" else SRC_DIR  # gốc dự án (chứa data/); gói chia sẻ đặt code trong src/

# Cache model HuggingFace để trên ổ E (ổ C gần đầy). Phải đặt trước khi import transformers.
os.environ.setdefault("HF_HOME", str(BASE / ".cache" / "huggingface"))
# Nạp trọng số song song (nhiều luồng) gây access violation trên Windows khi RAM căng -> tắt
os.environ.setdefault("HF_DEACTIVATE_ASYNC_LOAD", "1")  # transformers 5.x: nạp tuần tự
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
if (Path(os.environ["HF_HOME"]) / "hub" / "models--BAAI--bge-m3").exists():
    os.environ.setdefault("HF_HUB_OFFLINE", "1")  # model đã tải -> không gọi mạng (nhanh, không cảnh báo)

# ----- Dữ liệu thô (không sửa) -----
def _first_existing(*paths):
    return next((p for p in paths if p.exists()), paths[0])


RAW_DIR = BASE / "data" / "raw"
RAW_RESTAURANTS = _first_existing(RAW_DIR / "restaurants_hcm_fixed.csv",
                                  BASE / "restaurant-data-hcm" / "restaurant-data-hcm" / "data" / "restaurants_hcm_fixed.csv")
RAW_REVIEWS = _first_existing(RAW_DIR / "reviews_merged.csv", BASE / "data - reviews_merged.csv")

# ----- Dữ liệu sạch (đầu ra giai đoạn 1) -----
CLEAN_DIR = BASE / "data" / "clean"
RESTAURANTS_CLEAN = CLEAN_DIR / "restaurants_clean.csv"
REVIEWS_CLEAN = CLEAN_DIR / "reviews_clean.csv"
REVIEWS_OUT_OF_SCOPE = CLEAN_DIR / "reviews_out_of_scope.csv"
CATEGORY_MAP = CLEAN_DIR / "category_map.csv"
BAYES_PARAMS = CLEAN_DIR / "bayes_params.json"
TOP20 = CLEAN_DIR / "top20_bayes.csv"
STAGE1_REPORT = CLEAN_DIR / "stage1_report.txt"

# ----- Tham số -----
INITIAL_LOAD_DATE = "2026-10-14"   # ngày nạp dữ liệu gốc (first_seen của 853 quán ban đầu)
BAYES_M = 10                # số review "giả" kéo về trung bình (≈ trung vị số review/quán)
BAYES_DAILY_CAP = 3          # tối đa N review/quán/ngày được tính vào Bayes (chống seeding)
SUSPECT_MIN_N = 20           # quán có >= N review mới xét cờ rating_suspect
SUSPECT_PERFECT_SHARE = 0.9  # tỉ lệ review >= 9.8 điểm
SUSPECT_MAX_SPAN_DAYS = 31   # ...và tập trung trong <= N ngày, hoặc
SUSPECT_TOP_DAY_SHARE = 0.3  # ...ngày đông nhất chiếm >= 30% số review
PRICE_MIN_VALID = 1_000      # giá hợp lệ (VNĐ)
PRICE_MAX_VALID = 20_000_000
PRICE_SUSPECT_MAX = 2_000_000  # price_max vượt ngưỡng này -> gắn cờ nghi sai

# ----- Giai đoạn 2: embedding + tìm kiếm ngữ nghĩa -----
INDEX_DIR = BASE / "data" / "index"          # data/index/<version>/ + file con trỏ CURRENT
INDEX_KEEP_VERSIONS = 2                      # giữ lại N bản gần nhất để rollback
EMBED_MODEL = "BAAI/bge-m3"
EMBED_DEVICE = os.environ.get("EMBED_DEVICE", "auto")  # auto | cuda | cpu (đặt cpu khi GPU đang chạy Ollama)
EMBED_QUERY_PREFIX = ""                      # bge-m3 không cần; multilingual-e5 cần "query: "
EMBED_DOC_PREFIX = ""                        # multilingual-e5 cần "passage: "
EMBED_MAX_SEQ = 512                          # token; review dài được cắt chunk trước
EMBED_BATCH = 32
CHUNK_MAX_CHARS = 1000                       # review > ~1200 ký tự -> cắt thành nhiều chunk
SEM_TOP_REVIEWS = 3                          # điểm quán = trung bình top-3 review gần nhất
SEM_PROFILE_WEIGHT = 0.2                     # trọng số doc "hồ sơ quán" (tên, loại, món, quận, giá)

# ----- Giai đoạn 3: ABSA + food/date/couple score -----
ABSA_DIR = BASE / "data" / "absa"
ABSA_SAMPLE = ABSA_DIR / "absa_sample.csv"             # ~2.000 review được chọn để LLM gán nhãn
ABSA_SAMPLE_EXTRA = ABSA_DIR / "absa_sample_extra.csv" # review chứa từ khóa hẹn hò -> LLM gán trực tiếp
ABSA_LLM_LABELS =ABSA_DIR / "llm_labels.jsonl"        # cache nhãn LLM (chạy tiếp được nếu bị ngắt)
ABSA_MANUAL_CHECK = ABSA_DIR / "absa_manual_check.csv" # 200 dòng để kiểm tra tay
ABSA_REVIEW_PRED = ABSA_DIR / "review_aspects.csv"     # nhãn/xác suất khía cạnh cho TOÀN BỘ review
ABSA_PROBE = ABSA_DIR / "aspect_probe.pkl"             # bộ phân loại trên embedding (dùng cho review mới)
SCORES = CLEAN_DIR / "restaurant_scores.csv"
SCORE_REFERENCE = ABSA_DIR / "score_reference.json"    # phân phối tham chiếu để chuẩn hóa phân vị quán mới
TOP_COUPLE = CLEAN_DIR / "top_couple.csv"

ABSA_SAMPLE_SIZE = 2000
ABSA_TARGETED_SHARE = 0.5      # 50% mẫu lấy từ review gần các truy vấn hẹn hò (để có đủ ví dụ hiếm)
ABSA_MAX_PER_RESTAURANT = 8
ABSA_MANUAL_N = 200
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"  # không dùng "localhost": Windows thử IPv6 trước, chậm ~2s/request
OLLAMA_MODEL = "qwen3:8b"
OLLAMA_WORKERS = 2             # số request song song tới Ollama

ASPECT_MIN_PROB = 0.5          # chỉ đếm review có xác suất khen/chê >= ngưỡng (tránh cộng dồn nhiễu)
ASPECT_PRIOR_STRENGTH_DATE = 20   # khía cạnh hẹn hò (hiếm): làm mượt mạnh hơn, tránh quán 3 review có 1 lần "lãng mạn" vượt quán 40 review
ASPECT_PRIOR_STRENGTH = 5    # alpha: số review "giả" trong làm mượt Bayes cho từng khía cạnh
DATE_WEIGHTS = {"ambience": 0.30, "romantic": 0.25, "quiet": 0.15, "view": 0.15, "privacy": 0.15}
FOOD_RATING_WEIGHT = 0.5       # food_score = 0.5·phân vị(bayes_rating) + 0.5·phân vị(khía cạnh món ăn)
COUPLE_W = 0.5                 # couple = food^w · date^(1-w)
COUPLE_FOOD_MIN = 0.55
COUPLE_DATE_MIN = 0.50
COUPLE_MIN_PASS = 20           # ít hơn N quán qua ngưỡng -> hạ ngưỡng dần
COUPLE_RELAX_STEP = 0.05

# ----- Giai đoạn 4: TOPSIS + gộp hai người -----
# Tiêu chí: (tên cột, loại) — "benefit" càng cao càng tốt, "cost" càng thấp càng tốt
TOPSIS_CRITERIA = {
    "couple_score": "benefit",
    "personality_fit": "benefit",   # GĐ5; chưa có -> trung tính
    "semantic_match": "benefit",    # chỉ có khi người dùng nhập câu hỏi
    "price_fit": "benefit",
    "distance_km": "cost",          # Haversine từ vị trí MỖI người
    "image_score": "benefit",       # GĐ10; hiện để trống
    "interest_match": "benefit",    # khớp sở thích chung của hai người (chỉ khi có nhập sở thích)
    "bookable": "benefit",          # có Shop đã duyệt -> đặt chỗ được (BR-AI-13); chưa có dữ liệu Shop -> bỏ qua
}
# Tiêu chí trống (không có sở thích / dữ liệu Shop) tự bị bỏ qua và chia lại trọng số
DEFAULT_WEIGHTS = {"couple_score": 0.35, "semantic_match": 0.25, "price_fit": 0.15,
                   "distance_km": 0.15, "personality_fit": 0.10, "image_score": 0.0,
                   "interest_match": 0.30, "bookable": 0.10}
SEMANTIC_PRESELECT = 80        # có câu hỏi -> giữ top-N quán theo ngữ nghĩa trước khi áp ngưỡng couple
SEMANTIC_ALWAYS_KEEP = 5      # top-N khớp câu hỏi nhất luôn được xét dù chưa qua ngưỡng couple (gắn nhãn đánh đổi)
RANK_MIN_PASS = 10            # ít hơn N ứng viên qua ngưỡng couple -> hạ ngưỡng
GROUP_MEAN_WEIGHT = 0.5      # điểm đôi = 0.5·trung bình + 0.5·min (least-misery)

# ----- Giai đoạn 5: tính cách -----
PROFILE_DIR = BASE / "data" / "profiles"     # dữ liệu cá nhân nhạy cảm: mỗi người 1 file JSON, xóa được
RESTAURANT_TRAITS = CLEAN_DIR / "restaurant_traits.csv"
PERSONALITY_WEIGHT_FLOOR = 0.2               # trọng số chiều = floor + |p - 0.5| (rồi chuẩn hóa)
PERSONALITY_WEIGHT_NUDGE = 0.05              # hồ sơ chỉ chỉnh trọng số TOPSIS tối đa ±0.05 mỗi tiêu chí

# ----- Giai đoạn 6: LLM + phản hồi -----
BUDGET_UNSPECIFIED_SCOPE = "total"           # "dưới 400k" không nói rõ -> hiểu là tổng cho 2 người
FEEDBACK_DIR = BASE / "data" / "feedback"
FEEDBACK_EVENTS = FEEDBACK_DIR / "events.jsonl"  # nhật ký thích/không thích + đặc trưng -> dữ liệu LTR sau này
FEEDBACK_PRIOR_N = 10                        # độ "cứng" của hồ sơ từ bảng hỏi (số lượt phản hồi giả)
FEEDBACK_LIKE_STEP = 1.0                     # 1 lượt thích = 1 pseudo-count kéo p về phía q của quán
FEEDBACK_DISLIKE_STEP = 0.5                  # không thích: tín hiệu yếu hơn (không rõ lý do)

# ----- Giai đoạn 7: ingest quán mới -----
STAGING_DIR = BASE / "data" / "staging"      # mỗi đợt nhập: data/staging/<batch>/{restaurants,reviews}.csv
INGEST_LOG_DIR = BASE / "data" / "ingest_log"
INGEST_MAX_REJECT_SHARE = 0.3                # > 30% dòng lỗi -> hủy cả đợt (không ghi gì)
HCM_BBOX = (10.3, 11.2, 106.3, 107.1)        # lat_min, lat_max, lon_min, lon_max
NEW_RESTAURANT_DAYS = 60                     # quán nhập trong N ngày gần đây = "quán mới"
NEW_RESTAURANT_BONUS = 0.05                  # điểm cộng tối đa vào couple_score, giảm dần khi quán có đủ review

# ----- AI gợi ý & plan hẹn hò (Lovespot mục 4–5) -----
AI_LOG_DIR = BASE / "data" / "ai_log"        # nhật ký dạng bảng của tài liệu (JSONL, mỗi dòng 1 bản ghi)
AI_REQUESTS = AI_LOG_DIR / "ai_requests.jsonl"
AI_RESULTS = AI_LOG_DIR / "ai_suggestion_results.jsonl"
DATE_PLANS = AI_LOG_DIR / "date_plans.jsonl"
AI_PLANS = {"free": 5, "plus": 30, "premium": 200}  # lượt AI mỗi ngày theo gói (BR-AI-01/02); người mới = free
AI_TZ_OFFSET_HOURS = 7                       # hạn mức reset 0 giờ giờ Việt Nam
AI_SHORTLIST = 15                            # số quán gửi cho LLM chọn (4.3 bước 3)
AI_PICK_MIN, AI_PICK_MAX = 3, 5              # LLM chọn 3–5 quán (4.3 bước 4)
PLACE_TAGS = CLEAN_DIR / "place_tags.csv"    # nhãn quán do AI gắn (source = ai)
REVIEW_SNIPPET_MAX = 220                     # độ dài tối đa đoạn review đưa vào prompt (chống injection)
# ----- Đăng nhập (server web mở ra Internet qua Cloudflare Tunnel) -----
AUTH_DIR = BASE / "data" / "auth"            # accounts.json + jwt_secret (không chia sẻ thư mục này)
AUTH_REQUIRED = os.environ.get("LOVESPOT_AUTH", "on") != "off"  # tắt chỉ khi chạy thử trên máy, không mở ra ngoài
AUTH_ALLOW_REGISTER = os.environ.get("LOVESPOT_REGISTER", "on") != "off"  # cho người lạ tự đăng ký
AUTH_TOKEN_DAYS = 7
AUTH_MIN_PASSWORD = 8
AUTH_MAX_FAILS, AUTH_LOCK_MINUTES = 5, 15
BACKUP_DIR = Path(os.environ.get("LOVESPOT_BACKUP_DIR", str(BASE / "data" / "backups")))  # nên trỏ sang ổ ngoài / OneDrive
BACKUP_KEEP = 14                             # giữ N bản sao lưu gần nhất

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "auto")  # auto | ollama | anthropic (xem llm.py)
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-5-5")  # dự phòng khi máy yếu / Ollama tắt
ANTHROPIC_MAX_TOKENS = 4096
PLAN_MAX_HOP_KM = 5.0                       # hai chặng liên tiếp cách nhau tối đa (km, đường chim bay)
PLAN_STOPS = [                               # mẫu plan mặc định: (tên chặng, loại quán, phút ở lại)
    ("Ăn tối", ["Nhà hàng", "Quán ăn", "Sang trọng", "Ăn chay"], 90),
    ("Cà phê / tráng miệng", ["Café/Dessert", "Tiệm bánh"], 60),
    ("Đi dạo", "walk", 45),                  # "walk": lấy từ WALK_SPOTS (phố đi bộ, công viên, bờ sông), không phải quán
]
WALK_SPOTS = BASE / "data" / "walk_spots.json"   # địa điểm đi dạo công cộng (tự soạn, sửa tay được)
