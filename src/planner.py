"""Lập plan hẹn hò nhiều chặng (Lovespot BR-AI-06, mục 5.1).

Code xếp plan, LLM chỉ viết lời mô tả:
  1. mỗi chặng (mặc định: ăn tối -> cà phê/tráng miệng) lấy ứng viên đang MỞ CỬA đúng giờ chặng đó;
  2. chọn tổ hợp tốt nhất theo điểm đôi, trừ điểm khi hai chặng xa nhau, loại tổ hợp vượt ngân sách;
  3. kiểm tra lại bằng code: giờ mở cửa, khoảng cách giữa chặng, tổng chi phí -> lỗi thì tự đổi ứng viên,
     vẫn lỗi thì báo người dùng tự chỉnh.
Dùng qua:  python run.py plan "không khí yên tĩnh" --luc 19:00 --nguoi-a minh --nguoi-b lan
"""
import itertools
import json
import uuid

import pandas as pd

import config as cfg
from common import is_open_at
from explainer import _fmt_price, validate_explanations
from llm import DATA_RULE
from query_parser import parse_query
from ranker import haversine_km, rank_for_couple
from recommend import prepare_people

CANDIDATES_PER_STOP = 6
SPEED_KMH, TRAVEL_BUFFER_MIN = 20, 10   # ước lượng di chuyển nội thành khi chưa có Map Service


def add_minutes(hhmm, minutes):
    h, m = map(int, hhmm.split(":"))
    t = (h * 60 + m + int(minutes)) % (24 * 60)
    return f"{t // 60:02d}:{t % 60:02d}"


def est_cost(row):
    """Chi phí ước tính mỗi người: giữa khoảng giá; thiếu giá -> None (không tính vào tổng, có cảnh báo). Đi dạo: miễn phí."""
    if row.get("kind") == "walk":
        return 0.0
    return None if pd.isna(row["price_min"]) else float((row["price_min"] + row["price_max"]) / 2)


# ======================= Chặng "đi dạo" (không phải quán) =======================
_walk_cache = None


def walk_spots():
    """Địa điểm đi dạo công cộng (data/walk_spots.json, soạn tay). Thiếu file -> rỗng (plan bỏ chặng đi dạo)."""
    global _walk_cache
    if _walk_cache is None:
        _walk_cache = json.loads(cfg.WALK_SPOTS.read_text(encoding="utf-8"))["spots"] if cfg.WALK_SPOTS.exists() else []
    return _walk_cache


def walk_candidates(at, minutes, interests):
    """Chỗ đi dạo còn mở lúc `at` (hours = None: không gian mở, lúc nào cũng được).
    Điểm = 0,45 + 0,1 × số sở thích của cặp đôi trùng nhãn chỗ đó (tối đa 0,75); tổ hợp sẽ ưu tiên chỗ gần quán trước."""
    out = []
    for s in walk_spots():
        if s["hours"] and is_open_at(s["hours"], at, minutes) is False:
            continue
        match = len(set(s["tags"]) & set(interests))
        out.append({"kind": "walk", "restaurant_id": s["id"], "name": s["name"], "district": s["district"],
                    "address": s["address"], "opening_hours": s["hours"], "price_min": None, "price_max": None,
                    "latitude": s["lat"], "longitude": s["lng"], "about": s["about"],
                    "group_score": min(0.75, 0.45 + 0.1 * match)})
    return out


def hop_km(r1, r2):
    if any(pd.isna(v) for v in (r1["latitude"], r1["longitude"], r2["latitude"], r2["longitude"])):
        return None
    return float(haversine_km(r1["latitude"], r1["longitude"], r2["latitude"], r2["longitude"]))


def schedule(rows, start, stops):
    """Giờ bắt đầu từng chặng = chặng trước + thời gian ở lại + di chuyển."""
    out, cur = [], start
    for i, (r, (label, _, minutes)) in enumerate(zip(rows, stops)):
        km = hop_km(rows[i - 1], r) if i else None
        travel = 0 if i == 0 else int(round(((km or 3.0) / SPEED_KMH * 60 + TRAVEL_BUFFER_MIN) / 5) * 5)
        cur = add_minutes(cur, travel) if i else cur
        out.append({"order": i + 1, "label": label, "start": cur, "end": add_minutes(cur, minutes),
                    "hop_km_from_prev": None if km is None else round(km, 2), "travel_min": travel})
        cur = add_minutes(cur, minutes)
    return out


def validate_plan(plan, budget=None, max_hop_km=cfg.PLAN_MAX_HOP_KM):
    """Kiểm tra plan bằng code (dùng cho cả plan do LLM hay người dùng sửa). Trả về danh sách lỗi."""
    issues, seen = [], set()
    for s in plan["stops"]:
        if s["restaurant_id"] in seen:
            issues.append(f"Chặng {s['order']}: trùng quán với chặng trước")
        seen.add(s["restaurant_id"])
        minutes = (int(s["end"][:2]) * 60 + int(s["end"][3:])) - (int(s["start"][:2]) * 60 + int(s["start"][3:]))
        ok = is_open_at(s.get("opening_hours"), s["start"], minutes % (24 * 60))
        if ok is False:
            issues.append(f"Chặng {s['order']} ({s['name']}): không mở cửa {s['start']}–{s['end']} "
                          f"(giờ mở: {s['opening_hours']})")
        if s["hop_km_from_prev"] is not None and s["hop_km_from_prev"] > max_hop_km:
            issues.append(f"Chặng {s['order']}: cách chặng trước {s['hop_km_from_prev']} km (> {max_hop_km} km)")
    total = plan.get("total_est_cost")
    if budget and total and total > budget:
        issues.append(f"Tổng chi phí ước tính {total:,.0f}đ/người vượt ngân sách {budget:,.0f}đ")
    return issues


def _combo_score(rows, budget):
    """Điểm tổ hợp: tổng điểm đôi − phạt khoảng cách; vượt ngân sách / quá xa -> loại (None)."""
    s = sum(r["group_score"] for r in rows)
    for r1, r2 in zip(rows, rows[1:]):
        km = hop_km(r1, r2)
        if km is not None:
            if km > cfg.PLAN_MAX_HOP_KM:
                return None
            s -= 0.05 * max(0.0, km - 1.0)
    costs = [c for c in (est_cost(r) for r in rows) if c is not None]
    if budget and costs and sum(costs) > budget:
        return None
    return s


def _build(rows, times, budget):
    stops_out = []
    for r, t in zip(rows, times):
        walk = r.get("kind") == "walk"
        stops_out.append({**t, "kind": "walk" if walk else "place", "restaurant_id": r["restaurant_id"], "name": r["name"],
                          "district": r["district"], "address": r["address"],
                          "opening_hours": r["opening_hours"] if isinstance(r["opening_hours"], str) else None,
                          "price": "miễn phí" if walk else _fmt_price(r["price_min"], r["price_max"]), "est_cost": est_cost(r),
                          "group_score": round(float(r["group_score"]), 4), **({"about": r["about"]} if walk else {})})
    costs = [s["est_cost"] for s in stops_out if s["est_cost"] is not None]
    return {"stops": stops_out, "total_est_cost": round(sum(costs)) if costs else None, "budget": budget,
            "cost_unknown": [s["name"] for s in stops_out if s["est_cost"] is None]}


NARRATIVE_SCHEMA = {"type": "object", "properties": {
    "stops": {"type": "array", "items": {"type": "object", "properties": {
        "restaurant_id": {"type": "string"}, "note": {"type": "string"}}, "required": ["restaurant_id", "note"]}}},
    "required": ["stops"]}
NARRATIVE_SYSTEM = (
    "Bạn viết lịch trình hẹn hò ngắn gọn, ấm áp bằng tiếng Việt: với MỖI chặng một ghi chú 1-2 câu vì sao hợp. "
    "CHỈ dùng dữ liệu được cung cấp, không bịa món, giá, giờ, không thêm quán. "
    + DATA_RULE + " Trả JSON {\"stops\": [{\"restaurant_id\": ..., \"note\": ...}]}."
)


def _narrate(plan, request_info, use_llm, meta):
    ctx = {s["restaurant_id"]: {"ten": s["name"], "quan": s["district"], "gia_moi_nguoi": s["price"],
                                "gio": f"{s['start']}-{s['end']}", "chang": s["label"],
                                **({"mo_ta": s["about"]} if s.get("kind") == "walk" else {})} for s in plan["stops"]}
    title = "Hẹn hò " + " → ".join(s["label"].lower() for s in plan["stops"])  # tiêu đề cố định (LLM hay đặt sai)
    notes, source = {}, "template"
    if use_llm:
        try:
            from llm import llm_json
            obj = llm_json([{"role": "system", "content": NARRATIVE_SYSTEM},
                               {"role": "user", "content": json.dumps({"yeu_cau": request_info, "cac_chang": ctx},
                                                                      ensure_ascii=False)}],
                              NARRATIVE_SCHEMA, timeout=180, temperature=0.4, meta=meta)
            good, _ = validate_explanations([{"restaurant_id": x.get("restaurant_id"), "explanation": x.get("note", "")}
                                             for x in obj.get("stops", [])], ctx)
            notes = good
            source = "llm" if good else "template"
        except Exception:
            pass
    for s in plan["stops"]:
        fallback = (f"Đi dạo ở {s['name']}: {s['about']}." if s.get("kind") == "walk"
                    else f"{s['label']} tại {s['name']} ({s['district']}, {s['price']}/người).")
        s["note"] = notes.get(s["restaurant_id"]) or fallback
    plan.update(title=title, narrative_source=source)
    return plan


def make_plan(a, b, profiles=None, query="", start=None, budget=None, districts=None,
              stops=None, use_llm=True, meta=None, walk=True):
    """a = người tạo plan, b = người đi cùng. Trả về plan (dict) gồm các chặng, tổng chi phí, lỗi còn lại, ghi chú.
    walk=False: bỏ chặng đi dạo (chỉ ăn tối -> cà phê)."""
    stops = [s for s in (stops or cfg.PLAN_STOPS) if walk or s[1] != "walk"]
    parsed = parse_query(query or "hẹn hò", use_llm=False)  # quận / ngân sách / giờ bằng luật (nhanh, xác định)
    start = start or parsed["time"] or "19:00"
    if budget:
        parsed["budget_per_person"] = budget
    budget = parsed["budget_per_person"]
    districts = districts or parsed["districts"] or None
    prep = prepare_people(a, b, profiles or {}, parsed)
    notes = list(parsed["assumptions"]) + prep["notes"]

    # 1) Ứng viên từng chặng, lọc theo giờ dự kiến của chặng
    cand, cur = [], start
    for label, types, minutes in stops:
        if types == "walk":   # chặng đi dạo: chỗ công cộng còn mở, hợp sở thích chung; khoảng cách xét ở bước tổ hợp
            w = walk_candidates(cur, minutes, prep["allowed"])
            if not w:
                notes.append(f"{label}: không còn chỗ đi dạo mở cửa lúc {cur} -> bỏ chặng này")
                stops = [s for s in stops if s[1] != "walk"]
                break
            cand.append(w)
            cur = add_minutes(cur, minutes + 20)
            continue
        q = f"{label.lower()} {parsed['semantic_query']}".strip()
        r = rank_for_couple(*prep["people"], query=q, k=CANDIDATES_PER_STOP, districts=districts, place_types=types,
                            personality_fit=prep["pfit"], interest_fit=prep["interest_fit"],
                            at_time=cur, stay_minutes=minutes)
        notes += [f"{label}: không có quán khớp hết điều kiện -> đã {m}" for m in r.attrs["log"]["relaxed"]]
        cand.append([row for _, row in r.iterrows()])
        cur = add_minutes(cur, minutes + 20)
    if any(len(c) == 0 for c in cand):
        return {"plan_id": None, "stops": [], "issues": ["Không tìm được quán cho mọi chặng"], "notes": notes}

    # 2) Chọn tổ hợp tốt nhất (≤ 6^số chặng tổ hợp, rất nhỏ) rồi 3) kiểm tra lại bằng giờ chính xác
    combos = sorted(((sc, rows) for rows in itertools.product(*cand)
                     if len({r["restaurant_id"] for r in rows}) == len(rows)
                     and (sc := _combo_score(rows, budget)) is not None), key=lambda x: -x[0])
    if not combos:  # không tổ hợp nào đạt hết -> lấy tổ hợp điểm cao nhất, báo lỗi để người dùng chỉnh
        combos = [(0.0, tuple(c[0] for c in cand))]
        notes.append("Không có tổ hợp nào vừa ngân sách và đủ gần -> plan dưới đây cần chỉnh")
    plan = None
    for _, rows in combos[:20]:
        trial = _build(rows, schedule(rows, start, stops), budget)
        trial["issues"] = validate_plan(trial, budget)
        if plan is None or len(trial["issues"]) < len(plan["issues"]):
            plan = trial
        if not trial["issues"]:
            break
    if plan["cost_unknown"]:
        notes.append(f"Chưa có giá của: {', '.join(plan['cost_unknown'])} -> tổng chi phí chỉ là ước tính một phần")
    plan.update(plan_id=uuid.uuid4().hex[:12], start=start, notes=notes,
                common_interests=prep["common"])
    request_info = {"mong_muon": parsed["semantic_query"], "bat_dau": start, "ngan_sach_moi_nguoi": budget}
    return _narrate(plan, request_info, use_llm, meta)


def print_plan(plan):
    print(f"\n💑 {plan.get('title', 'Plan hẹn hò')}  (bắt đầu {plan.get('start')})")
    for s in plan["stops"]:
        hop = ""
        if s["order"] > 1:
            hop = (f" | đi {s['travel_min']} phút ({s['hop_km_from_prev']} km)" if s["hop_km_from_prev"] is not None
                   else f" | đi khoảng {s['travel_min']} phút (quán chưa có tọa độ, ước tính)")
        print(f"\n  {s['start']}–{s['end']}  Chặng {s['order']}: {s['label']}{hop}")
        print(f"     {s['name']}  [{s['district']}, {s['price']}]")
        print(f"     {s['address']}")
        print(f"     {s['note']}")
    if plan.get("total_est_cost"):
        print(f"\n  Tổng chi phí ước tính: {plan['total_est_cost']:,.0f}đ/người"
              + (f" (ngân sách {plan['budget']:,.0f}đ)" if plan.get("budget") else ""))
    print("  Kiểm tra plan:", "đạt (giờ mở cửa, khoảng cách, ngân sách)" if not plan["issues"] else "")
    for i in plan["issues"]:
        print("   ⚠", i)
    for n in plan.get("notes", []):
        print("   ℹ", n)
