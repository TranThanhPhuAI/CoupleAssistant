"""Giai đoạn 3b: lan nhãn ABSA ra toàn bộ review (bộ phân loại trên embedding bge-m3)
-> điểm khía cạnh theo quán -> food_score, date_score, couple_score.

Chạy:  python stage3_scores.py     (sau khi stage3_label.py đã gán nhãn xong)
Nếu bạn đã điền cột *_human trong absa_manual_check.csv: nhãn tay được ưu tiên + in độ khớp.
"""
import json
import pickle
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

import config as cfg
from absa import ASPECTS, POLARITIES
from scoring import SCORE_COLS, derive_tags, score_restaurants
from vector_store import VectorStore

sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 230)
pd.set_option("display.max_columns", 30)


def section(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


# ============================================================
# 1. Embedding mức review (trung bình các chunk) từ index hiện hành
# ============================================================
section("1. EMBEDDING MỨC REVIEW")
meta, emb, manifest = VectorStore(cfg.INDEX_DIR).load()
is_rev = (meta["doc_type"] == "review").to_numpy()
codes, review_ids = pd.factorize(meta.loc[is_rev, "review_id"])
X = np.zeros((len(review_ids), emb.shape[1]), dtype=np.float32)
np.add.at(X, codes, emb[is_rev])
X /= np.linalg.norm(X, axis=1, keepdims=True)
row_of = pd.Series(np.arange(len(review_ids)), index=review_ids)
print(f"{len(review_ids)} review, dim {X.shape[1]}, model {manifest['model']}")

# ============================================================
# 2. Nhãn: LLM (+ sửa tay nếu có)
# ============================================================
section("2. NHÃN HUẤN LUYỆN")
lab = pd.DataFrame([json.loads(l) for l in cfg.ABSA_LLM_LABELS.read_text(encoding="utf-8").splitlines() if l.strip()])
lab = lab.drop_duplicates("review_id", keep="last").set_index("review_id")
lab = lab[lab.index.isin(row_of.index)]
print(f"Nhãn LLM: {len(lab)} review")

if cfg.ABSA_MANUAL_CHECK.exists():
    mc = pd.read_csv(cfg.ABSA_MANUAL_CHECK, encoding="utf-8-sig", dtype=str).set_index("review_id")
    hum_cols = [f"{a}_human" for a in ASPECTS]
    filled = mc[hum_cols].notna().any(axis=1)
    if filled.any():
        print(f"Kiểm tra tay: {filled.sum()} dòng có sửa")
        agree = {}
        for a in ASPECTS:
            h = mc[f"{a}_human"].fillna(mc[f"{a}_llm"]).str.strip().str.lower()
            agree[a] = (h == mc[f"{a}_llm"]).mean()
            ok = h.isin(POLARITIES)
            lab.loc[lab.index.intersection(h[ok].index), a] = h[ok]  # nhãn tay ghi đè nhãn LLM
        print("Độ khớp LLM vs người (200 dòng):", {k: f"{v:.0%}" for k, v in agree.items()})
    else:
        print("absa_manual_check.csv chưa được điền -> dùng nhãn LLM (độ khớp với người: CHƯA ĐO)")

# ============================================================
# 3. Bộ phân loại từng khía cạnh: đánh giá chéo 5-fold rồi huấn luyện trên toàn bộ mẫu
# ============================================================
section("3. BỘ PHÂN LOẠI KHÍA CẠNH TRÊN EMBEDDING (so với nhãn LLM, 5-fold)")
XL = X[row_of[lab.index].to_numpy()]
probes, cv_rows = {}, []
for a in ASPECTS:
    y = lab[a].to_numpy()
    # Không dùng class_weight="balanced": nó thổi phồng xác suất lớp hiếm -> nhiều dương tính giả
    clf = LogisticRegression(C=2.0, max_iter=3000)
    min_class = pd.Series(y).value_counts().min()
    if min_class >= 5:
        cv = StratifiedKFold(5, shuffle=True, random_state=0)
        yp = cross_val_predict(clf, XL, y, cv=cv)
        rep = classification_report(y, yp, labels=POLARITIES, output_dict=True, zero_division=0)
        cv_rows.append({"aspect": a, "macro_f1": f1_score(y, yp, average="macro"), "acc": (yp == y).mean(),
                        "f1_pos": rep["pos"]["f1-score"], "prec_pos": rep["pos"]["precision"],
                        "rec_pos": rep["pos"]["recall"], "f1_neg": rep["neg"]["f1-score"],
                        "n_pos": int((y == "pos").sum()), "n_neg": int((y == "neg").sum())})
    probes[a] = clf.fit(XL, y)
print(pd.DataFrame(cv_rows).round(3).to_string(index=False))

with open(cfg.ABSA_PROBE, "wb") as f:
    pickle.dump({"model": manifest["model"], "aspects": list(ASPECTS), "probes": probes,
                 "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "n_train": len(lab)}, f)

# ============================================================
# 4. Dự đoán toàn bộ review (review đã có nhãn -> dùng nhãn)
# ============================================================
section("4. GÁN NHÃN TOÀN BỘ REVIEW")
rev = pd.read_csv(cfg.REVIEWS_CLEAN, encoding="utf-8-sig", usecols=["review_id", "restaurant_id"])
rev = rev[rev["review_id"].isin(row_of.index)].reset_index(drop=True)
XR = X[row_of[rev["review_id"]].to_numpy()]
labeled = rev["review_id"].isin(lab.index).to_numpy()
for a in ASPECTS:
    P = probes[a].predict_proba(XR)
    cls = list(probes[a].classes_)
    p_pos = P[:, cls.index("pos")] if "pos" in cls else np.zeros(len(rev))
    p_neg = P[:, cls.index("neg")] if "neg" in cls else np.zeros(len(rev))
    gold = rev.loc[labeled, "review_id"].map(lab[a])
    p_pos[labeled] = (gold == "pos").to_numpy(float)
    p_neg[labeled] = (gold == "neg").to_numpy(float)
    rev[f"{a}_pos"], rev[f"{a}_neg"] = p_pos.round(4), p_neg.round(4)
rev["label_source"] = np.where(labeled, "llm", "probe")
rev.to_csv(cfg.ABSA_REVIEW_PRED, index=False, encoding="utf-8-sig")
share = pd.DataFrame({a: [(rev[f"{a}_pos"] > 0.5).mean(), (rev[f"{a}_neg"] > 0.5).mean()] for a in ASPECTS},
                     index=["% pos", "% neg"]).T * 100
print(f"{len(rev)} review ({labeled.sum()} nhãn LLM, {(~labeled).sum()} dự đoán)")
print(share.round(1).to_string())

# ============================================================
# 5. Điểm khía cạnh theo quán (làm mượt Bayes) -> phân vị
# ============================================================
section("5. ĐIỂM KHÍA CẠNH THEO QUÁN")
R = pd.read_csv(cfg.RESTAURANTS_CLEAN, encoding="utf-8-sig")
S, reference = score_restaurants(R, rev)  # tính lại prior/z/phân phối tham chiếu (logic dùng chung với ingest)
print("Prior từng khía cạnh (mu):", {k: round(v, 3) for k, v in reference["priors"].items()})

# ============================================================
# 6. food_score, date_score, couple_score
# ============================================================
section("6. FOOD / DATE / COUPLE SCORE")
f_thr, d_thr = S.attrs["thresholds"]

print(f"Ngưỡng dùng: food >= {f_thr}, date >= {d_thr} | qua ngưỡng: {S['couple_pass'].sum()} quán")
print("Nhãn:", S["tradeoff_label"].value_counts().to_dict())
for c in ["food_score", "date_score", "couple_score"]:
    print(f"{c:13s}:", S[c].describe()[["mean", "25%", "50%", "75%", "max"]].round(3).to_dict())
print(f"Tương quan food vs date: {S['food_score'].corr(S['date_score']):.2f}")
print("\nKiểm tra hợp lý: date_score trung bình theo loại hình (kỳ vọng Café/Nhà hàng > Ăn vặt/Shop Online)")
print(S.groupby("place_type")["date_score"].agg(["mean", "size"]).sort_values("mean", ascending=False).round(2).to_string())

S[SCORE_COLS].round(4).to_csv(cfg.SCORES, index=False, encoding="utf-8-sig")
tags = derive_tags(S)
tags.to_csv(cfg.PLACE_TAGS, index=False, encoding="utf-8-sig")
print(f"Nhãn AI (place_tags): {len(tags)} nhãn cho {tags['restaurant_id'].nunique()} quán |",
      tags["tag"].value_counts().to_dict())
reference["computed_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
json.dump(reference, open(cfg.SCORE_REFERENCE, "w", encoding="utf-8"))

top = S.sort_values(["couple_pass", "couple_score"], ascending=False).head(30)
top.to_csv(cfg.TOP_COUPLE, index=False, encoding="utf-8-sig",
           columns=["restaurant_id", "name", "district", "place_type", "price_min", "price_max", "bayes_rating",
                    "food_score", "date_score", "couple_score", "tradeoff_label"])
section("TOP 20 'VỪA NGON VỪA HỢP HẸN HÒ'")
t = top.head(20).copy()
t["name"] = t["name"].str.slice(0, 38)
t["giá"] = (t["price_min"] // 1000).astype("Int64").astype(str) + "-" + (t["price_max"] // 1000).astype("Int64").astype(str) + "k"
print(t[["name", "district", "place_type", "giá", "bayes_rating", "food_score", "date_score", "couple_score",
         "romantic_z", "quiet_z", "view_z", "ambience_z"]].round(2).to_string(index=False))
print("\nĐã lưu:", cfg.SCORES.relative_to(cfg.BASE), "|", cfg.TOP_COUPLE.relative_to(cfg.BASE))
