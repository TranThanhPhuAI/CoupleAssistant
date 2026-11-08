"""Giai đoạn 4: xếp hạng xác định (deterministic) cho một cặp đôi.

    lọc cứng -> (có câu hỏi) top-N ngữ nghĩa -> ngưỡng couple (hạ dần) -> TOPSIS từng người
    -> gộp: 0.5·trung bình + 0.5·min

Dùng:
    from ranker import Person, rank_for_couple
    a = Person("An", location=(10.7769, 106.7009), budget_max=300_000, weights={"semantic_match": 0.4})
    b = Person("Bình", location=(10.8494, 106.7537))
    rank_for_couple(a, b, query="ăn tối lãng mạn", k=10)
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

import config as cfg
from common import is_open_at
from scoring import apply_threshold


@dataclass
class Person:
    name: str
    location: tuple | None = None      # (lat, lon)
    budget_max: float | None = None    # VNĐ/người
    weights: dict = field(default_factory=dict)  # ghi đè một phần DEFAULT_WEIGHTS
    personality: dict | None = None    # GĐ5

    def full_weights(self):
        w = {**cfg.DEFAULT_WEIGHTS, **self.weights}
        s = sum(w.values())
        return {k: v / s for k, v in w.items()}


# ======================= Tiêu chí =======================

def haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


def price_fit(price_min, price_max, budget):
    """Tỉ lệ khoảng giá của quán nằm trong ngân sách: 1 = cả thực đơn vừa túi, 0 = món rẻ nhất đã vượt.
    Thiếu giá hoặc không có ngân sách -> NaN (trung tính)."""
    if budget is None:
        return np.full(len(price_min), np.nan)
    lo, hi = np.asarray(price_min, float), np.asarray(price_max, float)
    span = np.where(hi > lo, hi - lo, 1.0)
    fit = np.clip((budget - lo) / span, 0, 1)
    fit = np.where(hi <= budget, 1.0, fit)
    return np.where(np.isnan(lo), np.nan, fit)


def shared_budget(a, b):
    """Ngân sách chung của đôi = mức thấp hơn trong hai người (không ai phải chi quá sức)."""
    vals = [x for x in (a.budget_max, b.budget_max) if x is not None]
    return min(vals) if vals else None


# ======================= TOPSIS =======================

def topsis(X, weights, kinds):
    """X: DataFrame tiêu chí (NaN được điền trung vị cột = trung tính).
    Tiêu chí toàn NaN hoặc hằng số bị bỏ qua (không phân biệt được ứng viên).
    Trả về (closeness 0-1, trọng số thực dùng)."""
    X = X.astype(float).copy()
    used = {}
    for c in X.columns:
        col = X[c]
        if col.isna().all() or weights.get(c, 0) <= 0:
            continue
        X[c] = col.fillna(col.median())
        if X[c].nunique() > 1:
            used[c] = weights[c]
    if not used:
        return np.full(len(X), 0.5), {}
    s = sum(used.values())
    used = {c: w / s for c, w in used.items()}
    cols = list(used)
    # Min-max về [0,1] trước: chuẩn hóa vector thuần "bóp" tiêu chí biên độ hẹp (vd semantic_match 0.55-0.65)
    # làm mọi ứng viên gần như bằng nhau -> trọng số của tiêu chí đó mất tác dụng.
    M = X[cols].to_numpy()
    lo, hi = M.min(axis=0), M.max(axis=0)
    M = (M - lo) / np.where(hi > lo, hi - lo, 1.0)
    norm = np.linalg.norm(M, axis=0)
    V = M / np.where(norm == 0, 1, norm) * np.array([used[c] for c in cols])
    benefit = np.array([kinds[c] == "benefit" for c in cols])
    best = np.where(benefit, V.max(axis=0), V.min(axis=0))
    worst = np.where(benefit, V.min(axis=0), V.max(axis=0))
    d_best = np.linalg.norm(V - best, axis=1)
    d_worst = np.linalg.norm(V - worst, axis=1)
    denom = d_best + d_worst
    return np.where(denom == 0, 0.5, d_worst / np.where(denom == 0, 1, denom)), used


# ======================= Xếp hạng cho cặp đôi =======================

_cache = {}


def new_restaurant_bonus(df, today=None):
    """Cold-start: quán nhập trong NEW_RESTAURANT_DAYS ngày được cộng tối đa NEW_RESTAURANT_BONUS vào couple_score,
    giảm tuyến tính về 0 khi số review đạt m (lúc đó Bayes đã đủ tin cậy)."""
    if "first_seen" not in df.columns:
        return np.zeros(len(df))
    today = pd.Timestamp(today or pd.Timestamp.now().normalize())
    age = (today - pd.to_datetime(df["first_seen"], errors="coerce")).dt.days
    fresh = age.between(0, cfg.NEW_RESTAURANT_DAYS)
    shrink = np.clip(1 - df["rating_n"].fillna(0) / cfg.BAYES_M, 0, 1)
    return np.where(fresh, cfg.NEW_RESTAURANT_BONUS * shrink, 0.0)


def load_candidates():
    if "base" not in _cache:
        R = pd.read_csv(cfg.RESTAURANTS_CLEAN, encoding="utf-8-sig")
        S = pd.read_csv(cfg.SCORES, encoding="utf-8-sig")
        base = R.merge(S[["restaurant_id", "food_score", "date_score", "couple_score"]], on="restaurant_id", how="left")
        base["image_score"] = np.nan  # GĐ10
        base["bookable"] = np.nan     # 1/0 khi backend có dữ liệu Shop đã duyệt (BR-AI-13); trống -> bỏ qua tiêu chí
        base["new_bonus"] = new_restaurant_bonus(base)
        base["couple_score"] = (base["couple_score"] + base["new_bonus"]).clip(upper=1.0)
        _cache["base"] = base
    return _cache["base"].copy()


RELAX_STEPS = [  # nới dần khi không quán nào qua lọc cứng (Lovespot 4.7) — mỗi bước giữ các bước trước
    ("budget", "nới ngân sách thêm 50%"),
    ("districts", "mở rộng ra mọi quận"),
    ("time", "bỏ điều kiện đang mở cửa vào giờ hẹn"),
]


def hard_filter(C, budget, districts, place_types, at_time, stay_minutes, relaxed=()):
    """Lọc cứng; dữ liệu thiếu (quận/giá/giờ mở cửa) -> giữ lại (trung tính)."""
    if districts and "districts" not in relaxed:
        C = C[C["district"].isna() | C["district"].isin(districts)]
    if place_types:
        C = C[C["place_type"].isin(place_types)]
    if budget is not None:
        b = budget * (1.5 if "budget" in relaxed else 1.0)
        C = C[C["price_min"].isna() | (C["price_min"] <= b)]
    if at_time and "time" not in relaxed:
        st = C["opening_hours"].map(lambda h: is_open_at(h, at_time, stay_minutes))
        C = C[st.isna() | (st == True)].assign(open_known=st.notna())  # noqa: E712
    return C


def rank_for_couple(a, b, query=None, k=10, districts=None, place_types=None,
                    personality_fit=None, interest_fit=None, at_time=None, stay_minutes=60,
                    mean_weight=cfg.GROUP_MEAN_WEIGHT):
    """personality_fit / interest_fit: tùy chọn, dict {tên người: Series theo restaurant_id}.
    at_time: "HH:MM" -> chỉ giữ quán đang mở cửa (còn mở thêm stay_minutes phút)."""
    C0 = load_candidates()
    budget = shared_budget(a, b)
    log = {"n_all": len(C0), "relaxed": []}

    # 1) Lọc cứng; không còn quán nào -> nới dần và ghi lại đã nới gì
    relaxed = []
    C = hard_filter(C0, budget, districts, place_types, at_time, stay_minutes)
    for key, msg in RELAX_STEPS:
        if len(C):
            break
        relaxed.append(key)
        log["relaxed"].append(msg)
        C = hard_filter(C0, budget, districts, place_types, at_time, stay_minutes, relaxed)
    log["n_after_filters"] = len(C)

    # 2) Ngữ nghĩa: chỉ giữ top-N liên quan tới câu hỏi
    C["semantic_match"] = np.nan
    evidence = {}
    if query:
        from semantic import search
        sem = search(query, k=10_000, evidence=3)
        sem = sem[sem["restaurant_id"].isin(C["restaurant_id"])].head(cfg.SEMANTIC_PRESELECT)
        C = C.merge(sem[["restaurant_id", "semantic_match"]], on="restaurant_id", suffixes=("_x", ""))
        C = C.drop(columns="semantic_match_x")
        evidence = dict(zip(sem["restaurant_id"], sem["evidence"]))
    log["n_after_semantic"] = len(C)

    # 3) Ngưỡng couple trên tập ứng viên (hạ dần nếu ít quán qua)
    C = apply_threshold(C, min_pass=cfg.RANK_MIN_PASS)
    log["thresholds"] = C.attrs["thresholds"]
    keep = C["couple_pass"].copy()
    if query:  # luôn giữ vài quán khớp câu hỏi nhất dù chưa qua ngưỡng -> gắn nhãn đánh đổi
        top_sem = C.nlargest(cfg.SEMANTIC_ALWAYS_KEEP, "semantic_match").index
        extra = top_sem[~keep.loc[top_sem]]
        C.loc[extra, "tradeoff_label"] = "đúng yêu cầu, không gian hẹn hò chưa nổi bật"
        keep.loc[top_sem] = True
        log["n_kept_by_relevance"] = len(extra)
    C = C[keep].copy()
    log["n_candidates"] = len(C)

    # 4) TOPSIS cho từng người
    C["price_fit"] = price_fit(C["price_min"], C["price_max"], budget)
    used_w = {}
    for p in (a, b):
        X = C.reindex(columns=list(cfg.TOPSIS_CRITERIA))  # cột chưa có -> NaN, được điền dưới đây
        if p.location is not None:
            X["distance_km"] = haversine_km(p.location[0], p.location[1], C["latitude"], C["longitude"])
        else:
            X["distance_km"] = np.nan
        X["personality_fit"] = (C["restaurant_id"].map(personality_fit[p.name])
                                if personality_fit and p.name in personality_fit else np.nan)
        X["interest_match"] = (C["restaurant_id"].map(interest_fit[p.name])
                               if interest_fit and interest_fit.get(p.name) is not None else np.nan)
        C[f"dist_{p.name}"] = X["distance_km"].to_numpy()
        C[f"pfit_{p.name}"] = X["personality_fit"].to_numpy()
        C[f"ifit_{p.name}"] = X["interest_match"].to_numpy()
        C[f"topsis_{p.name}"], used_w[p.name] = topsis(X, p.full_weights(), cfg.TOPSIS_CRITERIA)

    # 5) Gộp: trung bình + least-misery
    ta, tb = C[f"topsis_{a.name}"], C[f"topsis_{b.name}"]
    C["group_mean"] = (ta + tb) / 2
    C["group_min"] = np.minimum(ta, tb)
    C["group_score"] = mean_weight * C["group_mean"] + (1 - mean_weight) * C["group_min"]
    C = C.sort_values(["group_score", "restaurant_id"], ascending=[False, True]).head(k).reset_index(drop=True)
    C["evidence"] = C["restaurant_id"].map(evidence)
    C.attrs.update(log=log, weights=used_w, budget=budget)
    return C
