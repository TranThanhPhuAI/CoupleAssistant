"""LLM chọn 3–5 quán trong danh sách đã lọc + viết lý do, CHỈ dựa trên dữ liệu đã truy xuất (RAG).

Chống bịa: mã quán phải nằm trong danh sách đã gửi, mọi con số phải có trong dữ liệu của chính quán đó,
không nhắc tên quán khác. Vi phạm -> loại / dùng thứ tự chấm điểm và lý do theo mẫu (xác định).
Chống prompt injection: review được làm sạch (llm.clean_text) và đánh dấu là dữ liệu.
Quyền riêng tư: chỉ nói "hợp với cả hai" ở mức chung, không nêu chi tiết tính cách của ai.
"""
import json
import re

import numpy as np
import pandas as pd

import config as cfg
from common import fold
from llm import DATA_RULE, clean_text

ASPECT_VI = {"ambience": "không gian đẹp", "romantic": "lãng mạn", "quiet": "yên tĩnh", "view": "view đẹp",
             "privacy": "riêng tư", "food": "món ăn ngon", "service": "phục vụ tốt", "price": "giá hợp lý"}
_cache = {}


def _fmt_price(lo, hi):
    if pd.isna(lo):
        return "chưa có thông tin giá"
    return f"{int(lo) // 1000}k - {int(hi) // 1000}k" if hi != lo else f"{int(lo) // 1000}k"


def _review_evidence(rid, n=2):
    """Không có câu hỏi -> lấy review khen nhiều khía cạnh hẹn hò/món ăn nhất của quán."""
    if "aspects" not in _cache:
        A = pd.read_csv(cfg.ABSA_REVIEW_PRED, encoding="utf-8-sig")
        V = pd.read_csv(cfg.REVIEWS_CLEAN, encoding="utf-8-sig", usecols=["review_id", "review_text"])
        A["s"] = A[["ambience_pos", "romantic_pos", "quiet_pos", "view_pos", "food_pos"]].sum(axis=1)
        _cache["aspects"] = A.merge(V, on="review_id")
    A = _cache["aspects"]
    top = A[A["restaurant_id"] == rid].nlargest(n, "s")
    return [clean_text(t) for t in top["review_text"]]


def _strengths(rid, k=3):
    if "scores" not in _cache:
        _cache["scores"] = pd.read_csv(cfg.SCORES, encoding="utf-8-sig").set_index("restaurant_id")
    s = _cache["scores"].loc[rid]
    z = {a: s[f"{a}_z"] for a in cfg.DATE_WEIGHTS}
    z["food"] = (s["food_pct"] - 0.5) * 4  # đưa về thang gần với z để so sánh
    return [ASPECT_VI[a] for a, v in sorted(z.items(), key=lambda x: -x[1]) if v > 0.5][:k]


def _ai_tags(rid):
    if "tags" not in _cache:
        T = (pd.read_csv(cfg.PLACE_TAGS, encoding="utf-8-sig") if cfg.PLACE_TAGS.exists()
             else pd.DataFrame(columns=["restaurant_id", "tag"]))
        _cache["tags"] = T.groupby("restaurant_id")["tag"].apply(list).to_dict()
    return _cache["tags"].get(rid, [])


def build_context(ranked, both_fit=None, interest_ids=None):
    """Dữ liệu được phép dùng cho từng quán (dict theo restaurant_id).
    interest_ids: sở thích ĐƯỢC PHÉP dùng (của người hỏi + của người kia nếu họ chia sẻ)."""
    from interests import matched_labels
    ctx = {}
    for rank, (_, r) in enumerate(ranked.iterrows(), 1):
        ev = r.get("evidence")
        snippets = ([clean_text(t) for _, t in ev][:2] if isinstance(ev, list) and ev
                    else _review_evidence(r["restaurant_id"]))
        ctx[r["restaurant_id"]] = {
            "restaurant_id": r["restaurant_id"], "hang_he_thong": rank, "ten": r["name"],
            "loai_quan": r["place_types"] if isinstance(r.get("place_types"), str) else r.get("place_type"),
            "mon": r["cuisines"] if isinstance(r.get("cuisines"), str) and r["cuisines"] else None,
            "quan": r["district"],
            "dia_chi": r["address_new"] if isinstance(r.get("address_new"), str) else r["address"],
            "gia_moi_nguoi": _fmt_price(r["price_min"], r["price_max"]),
            "gio_mo_cua": r["opening_hours"] if isinstance(r["opening_hours"], str) else "chưa có thông tin",
            "danh_gia": r["tradeoff_label"], "diem_noi_bat": _strengths(r["restaurant_id"]),
            "hop_ca_hai": bool(both_fit and both_fit.get(r["restaurant_id"], False)),
            "nhan_ai": _ai_tags(r["restaurant_id"]),
            "hop_so_thich": matched_labels(r["restaurant_id"], interest_ids or []),
            "trich_review": snippets,
        }
    return ctx


PICK_SCHEMA = {"type": "object", "properties": {"picks": {"type": "array", "items": {
    "type": "object", "properties": {"restaurant_id": {"type": "string"}, "reason": {"type": "string"}},
    "required": ["restaurant_id", "reason"]}}}, "required": ["picks"]}

PICK_SYSTEM = (
    "Bạn là trợ lý chọn quán hẹn hò ở TP.HCM. Từ danh sách 'ung_vien' đã được hệ thống lọc và chấm điểm, "
    "chọn {kmin}-{kmax} quán hợp nhất với yêu cầu và sở thích của cặp đôi, mỗi quán viết lý do 2-3 câu tiếng Việt.\n"
    "QUY TẮC BẮT BUỘC: CHỈ dùng restaurant_id có trong 'ung_vien', không tạo quán mới; chỉ dùng thông tin trong dữ liệu, "
    "không bịa món, giá, giờ, địa chỉ, không nhắc quán khác; giá chỉ ghi đúng như 'gia_moi_nguoi'. "
    "Thứ tự ưu tiên: (1) quán ĐÚNG loại quán / món mà 'yeu_cau' nhắc tới (xem 'loai_quan', 'mon', 'ten'; "
    "vd hỏi cafe thì chọn quán Café/Dessert); (2) khớp 'so_thich_chung'; (3) có 'nhan_ai' hợp hẹn hò. "
    "'hang_he_thong' là thứ hạng do hệ thống chấm (1 = tốt nhất): nếu phân vân, giữ quán hạng cao. "
    "Không nói chi tiết tính cách của ai.\n"
    + DATA_RULE + "\n"
    "Trả về JSON {{\"picks\": [{{\"restaurant_id\": ..., \"reason\": ...}}]}}."
)


def _numbers(s):
    return set(re.findall(r"\d+", s))


def validate_explanations(items, ctx):
    """Trả về (dict id -> explanation hợp lệ, danh sách lỗi)."""
    out, errors = {}, []
    names = {rid: fold(c["ten"]) for rid, c in ctx.items()}
    for it in items if isinstance(items, list) else []:
        rid, text = str(it.get("restaurant_id", "")), str(it.get("explanation", "")).strip()
        if rid not in ctx:
            errors.append(f"id lạ: {rid}")
            continue
        if not 20 <= len(text) <= 700:
            errors.append(f"{rid}: độ dài {len(text)}")
            continue
        allowed = _numbers(json.dumps(ctx[rid], ensure_ascii=False))
        bad = _numbers(text) - allowed
        if bad:
            errors.append(f"{rid}: số không có trong dữ liệu {sorted(bad)}")
            continue
        others = [n for o, n in names.items() if o != rid and len(n) > 6 and n in fold(text)]
        if others:
            errors.append(f"{rid}: nhắc quán khác")
            continue
        out[rid] = text
    missing = set(ctx) - set(out)
    if missing:
        errors.append(f"thiếu/không hợp lệ: {len(missing)} quán")
    return out, errors


def template_explanation(c):
    parts = [f"{c['ten']} ({c['quan']}, {c['gia_moi_nguoi']}/người): {c['danh_gia']}."]
    if c["diem_noi_bat"]:
        parts.append("Điểm nổi bật theo review: " + ", ".join(c["diem_noi_bat"]) + ".")
    if c["hop_ca_hai"]:
        parts.append("Quán hợp với hồ sơ của cả hai bạn.")
    if c["trich_review"]:
        parts.append(f"Một review viết: “{c['trich_review'][0][:120]}…”")
    return " ".join(parts)


def validate_picks(picks, ctx, kmax):
    """Kiểm tra đầu ra 'LLM chọn quán' (Lovespot 4.3 bước 5, BR-AI-11).
    Mã quán ngoài danh sách -> loại (đếm n_invalid_id); lý do không qua kiểm tra chống bịa -> vẫn giữ lựa chọn
    nhưng thay lý do bằng mẫu câu. Trả về (list (id, lý do hoặc None), thống kê)."""
    stats = {"n_returned": 0, "n_invalid_id": 0, "n_duplicate": 0, "n_bad_reason": 0}
    out, seen = [], set()
    for it in picks if isinstance(picks, list) else []:
        stats["n_returned"] += 1
        rid = str(it.get("restaurant_id", "")).strip()
        if rid not in ctx:
            stats["n_invalid_id"] += 1
            continue
        if rid in seen:
            stats["n_duplicate"] += 1
            continue
        seen.add(rid)
        good, _ = validate_explanations([{"restaurant_id": rid, "explanation": it.get("reason", "")}], ctx)
        if rid not in good:
            stats["n_bad_reason"] += 1
        out.append((rid, good.get(rid)))
        if len(out) == kmax:
            break
    return out, stats


def choose(shortlist, request_info, k_fallback=cfg.AI_PICK_MIN, both_fit=None, interest_ids=None,
           common_labels=None, use_llm=True, meta=None):
    """LLM chọn AI_PICK_MIN–MAX quán trong danh sách đã lọc + viết lý do; code kiểm tra; thiếu/lỗi -> bù bằng
    thứ tự chấm điểm (lý do theo mẫu). Thứ tự hiển thị luôn theo điểm công thức (xác định).
    Trả về (list dict {restaurant_id, reason, reason_source, llm_rank}, thống kê)."""
    ctx = build_context(shortlist, both_fit, interest_ids)
    order = list(ctx)  # thứ tự điểm công thức
    picks, stats = [], {"llm_used": False, "llm_error": None}
    if use_llm:
        try:
            from llm import llm_json
            cand = [{**c, "trich_review": c["trich_review"][:1]} for c in ctx.values()]  # gọn prompt
            msg = json.dumps({"yeu_cau": request_info, "so_thich_chung": common_labels or [], "ung_vien": cand},
                             ensure_ascii=False)
            system = PICK_SYSTEM.format(kmin=cfg.AI_PICK_MIN, kmax=cfg.AI_PICK_MAX)
            obj = llm_json([{"role": "system", "content": system}, {"role": "user", "content": msg}],
                              PICK_SCHEMA, timeout=300, temperature=0.2, num_ctx=12288, meta=meta)
            picks, s = validate_picks(obj.get("picks"), ctx, cfg.AI_PICK_MAX)
            stats.update(s, llm_used=True)
        except Exception as e:  # LLM lỗi / quá chậm -> vẫn hiện quán theo điểm, chỉ thiếu lý do hay
            stats["llm_error"] = f"{type(e).__name__}: {e}"
    target = cfg.AI_PICK_MIN if stats["llm_used"] else k_fallback
    llm_rank = {rid: i + 1 for i, (rid, _) in enumerate(picks)}
    chosen = dict(picks)
    for rid in order:  # bù cho đủ bằng thứ tự chấm điểm
        if len(chosen) >= target:
            break
        chosen.setdefault(rid, None)
    stats["n_fallback"] = sum(1 for r in chosen if r not in llm_rank)
    return [{"restaurant_id": rid, "reason": chosen[rid] or template_explanation(ctx[rid]),
             "reason_source": "llm" if chosen[rid] else "template", "llm_rank": llm_rank.get(rid)}
            for rid in order if rid in chosen], stats
