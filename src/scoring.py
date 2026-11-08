"""Hàm tính điểm dùng chung (giai đoạn 3, 4, 7): chuẩn hóa phân vị theo phân phối tham chiếu,
làm mượt Bayes cho khía cạnh, couple_score có ngưỡng + hạ ngưỡng dần."""
import numpy as np
import pandas as pd

import config as cfg


def pct_from_ref(x, ref):
    """Phân vị của x trong phân phối tham chiếu ref (0-1). Quán mới dùng chung ref -> không phải tính lại cả bảng."""
    # Làm tròn 6 chữ số: nhiều quán có điểm TRÙNG nhau (bằng prior) -> sai số float cỡ 1e-12 không được làm nhảy phân vị
    ref = np.sort(np.round(np.asarray(ref, dtype=float), 6))
    x = np.round(np.asarray(x, dtype=float), 6)
    lo = np.searchsorted(ref, x, side="left")
    hi = np.searchsorted(ref, x, side="right")
    return (lo + hi) / 2 / len(ref)


def smoothed_ratio(pos, neg, mu, alpha):
    """Tỉ lệ khen trong số lần nhắc tới, làm mượt về mu (dùng cho món ăn, phục vụ, giá)."""
    return (pos + alpha * mu) / (pos + neg + alpha)


def smoothed_net_rate(pos, neg, n, mu, alpha):
    """(khen - chê)/số review, làm mượt về mu (dùng cho khía cạnh hẹn hò: hiếm khi được nhắc,
    nên quán được NHIỀU review khen mới nổi bật)."""
    return (pos - neg + alpha * mu) / (n + alpha)


def couple_scores(food, date, w=cfg.COUPLE_W):
    """Trung bình nhân có trọng số: một trong hai thấp thì kéo cả điểm xuống."""
    eps = 1e-6
    return np.power(np.clip(food, eps, 1), w) * np.power(np.clip(date, eps, 1), 1 - w)


ASPECT_KEYS = ["food", "ambience", "quiet", "romantic", "view", "privacy", "service", "price"]
RATIO_ASPECTS = ["food", "service", "price"]


def score_restaurants(R, aspects, reference=None):
    """Điểm khía cạnh -> food_score, date_score, couple_score cho mọi quán trong R.

    aspects: xác suất khía cạnh mức review (review_id, restaurant_id, <aspect>_pos/_neg).
    reference=None -> tính lại prior/z/phân phối tham chiếu từ dữ liệu (stage3_scores, chạy theo lịch).
    reference cho trước -> GIỮ NGUYÊN tham số cũ, chỉ chấm điểm (ingest quán mới: không làm xê dịch quán cũ).
    Trả về (S, reference)."""
    cnt = aspects.copy()
    for a in ASPECT_KEYS:
        for p in ("pos", "neg"):
            c = f"{a}_{p}"
            cnt[c] = cnt[c].where(cnt[c] >= cfg.ASPECT_MIN_PROB, 0.0)  # chỉ đếm review chắc chắn
    agg = cnt.groupby("restaurant_id").agg(n_absa=("review_id", "size"),
                                           **{f"{a}_{p}": (f"{a}_{p}", "sum") for a in ASPECT_KEYS for p in ("pos", "neg")})
    S = R[["restaurant_id", "name", "district", "place_type", "price_min", "price_max", "bayes_rating",
           "rating_suspect", "rating_n"]].merge(agg, on="restaurant_id", how="left").fillna({c: 0 for c in agg.columns})
    fresh = reference is None
    ref = {} if fresh else reference["ref"]
    priors = {} if fresh else reference["priors"]
    zstats = {} if fresh else reference["zstats"]
    if fresh:
        alpha = {a: cfg.ASPECT_PRIOR_STRENGTH if a in RATIO_ASPECTS else cfg.ASPECT_PRIOR_STRENGTH_DATE
                 for a in ASPECT_KEYS}
    else:
        alpha = reference["alpha"]
        alpha = alpha if isinstance(alpha, dict) else {a: alpha for a in ASPECT_KEYS}  # tham chiếu cũ: 1 số

    for a in ASPECT_KEYS:
        P, N, n = S[f"{a}_pos"], S[f"{a}_neg"], S["n_absa"]
        if fresh:
            priors[a] = float(P.sum() / (P.sum() + N.sum()) if a in RATIO_ASPECTS else (P.sum() - N.sum()) / n.sum())
        mu = priors[a]
        S[f"{a}_raw"] = (smoothed_ratio(P, N, mu, alpha[a]) if a in RATIO_ASPECTS
                         else smoothed_net_rate(P, N, n, mu, alpha[a]))
        if fresh:
            ref[a] = S[f"{a}_raw"].tolist()
        S[f"{a}_pct"] = pct_from_ref(S[f"{a}_raw"], ref[a])

    if fresh:
        ref["bayes_rating"] = S["bayes_rating"].tolist()
    S["food_raw"] = (cfg.FOOD_RATING_WEIGHT * pct_from_ref(S["bayes_rating"], ref["bayes_rating"])
                     + (1 - cfg.FOOD_RATING_WEIGHT) * S["food_pct"])
    # Khía cạnh hẹn hò: z-score (cắt ±3) thay vì phân vị (đa số quán không được nhắc -> phân vị khuếch đại nhiễu)
    for a in cfg.DATE_WEIGHTS:
        if fresh:
            zstats[a] = (float(S[f"{a}_raw"].mean()), float(S[f"{a}_raw"].std()))
        mu_a, sd_a = zstats[a]
        S[f"{a}_z"] = ((S[f"{a}_raw"] - mu_a) / sd_a).clip(-3, 3)
    S["date_raw"] = sum(w * S[f"{a}_z"] for a, w in cfg.DATE_WEIGHTS.items())
    if fresh:
        ref["food_raw"], ref["date_raw"] = S["food_raw"].tolist(), S["date_raw"].tolist()
    S["food_score"] = pct_from_ref(S["food_raw"], ref["food_raw"])
    S["date_score"] = pct_from_ref(S["date_raw"], ref["date_raw"])
    S["couple_score"] = couple_scores(S["food_score"], S["date_score"])
    S = apply_threshold(S)
    reference = {"priors": priors, "alpha": alpha, "date_weights": cfg.DATE_WEIGHTS, "zstats": zstats, "ref": ref}
    return S, reference


# Nhãn quán do AI gắn từ review (bảng place_tags, source = ai). (khía cạnh, nhãn, điều kiện)
_TAG_RULES = [("ambience", "không gian đẹp"), ("romantic", "lãng mạn"), ("quiet", "yên tĩnh"),
              ("view", "view đẹp"), ("privacy", "riêng tư")]
_TAG_PCT_RULES = [("food", "món ngon"), ("service", "phục vụ tốt"), ("price", "giá hợp lý")]


def derive_tags(S, z_min=1.0, pct_min=0.8, min_support=2, min_reviews=5):
    """Nhãn có bằng chứng: khía cạnh hẹn hò cần z ≥ z_min VÀ ≥ min_support review khen;
    món/phục vụ/giá cần phân vị ≥ pct_min trên quán có ≥ min_reviews review.
    confidence 0.5–1.0 tăng theo độ mạnh của bằng chứng. Thêm nhãn tiêu cực 'ồn ào' để giải thích trung thực."""
    rows = []
    for a, tag in _TAG_RULES:
        ok = (S[f"{a}_z"] >= z_min) & (S[f"{a}_pos"] >= min_support)
        for rid, z, sup in S.loc[ok, ["restaurant_id", f"{a}_z", f"{a}_pos"]].itertuples(index=False):
            rows.append((rid, tag, round(min(1.0, 0.5 + z / 6), 3), int(round(sup))))
    for a, tag in _TAG_PCT_RULES:
        ok = (S[f"{a}_pct"] >= pct_min) & (S["n_absa"] >= min_reviews)
        for rid, p, sup in S.loc[ok, ["restaurant_id", f"{a}_pct", f"{a}_pos"]].itertuples(index=False):
            rows.append((rid, tag, round(min(1.0, 0.5 + (p - pct_min) / (1 - pct_min) / 2), 3), int(round(sup))))
    loud = (S["quiet_z"] <= -1.5) & (S["quiet_neg"] >= min_support)
    for rid, z, sup in S.loc[loud, ["restaurant_id", "quiet_z", "quiet_neg"]].itertuples(index=False):
        rows.append((rid, "ồn ào", round(min(1.0, 0.5 - z / 6), 3), int(round(sup))))
    return pd.DataFrame(rows, columns=["restaurant_id", "tag", "confidence", "support"]).assign(source="ai")


SCORE_COLS = (["restaurant_id", "n_absa"] + [f"{a}_{p}" for a in ASPECT_KEYS for p in ("pos", "neg")]
              + [f"{a}_raw" for a in ASPECT_KEYS] + [f"{a}_pct" for a in ASPECT_KEYS]
              + [f"{a}_z" for a in cfg.DATE_WEIGHTS]
              + ["food_raw", "date_raw", "food_score", "date_score", "couple_score", "couple_pass", "tradeoff_label"])


def apply_threshold(df, food_min=cfg.COUPLE_FOOD_MIN, date_min=cfg.COUPLE_DATE_MIN,
                    min_pass=cfg.COUPLE_MIN_PASS, step=cfg.COUPLE_RELAX_STEP):
    """Gắn couple_pass + nhãn đánh đổi. Nếu ít hơn min_pass quán qua ngưỡng (vd sau khi lọc quận/giá)
    thì hạ cả hai ngưỡng từng bước `step`; quán qua ở ngưỡng đã hạ được ghi chú."""
    df = df.copy()
    f0, d0 = food_min, date_min
    f, d = f0, d0
    while True:
        ok = (df["food_score"] >= f) & (df["date_score"] >= d)
        if ok.sum() >= min(min_pass, len(df)) or (f <= 0 and d <= 0):
            break
        f, d = max(f - step, 0), max(d - step, 0)
    strict = (df["food_score"] >= f0) & (df["date_score"] >= d0)
    df["couple_pass"] = ok
    df["tradeoff_label"] = np.select(
        [strict, ok & ~strict,
         (df["food_score"] >= f) & (df["date_score"] < d),
         (df["date_score"] >= d) & (df["food_score"] < f)],
        ["vừa ngon vừa hợp hẹn hò", "đạt ở ngưỡng đã hạ (đánh đổi nhẹ)",
         "ngon, không gian hẹn hò chưa nổi bật", "hợp hẹn hò, món ăn ở mức khá"],
        default="chưa nổi bật")
    df.attrs["thresholds"] = (round(f, 2), round(d, 2))
    return df
