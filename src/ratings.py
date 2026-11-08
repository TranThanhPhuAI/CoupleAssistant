"""Tính rating quán (dùng chung cho stage1_clean.py và ingest.py):
giới hạn N review/quán/ngày, cờ nghi seeding, 3 bậc nguồn rating, Bayesian average."""
import numpy as np
import pandas as pd

import config as cfg
from common import bayes_avg

STAT_COLS = ["n_reviews", "n_rated_raw", "rating_mean_raw", "n_rated", "rating_mean", "rating_std",
             "last_review_date", "rating_suspect", "rating_source", "rating_v", "rating_n", "bayes_rating"]


def compute_rating_stats(R, rev, C=None, m=cfg.BAYES_M):
    """R: bảng quán (cần restaurant_id, source_rating, source_review_count).
    rev: review (restaurant_id, review_id, rating, review_date dạng datetime).
    C=None -> tính lại từ dữ liệu (theo lịch); C cho trước -> giữ tham số cũ (khi ingest).
    Trả về (R có thêm các cột STAT_COLS, C, info)."""
    R = R.drop(columns=[c for c in STAT_COLS if c in R.columns])
    g = rev.groupby("restaurant_id")
    rated = rev[rev["rating"].notna()].sort_values("review_id")
    gr = rated.groupby("restaurant_id")

    # Cờ nghi seeding: gần như toàn 10 điểm VÀ dồn trong ít ngày
    sus = pd.DataFrame({
        "n": gr.size(),
        "perfect": gr["rating"].apply(lambda x: (x >= 9.8).mean()),
        "span": (gr["review_date"].max() - gr["review_date"].min()).dt.days,
        "top_day": gr["review_date"].apply(lambda d: d.value_counts(normalize=True).iloc[0] if d.notna().any() else 0.0),
    })
    sus["rating_suspect"] = ((sus["n"] >= cfg.SUSPECT_MIN_N) & (sus["perfect"] >= cfg.SUSPECT_PERFECT_SHARE)
                             & ((sus["span"] <= cfg.SUSPECT_MAX_SPAN_DAYS) | (sus["top_day"] >= cfg.SUSPECT_TOP_DAY_SHARE)))

    # Giới hạn N review/quán/ngày khi tính điểm (review vẫn giữ cho embedding)
    day_rank = rated.groupby(["restaurant_id", "review_date"]).cumcount()
    capped = rated[rated["review_date"].isna() | (day_rank < cfg.BAYES_DAILY_CAP)]
    gc = capped.groupby("restaurant_id")
    stats = pd.DataFrame({
        "n_reviews": g.size(), "n_rated_raw": gr.size(), "rating_mean_raw": gr["rating"].mean(),
        "n_rated": gc.size(), "rating_mean": gc["rating"].mean(), "rating_std": gc["rating"].std(),
        "last_review_date": g["review_date"].max(), "rating_suspect": sus["rating_suspect"],
    })
    R = R.merge(stats, left_on="restaurant_id", right_index=True, how="left")
    R[["n_reviews", "n_rated", "n_rated_raw"]] = R[["n_reviews", "n_rated", "n_rated_raw"]].fillna(0).astype(int)
    R["rating_suspect"] = R["rating_suspect"].astype("boolean").fillna(False).astype(bool)

    # Ba bậc nguồn rating: review trong file > điểm tổng hợp của nguồn > prior
    R["rating_source"] = np.select(
        [R["n_rated"] > 0, R["source_rating"].notna() & (R["source_review_count"].fillna(0) > 0)],
        ["reviews", "source_aggregate"], default="prior")
    v = np.where(R["rating_source"] == "reviews", R["rating_mean"],
                 np.where(R["rating_source"] == "source_aggregate", R["source_rating"], np.nan))
    n = np.where(R["rating_source"] == "reviews", R["n_rated"],
                 np.where(R["rating_source"] == "source_aggregate", R["source_review_count"].fillna(0), 0)).astype(float)
    n = np.where(R["rating_suspect"], np.minimum(n, m), n)  # quán nghi seeding: n <= m
    R["rating_v"], R["rating_n"] = v.astype(float), n

    if C is None:
        C = float(np.nanmean(v))
    R["bayes_rating"] = bayes_avg(R["rating_v"].to_numpy(float), R["rating_n"].to_numpy(float), C, m)
    info = {"n_rated_total": len(rated), "n_rated_capped": len(capped),
            "n_capped_restaurants": int(R["n_rated"].lt(R["n_rated_raw"]).sum())}
    return R, C, info
