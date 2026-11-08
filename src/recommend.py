"""Lõi gợi ý quán (dùng cho CLI và API web) — đúng quy trình Lovespot 4.3:

    hiểu câu hỏi -> lọc cứng (khu vực, ngân sách, đang mở cửa; nới dần nếu trống)
    -> chấm điểm xác định (TOPSIS từng người + gộp hai người) giữ AI_SHORTLIST quán
    -> LLM chọn 3–5 quán + lý do -> code kiểm tra, sai thì dùng thứ tự chấm điểm

Kiểm tra lượt AI và ghi nhật ký nằm ở ai_service.py (lớp dịch vụ phía trên).
"""
import numpy as np
import pandas as pd

import config as cfg
from explainer import _ai_tags, choose
from interests import LABEL, couple_interest_scores
from personality import adjust_weights, personality_fit
from query_parser import parse_query
from ranker import Person, rank_for_couple

_traits = None


def _get_traits():
    global _traits
    if _traits is None:
        _traits = pd.read_csv(cfg.RESTAURANT_TRAITS, encoding="utf-8-sig")
    return _traits


def _num(v, nd=4):
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else round(float(v), nd)


def prepare_people(a, b, profiles, parsed):
    """Dùng chung cho gợi ý quán và lập plan: trọng số, sở thích, tính cách của hai người.
    Sở thích của b chỉ được dùng khi b bật share_interests_with_partner (BR-AI-12).
    Trả về dict: people, pfit, interest_fit, allowed (sở thích được dùng), common (sở thích chung), notes."""
    pa, pb = profiles.get(a.name, {}), profiles.get(b.name, {})
    b_shares = bool(pb.get("share_interests_with_partner"))
    ia, ib, common, notes = couple_interest_scores(pa.get("interests", []), pb.get("interests", []), b_shares)
    allowed = list(dict.fromkeys(pa.get("interests", []) + (pb.get("interests", []) if b_shares else [])))
    # Trọng số: mặc định -> chỉnh nhẹ theo tính cách -> ghi đè theo điều người dùng vừa nói
    people, pfit = [], {}
    for p, prof, w_query in ((a, pa, parsed["weights_a"]), (b, pb, parsed["weights_b"])):
        w = adjust_weights(prof) if "p" in prof else dict(cfg.DEFAULT_WEIGHTS)
        w.update(w_query)
        people.append(Person(p.name, p.location, parsed["budget_per_person"] or p.budget_max, weights=w))
        if "p" in prof:
            pfit[p.name] = personality_fit(prof, _get_traits())
    return {"people": people, "pfit": pfit or None, "interest_fit": {a.name: ia, b.name: ib},
            "allowed": allowed, "common": common, "notes": notes}


def both_fit_map(ranked, a, b, pfit):
    if not pfit or len(pfit) < 2:
        return None
    return dict(zip(ranked["restaurant_id"], (ranked[f"pfit_{a.name}"] >= 0.6) & (ranked[f"pfit_{b.name}"] >= 0.6)))


def recommend(query, a, b, profiles=None, k=cfg.AI_PICK_MIN, use_llm=True, at_time=None, meta=None):
    """a = người hỏi, b = người đi cùng (Person: tên, vị trí, ngân sách).
    profiles: {tên: hồ sơ} chỉ của người ĐÃ đồng ý lưu (xem personality.ProfileStore).
    k: số quán trả về khi không dùng được LLM (có LLM thì LLM chọn 3–5)."""
    parsed = parse_query(query, use_llm=use_llm)
    at_time = at_time or parsed.get("time")
    prep = prepare_people(a, b, profiles or {}, parsed)
    notes = list(parsed["assumptions"]) + prep["notes"]
    common, allowed = prep["common"], prep["allowed"]

    ranked = rank_for_couple(*prep["people"], query=parsed["semantic_query"], k=cfg.AI_SHORTLIST,
                             districts=parsed["districts"] or None, personality_fit=prep["pfit"],
                             interest_fit=prep["interest_fit"], at_time=at_time)
    log = ranked.attrs["log"]
    notes += [f"Không có quán nào khớp hết điều kiện -> đã {msg}" for msg in log["relaxed"]]
    both_fit = both_fit_map(ranked, a, b, prep["pfit"])

    request_info = {"mong_muon": parsed["semantic_query"], "gio_hen": at_time,
                    "ngan_sach_moi_nguoi": parsed["budget_per_person"], "khu_vuc": parsed["districts"]}
    picks, stats = choose(ranked, request_info, k_fallback=k, both_fit=both_fit, interest_ids=allowed,
                          common_labels=[LABEL[i] for i in common], use_llm=use_llm, meta=meta)
    if stats.get("llm_error"):
        notes.append("LLM lỗi hoặc quá chậm -> dùng kết quả chấm điểm, lý do theo mẫu")

    R = ranked.set_index("restaurant_id")
    items = []
    for i, pk in enumerate(picks, 1):
        r = R.loc[pk["restaurant_id"]]
        breakdown = {c: _num(r.get(c)) for c in ["couple_score", "semantic_match", "price_fit", "food_score", "date_score"]}
        for p in (a, b):
            breakdown.update({f"topsis_{p.name}": _num(r[f"topsis_{p.name}"]), f"distance_km_{p.name}": _num(r[f"dist_{p.name}"], 2),
                              f"interest_{p.name}": _num(r[f"ifit_{p.name}"]), f"personality_{p.name}": _num(r[f"pfit_{p.name}"])})
        items.append({"rank": i, "restaurant_id": pk["restaurant_id"], "name": r["name"], "district": r["district"],
                      "address": r["address"], "opening_hours": r["opening_hours"] if isinstance(r["opening_hours"], str) else None,
                      "price_min": None if pd.isna(r["price_min"]) else int(r["price_min"]),
                      "price_max": None if pd.isna(r["price_max"]) else int(r["price_max"]),
                      "group_score": round(float(r["group_score"]), 4), "tradeoff_label": r["tradeoff_label"],
                      "tags": _ai_tags(pk["restaurant_id"]), "explanation": pk["reason"],
                      "explanation_source": pk["reason_source"], "llm_rank": pk["llm_rank"], "score_breakdown": breakdown})
    return {"parsed": parsed, "at_time": at_time, "items": items, "notes": notes,
            "common_interests": [LABEL[i] for i in common], "shortlist": ranked["restaurant_id"].tolist(),
            "choose_stats": stats, "ranking_log": log, "ranked_frame": ranked}
