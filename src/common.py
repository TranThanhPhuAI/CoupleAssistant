"""Hàm chuẩn hóa dùng chung (giai đoạn 1 và ingest.py giai đoạn 7).

Nguyên tắc: hàm thuần (không đọc/ghi file), chạy được trên từng dòng mới
để quán thêm sau được chuẩn hóa giống hệt dữ liệu ban đầu.
"""
import hashlib
import re
import unicodedata

import numpy as np
import pandas as pd

# ======================= Chuỗi =======================

def nfc(s):
    """Chuẩn Unicode NFC + gộp khoảng trắng. Giữ NaN."""
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return np.nan
    s = unicodedata.normalize("NFC", str(s))
    s = re.sub(r"\s+", " ", s).strip()
    return s if s else np.nan


def fold(s):
    """Bỏ dấu tiếng Việt + chữ thường + bỏ ký tự đặc biệt -> khóa so khớp."""
    s = unicodedata.normalize("NFD", str(s).lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d")
    s = re.sub(r"[^a-z0-9/ ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# ======================= Địa chỉ & ID =======================

# Đoạn địa chỉ bắt đầu bằng đơn vị hành chính -> dừng (chỉ giữ số nhà + tên đường)
_ADMIN = re.compile(r"^\s*(p\.|p\s\d|phường|phuong|quận|quan|q\.|tp\.|tp\s|thành phố|huyện|xã|thị trấn|tt\.)", re.I)


def street_part(address):
    """'84/6 Nguyễn Biểu, P. 1, Quận 5, TP. HCM' -> '84/6 Nguyễn Biểu'.
    Không phụ thuộc tên phường/quận (cũ hay mới sau sáp nhập 2025) nên ID ổn định."""
    if pd.isna(address):
        return ""
    a = re.sub(r"\([^)]*\)", " ", str(address))  # bỏ phần trong ngoặc, vd "(cũ: ...)"
    keep = []
    for seg in a.split(","):
        if _ADMIN.match(seg) and keep:
            break
        keep.append(seg)
    return ", ".join(s.strip() for s in keep)


def name_key(name):
    return fold(name)


def make_restaurant_id(name, address):
    """ID ổn định = hash(tên chuẩn hóa | số nhà + đường chuẩn hóa)."""
    key = f"{fold(name)}|{fold(street_part(address))}"
    return "r_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def make_review_id(restaurant_id, author, date, text):
    key = f"{restaurant_id}|{fold(author) if pd.notna(author) else ''}|{date if pd.notna(date) else ''}|{fold(text)}"
    return "rv_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def parse_city(address):
    """Lấy tỉnh/thành từ địa chỉ dạng '..., TP. Hà Nội (cũ: ...)'."""
    if pd.isna(address):
        return np.nan
    m = re.search(r"TP\.\s*([^,(]+?)\s*(\(|$)", str(address))
    return m.group(1).strip() if m else np.nan


_OLD_DISTRICT = re.compile(r"(Quận\s+[\wÀ-ỹ]+(?:\s+[\wÀ-ỹ]+)?|Huyện\s+[\wÀ-ỹ]+(?:\s+[\wÀ-ỹ]+)?|TP\.\s*Thủ Đức)")


def parse_old_district_ward(address):
    """Từ '(cũ: Phường 6, Quận 3)' -> ('Quận 3', 'Phường 6'). Khớp định dạng bảng quán."""
    if pd.isna(address):
        return np.nan, np.nan
    m = re.search(r"\(cũ:\s*([^)]*)\)", str(address))
    if not m:
        return np.nan, np.nan
    old = m.group(1)
    d = _OLD_DISTRICT.findall(old)
    w = re.search(r"Phường\s+[^,)]+", old)
    district = re.sub(r"\s+", " ", d[-1]).strip() if d else np.nan
    if isinstance(district, str) and district.startswith("TP."):
        district = "TP. Thủ Đức"
    return district, (w.group(0).strip() if w else np.nan)


# ======================= Giá =======================

_AMOUNT = re.compile(r"(\d{1,3}(?:[.,]\d{3})+|\d+)\s*(k\b|K\b|đ|VNĐ|vnđ|VND|vnd)?")


def parse_price_text(text, lo=1_000, hi=20_000_000):
    """'Khoảng 55.000 – 60.000 VNĐ. Quẩy: 5.000 VNĐ' -> (5000, 60000).
    Lấy min/max của mọi số tiền hợp lệ trong chuỗi."""
    if pd.isna(text):
        return np.nan, np.nan
    vals = []
    for num, unit in _AMOUNT.findall(str(text)):
        v = float(re.sub(r"[.,]", "", num))
        if unit and unit.lower() == "k":
            v *= 1000
        if lo <= v <= hi:
            vals.append(v)
    if not vals:
        return np.nan, np.nan
    return min(vals), max(vals)


# ======================= Giờ mở cửa =======================

_HOURS = re.compile(r"(\d{1,2})\s*[:h]\s*(\d{2})\s*[-–—]\s*(\d{1,2})\s*[:h]\s*(\d{2})")


def parse_hours(text):
    """'10:30 - 14:30 | 17:30 - 22:00 (nghỉ rằm)' -> '10:30-14:30|17:30-22:00'."""
    if pd.isna(text):
        return np.nan
    spans = [f"{int(a):02d}:{b}-{int(c):02d}:{d}" for a, b, c, d in _HOURS.findall(str(text))]
    return "|".join(dict.fromkeys(spans)) if spans else np.nan


def _minutes(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def is_open_at(hours, at, stay_minutes=60):
    """Quán có mở cửa từ `at` ("HH:MM") và còn mở thêm ít nhất stay_minutes không?
    hours dạng chuẩn hóa "10:00-14:00|17:00-02:00" (khung qua nửa đêm được hiểu là sang hôm sau).
    Trả về True / False, hoặc None nếu chưa có giờ mở cửa (để xử lý trung tính, không loại quán)."""
    if not isinstance(hours, str) or not hours:
        return None
    t = _minutes(at)
    for span in hours.split("|"):
        o, c = (_minutes(x) for x in span.split("-"))
        if c <= o:  # mở qua nửa đêm
            c += 24 * 60
        for tt in (t, t + 24 * 60):  # giờ hẹn sau nửa đêm thuộc khung của hôm trước
            if o <= tt and tt + stay_minutes <= c:
                return True
    return False


# ======================= Category =======================

PLACE_TYPES = [
    "Quán ăn", "Nhà hàng", "Café/Dessert", "Ăn vặt/vỉa hè", "Tiệm bánh", "Ăn chay",
    "Sang trọng", "Quán nhậu", "Bar/Pub", "Karaoke", "Shop Online", "Giao cơm văn phòng",
]
_PT_KEY = {fold(t): t for t in PLACE_TYPES}

# Hai nhãn "tuyển chọn" xuất hiện trong dữ liệu gốc: giữ lại thành tag, không coi là loại hình
CURATED = {"cafe / date drinks": "date_drinks", "romantic dining / bistro": "romantic_bistro"}

# Suy loại hình từ tên quán (dùng khi không có category / nhãn tuyển chọn)
_NAME_RULES = [
    (r"\b(cafe|coffee|ca phe|caphe|tra sua|milk tea|tea|dessert|che|kem|gelato|smoothie|juice)\b", "Café/Dessert"),
    (r"\b(bakery|banh ngot|cake|tiem banh)\b", "Tiệm bánh"),
    (r"\b(chay|vegetarian|vegan)\b", "Ăn chay"),
    (r"\b(bar|pub|beer|lounge|rooftop)\b", "Bar/Pub"),
    (r"\b(nha hang|restaurant|steak|beefsteak|bistro|buffet|lau|nuong|bbq|pizza|sushi|shabu)\b", "Nhà hàng"),
]


def infer_type_from_name(name):
    f = fold(name)
    for pat, t in _NAME_RULES:
        if re.search(pat, f):
            return t
    return np.nan


def parse_category(raw):
    """'#Quán ăn, # Món Việt' -> (['Quán ăn'], ['Món Việt'], curated_tag)."""
    if pd.isna(raw):
        return [], [], np.nan
    raw = nfc(raw)
    if fold(raw) in {fold(k) for k in CURATED}:
        tag = next(v for k, v in CURATED.items() if fold(k) == fold(raw))
        return [], [], tag
    types, cuisines = [], []
    for part in raw.split(","):
        p = nfc(part.replace("#", ""))
        if not isinstance(p, str):
            continue
        t = _PT_KEY.get(fold(p))
        if t:
            types.append(t)
        else:
            cuisines.append(p)
    return list(dict.fromkeys(types)), list(dict.fromkeys(cuisines)), np.nan


# ======================= Bayesian average =======================

def bayes_avg(v, n, C, m):
    """(n·v + m·C)/(n + m). n=0 hoặc v thiếu -> trả về C (prior)."""
    v = np.where(np.isnan(v), C, v)
    n = np.nan_to_num(n, nan=0.0)
    return (n * v + m * C) / (n + m)
