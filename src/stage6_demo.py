"""Giai đoạn 6: demo trích tiêu chí (luật + LLM), giải thích có kiểm tra chống bịa, vòng phản hồi.

Chạy:  python stage6_demo.py            (đầy đủ, cần Ollama đang chạy)
       python stage6_demo.py --no-llm   (chỉ luật + giải thích theo mẫu)
"""
import json
import sys
import time

import pandas as pd

import config as cfg
from feedback import log_event, update_profile
from personality import build_profile
from query_parser import parse_budget, parse_districts, parse_query
from ranker import Person
from recommend import recommend

sys.stdout.reconfigure(encoding="utf-8")
USE_LLM = "--no-llm" not in sys.argv

# 1) Kiểm tra luật trích quận/ngân sách (xác định)
RULE_CASES = [
    ("chỗ ăn tối lãng mạn Quận 3 dưới 400k", ["Quận 3"], 200_000),
    ("cafe yên tĩnh ở Bình Thạnh tầm 100k/người", ["Quận Bình Thạnh"], 100_000),
    ("q1 hoặc q.10, khoảng 1tr cho 2 người", ["Quận 1", "Quận 10"], 500_000),
    ("đi ăn lẩu ở Thủ Đức, mỗi người 250 nghìn", ["TP. Thủ Đức"], 250_000),
    ("nhà hàng view đẹp, không quan trọng giá", [], None),
    ("ngân sách 300.000đ/người, gần Phú Nhuận", ["Quận Phú Nhuận"], 300_000),
    ("quận 1 không phải quận 10, 1,5tr cho cả hai", ["Quận 1"], 750_000),
]
print("=" * 70 + "\n1. LUẬT TRÍCH QUẬN / NGÂN SÁCH\n" + "=" * 70)
ok = 0
for text, d_exp, b_exp in RULE_CASES:
    d, (b, scope) = parse_districts(text), parse_budget(text)
    good = sorted(d) == sorted(d_exp) and (b == b_exp)
    ok += good
    print(f"  [{'OK ' if good else 'SAI'}] {text!r} -> quận={d}, ngân sách/người={b} ({scope})")
print(f"  Đúng {ok}/{len(RULE_CASES)}  (ca cuối cố ý khó: luật không hiểu phủ định 'không phải')")

# 2) Gợi ý đầy đủ cho một cặp đôi
AN = Person("An", location=(10.7769, 106.7009), budget_max=400_000)
BINH = Person("Binh", location=(10.8494, 106.7537), budget_max=400_000)
profiles = {
    "An": build_profile({"b1": 5, "b6": 2, "b10": 4, "b8": 5, "p1": 1, "p2": 2, "p3": 5, "p4": 5}),
    "Binh": build_profile({"b1": 1, "b6": 5, "b10": 5, "p1": 4, "p2": 5, "p3": 2, "p4": 3}),
}
QUERIES = [
    "Tối thứ 7 muốn đi ăn tối lãng mạn ở Quận 3 hoặc Quận 1, dưới 800k cho 2 người. "
    "Mình thích chỗ yên tĩnh, còn bạn gái mê đồ ăn ngon, không ngại đi xa.",
    "cafe yên tĩnh để trò chuyện, tầm 100k/người",
]
results = []
for q in QUERIES:
    print("\n" + "=" * 70 + f"\n2. GỢI Ý: {q}\n" + "=" * 70)
    t = time.time()
    res = recommend(q, AN, BINH, profiles=profiles, use_llm=USE_LLM)
    results.append((q, res))
    p = res["parsed"]
    print(json.dumps({k: p[k] for k in ["districts", "budget_per_person", "budget_scope", "semantic_query",
                                        "llm_ok", "assumptions"]}, ensure_ascii=False, indent=1))
    if p.get("importance_a"):
        print("  Mức quan tâm An  :", p["importance_a"])
        print("  Mức quan tâm Binh:", p["importance_b"])
    print("  Xếp hạng:", res["ranking_log"])
    for it in res["items"]:
        price = f"{it['price_min'] // 1000}-{it['price_max'] // 1000}k" if it["price_min"] else "?"
        print(f"\n  #{it['rank']} {it['name']} — {it['district']}, {price} | điểm {it['group_score']} "
              f"| {it['tradeoff_label']}\n     [{it['explanation_source']}] {it['explanation']}")
    print("\n  Kiểm tra lựa chọn của LLM:", res["choose_stats"])
    print(f"  Thời gian: {time.time() - t:.1f}s")

# 3) Kiểm tra bộ chống bịa với lời giải thích giả
print("\n" + "=" * 70 + "\n3. KIỂM TRA CHỐNG BỊA\n" + "=" * 70)
from explainer import build_context, validate_explanations
ranked = results[0][1]["ranked_frame"].head(2)
ctx = build_context(ranked)
r0, r1 = list(ctx)
fake = [{"restaurant_id": r0, "explanation": f"Quán có giá chỉ 999k, món bò Wagyu tuyệt hảo, mở cửa 24/7."},
        {"restaurant_id": r1, "explanation": f"Không gian đẹp như {ctx[r0]['ten']}, rất hợp hẹn hò buổi tối."},
        {"restaurant_id": "r_khongtontai", "explanation": "Quán bịa ra, rất lãng mạn và yên tĩnh."}]
_, errs = validate_explanations(fake, ctx)
print("  Lời giải thích giả bị chặn:", errs)

# 4) Vòng phản hồi: An thích 3 quán, không thích 1 quán -> hồ sơ dịch chuyển
print("\n" + "=" * 70 + "\n4. VÒNG PHẢN HỒI\n" + "=" * 70)
T = pd.read_csv(cfg.RESTAURANT_TRAITS, encoding="utf-8-sig").set_index("restaurant_id")
rec = dict(profiles["An"])
print("  p ban đầu:", rec["p"])
ranked2 = results[1][1]["ranked_frame"]
n0 = sum(1 for _ in open(cfg.FEEDBACK_EVENTS, encoding="utf-8")) if cfg.FEEDBACK_EVENTS.exists() else 0
for pos, (_, row) in enumerate(ranked2.head(4).iterrows(), 1):
    liked = pos <= 3
    rec = update_profile(rec, T.loc[row["restaurant_id"]], liked)
    log_event("demo_an", QUERIES[1], row["restaurant_id"], liked, row.to_dict(), pos, session_id="demo")
    print(f"  {'thích' if liked else 'không thích':12s} {row['name'][:34]:34s} -> p = {rec['p']}")
n1 = sum(1 for _ in open(cfg.FEEDBACK_EVENTS, encoding="utf-8"))
print(f"  Sự kiện đã ghi cho LTR: +{n1 - n0} (tổng {n1}) -> {cfg.FEEDBACK_EVENTS.relative_to(cfg.BASE)}")
