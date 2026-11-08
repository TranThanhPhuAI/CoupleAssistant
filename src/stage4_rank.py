"""Giai đoạn 4: demo TOPSIS từng người + gộp hai người (trung bình + least-misery).

Chạy:  python stage4_rank.py
"""
import sys

import numpy as np
import pandas as pd

from ranker import Person, rank_for_couple

sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 240)
pd.set_option("display.max_columns", 20)

# Hai người ở hai đầu thành phố, ưu tiên khác nhau
AN = Person("An", location=(10.7769, 106.7009),            # Quận 1 (Nhà thờ Đức Bà)
            budget_max=400_000, weights={"semantic_match": 0.35, "couple_score": 0.35, "distance_km": 0.05})
BINH = Person("Binh", location=(10.8494, 106.7537),        # TP. Thủ Đức
              budget_max=250_000, weights={"distance_km": 0.30, "price_fit": 0.25})


def show(res, a, b, title):
    log = res.attrs["log"]
    print(f"\n### {title}")
    print(f"  Quán: {log['n_all']} -> lọc cứng {log['n_after_filters']} -> ngữ nghĩa {log['n_after_semantic']} "
          f"-> qua ngưỡng couple {log['n_candidates']} (ngưỡng food/date = {log['thresholds']}) | "
          f"ngân sách chung {res.attrs['budget']:,.0f}đ")
    for p, w in res.attrs["weights"].items():
        print(f"  Trọng số thực dùng ({p}):", {k: round(v, 2) for k, v in w.items()})
    t = res.copy()
    t["name"] = t["name"].str.slice(0, 34)
    t["giá"] = (t["price_min"] // 1000).astype("Int64").astype(str) + "-" + (t["price_max"] // 1000).astype("Int64").astype(str) + "k"
    cols = ["name", "district", "giá", "couple_score", "semantic_match", "price_fit",
            f"dist_{a.name}", f"dist_{b.name}", f"topsis_{a.name}", f"topsis_{b.name}", "group_score", "tradeoff_label"]
    print(t[cols].round(2).to_string(index=False))


if __name__ == "__main__":
    r1 = rank_for_couple(AN, BINH, query="ăn tối lãng mạn, không gian đẹp yên tĩnh", k=10)
    show(r1, AN, BINH, "Truy vấn: 'ăn tối lãng mạn, không gian đẹp yên tĩnh'")

    r2 = rank_for_couple(AN, BINH, query="cafe yên tĩnh để trò chuyện", k=8, districts=["Quận 1", "Quận 3", "Quận Bình Thạnh"])
    show(r2, AN, BINH, "Truy vấn: 'cafe yên tĩnh để trò chuyện' + lọc Quận 1/3/Bình Thạnh")

    r3 = rank_for_couple(AN, BINH, query=None, k=8)
    show(r3, AN, BINH, "Không có câu hỏi (chỉ couple_score + giá + khoảng cách)")

    # So sánh: chỉ trung bình vs trung bình + least-misery
    print("\n### Ảnh hưởng của least-misery (truy vấn 1, top 10)")
    m = rank_for_couple(AN, BINH, query="ăn tối lãng mạn, không gian đẹp yên tĩnh", k=10, mean_weight=1.0)
    only_mean, with_min = list(m["name"].str.slice(0, 30)), list(r1["name"].str.slice(0, 30))
    print("  Chỉ trung bình      :", only_mean[:6])
    print("  Trung bình + min    :", with_min[:6])
    print(f"  Chênh lệch TOPSIS |An - Binh| trung bình top10: chỉ TB = {np.abs(m['topsis_An'] - m['topsis_Binh']).mean():.3f}"
          f" | TB+min = {np.abs(r1['topsis_An'] - r1['topsis_Binh']).mean():.3f}")

    # Kiểm tra giá trị thiếu: quán thiếu tọa độ / giá vẫn được xét (trung tính)
    allc = rank_for_couple(AN, BINH, query="ăn tối lãng mạn, không gian đẹp yên tĩnh", k=1000)
    print(f"\nỨng viên thiếu tọa độ: {allc['dist_An'].isna().sum()} | thiếu giá: {allc['price_fit'].isna().sum()} "
          f"(trên {len(allc)} ứng viên, không bị loại)")
    print("Xác định (deterministic): chạy lại cho cùng kết quả =",
          rank_for_couple(AN, BINH, query="ăn tối lãng mạn, không gian đẹp yên tĩnh", k=10)["restaurant_id"].tolist()
          == r1["restaurant_id"].tolist())
