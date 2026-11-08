"""Giai đoạn 6a: câu hỏi tự nhiên -> tiêu chí + trọng số từng người (JSON đã kiểm tra).

Phần CỨNG (quận, ngân sách) trích bằng luật -> xác định, không bịa.
Phần MỀM (câu tìm kiếm ngữ nghĩa, mức quan tâm từng người) do LLM trích, có schema + kiểm tra;
LLM lỗi -> vẫn trả kết quả từ luật (trọng số mặc định).
"""
import re

import pandas as pd

import config as cfg
from common import fold

# ======================= Luật: quận =======================

def _district_aliases():
    R = pd.read_csv(cfg.RESTAURANTS_CLEAN, encoding="utf-8-sig", usecols=["district"])
    aliases = {}
    for d in R["district"].dropna().unique():
        name = re.sub(r"^(Quận|Huyện|TP\.)\s*", "", d)
        if not name.isdigit():
            aliases[fold(name)] = d          # "binh thanh" -> "Quận Bình Thạnh"
    return aliases, set(R["district"].dropna())


_ALIASES, _DISTRICTS = None, None


def parse_districts(text):
    global _ALIASES, _DISTRICTS
    if _ALIASES is None:
        _ALIASES, _DISTRICTS = _district_aliases()
    f = fold(text)
    found = [f"Quận {int(n)}" for n in re.findall(r"\b(?:quan|q)\s*\.?\s*(\d{1,2})\b", f)]
    found += [d for a, d in _ALIASES.items() if re.search(rf"\b{re.escape(a)}\b", f)]
    return [d for d in dict.fromkeys(found) if d in _DISTRICTS]


# ======================= Luật: ngân sách =======================

# Số có dấu phân cách nghìn (300.000) hoặc thập phân (1,5) + đơn vị; "ngân sách" không phải đơn vị "ngàn"
_MONEY = re.compile(r"(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)\s*(k|nghin|ngan(?!\s*sach)|trieu|tr|cu|d|vnd|dong)\b")
_UNIT = {"k": 1e3, "nghin": 1e3, "ngan": 1e3, "tr": 1e6, "trieu": 1e6, "cu": 1e6, "d": 1, "vnd": 1, "dong": 1}


def _fold_keep_punct(s):
    """Bỏ dấu tiếng Việt, chữ thường, GIỮ dấu chấm/phẩy (để đọc 300.000đ)."""
    import unicodedata
    s = unicodedata.normalize("NFD", str(s).lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")


def _to_number(n):
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", n):
        return float(re.sub(r"[.,]", "", n))
    return float(n.replace(",", "."))


def parse_budget(text):
    """Trả về (ngân sách VNĐ/người hoặc None, phạm vi 'per_person'|'total'|'unspecified')."""
    f = _fold_keep_punct(text)
    amounts = [(_to_number(n) * _UNIT[u], m.end()) for m in _MONEY.finditer(f) for n, u in [m.groups()]]
    amounts = [(v, e) for v, e in amounts if 10_000 <= v <= 50_000_000]
    if not amounts:
        return None, None
    value, end = amounts[-1]
    tail = f[end:end + 25]
    if re.search(r"(/|mot|moi|1)\s*(nguoi|ng)\b", tail) or re.search(r"\b(moi|1) nguoi\b", f):
        return value, "per_person"
    if re.search(r"\b(2|hai) (nguoi|dua)\b|\bca hai\b|\bca 2\b|\bcho 2\b|\bcho hai\b", f):
        return value / 2, "total"
    # Không nói rõ: giả định là tổng cho cả buổi của 2 người (cấu hình được)
    if cfg.BUDGET_UNSPECIFIED_SCOPE == "total":
        return value / 2, "unspecified"
    return value, "unspecified"


# ======================= Luật: giờ hẹn =======================

_PART_OF_DAY = {"sang": (8, "08:00"), "trua": (12, "12:00"), "chieu": (15, "15:00"),
                "toi": (19, "19:00"), "khuya": (22, "22:00")}


def parse_time(text):
    """'19h30' / '7 giờ tối' / '19:00' / 'tối nay' -> 'HH:MM'; không nhắc giờ -> None."""
    f = _fold_keep_punct(text)
    m = re.search(r"\b(\d{1,2})\s*(?:h|:|gio)\s*(\d{2})?\b(?:\s*(sang|trua|chieu|toi|dem|khuya))?", f)
    if m:
        h, mm, part = int(m.group(1)), int(m.group(2) or 0), m.group(3)
        if part in {"chieu", "toi", "dem"} and h < 12:
            h += 12
        if 0 <= h <= 23 and 0 <= mm <= 59:
            return f"{h:02d}:{mm:02d}"
    for word, (_, hhmm) in _PART_OF_DAY.items():
        if re.search(rf"\b(buoi )?{word}\b", f):
            return hhmm
    return None


def strip_hard_constraints(text):
    """Bỏ cụm quận/giá khỏi câu để làm câu tìm kiếm ngữ nghĩa dự phòng."""
    t = re.sub(r"(?i)\b(dưới|tối đa|không quá|khoảng|tầm|giá)?\s*\d+(?:[.,]\d+)?\s*(k|nghìn|ngàn|tr|triệu|củ|đ|vnđ|đồng)\b(\s*/\s*người)?", " ", text)
    t = re.sub(r"(?i)\b(ở|tại|khu|gần)?\s*(quận|q\.?)\s*\d{1,2}\b", " ", t)
    global _ALIASES
    if _ALIASES is None:
        parse_districts("")
    for d in set(_ALIASES.values()):  # tên quận dạng chữ: "Bình Thạnh", "Quận Bình Thạnh", "TP. Thủ Đức"
        short = re.sub(r"^(Quận|Huyện|TP\.)\s*", "", d)
        t = re.sub(rf"(?i)\b(ở|tại|khu|gần)?\s*((quận|huyện|tp\.?)\s*)?{re.escape(short)}\b", " ", t)
    t = re.sub(r"(?i)\b(cho|của)\s+(2|hai)\s+(người|đứa)\b|\bcả hai\b|\b(mỗi|một|1)\s+người\b|/\s*người", " ", t)
    t = re.sub(r"(?i)\b(lúc|vào)?\s*\d{1,2}\s*(h|giờ|:)\s*(\d{2})?\b(\s*(sáng|trưa|chiều|tối|đêm|khuya))?", " ", t)
    t = re.sub(r"(?i)\s+(hoặc|và|hay)\s*(?=[,.]|$)", " ", t)   # "Quận 3 hoặc Quận 1" -> bỏ liên từ còn sót
    t = re.sub(r"\s+([,.])", r"\1", t)
    t = re.sub(r"([,.])\s*[,.]+", r"\1", t)
    return re.sub(r"\s+", " ", t).strip(" ,.")


# ======================= LLM: phần mềm =======================

IMPORTANCE_KEYS = ["food", "date_vibe", "relevance", "price", "distance"]
_IMP = {"type": "object", "properties": {k: {"type": "integer", "minimum": 0, "maximum": 5} for k in IMPORTANCE_KEYS},
        "required": IMPORTANCE_KEYS}
SCHEMA = {"type": "object",
          "properties": {"semantic_query": {"type": "string"}, "person_a": _IMP, "person_b": _IMP},
          "required": ["semantic_query", "person_a", "person_b"]}

SYSTEM = (
    "Bạn trích tiêu chí tìm quán hẹn hò ở TP.HCM từ câu hỏi tiếng Việt của một cặp đôi. Trả về JSON:\n"
    "- semantic_query: câu ngắn mô tả quán mong muốn (món, không khí, dịp). BỎ tên quận và số tiền.\n"
    "- person_a (người đang nói, 'tôi/mình/em/anh') và person_b (người yêu/bạn đi cùng): mức quan tâm 0-5 cho\n"
    "  food (đồ ăn ngon), date_vibe (không gian lãng mạn/hợp hẹn hò), relevance (đúng loại quán/món đã hỏi),\n"
    "  price (giá rẻ/vừa túi), distance (gần). Không nhắc tới -> 3. Nhấn mạnh -> 4-5. Nói không quan trọng -> 0-1.\n"
    "  Nếu câu không phân biệt hai người, cho hai người giống nhau. Không bịa thêm yêu cầu."
)


def _validate_llm(obj):
    if not isinstance(obj, dict) or not str(obj.get("semantic_query", "")).strip():
        raise ValueError("thiếu semantic_query")
    out = {"semantic_query": str(obj["semantic_query"]).strip()[:200]}
    for p in ("person_a", "person_b"):
        imp = obj.get(p) or {}
        out[p] = {k: int(min(5, max(0, int(imp.get(k, 3))))) for k in IMPORTANCE_KEYS}
    return out


def importance_to_weights(imp):
    """Mức quan tâm 0-5 -> nhân với trọng số mặc định (3 = giữ nguyên)."""
    d = cfg.DEFAULT_WEIGHTS
    return {"couple_score": d["couple_score"] * (imp["food"] + imp["date_vibe"]) / 6,
            "semantic_match": d["semantic_match"] * imp["relevance"] / 3,
            "price_fit": d["price_fit"] * imp["price"] / 3,
            "distance_km": d["distance_km"] * imp["distance"] / 3}


def parse_query(text, use_llm=True):
    budget, scope = parse_budget(text)
    res = {"raw": text, "districts": parse_districts(text), "budget_per_person": budget, "budget_scope": scope,
           "semantic_query": strip_hard_constraints(text) or text,
           "time": parse_time(text), "weights_a": {}, "weights_b": {}, "llm_ok": False, "assumptions": []}
    if scope == "unspecified":
        res["assumptions"].append(f"Ngân sách không nói rõ cho 1 hay 2 người -> hiểu là tổng cho 2 người "
                                  f"({budget:,.0f}đ/người)")
    if use_llm:
        try:
            from llm import llm_json
            out = _validate_llm(llm_json([{"role": "system", "content": SYSTEM},
                                             {"role": "user", "content": text}], SCHEMA, timeout=120))
            res.update(semantic_query=out["semantic_query"], importance_a=out["person_a"],
                       importance_b=out["person_b"], weights_a=importance_to_weights(out["person_a"]),
                       weights_b=importance_to_weights(out["person_b"]), llm_ok=True)
        except Exception as e:  # LLM không chạy/không hợp lệ -> dùng luật + trọng số mặc định
            res["assumptions"].append(f"LLM không trích được ({type(e).__name__}) -> dùng luật + trọng số mặc định")
    return res
