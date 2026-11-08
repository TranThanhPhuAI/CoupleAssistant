"""Giai đoạn 1: làm sạch dữ liệu + restaurant_id ổn định + Bayesian average.

Chạy:  python stage1_clean.py
Đầu ra: data/clean/{restaurants_clean, reviews_clean, reviews_out_of_scope,
        category_map, top20_bayes}.csv, bayes_params.json, stage1_report.txt
"""
import json
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config as cfg
from ratings import compute_rating_stats
from common import (
    fold, infer_type_from_name, make_restaurant_id, make_review_id, name_key, nfc,
    parse_category, parse_city, parse_hours, parse_old_district_ward, parse_price_text,
)

sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 20)
pd.set_option("display.max_colwidth", 45)

_log = []


def log(*args):
    msg = " ".join(str(a) for a in args)
    print(msg)
    _log.append(msg)


def section(title):
    log("\n" + "=" * 70 + f"\n{title}\n" + "=" * 70)


# ============================================================
# 1. Đọc dữ liệu thô
# ============================================================
section("1. ĐỌC DỮ LIỆU THÔ")
rest = pd.read_csv(cfg.RAW_RESTAURANTS, encoding="utf-8-sig")
rev = pd.read_csv(cfg.RAW_REVIEWS, encoding="utf-8-sig")
rev.columns = [c.strip() for c in rev.columns]          # " open-close" -> "open-close"
rev = rev.rename(columns={"city": "address_raw", "open-close": "open_close_raw",
                          "value": "price_text", "review_id": "legacy_review_id"})
log(f"Quán (thô): {len(rest)} | Review (thô): {len(rev)}")
log("Review theo source_file:", rev["source_file"].value_counts().to_dict())

# Chuẩn hóa chuỗi
for c in ["name", "category", "address", "district", "ward", "opening_hours"]:
    rest[c] = rest[c].map(nfc)
for c in ["place_name", "address_raw", "open_close_raw", "price_text", "author", "review_text"]:
    rev[c] = rev[c].map(nfc)

# ============================================================
# 2. Bỏ khối review trùng "cleaned_reviews.csv"
# ============================================================
section("2. BỎ KHỐI REVIEW TRÙNG")
n0 = len(rev)
dup_block = rev["source_file"] == "cleaned_reviews.csv"
# Kiểm tra: mỗi dòng của khối trùng có bản giống hệt (text+rating+ngày) trong cleaned_reviews
k = ["review_text", "rating", "review_date"]
keyset = set(rev.loc[rev["source_file"] == "cleaned_reviews", k].astype(str).agg("|".join, axis=1))
matched = rev.loc[dup_block, k].astype(str).agg("|".join, axis=1).isin(keyset).sum()
log(f"Khối 'cleaned_reviews.csv': {dup_block.sum()} dòng, có bản gốc trùng: {matched}")
rev = rev[~dup_block].copy()
log(f"Review: {n0} -> {len(rev)} (kỳ vọng 22741)")

# ============================================================
# 3. Lọc phạm vi TP.HCM
# ============================================================
section("3. LỌC PHẠM VI TP.HCM")
rev["city_name"] = rev["address_raw"].map(parse_city)
log("Review theo thành phố:", rev["city_name"].value_counts(dropna=False).to_dict())
out_scope = rev[rev["city_name"] != "Hồ Chí Minh"].copy()
rev = rev[rev["city_name"] == "Hồ Chí Minh"].copy()
log(f"Ngoài phạm vi (lưu riêng): {len(out_scope)} review, {out_scope['place_name'].nunique()} quán")
log(f"Trong phạm vi HCM: {len(rev)} review")

# ============================================================
# 4. Bảng quán: category, giá, giờ, restaurant_id
# ============================================================
section("4. CHUẨN HÓA BẢNG QUÁN (811)")
rest = rest.rename(columns={"restaurant_id": "legacy_id", "rating": "source_rating",
                            "review_count": "source_review_count",
                            "opening_hours": "opening_hours_raw"})
rest["restaurant_id"] = [make_restaurant_id(n, a) for n, a in zip(rest["name"], rest["address"])]
assert rest["restaurant_id"].is_unique, "Trùng restaurant_id trong bảng quán!"
rest["category_source"] = "source"
rest["price_source"] = np.where(rest["price_min"].notna(), "source", None)
rest["city"] = "TP. HCM"

# Địa chỉ mới (sau sáp nhập) lấy từ review
addr_new = (rev[rev["source_file"] == "reviews_hcm_fixed"]
            .groupby("restaurant_id")["address_raw"].first())
rest["address_new"] = rest["legacy_id"].map(addr_new)
log(f"Quán có address_new từ review: {rest['address_new'].notna().sum()}")

# ============================================================
# 5. Gắn review vào quán + tạo 42 quán mới từ cleaned_reviews
# ============================================================
section("5. GẮN REVIEW VÀO QUÁN")
legacy_map = rest.set_index("legacy_id")["restaurant_id"]
rev["restaurant_id"] = rev["restaurant_id"].map(legacy_map)  # hcm_res_xxxx -> r_xxxx

cr = rev["source_file"] == "cleaned_reviews"
name_map = rest.assign(k=rest["name"].map(name_key)).set_index("k")["restaurant_id"]
assert name_map.index.is_unique
rev.loc[cr, "restaurant_id"] = rev.loc[cr, "place_name"].map(name_key).map(name_map)
log(f"cleaned_reviews khớp tên với bảng quán: {rev.loc[cr, 'restaurant_id'].notna().sum()} review, "
    f"{rev.loc[cr & rev['restaurant_id'].notna(), 'place_name'].nunique()} quán")

# Kiểm tra độ ổn định ID: ID tính từ địa chỉ dạng mới phải trùng ID từ địa chỉ dạng cũ
chk = rev[cr & rev["restaurant_id"].notna()].drop_duplicates("place_name")
same = sum(make_restaurant_id(n, a) == rid for n, a, rid in zip(chk["place_name"], chk["address_raw"], chk["restaurant_id"]))
log(f"Kiểm tra ổn định ID (địa chỉ cũ vs mới) cho quán trùng: {same}/{len(chk)} giống nhau")

# Quán mới
new_mask = cr & rev["restaurant_id"].isna()
rev.loc[new_mask, "restaurant_id"] = [make_restaurant_id(n, a) for n, a in
                                      zip(rev.loc[new_mask, "place_name"], rev.loc[new_mask, "address_raw"])]
newp = rev[new_mask].groupby("restaurant_id").agg(
    name=("place_name", "first"), address=("address_raw", "first"),
    price_text=("price_text", "first"), opening_hours_raw=("open_close_raw", "first")).reset_index()
dw = newp["address"].map(parse_old_district_ward)
newp["district"] = [d for d, _ in dw]
newp["ward"] = [w for _, w in dw]
newp["address_new"] = newp["address"]
newp["category"] = np.nan
newp["category_source"] = "inferred_name"
newp["source"] = "cleaned_reviews"
newp["city"] = "TP. HCM"
pm = newp["price_text"].map(lambda t: parse_price_text(t, cfg.PRICE_MIN_VALID, cfg.PRICE_MAX_VALID))
newp["price_min"] = [a for a, _ in pm]
newp["price_max"] = [b for _, b in pm]
newp["price_source"] = np.where(newp["price_min"].notna(), "review_text", None)
log(f"Quán mới từ cleaned_reviews: {len(newp)} | thiếu quận: {newp['district'].isna().sum()}")
log("  Quận của quán mới:", newp["district"].value_counts().to_dict())
assert not set(newp["restaurant_id"]) & set(rest["restaurant_id"])

R = pd.concat([rest, newp.drop(columns=["price_text"])], ignore_index=True)
assert R["restaurant_id"].is_unique
log(f"Tổng số quán: {len(R)}")

# ============================================================
# 6. Bổ sung giá / giờ thiếu từ cột chữ trong review
# ============================================================
section("6. GIÁ & GIỜ MỞ CỬA")
per_rest = rev.groupby("restaurant_id").agg(price_text=("price_text", "first"),
                                            oc=("open_close_raw", "first"))
pt = R["restaurant_id"].map(per_rest["price_text"])
parsed = pt.map(lambda t: parse_price_text(t, cfg.PRICE_MIN_VALID, cfg.PRICE_MAX_VALID))
pmin = pd.Series([a for a, _ in parsed], index=R.index)
pmax = pd.Series([b for _, b in parsed], index=R.index)

both = R["price_min"].notna() & pmin.notna()
agree = ((R.loc[both, "price_min"] == pmin[both]) & (R.loc[both, "price_max"] == pmax[both])).mean()
log(f"Đối chiếu giá bảng quán vs giá parse từ chữ: {both.sum()} quán, trùng khớp hoàn toàn {agree:.1%}")

miss_before = R["price_min"].isna().sum()
fill = R["price_min"].isna() & pmin.notna()
R.loc[fill, ["price_min", "price_max"]] = np.c_[pmin[fill], pmax[fill]]
R.loc[fill, "price_source"] = "review_text"
log(f"Thiếu giá: {miss_before} -> {R['price_min'].isna().sum()} (bổ sung {fill.sum()})")
bad = R["price_min"] > R["price_max"]
R.loc[bad, ["price_min", "price_max"]] = R.loc[bad, ["price_max", "price_min"]].values
R["price_mid"] = (R["price_min"] + R["price_max"]) / 2
R["price_suspect"] = R["price_max"] > cfg.PRICE_SUSPECT_MAX
log(f"Gắn cờ price_suspect (price_max > {cfg.PRICE_SUSPECT_MAX:,}): {R['price_suspect'].sum()} quán")

oc = R["restaurant_id"].map(per_rest["oc"])
R["opening_hours_raw"] = R["opening_hours_raw"].fillna(oc)
R["opening_hours"] = R["opening_hours_raw"].map(parse_hours)
log(f"Thiếu giờ mở cửa (sau bổ sung từ review): {R['opening_hours'].isna().sum()} "
    f"(raw có nhưng không parse được: {(R['opening_hours_raw'].notna() & R['opening_hours'].isna()).sum()})")

# ============================================================
# 7. Chuẩn hóa category
# ============================================================
section("7. CHUẨN HÓA CATEGORY")
cats = R["category"].map(parse_category)
R["place_types"] = [t for t, _, _ in cats]
R["cuisines"] = [c for _, c, _ in cats]
R["curated_tag"] = [g for _, _, g in cats]
no_type = R["place_types"].map(len) == 0
inferred = R.loc[no_type, "name"].map(infer_type_from_name)
default = np.where(R.loc[no_type, "curated_tag"] == "romantic_bistro", "Nhà hàng",
          np.where(R.loc[no_type, "curated_tag"] == "date_drinks", "Café/Dessert", "Quán ăn"))
fixed = pd.Series([[t if isinstance(t, str) else d] for t, d in zip(inferred, default)], index=inferred.index)
R["place_types"] = R["place_types"].where(~no_type, fixed)
R.loc[no_type & (R["category_source"] == "source"), "category_source"] = "inferred_name"
R["place_type"] = R["place_types"].map(lambda x: x[0])
log(f"Category gốc: {R['category'].nunique()} giá trị -> place_type: {R['place_type'].nunique()} loại, "
    f"cuisine: {R['cuisines'].explode().nunique()} loại")
log(f"Suy loại hình từ tên: {no_type.sum()} quán (nhãn tuyển chọn: {R['curated_tag'].notna().sum()}, quán mới: {len(newp)})")
log("place_type:", R["place_type"].value_counts().to_dict())
log("Top cuisine:", R["cuisines"].explode().value_counts().head(12).to_dict())

cmap = (pd.DataFrame({"category_raw": R["category"], "place_types": R["place_types"].map("; ".join),
                      "cuisines": R["cuisines"].map("; ".join), "curated_tag": R["curated_tag"]})
        .dropna(subset=["category_raw"]).drop_duplicates("category_raw").sort_values("category_raw"))

# ============================================================
# 8. Làm sạch review: trùng lặp, ID, độ dài
# ============================================================
section("8. LÀM SẠCH REVIEW")
assert rev["restaurant_id"].notna().all()
n0 = len(rev)
rev["_k"] = rev["review_text"].map(fold)  # bỏ dấu câu/emoji -> bắt cả bản gần trùng
rev = rev.sort_values(["source_file"], ascending=False)  # ưu tiên giữ bản reviews_hcm_fixed
dups = rev.duplicated(["restaurant_id", "_k"])
log(f"Review trùng nội dung trong cùng quán: {dups.sum()} (vd giữa 2 nguồn ở 7 quán trùng)")
rev = rev[~dups].drop(columns="_k")
rev["review_date"] = pd.to_datetime(rev["review_date"], errors="coerce")
rev["review_id"] = [make_review_id(r, a, d, t) for r, a, d, t in
                    zip(rev["restaurant_id"], rev["author"], rev["review_date"].astype(str), rev["review_text"])]
assert rev["review_id"].is_unique
rev["text_len"] = rev["review_text"].str.len()
rev["rating"] = rev["rating"].where(rev["rating"].between(1, 10))
log(f"Review: {n0} -> {len(rev)}")
log(f"Thiếu rating: {rev['rating'].isna().sum()} | thiếu ngày: {rev['review_date'].isna().sum()} | "
    f"text < 20 ký tự: {(rev['text_len'] < 20).sum()}")
log("Độ dài text (ký tự):", rev["text_len"].describe()[["min", "25%", "50%", "75%", "max"]].round(0).to_dict())

# ============================================================
# 9. Bayesian average
# ============================================================
section("9. BAYESIAN AVERAGE")
R, C, info = compute_rating_stats(R, rev)     # logic dùng chung với ingest.py
v = R["rating_v"].to_numpy()
C_review = float(rev["rating"].mean())        # tham khảo: trung bình theo review
m = cfg.BAYES_M
log(f"Giới hạn {cfg.BAYES_DAILY_CAP} review/quán/ngày: {info['n_rated_total']} -> {info['n_rated_capped']} review "
    f"có rating được tính ({info['n_capped_restaurants']} quán bị ảnh hưởng)")
log(f"Quán gắn cờ rating_suspect: {R['rating_suspect'].sum()} -> "
    + ", ".join(R.loc[R['rating_suspect'], 'name'].str.slice(0, 30)))
log(f"C (trung bình theo quán) = {C:.3f} | (theo review = {C_review:.3f}) | m = {m} "
    f"| trung vị số review/quán = {R['rating_n'].median():.0f}")
log("Nguồn rating:", R["rating_source"].value_counts().to_dict())
log(f"Quán < 10 review: {(R['rating_n'] < 10).sum()}")
log("Phân bố rating thô  :", pd.Series(v).describe()[["mean", "std", "min", "25%", "50%", "75%", "max"]].round(2).to_dict())
log("Phân bố bayes_rating:", R["bayes_rating"].describe()[["mean", "std", "min", "25%", "50%", "75%", "max"]].round(2).to_dict())
log("Histogram bayes_rating:",
    pd.cut(R["bayes_rating"], [0, 5, 6, 6.5, 7, 7.5, 8, 8.5, 10]).value_counts().sort_index().to_dict())

# ============================================================
# 10. Xuất file
# ============================================================
section("10. XUẤT FILE")
cfg.CLEAN_DIR.mkdir(parents=True, exist_ok=True)
now = datetime.now(timezone.utc).isoformat(timespec="seconds")
R["has_coords"] = R["latitude"].notna() & R["longitude"].notna()
R["updated_at"] = now
R["first_seen"] = cfg.INITIAL_LOAD_DATE  # dữ liệu gốc; quán ingest sau mang ngày nhập thật (cold-start)
R["place_types"] = R["place_types"].map("; ".join)
R["cuisines"] = R["cuisines"].map("; ".join)
R = R.rename(columns={"category": "category_raw"})
rcols = ["restaurant_id", "legacy_id", "name", "place_type", "place_types", "cuisines", "category_raw",
         "category_source", "curated_tag", "address", "address_new", "district", "ward", "city",
         "latitude", "longitude", "has_coords", "price_min", "price_max", "price_mid", "price_source",
         "price_suspect", "opening_hours", "opening_hours_raw", "source_rating", "source_review_count",
         "n_reviews", "n_rated_raw", "rating_mean_raw", "n_rated", "rating_mean", "rating_std",
         "rating_suspect", "rating_source", "rating_v", "rating_n",
         "bayes_rating", "last_review_date", "website", "source", "source_url", "first_seen", "updated_at"]
R = R[rcols].sort_values("restaurant_id")
R.to_csv(cfg.RESTAURANTS_CLEAN, index=False, encoding="utf-8-sig")

rev["review_date"] = rev["review_date"].dt.strftime("%Y-%m-%d")
vcols = ["review_id", "legacy_review_id", "restaurant_id", "author", "review_text", "rating", "review_date",
         "text_len", "language", "source", "source_url", "source_file"]
rev[vcols].sort_values(["restaurant_id", "review_date"]).to_csv(cfg.REVIEWS_CLEAN, index=False, encoding="utf-8-sig")
out_scope.drop(columns=["restaurant_id"]).to_csv(cfg.REVIEWS_OUT_OF_SCOPE, index=False, encoding="utf-8-sig")
cmap.to_csv(cfg.CATEGORY_MAP, index=False, encoding="utf-8-sig")
json.dump({"C": C, "m": m,  # C đủ độ chính xác: ingest dùng lại đúng giá trị này "C_review_level": round(C_review, 4), "n_restaurants": int(len(R)),
           "n_reviews": int(len(rev)), "computed_at": now}, open(cfg.BAYES_PARAMS, "w", encoding="utf-8"), indent=2)

top = R.sort_values(["bayes_rating", "rating_n"], ascending=False).head(20)
tcols = ["name", "district", "place_type", "rating_n", "rating_v", "bayes_rating", "rating_suspect",
         "price_min", "price_max"]
top[["restaurant_id"] + tcols].to_csv(cfg.TOP20, index=False, encoding="utf-8-sig")
for p in [cfg.RESTAURANTS_CLEAN, cfg.REVIEWS_CLEAN, cfg.REVIEWS_OUT_OF_SCOPE, cfg.CATEGORY_MAP, cfg.BAYES_PARAMS, cfg.TOP20]:
    log(f"  {p.relative_to(cfg.BASE)}")

section("TOP 20 THEO BAYESIAN RATING")
t = top[tcols].copy()
t["name"] = t["name"].str.slice(0, 42)
t[["rating_v", "bayes_rating"]] = t[["rating_v", "bayes_rating"]].round(2)
log(t.to_string(index=False))

section("SO SÁNH: TOP 10 THEO RATING THÔ (vì sao cần Bayesian)")
raw = R.sort_values(["rating_v", "rating_n"], ascending=False).head(10)[["name", "rating_n", "rating_v", "bayes_rating"]]
raw["name"] = raw["name"].str.slice(0, 42)
log(raw.round(2).to_string(index=False))

cfg.STAGE1_REPORT.write_text("\n".join(_log), encoding="utf-8")
