"""Lớp dịch vụ AI (Lovespot 4.3 bước 1 và 6, mục 5.3) — bọc ngoài recommend.py / planner.py.

  - Kiểm tra điều kiện: phải có hồ sơ; còn lượt AI trong ngày theo gói (reset 0 giờ giờ VN)  BR-AI-01/02
  - Hết lượt -> thông báo + đề nghị nâng gói (không gọi AI)                                  BR-AI-04
  - Mỗi yêu cầu tính 1 lượt; lỗi hệ thống và lần không ra kết quả KHÔNG tính                 BR-AI-14
  - Ghi nhật ký theo đúng bảng trong tài liệu: ai_requests, ai_suggestion_results, date_plans (JSONL)
  - chosen_at khi người dùng chọn quán -> tỷ lệ chọn quán AI gợi ý; đồng thời cập nhật hồ sơ (phản hồi)
Nhật ký chỉ lưu mã người dùng đã băm.

Chạy:  python ai_service.py thongke          (chỉ số đánh giá AI)
"""
import hashlib
import json
import os
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

import config as cfg
from personality import ProfileStore
from ranker import Person

VN = timezone(timedelta(hours=cfg.AI_TZ_OFFSET_HOURS))
PARTNER = "nguoi_di_cung"  # tên nội bộ khi người đi cùng chưa có hồ sơ


def _hash(uid):
    return hashlib.sha256(str(uid).encode()).hexdigest()[:16]


def _couple(a, b):
    return _hash("|".join(sorted([str(a), str(b)]))) if b else None


class AiLog:
    """Đường dẫn nhật ký (đổi được để kiểm thử trên thư mục tạm)."""

    def __init__(self, root=cfg.AI_LOG_DIR):
        self.root = Path(root)
        self.requests = self.root / cfg.AI_REQUESTS.name
        self.results = self.root / cfg.AI_RESULTS.name
        self.plans = self.root / cfg.DATE_PLANS.name

    def read(self, path):
        if not path.exists():
            return []
        return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]

    def append(self, path, rec):
        self.root.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


# ======================= Hạn mức =======================

def quota(user_id, plan, log):
    """(đã dùng hôm nay, hạn mức) — đếm từ ai_requests, không lưu cột đếm riêng."""
    today = datetime.now(VN).date().isoformat()
    used = sum(1 for r in log.read(log.requests)
               if r["user"] == _hash(user_id) and r["local_date"] == today and r["counted"])
    return used, cfg.AI_PLANS.get(plan, cfg.AI_PLANS["free"])


def _new_request(kind, user_a, user_b, input_json):
    now = datetime.now(timezone.utc)
    return {"request_id": uuid.uuid4().hex[:16], "kind": kind, "user": _hash(user_a), "couple": _couple(user_a, user_b),
            "created_at": now.isoformat(timespec="seconds"), "local_date": now.astimezone(VN).date().isoformat(),
            "input_json": input_json, "status": None, "counted": False}


def _load_people(user_a, user_b, loc_a, loc_b, budget, store):
    pa = store.load(user_a)
    if pa is None:
        return None, None, f"Bạn ({user_a}) chưa có hồ sơ sở thích — cần tạo hồ sơ trước khi hỏi AI."
    pb = store.load(user_b) if user_b else None
    name_b = user_b if pb else PARTNER
    profiles = {user_a: pa, **({name_b: pb} if pb else {})}
    return (Person(user_a, loc_a, budget), Person(name_b, loc_b, budget)), profiles, None


def _check_quota(user_a, profile, log, req, unlimited=False):
    used, limit = quota(user_a, profile.get("plan", "free"), log)
    if unlimited:   # quản trị viên: không giới hạn lượt (vẫn ghi nhật ký để thống kê)
        return {"quota": {"used": used, "limit": None}}
    if used >= limit:
        req.update(status="quota_exceeded", counted=False)
        log.append(log.requests, req)
        return {"status": "quota_exceeded", "request_id": req["request_id"], "quota": {"used": used, "limit": limit},
                "message": f"Bạn đã dùng hết {limit} lượt AI hôm nay (gói {profile.get('plan', 'free')}). "
                           f"Nâng cấp gói để có thêm lượt, hoặc quay lại sau 0 giờ."}
    return {"quota": {"used": used, "limit": limit}}


# ======================= Gợi ý quán =======================

def suggest(query, user_a, user_b=None, loc_a=None, loc_b=None, budget=None, at_time=None, use_llm=True,
            k=cfg.AI_PICK_MIN, store=None, log=None, unlimited=False):
    """Gợi ý quán cho người dùng có hồ sơ. Trả về dict có status: success | no_result | error | quota_exceeded | no_profile.
    unlimited=True (quản trị viên): bỏ qua hạn mức lượt AI trong ngày."""
    store, log = store or ProfileStore(), log or AiLog()
    people, profiles, err = _load_people(user_a, user_b, loc_a, loc_b, budget, store)
    if err:
        return {"status": "no_profile", "message": err}
    req = _new_request("suggest", user_a, user_b, {"query": query, "at_time": at_time, "budget": budget,
                                                   "has_partner_profile": len(profiles) == 2})
    q = _check_quota(user_a, profiles[user_a], log, req, unlimited)
    if q.get("status"):
        return q
    from recommend import recommend
    meta, t0, res = {}, time.time(), None
    try:
        res = recommend(query, *people, profiles=profiles, k=k, use_llm=use_llm, at_time=at_time, meta=meta)
        status = "success" if res["items"] else "no_result"
    except Exception as e:  # lỗi hệ thống: không tính lượt (BR-AI-14)
        status, meta["error"] = "error", f"{type(e).__name__}: {e}"
    st = (res or {}).get("choose_stats", {})
    req.update(status=status, counted=status == "success", latency_ms=int((time.time() - t0) * 1000),
               llm_latency_ms=meta.get("latency_ms"), prompt_tokens=meta.get("prompt_tokens"),
               output_tokens=meta.get("output_tokens"), model=meta.get("model"), llm_provider=meta.get("provider"), error=meta.get("error"),
               llm_used=st.get("llm_used", False), llm_error=st.get("llm_error"),
               n_returned=st.get("n_returned"), n_invalid_id=st.get("n_invalid_id", 0),
               n_bad_reason=st.get("n_bad_reason", 0), n_fallback=st.get("n_fallback", 0),
               formula_top=(res or {}).get("shortlist", [])[:cfg.AI_PICK_MAX])
    log.append(log.requests, req)
    for it in (res or {}).get("items", []):
        log.append(log.results, {"request_id": req["request_id"], "place_id": it["restaurant_id"], "rank": it["rank"],
                                 "score": it["group_score"], "score_breakdown_json": it["score_breakdown"],
                                 "reason": it["explanation"], "reason_source": it["explanation_source"],
                                 "llm_rank": it["llm_rank"], "chosen_at": None})
    used = q["quota"]["used"] + (1 if req["counted"] else 0)
    out = {"status": status, "request_id": req["request_id"], "quota": {"used": used, "limit": q["quota"]["limit"]}}
    if status == "error":
        out["message"] = "Hệ thống AI đang lỗi, lượt này không bị tính. Vui lòng thử lại."
    return {**(res or {}), **out}


def _owns(log, request_id, user_id):
    """Yêu cầu gợi ý này có phải của người đang thao tác không (không cho đánh dấu hộ người khác)."""
    return any(r["request_id"] == request_id and r["user"] == _hash(user_id) for r in log.read(log.requests))


def _rewrite_results(log, rows):
    tmp = log.results.with_suffix(".tmp")
    tmp.write_text("".join(json.dumps(r, ensure_ascii=False, default=str) + "\n" for r in rows), encoding="utf-8")
    os.replace(tmp, log.results)


def choose_place(request_id, place_id, user_id, liked=True, store=None, log=None):
    """Người dùng chọn quán từ gợi ý (BR-AI-15): ghi chosen_at + dùng làm phản hồi cập nhật hồ sơ.
    Chọn lại quán đã chọn thì không cập nhật hồ sơ lần nữa."""
    store, log = store or ProfileStore(), log or AiLog()
    if not _owns(log, request_id, user_id):
        return False
    rows = log.read(log.results)
    found = next((r for r in rows if r["request_id"] == request_id and r["place_id"] == place_id), None)
    if not found:
        return False
    if found.get("chosen_at"):
        return True
    found["chosen_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    prof = store.load(user_id)
    if prof and "p" in prof:  # có hồ sơ tính cách -> cập nhật Bayes (feedback.py); giữ bản cũ để bỏ chọn trả lại đúng
        import pandas as pd
        from feedback import update_profile
        traits = pd.read_csv(cfg.RESTAURANT_TRAITS, encoding="utf-8-sig").set_index("restaurant_id")
        found["p_before"] = prof["p"]
        store.write(update_profile(prof, traits.loc[place_id], liked))
    _rewrite_results(log, rows)
    return True


def unchoose_place(request_id, place_id, user_id, store=None, log=None):
    """Bỏ chọn quán: xóa chosen_at và trả hồ sơ tính cách về như trước khi chọn (nếu lúc chọn có cập nhật)."""
    store, log = store or ProfileStore(), log or AiLog()
    if not _owns(log, request_id, user_id):
        return False
    rows = log.read(log.results)
    found = next((r for r in rows if r["request_id"] == request_id and r["place_id"] == place_id), None)
    if not found:
        return False
    if not found.pop("chosen_at", None):
        return True
    before = found.pop("p_before", None)
    if before is not None:
        prof = store.load(user_id)
        if prof and "p" in prof:
            prof["p"] = before
            store.write(prof)
    _rewrite_results(log, rows)
    return True


# ======================= Lập plan =======================

def plan(query, user_a, user_b=None, loc_a=None, loc_b=None, budget=None, start=None, use_llm=True,
         store=None, log=None, unlimited=False, walk=True):
    """Lập plan hẹn hò (BR-AI-06), tính 1 lượt AI như gợi ý quán. unlimited=True: quản trị viên, không giới hạn lượt.
    walk=True: thêm chặng đi dạo sau cà phê."""
    store, log = store or ProfileStore(), log or AiLog()
    people, profiles, err = _load_people(user_a, user_b, loc_a, loc_b, budget, store)
    if err:
        return {"status": "no_profile", "message": err}
    req = _new_request("plan", user_a, user_b, {"query": query, "start": start, "budget": budget})
    q = _check_quota(user_a, profiles[user_a], log, req, unlimited)
    if q.get("status"):
        return q
    from planner import make_plan
    meta, t0, p = {}, time.time(), None
    try:
        p = make_plan(*people, profiles=profiles, query=query, start=start, budget=budget, use_llm=use_llm, meta=meta, walk=walk)
        status = "success" if p.get("stops") else "no_result"
    except Exception as e:
        status, meta["error"] = "error", f"{type(e).__name__}: {e}"
    req.update(status=status, counted=status == "success", latency_ms=int((time.time() - t0) * 1000),
               llm_latency_ms=meta.get("latency_ms"), prompt_tokens=meta.get("prompt_tokens"),
               output_tokens=meta.get("output_tokens"), model=meta.get("model"), llm_provider=meta.get("provider"), error=meta.get("error"),
               plan_issues=len((p or {}).get("issues", [])))
    log.append(log.requests, req)
    if p and p.get("stops"):
        log.append(log.plans, {"plan_id": p["plan_id"], "request_id": req["request_id"], "couple": req["couple"],
                               "start": p["start"], "total_est_cost": p["total_est_cost"], "issues": p["issues"],
                               "date_plan_stops": [{k: s[k] for k in ("order", "label", "restaurant_id", "start", "end",
                                                                      "hop_km_from_prev", "est_cost")} for s in p["stops"]]})
    used = q["quota"]["used"] + (1 if req["counted"] else 0)
    return {**(p or {}), "status": status, "request_id": req["request_id"],
            "quota": {"used": used, "limit": q["quota"]["limit"]}}


# ======================= Chỉ số (mục 5.3) =======================

def metrics(log=None):
    log = log or AiLog()
    reqs, res = log.read(log.requests), log.read(log.results)
    if not reqs:
        return {"n_requests": 0}
    by = {}
    for r in reqs:
        by[r["status"]] = by.get(r["status"], 0) + 1
    sug = [r for r in reqs if r["kind"] == "suggest" and r["status"] == "success"]
    chosen = {r["request_id"] for r in res if r.get("chosen_at")}
    lat = [r["latency_ms"] for r in reqs if r.get("latency_ms")]
    llm = [r for r in sug if r.get("llm_used")]
    returned = sum(r.get("n_returned") or 0 for r in llm)
    picks = {}
    for r in res:
        picks.setdefault(r["request_id"], []).append(r["place_id"])
    overlap = [len(set(picks.get(r["request_id"], [])) & set(r.get("formula_top", [])[:len(picks.get(r["request_id"], []))]))
               / max(1, len(picks.get(r["request_id"], []))) for r in llm]
    counts = {}
    for r in res:
        counts[r["place_id"]] = counts.get(r["place_id"], 0) + 1
    return {
        "n_requests": len(reqs), "by_status": by,
        "choose_rate": round(len(chosen & {r["request_id"] for r in sug}) / len(sug), 3) if sug else None,
        "llm_used_rate": round(len(llm) / len(sug), 3) if sug else None,
        "invalid_id_blocked": sum(r.get("n_invalid_id", 0) for r in llm),
        "invalid_id_rate": round(sum(r.get("n_invalid_id", 0) for r in llm) / returned, 3) if returned else None,
        "bad_reason_replaced": sum(r.get("n_bad_reason", 0) for r in llm),
        "fallback_rate": round(sum(1 for r in sug if r.get("n_fallback")) / len(sug), 3) if sug else None,
        "latency_ms_avg": int(np.mean(lat)) if lat else None, "latency_ms_p95": int(np.percentile(lat, 95)) if lat else None,
        "tokens_avg": int(np.mean([(r.get("prompt_tokens") or 0) + (r.get("output_tokens") or 0) for r in llm])) if llm else None,
        "llm_vs_formula_overlap": round(float(np.mean(overlap)), 3) if overlap else None,
        "top_suggested": sorted(counts.items(), key=lambda x: -x[1])[:5],
    }


def print_metrics(m):
    import pandas as pd
    if not m.get("n_requests"):
        print("Chưa có yêu cầu AI nào trong nhật ký.")
        return
    names = pd.read_csv(cfg.RESTAURANTS_CLEAN, encoding="utf-8-sig").set_index("restaurant_id")["name"]
    pct = lambda v: "—" if v is None else f"{v:.0%}"  # noqa: E731
    print("CHỈ SỐ AI (Lovespot mục 5.3)\n")
    print(f"  Số yêu cầu: {m['n_requests']}  | theo trạng thái: {m['by_status']}")
    print(f"  Tỷ lệ chọn quán AI gợi ý:            {pct(m['choose_rate'])}")
    print(f"  Tỷ lệ dùng được LLM:                  {pct(m['llm_used_rate'])}")
    print(f"  Mã quán bịa bị chặn:                  {m['invalid_id_blocked']} ({pct(m['invalid_id_rate'])} số quán LLM trả về)")
    print(f"  Lý do bị thay vì không qua kiểm tra:  {m['bad_reason_replaced']}")
    print(f"  Tỷ lệ phải bù bằng thứ tự chấm điểm:  {pct(m['fallback_rate'])}")
    print(f"  Độ trễ: trung bình {m['latency_ms_avg']} ms, p95 {m['latency_ms_p95']} ms | token TB/lần: {m['tokens_avg']}")
    print(f"  LLM chọn trùng top chấm điểm:         {pct(m['llm_vs_formula_overlap'])} (thấp = LLM thay đổi kết quả nhiều)")
    print("  Quán được gợi ý nhiều nhất:", ", ".join(f"{names.get(p, p)[:28]} ({c})" for p, c in m["top_suggested"]))
    print("\n  Tỷ lệ gợi ý dẫn đến đặt chỗ done: cần dữ liệu bookings từ backend (chưa có trong module này).")
    print("  So sánh chất lượng AI với chỉ chấm điểm: python run.py danhgia (NDCG@5 của V3 so với V5_llm).")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) > 1 and sys.argv[1] == "thongke":
        print_metrics(metrics())
    else:
        print(__doc__)
