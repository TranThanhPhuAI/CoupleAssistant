"""Hỏi gợi ý quán / lập plan hẹn hò trên terminal.

    python run.py hoi "chỗ ăn tối lãng mạn Quận 3 dưới 800k cho 2 người"
    python run.py hoi "cafe yên tĩnh lúc 20h" --nguoi-a minh --nguoi-b lan
    python run.py plan "không khí yên tĩnh" --luc 19:00 --ngan-sach 300000 --nguoi-a minh --nguoi-b lan
    python run.py hoi                      (hỏi liên tục, gõ q để thoát)

--nguoi-a / --nguoi-b : mã hồ sơ (tạo bằng: python run.py hoso tao <mã>) -> dùng sở thích, tính lượt AI, ghi nhật ký.
                        Không ghi -> chế độ khách (dùng thử, không lưu gì).
--luc 19:30           : giờ hẹn -> chỉ gợi ý quán đang mở cửa (cũng hiểu từ câu hỏi: "lúc 7 giờ tối")
--loc-a / --loc-b     : vị trí (vĩ độ,kinh độ) của hai người   --budget/--ngan-sach: ngân sách mỗi người
--no-llm              : không cần Ollama
"""
import argparse
import sys

import config as cfg  # noqa: F401  (đặt biến môi trường trước khi nạp model)


def _loc(s):
    if not s:
        return None
    lat, lon = (float(x) for x in s.split(","))
    return lat, lon


def warn(res):
    hint = "\n  Tạo bằng: python run.py hoso tao <mã>   (hoặc trên web: tab \"Hồ sơ sở thích\")" \
        if res["status"] == "no_profile" else ""
    print(f"\n⚠ {res['message']}{hint}")


def show(res):
    if res.get("status") in {"quota_exceeded", "no_profile", "error"}:
        warn(res)
        return
    p = res["parsed"]
    budget = f"{p['budget_per_person']:,.0f}đ" if p["budget_per_person"] else "không giới hạn"
    print(f"\nHiểu câu hỏi: quận={p['districts'] or 'bất kỳ'} | ngân sách/người={budget} | giờ hẹn={res.get('at_time') or '—'}"
          f" | tìm: \"{p['semantic_query']}\"" + ("" if p["llm_ok"] else "  (không dùng LLM)"))
    if res.get("common_interests"):
        print("Sở thích chung:", ", ".join(res["common_interests"]))
    for n in res.get("notes", []):
        print("  ℹ", n)
    if not res["items"]:
        print("Không tìm thấy quán phù hợp. Thử nới quận/ngân sách/giờ.")
    for it in res["items"]:
        price = f"{it['price_min'] // 1000}k-{it['price_max'] // 1000}k" if it["price_min"] else "chưa rõ giá"
        print(f"\n#{it['rank']} {it['name']}  [{it['district']}, {price}]  điểm {it['group_score']:.2f}")
        print(f"   {it['address']}" + (f" | mở cửa {it['opening_hours']}" if it.get("opening_hours") else ""))
        tags = f" | nhãn: {', '.join(it['tags'][:4])}" if it.get("tags") else ""
        print(f"   -> {it['tradeoff_label']}{tags}")
        print(f"   {it['explanation']}")
    if res.get("request_id"):
        q = res["quota"]
        print(f"\n(mã yêu cầu {res['request_id']} | lượt AI hôm nay: {q['used']}/{q['limit']})")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Gợi ý quán / lập plan hẹn hò cho cặp đôi ở TP.HCM")
    ap.add_argument("query", nargs="?", help="câu hỏi tự nhiên")
    ap.add_argument("--plan", action="store_true", help="lập plan nhiều chặng thay vì gợi ý quán")
    ap.add_argument("--nguoi-a")
    ap.add_argument("--nguoi-b")
    ap.add_argument("--luc", help="giờ hẹn HH:MM")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--k", type=int, default=cfg.AI_PICK_MIN, help="số quán khi không dùng LLM")
    ap.add_argument("--loc-a")
    ap.add_argument("--loc-b")
    ap.add_argument("--budget", "--ngan-sach", dest="budget", type=float)
    args = ap.parse_args()
    loc_a, loc_b, use_llm = _loc(args.loc_a), _loc(args.loc_b), not args.no_llm

    def ask(q):
        if args.plan:
            from ai_service import plan
            from planner import make_plan, print_plan
            from ranker import Person
            p = (plan(q, args.nguoi_a, args.nguoi_b, loc_a, loc_b, args.budget, args.luc, use_llm) if args.nguoi_a
                 else make_plan(Person("A", loc_a, args.budget), Person("B", loc_b, args.budget), query=q,
                                start=args.luc, budget=args.budget, use_llm=use_llm))
            if p.get("status") in {"quota_exceeded", "no_profile", "error"}:
                warn(p)
            elif not p.get("stops"):
                print("\nKhông lập được plan:", "; ".join(p.get("issues", [])))
            else:
                print_plan(p)
            return
        if args.nguoi_a:
            from ai_service import suggest
            show(suggest(q, args.nguoi_a, args.nguoi_b, loc_a, loc_b, args.budget, args.luc, use_llm, k=args.k))
        else:
            from ranker import Person
            from recommend import recommend
            show(recommend(q, Person("A", loc_a, args.budget), Person("B", loc_b, args.budget), k=args.k,
                           use_llm=use_llm, at_time=args.luc))

    if args.query is not None:
        ask(args.query)
        return
    print("Nhập câu hỏi (vd: 'cafe yên tĩnh Quận 1 tầm 100k/người lúc 20h'), 'q' để thoát.")
    while True:
        try:
            q = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in {"q", "quit", "exit"}:
            break
        if q:
            ask(q)


if __name__ == "__main__":
    main()
