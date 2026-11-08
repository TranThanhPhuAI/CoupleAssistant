"""Sở thích cá nhân: danh mục, độ khớp quán–sở thích, và điểm "khớp sở thích chung" cho hai người.

Độ khớp (0–1) của mỗi quán với mỗi sở thích được tính từ bằng chứng có thật:
  - từ khóa trong tên / loại quán / món        -> 1.0
  - nhãn khía cạnh AI gắn từ review (place_tags) -> độ tin của nhãn
  - tìm kiếm ngữ nghĩa trên review               -> phân vị độ khớp × 0.5 (chỉ để phân hạng)
Ma trận được cache ở data/clean/place_interests.csv (xây lại: python interests.py).
"""
import re
import sys

import numpy as np
import pandas as pd

import config as cfg
from common import fold

PLACE_INTERESTS = cfg.CLEAN_DIR / "place_interests.csv"
SEMANTIC_MAX = 0.5

# id: (nhãn hiển thị, nhóm, câu tìm ngữ nghĩa, regex từ khóa (đã bỏ dấu) trên tên + loại quán,
#      nhãn món có sẵn trong dữ liệu (cột cuisines), nhãn AI gắn từ review)
CATALOG = {
    "ca_phe":      ("Cà phê", "Món", "quán cà phê ngon", r"\b(cafe|coffee|ca phe|caphe)\b", None, None),
    "tra_sua":     ("Trà sữa / trà trái cây", "Món", "trà sữa trà trái cây ngon",
                    r"\b(tra sua|milk tea|tra trai cay|koi the|gong cha|tocotoco)\b", None, None),
    "lau":         ("Lẩu", "Món", "quán lẩu ngon", r"\b(lau|hotpot|hot pot|shabu)\b", None, None),
    "nuong":       ("Nướng / BBQ", "Món", "đồ nướng BBQ ngon", r"\b(nuong|bbq|grill|gogi)\b", None, None),
    "nhat":        ("Món Nhật / sushi", "Món", "sushi món Nhật Bản", r"\b(sushi|ramen|sashimi|takoyaki)\b",
                    {"Món Nhật"}, None),
    "han":         ("Món Hàn", "Món", "món Hàn Quốc", r"\b(han quoc|korea|tokbokki|kimbap|gogi)\b", {"Món Hàn"}, None),
    "au":          ("Món Âu (steak, pizza, mì Ý)", "Món", "nhà hàng Âu steak pizza mì Ý",
                    r"\b(steak|beefsteak|pizza|pasta|bistro|mi y)\b", {"Ý", "Mỹ", "Pháp", "Món Âu"}, None),
    "thai":        ("Món Thái", "Món", "món Thái chua cay", r"\b(thai lan|lau thai)\b", {"Món Thái"}, None),
    "hoa":         ("Món Hoa / dimsum", "Món", "món Hoa dimsum há cảo", r"\b(dimsum|dim sum|ha cao|mi gia)\b",
                    {"Món Trung Hoa"}, None),
    "viet":        ("Món Việt truyền thống", "Món", "món Việt truyền thống", r"\b(com nieu|com tam|bun bo|pho)\b",
                    {"Món Huế", "Món Bắc", "Món Miền Trung", "Món Miền Nam", "Hà Nội", "Món Quảng"}, None),
    "chay":        ("Ăn chay", "Món", "quán chay ngon", r"\b(chay|vegetarian|vegan|veggie)\b", None, None),
    "hai_san":     ("Hải sản", "Món", "hải sản tươi ngon", r"\b(hai san|seafood|oc|ghe|cua bien)\b", None, None),
    "an_vat":      ("Ăn vặt", "Món", "quán ăn vặt ngon", r"\b(an vat|via he|banh trang|ca vien)\b", None, None),
    "trang_mieng": ("Bánh ngọt / kem / tráng miệng", "Món", "bánh ngọt kem bingsu tráng miệng",
                    r"\b(banh ngot|cake|bakery|kem|bingsu|dessert|tiem banh)\b", None, None),
    "yen_tinh":    ("Yên tĩnh", "Không khí", "quán yên tĩnh để nói chuyện", None, None, "yên tĩnh"),
    "lang_man":    ("Lãng mạn", "Không khí", "không gian lãng mạn hợp hẹn hò", None, None, "lãng mạn"),
    "view_dep":    ("View đẹp", "Không khí", "quán có view đẹp", None, None, "view đẹp"),
    "rieng_tu":    ("Riêng tư", "Không khí", "góc riêng tư kín đáo", None, None, "riêng tư"),
    "khong_gian":  ("Không gian đẹp / decor xinh", "Không khí", "không gian đẹp decor xinh xắn", None, None, "không gian đẹp"),
    "chup_anh":    ("Chụp ảnh / sống ảo", "Không khí", "nhiều góc chụp ảnh sống ảo", None, None, "view đẹp"),
    "soi_dong":    ("Sôi động, vui nhộn", "Không khí", "quán sôi động vui nhộn đông vui", None, None, None),
    "sang_trong":  ("Sang trọng", "Không khí", "nhà hàng sang trọng", r"\b(sang trong|fine dining)\b", None, None),
    "san_vuon":    ("Sân vườn / cây xanh", "Không khí", "sân vườn nhiều cây xanh thoáng mát",
                    r"\b(san vuon|garden)\b", None, None),
    "gia_re":      ("Giá rẻ, bình dân", "Ngân sách", None, None, None, None),
}
LABEL = {k: v[0] for k, v in CATALOG.items()}


def validate_interests(ids):
    """Chỉ giữ id có trong danh mục, bỏ trùng, giữ thứ tự."""
    bad = [i for i in ids if i not in CATALOG]
    if bad:
        raise ValueError(f"Sở thích không có trong danh mục: {bad}")
    return list(dict.fromkeys(ids))


# ======================= Ma trận độ khớp quán–sở thích =======================

def build_matrix(clean_dir=cfg.CLEAN_DIR, index_dir=cfg.INDEX_DIR, save=True):
    """Tính độ khớp 0–1 cho mọi (quán, sở thích). Cần model embedding (~30 giây).
    clean_dir/index_dir đổi được để chạy trên bản sao dữ liệu (ingest sandbox)."""
    from scoring import pct_from_ref
    from semantic import Searcher
    R = pd.read_csv(clean_dir / "restaurants_clean.csv", encoding="utf-8-sig")
    tag_path = clean_dir / cfg.PLACE_TAGS.name
    tags = pd.read_csv(tag_path, encoding="utf-8-sig") if tag_path.exists() else pd.DataFrame(
        columns=["restaurant_id", "tag", "confidence"])
    traits = pd.read_csv(clean_dir / cfg.RESTAURANT_TRAITS.name, encoding="utf-8-sig").set_index("restaurant_id")
    text = (R["name"].fillna("") + " " + R["place_types"].fillna("")).map(fold)
    cuisines = R["cuisines"].fillna("").map(lambda s: {c.strip() for c in s.split(";") if c.strip()})
    s = Searcher(index_dir=index_dir, restaurants_path=clean_dir / "restaurants_clean.csv")
    M = pd.DataFrame({"restaurant_id": R["restaurant_id"]})
    for iid, (_, _, phrase, kw, cuis, tag) in CATALOG.items():
        score = np.zeros(len(R))
        if phrase:
            sem = s.search(phrase, k=10_000, evidence=0).set_index("restaurant_id")["semantic_match"]
            raw = R["restaurant_id"].map(sem).to_numpy(float)
            # tối đa 0.5 < ngưỡng "khớp rõ" 0.6: ngữ nghĩa chỉ phân hạng, "khớp rõ" cần từ khóa / nhãn món / nhãn AI
            score = np.maximum(score, SEMANTIC_MAX * pct_from_ref(np.nan_to_num(raw, nan=np.nanmin(raw)),
                                                                  raw[~np.isnan(raw)]))
        if kw:
            score = np.maximum(score, text.str.contains(kw, regex=True).to_numpy(float))
        if cuis:
            score = np.maximum(score, cuisines.map(lambda c: bool(c & cuis)).to_numpy(float))
        if tag:
            conf = tags[tags["tag"] == tag].set_index("restaurant_id")["confidence"]
            score = np.maximum(score, R["restaurant_id"].map(conf).fillna(0).to_numpy(float))
        if iid == "soi_dong":
            score = np.maximum(score, R["restaurant_id"].map(traits["lively"]).fillna(0.5).to_numpy(float))
        if iid == "gia_re":  # giá càng thấp càng khớp; thiếu giá -> trung tính
            pm = R["price_mid"].to_numpy(float)
            ok = ~np.isnan(pm)
            score = np.full(len(R), 0.5)
            score[ok] = 1 - pct_from_ref(pm[ok], pm[ok])
        M[iid] = np.round(score, 4)
    if save:
        M.to_csv(clean_dir / PLACE_INTERESTS.name, index=False, encoding="utf-8-sig")
    return M


_matrix = None


def load_matrix():
    global _matrix
    if _matrix is None:
        _matrix = (pd.read_csv(PLACE_INTERESTS, encoding="utf-8-sig") if PLACE_INTERESTS.exists()
                   else build_matrix()).set_index("restaurant_id")
    return _matrix


# ======================= Điểm cho cặp đôi =======================

def couple_interest_scores(own_a, own_b, b_shares):
    """Trả về (Series điểm cho A, Series cho B hoặc None, danh sách sở thích CHUNG, ghi chú).

    BR-AI-12: sở thích của B chỉ được dùng khi B bật chia sẻ. Sở thích chung (cả hai cùng chọn)
    được nhân đôi trọng số -> đúng tiêu chí "khớp sở thích chung của hai người"."""
    M = load_matrix()
    notes = []
    usable_b = own_b if b_shares else []
    if own_b and not b_shares:
        notes.append("Người kia chưa bật chia sẻ sở thích -> chỉ dùng sở thích của người hỏi")
    common = [i for i in own_a if i in usable_b]

    def score(own):
        if not own:
            return None
        w = np.array([2.0 if i in common else 1.0 for i in own])
        return pd.Series(M[own].to_numpy() @ w / w.sum(), index=M.index, name="interest_match")

    return score(own_a), score(usable_b), common, notes


def matched_labels(restaurant_id, interest_ids, threshold=0.6, k=3):
    """Sở thích khớp rõ nhất của một quán (để giải thích)."""
    M = load_matrix()
    if restaurant_id not in M.index or not interest_ids:
        return []
    row = M.loc[restaurant_id, interest_ids].sort_values(ascending=False)
    return [LABEL[i] for i, v in row.items() if v >= threshold][:k]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    m = build_matrix()
    print(f"Đã lưu {PLACE_INTERESTS.relative_to(cfg.BASE)}: {len(m)} quán × {len(CATALOG)} sở thích")
    print("Số quán khớp rõ (≥0.6) mỗi sở thích:",
          {LABEL[c]: int((m[c] >= 0.6).sum()) for c in CATALOG})
