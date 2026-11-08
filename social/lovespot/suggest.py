"""Gợi ý kiểu 'People you may know', theo khuynh hướng Couple Assistant: cùng gu ăn uống quan trọng hơn chức danh.

Điểm một người lạ = 2 × số bạn chung + 1 × số sở thích chung (chỉ khi họ cho hiện gu) + 1 nếu cùng quận.
Công thức xác định, giải thích được: mỗi gợi ý kèm lý do ("3 bạn chung", "Cùng thích: Cà phê, Yên tĩnh").
"""
import json

from . import config as cfg
from .catalog import INTERESTS, place_public, places
from .db import connection_ids


def interests_of(row):
    try:
        return [i for i in json.loads(row["interests"] or "[]") if i in INTERESTS]
    except (ValueError, TypeError):
        return []


def shared_labels(a_row, b_row):
    if not b_row["show_interests"]:
        return []
    common = set(interests_of(a_row)) & set(interests_of(b_row))
    return [INTERESTS[i][0] for i in interests_of(a_row) if i in common]


def people(con, me, limit=cfg.SUGGEST_PEOPLE):
    mine = connection_ids(con, me["id"])
    busy = {r["o"] for r in con.execute(   # đã kết nối hoặc đang chờ
        "SELECT CASE WHEN a=? THEN b ELSE a END AS o FROM connections WHERE a=? OR b=?", (me["id"],) * 3)}
    out = []
    for u in con.execute("SELECT * FROM users WHERE id != ?", (me["id"],)):
        if u["id"] in busy:
            continue
        mutual = len(mine & connection_ids(con, u["id"])) if mine else 0
        shared = shared_labels(me, u)
        same_district = bool(me["district"]) and me["district"] == u["district"]
        score = 2 * mutual + len(shared) + (1 if same_district else 0)
        if score == 0:
            continue
        why = ([f"{mutual} bạn chung"] if mutual else []) + \
              ([f"Cùng thích: {', '.join(shared[:3])}"] if shared else []) + \
              ([f"Cùng {u['district']}"] if same_district else [])
        out.append((score, u["id"], {"username": u["username"], "display_name": u["display_name"], "headline": u["headline"],
                                     "is_demo": bool(u["is_demo"]), "reason": " · ".join(why)}))
    out.sort(key=lambda x: (-x[0], x[1]))
    return [x[2] for x in out[:limit]]


def places_for(con, me, limit=cfg.SUGGEST_PLACES):
    """Quán bạn bè review nhiều (chưa theo dõi), rồi tới quán được review nhiều nhất toàn mạng."""
    mine = connection_ids(con, me["id"])
    followed = {r["place_id"] for r in con.execute("SELECT place_id FROM place_follows WHERE user_id=?", (me["id"],))}
    counts = {}
    for r in con.execute("SELECT place_id, author_id FROM posts WHERE place_id IS NOT NULL AND visibility='public' "
                         "OR (place_id IS NOT NULL AND author_id IN (SELECT value FROM json_each(?)))",
                         (json.dumps(sorted(mine)),)):
        if r["place_id"] in followed or r["place_id"] not in places():
            continue
        c = counts.setdefault(r["place_id"], [0, 0])
        c[0 if r["author_id"] in mine else 1] += 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1][0], -kv[1][1], kv[0]))[:limit]
    return [{**place_public(places()[pid]),
             "reason": f"{f} bạn đã nhắc tới" if f else f"{n} bài viết trên Lovespot"} for pid, (f, n) in ranked]
