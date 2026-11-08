"""Giai đoạn 7: kiểm thử ingest.py trên BẢN SAO dữ liệu (.cache/sandbox) — dữ liệu thật không bị đụng tới.

Chạy:  python stage7_test_ingest.py
Đợt thử gồm dòng tốt + dòng lỗi cố ý; các quán/review "[TEST]" là dữ liệu giả CHỈ nằm trong sandbox.
"""
import shutil
import sys

import pandas as pd

import config as cfg
from ingest import Paths, ingest
from ranker import new_restaurant_bonus
from semantic import Searcher

sys.stdout.reconfigure(encoding="utf-8")
SB = cfg.BASE / ".cache" / "sandbox"


def setup():
    if SB.exists():
        shutil.rmtree(SB)
    (SB / "data").mkdir(parents=True)
    shutil.copytree(cfg.CLEAN_DIR, SB / "data" / "clean")
    absa = SB / "data" / "absa"
    absa.mkdir()
    for f in [cfg.ABSA_REVIEW_PRED, cfg.ABSA_PROBE, cfg.SCORE_REFERENCE]:
        shutil.copy2(f, absa / f.name)
    cur = (cfg.INDEX_DIR / "CURRENT").read_text().strip()
    shutil.copytree(cfg.INDEX_DIR / cur, SB / "data" / "index" / cur)
    shutil.copy2(cfg.INDEX_DIR / "CURRENT", SB / "data" / "index" / "CURRENT")

    R = pd.read_csv(cfg.RESTAURANTS_CLEAN, encoding="utf-8-sig")
    V = pd.read_csv(cfg.REVIEWS_CLEAN, encoding="utf-8-sig")
    oos = pd.read_csv(cfg.REVIEWS_OUT_OF_SCOPE, encoding="utf-8-sig").iloc[0]  # quán Hà Nội thật
    santo = R[R["name"].str.startswith("Santorino")].iloc[0]
    santo_rev = V[V["restaurant_id"] == santo["restaurant_id"]].iloc[0]

    batch = SB / "staging" / "test_batch"
    batch.mkdir(parents=True)
    test_name, test_addr = "[TEST] Quán Thử Nghiệm Hẹn Hò", "99 Đường Thử Nghiệm, Phường 6, Quận 3, TP. HCM"
    pd.DataFrame([
        # quán đã có: cập nhật giờ mở cửa (phải UPDATE, không nhân đôi)
        {"name": santo["name"], "address": santo["address"], "opening_hours": "07:00 - 23:00"},
        # quán mới hợp lệ
        {"name": test_name, "address": test_addr, "category": "Nhà hàng, Món Âu", "latitude": 10.78,
         "longitude": 106.69, "price_text": "150.000đ - 400.000đ", "opening_hours": "17:00 - 23:00"},
        # ngoài TP.HCM -> từ chối
        {"name": oos["place_name"], "address": oos["address_raw"]},
        # thiếu tên -> từ chối
        {"name": None, "address": "1 Lê Lợi, Quận 1, TP. HCM"},
    ]).to_csv(batch / "restaurants.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame([
        {"restaurant_name": test_name, "restaurant_address": test_addr, "rating": 9.0, "review_date": "2026-10-01",
         "review_text": "[TEST] Không gian lãng mạn, ánh nến ấm cúng, rất yên tĩnh, hợp hẹn hò với người yêu. Steak ngon."},
        {"restaurant_name": test_name, "restaurant_address": test_addr, "rating": 4.5, "rating_scale": 5,
         "review_date": "2026-10-05", "review_text": "[TEST] View nhìn ra phố rất đẹp, góc riêng tư, phục vụ chu đáo."},
        {"restaurant_name": test_name, "restaurant_address": test_addr, "rating": 8.0, "review_date": "2026-10-08",
         "review_text": "[TEST] Món mì Ý vừa vị, giá hơi cao nhưng xứng đáng cho dịp kỷ niệm."},
        # trùng review đã có của Santorino -> bỏ qua
        {"restaurant_id": santo["restaurant_id"], "review_text": santo_rev["review_text"], "rating": santo_rev["rating"]},
        # quán không tồn tại -> từ chối
        {"restaurant_name": "Quán Ma", "restaurant_address": "0 Không Có", "review_text": "Ngon tuyệt vời ông mặt trời"},
        # review rỗng -> từ chối
        {"restaurant_name": test_name, "restaurant_address": test_addr, "review_text": "ok"},
    ]).to_csv(batch / "reviews.csv", index=False, encoding="utf-8-sig")
    return batch


def main():
    batch = setup()
    P = Paths(SB / "data")
    R0 = pd.read_csv(P.restaurants, encoding="utf-8-sig")
    # Mốc so sánh: chấm điểm lại TRƯỚC khi nhập bằng đúng tham chiếu đã lưu (cô lập tác động của ingest)
    import json
    from scoring import score_restaurants
    S0, _ = score_restaurants(R0, pd.read_csv(P.aspects, encoding="utf-8-sig"),
                              reference=json.loads(P.score_ref.read_text(encoding="utf-8")))
    S0 = S0.set_index("restaurant_id")

    print("=" * 70 + "\n1. ĐỢT CÓ QUÁ NHIỀU DÒNG LỖI -> PHẢI HỦY\n" + "=" * 70)
    r = ingest(batch, P)
    unchanged = len(pd.read_csv(P.restaurants, encoding="utf-8-sig")) == len(R0)
    print(f"-> trạng thái: {r['status']} | dữ liệu không đổi: {unchanged}")

    print("\n" + "=" * 70 + "\n2. CHO PHÉP 50% LỖI -> NHẬP PHẦN HỢP LỆ\n" + "=" * 70)
    r = ingest(batch, P, max_reject=0.5)
    print("-> trạng thái:", r["status"])

    print("\n" + "=" * 70 + "\n3. CHẠY LẠI CÙNG ĐỢT -> KHÔNG NHÂN ĐÔI\n" + "=" * 70)
    r2 = ingest(batch, P, max_reject=0.5)
    print("-> trạng thái:", r2["status"])

    print("\n" + "=" * 70 + "\n4. KIỂM TRA SAU NHẬP\n" + "=" * 70)
    R1 = pd.read_csv(P.restaurants, encoding="utf-8-sig")
    V1 = pd.read_csv(P.reviews, encoding="utf-8-sig")
    S1 = pd.read_csv(P.scores, encoding="utf-8-sig").set_index("restaurant_id")
    print(f"Quán: {len(R0)} -> {len(R1)} | restaurant_id duy nhất: {R1['restaurant_id'].is_unique} "
          f"| review_id duy nhất: {V1['review_id'].is_unique}")
    t = R1[R1["name"].str.startswith("[TEST]")].iloc[0]
    print(f"Quán mới: {t['name']} | {t['district']} | giá {t['price_min']:.0f}-{t['price_max']:.0f} | "
          f"giờ {t['opening_hours']} | loại {t['place_type']} | first_seen {t['first_seen']}")
    print(f"  rating: n={t['rating_n']:.0f}, trung bình={t['rating_v']:.2f} (review thang 5: 4.5 -> 9.0), "
          f"bayes={t['bayes_rating']:.2f} (kéo về C vì ít review)")
    st = S1.loc[t["restaurant_id"]]
    print(f"  food={st['food_score']:.2f} date={st['date_score']:.2f} couple={st['couple_score']:.2f} "
          f"| romantic_z={st['romantic_z']:.2f} quiet_z={st['quiet_z']:.2f}")
    bonus = new_restaurant_bonus(R1[R1["restaurant_id"] == t["restaurant_id"]])[0]
    print(f"  điểm cộng quán mới (cold-start): +{bonus:.3f}")
    santo = R1[R1["name"].str.startswith("Santorino")].iloc[0]
    print(f"Santorino: giờ mở cửa cập nhật -> {santo['opening_hours']} | số dòng Santorino: "
          f"{(R1['name'] == santo['name']).sum()}")
    old = S0.index
    diff = (S1.loc[old, "couple_score"] - S0["couple_score"]).abs().max()
    print(f"Điểm couple của {len(old)} quán cũ thay đổi tối đa: {diff:.6f} (kỳ vọng 0: giữ tham chiếu cũ)")
    s = Searcher(index_dir=P.index, restaurants_path=P.restaurants)
    res = s.search("nhà hàng lãng mạn ánh nến yên tĩnh có view", k=10_000, evidence=0)
    rank = res.index[res["restaurant_id"] == t["restaurant_id"]][0] + 1
    print(f"Tìm kiếm trong sandbox 'nhà hàng lãng mạn ánh nến yên tĩnh có view': quán mới xếp hạng ngữ nghĩa "
          f"{rank}/{len(res)} (đã có trong index, chỉ 3 review nên bị làm mượt về mức nền)")
    print(f"\nDữ liệu thật không bị đụng: {len(pd.read_csv(cfg.RESTAURANTS_CLEAN, encoding='utf-8-sig'))} quán")


if __name__ == "__main__":
    main()
