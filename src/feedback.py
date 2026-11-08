"""Giai đoạn 6c: vòng phản hồi thích/không thích.

1) Cập nhật hồ sơ tính cách bằng Bayes đơn giản (pseudo-count Beta mỗi chiều):
   khởi tạo từ bảng hỏi: alpha = p·N0, beta = (1-p)·N0
   thích quán có tính chất q:     alpha += s·q,      beta += s·(1-q)      (kéo p về phía q)
   không thích:                   alpha += s'·(1-q), beta += s'·q         (đẩy p ra xa q, tín hiệu yếu hơn)
   p mới = alpha / (alpha + beta). Xác định, không cần huấn luyện lại.
2) Ghi nhật ký sự kiện kèm đặc trưng lúc xếp hạng -> dữ liệu cho Learning-to-Rank (LightGBM lambdarank) sau này.
"""
import hashlib
import json
from datetime import datetime, timezone

import config as cfg
from personality import DIMENSIONS

LTR_FEATURES = ["couple_score", "food_score", "date_score", "semantic_match", "price_fit", "bayes_rating"]


def init_beta(profile):
    n0 = cfg.FEEDBACK_PRIOR_N
    return {k: [profile["p"][k] * n0, (1 - profile["p"][k]) * n0] for k in DIMENSIONS}


def update_profile(record, traits_row, liked):
    """record: hồ sơ (dict từ ProfileStore). traits_row: q của quán (Series/dict). Trả về record đã cập nhật."""
    beta = record.get("beta") or init_beta(record)
    s = cfg.FEEDBACK_LIKE_STEP if liked else cfg.FEEDBACK_DISLIKE_STEP
    for k in DIMENSIONS:
        q = float(traits_row[k])
        a_inc, b_inc = (q, 1 - q) if liked else (1 - q, q)
        beta[k][0] += s * a_inc
        beta[k][1] += s * b_inc
    record["beta"] = beta
    record["p"] = {k: round(a / (a + b), 4) for k, (a, b) in beta.items()}
    return record


def log_event(user_id, query, restaurant_id, liked, rank_row, position, session_id=None):
    """Ghi 1 dòng JSONL. user_id được băm (không lưu định danh gốc trong nhật ký)."""
    cfg.FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    feats = {f: (None if rank_row.get(f) is None or rank_row.get(f) != rank_row.get(f) else float(rank_row[f]))
             for f in LTR_FEATURES}
    ev = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
          "user": hashlib.sha256(str(user_id).encode()).hexdigest()[:16], "session": session_id,
          "query": query, "restaurant_id": restaurant_id, "label": int(bool(liked)), "position": position,
          "features": feats}
    with open(cfg.FEEDBACK_EVENTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return ev
