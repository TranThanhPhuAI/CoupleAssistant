"""Danh mục dùng chung với Couple Assistant: 24 sở thích (chép lại, để hai bên độc lập) và danh sách quán (chỉ đọc CSV)."""
import csv
import unicodedata
from functools import lru_cache

from . import config as cfg

# Cùng mã với src/interests.py của Couple Assistant -> sau này nối hai hệ thống không phải đổi dữ liệu
INTERESTS = {
    "ca_phe": ("Cà phê", "Món"), "tra_sua": ("Trà sữa / trà trái cây", "Món"), "lau": ("Lẩu", "Món"),
    "nuong": ("Nướng / BBQ", "Món"), "nhat": ("Món Nhật / sushi", "Món"), "han": ("Món Hàn", "Món"),
    "au": ("Món Âu (steak, pizza, mì Ý)", "Món"), "thai": ("Món Thái", "Món"), "hoa": ("Món Hoa / dimsum", "Món"),
    "viet": ("Món Việt truyền thống", "Món"), "chay": ("Ăn chay", "Món"), "hai_san": ("Hải sản", "Món"),
    "an_vat": ("Ăn vặt", "Món"), "trang_mieng": ("Bánh ngọt / kem / tráng miệng", "Món"),
    "yen_tinh": ("Yên tĩnh", "Không khí"), "lang_man": ("Lãng mạn", "Không khí"), "view_dep": ("View đẹp", "Không khí"),
    "rieng_tu": ("Riêng tư", "Không khí"), "khong_gian": ("Không gian đẹp / decor xinh", "Không khí"),
    "chup_anh": ("Chụp ảnh / sống ảo", "Không khí"), "soi_dong": ("Sôi động, vui nhộn", "Không khí"),
    "sang_trong": ("Sang trọng", "Không khí"), "san_vuon": ("Sân vườn / cây xanh", "Không khí"),
    "gia_re": ("Giá rẻ, bình dân", "Ngân sách"),
}


def fold(s):
    """Bỏ dấu + chữ thường để tìm kiếm: 'Quận Bình Thạnh' -> 'quan binh thanh'."""
    s = unicodedata.normalize("NFD", s or "").replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def _num(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


@lru_cache(maxsize=1)
def places():
    """{restaurant_id: {...}} — đọc một lần. Thiếu file thì trả rỗng (mạng xã hội vẫn chạy, chỉ không gắn được quán)."""
    out = {}
    if not cfg.PLACES_CSV.exists():
        return out
    with open(cfg.PLACES_CSV, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            out[r["restaurant_id"]] = {
                "id": r["restaurant_id"], "name": r["name"], "district": r.get("district") or "",
                "address": r.get("address") or "", "type": r.get("place_type") or "",
                "price_min": _num(r.get("price_min")), "price_max": _num(r.get("price_max")),
                "opening_hours": r.get("opening_hours") or None,
                "rating": round(float(r["bayes_rating"]), 1) if r.get("bayes_rating") else None,
                "_key": fold(f"{r['name']} {r.get('district', '')} {r.get('address', '')}"),
            }
    return out


def place_public(p):
    return {k: v for k, v in p.items() if not k.startswith("_")} if p else None


def search_places(q, limit=8, district=None):
    words = fold(q).split()
    hits = [p for p in places().values()
            if all(w in p["_key"] for w in words) and (not district or p["district"] == district)]
    hits.sort(key=lambda p: (-(p["rating"] or 0), p["name"]))
    return [place_public(p) for p in hits[:limit]]
