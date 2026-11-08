# THAM KHẢO: script gốc đã gộp 2 nguồn review thành data/raw/reviews_merged.csv.
# Cần reviews_hcm_fixed.csv + cleaned_reviews.csv gốc (không kèm trong gói) -> không cần chạy lại.
import pandas as pd
from pathlib import Path

# ===== Đường dẫn =====
BASE = Path(__file__).resolve().parent                      # E:\CoupleAssistant
DATA = BASE / "restaurant-data-hcm" / "restaurant-data-hcm" / "data"

# ===== 1) Đọc file =====
rev1 = pd.read_csv(DATA / "reviews_hcm_fixed.csv", encoding="utf-8-sig")
rev2 = pd.read_csv(BASE / "cleaned_reviews.csv", encoding="utf-8-sig")
rest = pd.read_csv(DATA / "restaurants_hcm_fixed.csv", encoding="utf-8-sig")
print("reviews_hcm_fixed:", rev1.shape, "| cleaned_reviews:", rev2.shape)

# ===== 2) reviews_hcm_fixed: thêm tên quán từ bảng restaurants =====
rev1 = rev1.merge(
    rest[["restaurant_id", "name"]].rename(columns={"name": "place_name"}),
    on="restaurant_id", how="left")
rev1["author"] = None
rev1["city"] = "TP. HCM"
rev1["source_file"] = "reviews_hcm_fixed"
rev1["review_date"] = pd.to_datetime(rev1["review_date"], errors="coerce")

# ===== 3) cleaned_reviews: đổi tên cột, cắt đuôi "ở Quận X, Thành phố" =====
rev2 = rev2.rename(columns={"clean_text": "review_text", "date": "review_date"})
ext = rev2["place_name"].str.extract(r"^(.*?)\s+ở\s+([^,]+),\s*([^,]+)$")
rev2["place_name"] = ext[0].fillna(rev2["place_name"])
rev2["city"] = ext[2]
rev2["review_date"] = pd.to_datetime(rev2["review_date"], format="%m/%d/%Y", errors="coerce")
rev2["restaurant_id"] = None
rev2["language"] = None
rev2["source"] = None
rev2["source_url"] = None
rev2["source_file"] = "cleaned_reviews"

# ===== 4) Gộp (giữ nguyên mọi review) =====
cols = ["restaurant_id", "place_name", "city", "author", "review_text", "rating",
        "review_date", "language", "source", "source_url", "source_file"]
merged = pd.concat([rev1[cols], rev2[cols]], ignore_index=True)
merged.insert(0, "review_id", range(1, len(merged) + 1))
merged["review_date"] = merged["review_date"].dt.strftime("%Y-%m-%d")

# ===== 5) Xuất file & kiểm tra =====
out = BASE / "reviews_merged.csv"
merged.to_csv(out, index=False, encoding="utf-8-sig")

print("Tổng số dòng:", len(merged), "(kỳ vọng 22741)")
print(merged["source_file"].value_counts().to_dict())
print(merged["city"].value_counts().to_dict())
print("Đã lưu:", out)