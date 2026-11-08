"""Bài viết (trạng thái / review / check-in tại quán thật), bảng tin, thích, bình luận, trang quán, thông báo.

Quyền xem bài: 'public' = mọi người đăng nhập; 'connections' = tác giả và người đã kết nối với tác giả.
"""
import json
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from . import config as cfg
from . import media
from .catalog import place_public, places, search_places
from .db import connection_ids, notify, session
from .security import current_user

router = APIRouter(prefix="/api")


class PostIn(BaseModel):
    kind: Literal["status", "review", "checkin"] = "status"
    body: str = Field("", max_length=cfg.MAX_POST)
    place_id: Optional[str] = Field(None, max_length=64)
    rating: Optional[int] = Field(None, ge=1, le=5)
    visibility: Literal["public", "connections"] = "public"
    images: List[str] = Field(default_factory=list, max_length=cfg.MAX_IMAGES)   # tên file từ /api/uploads

    @model_validator(mode="after")
    def _rules(self):
        self.body = self.body.strip()
        if not self.body and not self.images:
            raise ValueError("Bài viết cần nội dung hoặc ảnh")
        if self.kind in ("review", "checkin") and not self.place_id:
            raise ValueError("Review và check-in phải gắn với một quán")
        if self.kind == "review" and self.rating is None:
            raise ValueError("Review cần chấm sao (1–5)")
        if self.kind != "review":
            self.rating = None
        return self


class CommentIn(BaseModel):
    body: str = Field(..., min_length=1, max_length=cfg.MAX_COMMENT)


def can_see(con, viewer_id, post):
    return post["visibility"] == "public" or post["author_id"] == viewer_id or \
        post["author_id"] in connection_ids(con, viewer_id)


def serialize(con, viewer_id, rows):
    """Bài viết kèm tác giả, quán, số thích / bình luận, mình đã thích chưa."""
    out = []
    for p in rows:
        a = dict(con.execute("SELECT username, display_name, headline, is_demo FROM users WHERE id=?", (p["author_id"],)).fetchone())
        a["is_demo"] = bool(a["is_demo"])
        n_like = con.execute("SELECT COUNT(*) FROM likes WHERE post_id=?", (p["id"],)).fetchone()[0]
        n_cmt = con.execute("SELECT COUNT(*) FROM comments WHERE post_id=?", (p["id"],)).fetchone()[0]
        liked = con.execute("SELECT 1 FROM likes WHERE post_id=? AND user_id=?", (p["id"], viewer_id)).fetchone() is not None
        out.append({"id": p["id"], "kind": p["kind"], "body": p["body"], "rating": p["rating"], "visibility": p["visibility"],
                    "created_at": p["created_at"], "author": a, "mine": p["author_id"] == viewer_id,
                    "place": place_public(places().get(p["place_id"])) if p["place_id"] else None,
                    "images": media.public(p["images"]),
                    "likes": n_like, "comments": n_cmt, "liked": liked})
    return out


def _post_or_404(con, viewer_id, post_id):
    p = con.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
    if p is None or not can_see(con, viewer_id, p):
        raise HTTPException(404, "Không tìm thấy bài viết")
    return p


@router.post("/posts", status_code=201)
def create_post(body: PostIn, me=Depends(current_user)):
    if body.place_id and body.place_id not in places():
        raise HTTPException(422, "Không có quán này trong danh sách")
    images = media.check_uploads(body.images)
    with session() as con:
        cur = con.execute("INSERT INTO posts(author_id, kind, body, place_id, rating, visibility, images) VALUES (?,?,?,?,?,?,?)",
                          (me["id"], body.kind, body.body, body.place_id, body.rating, body.visibility, json.dumps(images)))
        return serialize(con, me["id"], [con.execute("SELECT * FROM posts WHERE id=?", (cur.lastrowid,)).fetchone()])[0]


@router.delete("/posts/{post_id}")
def delete_post(post_id: int, me=Depends(current_user)):
    with session() as con:
        row = con.execute("SELECT images FROM posts WHERE id=? AND author_id=?", (post_id, me["id"])).fetchone()
        if row is None:
            raise HTTPException(404, "Không tìm thấy bài viết của bạn")
        con.execute("DELETE FROM posts WHERE id=?", (post_id,))
    media.delete_files([row["images"]])   # xóa luôn file ảnh đã tải lên
    return {"deleted": post_id}


@router.get("/feed")
def feed(before: Optional[int] = Query(None, ge=1), limit: int = Query(cfg.FEED_PAGE, ge=1, le=50), me=Depends(current_user)):
    """Bài của mình + người đã kết nối + bài công khai về quán mình theo dõi. Trang sau: ?before=<id cuối>."""
    with session() as con:
        friends = sorted(connection_ids(con, me["id"]) | {me["id"]})
        marks = ",".join("?" * len(friends))
        rows = con.execute(
            f"SELECT * FROM posts WHERE (author_id IN ({marks}) OR (visibility='public' AND place_id IN "
            f"(SELECT place_id FROM place_follows WHERE user_id=?))) AND id < ? ORDER BY id DESC LIMIT ?",
            (*friends, me["id"], before or 2**62, limit)).fetchall()
        items = serialize(con, me["id"], rows)
    return {"items": items, "next": items[-1]["id"] if len(items) == limit else None}


@router.get("/explore")
def explore(before: Optional[int] = Query(None, ge=1), limit: int = Query(cfg.FEED_PAGE, ge=1, le=50), me=Depends(current_user)):
    """Mọi bài công khai, mới nhất trước (cho người mới chưa có kết nối)."""
    with session() as con:
        rows = con.execute("SELECT * FROM posts WHERE visibility='public' AND id < ? ORDER BY id DESC LIMIT ?",
                           (before or 2**62, limit)).fetchall()
        items = serialize(con, me["id"], rows)
    return {"items": items, "next": items[-1]["id"] if len(items) == limit else None}


@router.post("/posts/{post_id}/like")
def like(post_id: int, me=Depends(current_user)):
    with session() as con:
        p = _post_or_404(con, me["id"], post_id)
        if con.execute("INSERT OR IGNORE INTO likes(post_id, user_id) VALUES (?,?)", (post_id, me["id"])).rowcount:
            notify(con, p["author_id"], "like", me["id"], post_id)
        n = con.execute("SELECT COUNT(*) FROM likes WHERE post_id=?", (post_id,)).fetchone()[0]
    return {"liked": True, "likes": n}


@router.delete("/posts/{post_id}/like")
def unlike(post_id: int, me=Depends(current_user)):
    with session() as con:
        _post_or_404(con, me["id"], post_id)
        con.execute("DELETE FROM likes WHERE post_id=? AND user_id=?", (post_id, me["id"]))
        n = con.execute("SELECT COUNT(*) FROM likes WHERE post_id=?", (post_id,)).fetchone()[0]
    return {"liked": False, "likes": n}


@router.get("/posts/{post_id}/comments")
def comments(post_id: int, me=Depends(current_user)):
    with session() as con:
        _post_or_404(con, me["id"], post_id)
        rows = con.execute("SELECT c.id, c.body, c.created_at, c.author_id, u.username, u.display_name, u.is_demo FROM comments c "
                           "JOIN users u ON u.id=c.author_id WHERE post_id=? ORDER BY c.id", (post_id,)).fetchall()
    return [{"id": r["id"], "body": r["body"], "created_at": r["created_at"], "mine": r["author_id"] == me["id"],
             "author": {"username": r["username"], "display_name": r["display_name"], "is_demo": bool(r["is_demo"])}} for r in rows]


@router.post("/posts/{post_id}/comments", status_code=201)
def add_comment(post_id: int, body: CommentIn, me=Depends(current_user)):
    text = body.body.strip()
    if not text:
        raise HTTPException(422, "Bình luận trống")
    with session() as con:
        p = _post_or_404(con, me["id"], post_id)
        cur = con.execute("INSERT INTO comments(post_id, author_id, body) VALUES (?,?,?)", (post_id, me["id"], text))
        notify(con, p["author_id"], "comment", me["id"], post_id)
    return {"id": cur.lastrowid, "body": text, "mine": True,
            "author": {"username": me["username"], "display_name": me["display_name"]}}


@router.delete("/comments/{comment_id}")
def delete_comment(comment_id: int, me=Depends(current_user)):
    with session() as con:
        if con.execute("DELETE FROM comments WHERE id=? AND author_id=?", (comment_id, me["id"])).rowcount == 0:
            raise HTTPException(404, "Không tìm thấy bình luận của bạn")
    return {"deleted": comment_id}


# ===== Quán (giống "trang công ty" của LinkedIn) =====
@router.get("/places")
def list_places(q: str = Query("", max_length=80), district: Optional[str] = Query(None, max_length=40), me=Depends(current_user)):
    return search_places(q, limit=20, district=district)


@router.get("/places/{place_id}")
def place_page(place_id: str, me=Depends(current_user)):
    p = places().get(place_id)
    if p is None:
        raise HTTPException(404, "Không có quán này")
    with session() as con:
        followers = con.execute("SELECT COUNT(*) FROM place_follows WHERE place_id=?", (place_id,)).fetchone()[0]
        following = con.execute("SELECT 1 FROM place_follows WHERE place_id=? AND user_id=?", (place_id, me["id"])).fetchone() is not None
        rows = [r for r in con.execute("SELECT * FROM posts WHERE place_id=? ORDER BY id DESC LIMIT 50", (place_id,))
                if can_see(con, me["id"], r)]
        ratings = [r["rating"] for r in rows if r["rating"]]
        mine = connection_ids(con, me["id"])
        friends_here = sorted({r["author_id"] for r in rows if r["author_id"] in mine})
        names = [con.execute("SELECT display_name FROM users WHERE id=?", (i,)).fetchone()[0] for i in friends_here[:3]]
        return {**place_public(p), "followers": followers, "following": following,
                "community_rating": round(sum(ratings) / len(ratings), 1) if ratings else None, "n_reviews": len(ratings),
                "friends_here": names, "n_friends_here": len(friends_here), "posts": serialize(con, me["id"], rows[:20])}


@router.post("/places/{place_id}/follow")
def follow_place(place_id: str, me=Depends(current_user)):
    if place_id not in places():
        raise HTTPException(404, "Không có quán này")
    with session() as con:
        con.execute("INSERT OR IGNORE INTO place_follows(user_id, place_id) VALUES (?,?)", (me["id"], place_id))
    return {"following": True}


@router.delete("/places/{place_id}/follow")
def unfollow_place(place_id: str, me=Depends(current_user)):
    with session() as con:
        con.execute("DELETE FROM place_follows WHERE user_id=? AND place_id=?", (me["id"], place_id))
    return {"following": False}


# ===== Thông báo =====
TEXT = {"connect_request": "muốn kết nối với bạn", "connect_accepted": "đã chấp nhận lời mời kết nối",
        "like": "đã thích bài viết của bạn", "comment": "đã bình luận bài viết của bạn"}


@router.get("/notifications")
def notifications(me=Depends(current_user)):
    with session() as con:
        rows = con.execute("SELECT n.*, u.username, u.display_name FROM notifications n JOIN users u ON u.id=n.actor_id "
                           "WHERE n.user_id=? ORDER BY n.id DESC LIMIT 50", (me["id"],)).fetchall()
        unread = con.execute("SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0", (me["id"],)).fetchone()[0]
    return {"unread": unread, "items": [{"id": r["id"], "kind": r["kind"], "text": TEXT.get(r["kind"], r["kind"]),
                                         "post_id": r["post_id"], "read": bool(r["is_read"]), "created_at": r["created_at"],
                                         "actor": {"username": r["username"], "display_name": r["display_name"]}} for r in rows]}


@router.post("/notifications/read")
def mark_read(me=Depends(current_user)):
    with session() as con:
        con.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (me["id"],))
    return {"ok": True}
