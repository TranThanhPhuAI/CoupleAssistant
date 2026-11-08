"""Giai đoạn 5: tính chất quán q + demo personality_fit cho hai hồ sơ khác nhau, đưa vào TOPSIS.

Chạy:  python stage5_personality.py         (tính restaurant_traits.csv + demo với 2 hồ sơ mẫu)
       python stage5_personality.py --ask   (tự trả lời bảng hỏi trên terminal, KHÔNG lưu)
"""
import sys

import pandas as pd

import config as cfg
from personality import (DIMENSIONS, ProfileStore, adjust_weights, ask_in_terminal, build_profile,
                         explain_fit, personality_fit, restaurant_traits)
from ranker import Person, rank_for_couple

sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 230)
pd.set_option("display.max_columns", 20)

# Hai hồ sơ mẫu (giả lập câu trả lời 1-5)
ANS_AN = {  # hướng nội, thích yên tĩnh, thích chụp ảnh, lên kế hoạch kỹ
    "b1": 5, "b2": 4, "b3": 2, "b4": 3, "b5": 1, "b6": 2, "b7": 2, "b8": 5, "b9": 3, "b10": 4,
    "p1": 1, "p2": 2, "p3": 5, "p4": 5}
ANS_BINH = {  # hướng ngoại, thích sôi động, thích món lạ, tùy hứng
    "b1": 1, "b2": 4, "b3": 3, "b4": 4, "b5": 3, "b6": 5, "b7": 2, "b8": 3, "b9": 2, "b10": 5,
    "p1": 5, "p2": 5, "p3": 1, "p4": 2}


def main():
    R = pd.read_csv(cfg.RESTAURANTS_CLEAN, encoding="utf-8-sig")
    S = pd.read_csv(cfg.SCORES, encoding="utf-8-sig")
    T = restaurant_traits(R, S)
    T.to_csv(cfg.RESTAURANT_TRAITS, index=False, encoding="utf-8-sig")
    print(f"Tính chất quán q ({len(T)} quán) -> {cfg.RESTAURANT_TRAITS.relative_to(cfg.BASE)}")
    print(T[DIMENSIONS].describe().loc[["mean", "std", "min", "50%", "max"]].round(2).to_string())

    # ---- Hồ sơ + lưu trữ có xin phép ----
    store = ProfileStore(cfg.PROFILE_DIR / "_demo")
    try:
        store.save("demo_an", ANS_AN, consent=False)
    except PermissionError as e:
        print("\n[Kiểm tra xin phép] không đồng ý ->", e)
    store.save("demo_an", ANS_AN, consent=True, share_with_partner=False)
    store.save("demo_binh", ANS_BINH, consent=True, share_with_partner=True)
    print("[Kiểm tra chia sẻ] Bình xem hồ sơ An:", store.partner_view("demo_an"))
    print("[Kiểm tra chia sẻ] An xem hồ sơ Bình:", store.partner_view("demo_binh"))

    pa, pb = build_profile(ANS_AN), build_profile(ANS_BINH)
    print("\nHồ sơ p — An  :", pa["p"])
    print("Hồ sơ p — Bình:", pb["p"])

    fa, fb = personality_fit(pa, T), personality_fit(pb, T)
    print(f"\npersonality_fit An  : {fa.describe()[['min', '50%', 'max']].round(3).to_dict()}")
    print(f"personality_fit Bình: {fb.describe()[['min', '50%', 'max']].round(3).to_dict()}")
    print(f"Tương quan fit An vs Bình: {fa.corr(fb):.2f} (âm = hai người hợp những quán khác nhau)")

    names = R.set_index("restaurant_id")["name"].str.slice(0, 36)
    Ti = T.set_index("restaurant_id")
    for who, f, prof in (("An", fa, pa), ("Bình", fb, pb)):
        top = f.sort_values(ascending=False).head(5)
        print(f"\nHợp nhất với {who}:")
        for rid, v in top.items():
            print(f"  {v:.3f}  {names[rid]:36s}  khớp ở: {', '.join(explain_fit(prof, Ti.loc[rid]))}")

    # ---- Đưa vào TOPSIS: so sánh có / không có tính cách ----
    wa, wb = adjust_weights(pa), adjust_weights(pb)
    print("\nTrọng số sau điều chỉnh — An :", {k: round(v, 3) for k, v in wa.items()})
    print("Trọng số sau điều chỉnh — Bình:", {k: round(v, 3) for k, v in wb.items()})
    loc_a, loc_b = (10.7769, 106.7009), (10.8494, 106.7537)
    q = None  # không có câu hỏi: thấy rõ tác động của tính cách (và không cần nạp model embedding)
    base = rank_for_couple(Person("An", loc_a, 400_000), Person("Binh", loc_b, 400_000), query=q, k=10)
    pers = rank_for_couple(Person("An", loc_a, 400_000, weights=wa), Person("Binh", loc_b, 400_000, weights=wb),
                           query=q, k=10, personality_fit={"An": fa, "Binh": fb})
    print("\n### Không câu hỏi, ngân sách 400k — KHÔNG tính cách vs CÓ tính cách")
    out = pd.DataFrame({"không tính cách": base["name"].str.slice(0, 32),
                        "có tính cách": pers["name"].str.slice(0, 32),
                        "pfit_An": pers["pfit_An"].round(2), "pfit_Binh": pers["pfit_Binh"].round(2),
                        "group": pers["group_score"].round(3)})
    print(out.to_string(index=False))
    print(f"Số quán khác nhau trong top 10: {len(set(base['restaurant_id']) ^ set(pers['restaurant_id'])) // 2}")

    # ---- Xóa hồ sơ ----
    print("\n[Kiểm tra xóa] xóa demo_an:", store.delete("demo_an"), "| còn tồn tại:", store.load("demo_an") is not None)
    store.delete("demo_binh")


if __name__ == "__main__":
    if "--ask" in sys.argv:
        prof = build_profile(ask_in_terminal())
        print("\nHồ sơ của bạn (không được lưu):", prof["p"])
    else:
        main()
