"""Tài khoản, hồ sơ, kết nối (mời / chấp nhận / gỡ), tìm kiếm, gợi ý."""
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from . import config as cfg
from . import media, security, suggest
from .catalog import INTERESTS, fold, places, search_places
from .db import connection_ids, notify, pair, relation, session
from .routes_posts import can_see, serialize
from .security import check_lock, check_password, current_user, hash_password, issue_token, record_fail

router = APIRouter(prefix="/api")


class RegisterIn(BaseModel):
    username: str = Field(..., pattern=cfg.USERNAME)
    password: str = Field(..., min_length=cfg.MIN_PASSWORD, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=60)


class LoginIn(BaseModel):
    username: str = Field(..., max_length=30)
    password: str = Field(..., max_length=128)


class ProfileIn(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=60)
    headline: Optional[str] = Field(None, max_length=120)
    bio: Optional[str] = Field(None, max_length=cfg.MAX_BIO)
    district: Optional[str] = Field(None, max_length=40)
    interests: Optional[List[str]] = Field(None, max_length=len(INTERESTS))
    show_interests: Optional[bool] = None

    @field_validator("interests")
    @classmethod
    def _known(cls, v):
        bad = [i for i in v or [] if i not in INTERESTS]
        if bad:
            raise ValueError(f"Sở thích không có trong danh mục: {', '.join(bad)}")
        return list(dict.fromkeys(v)) if v is not None else v


def card(u):
    return {"username": u["username"], "display_name": u["display_name"], "headline": u["headline"], "district": u["district"],
            "is_demo": bool(u["is_demo"])}


def me_view(con, u):
    return {**card(u), "bio": u["bio"], "interests": suggest.interests_of(u), "show_interests": bool(u["show_interests"]),
            "connections": len(connection_ids(con, u["id"])),
            "following_places": con.execute("SELECT COUNT(*) FROM place_follows WHERE user_id=?", (u["id"],)).fetchone()[0],
            "pending_requests": con.execute("SELECT COUNT(*) FROM connections WHERE (a=? OR b=?) AND status='pending' "
                                            "AND requested_by != ?", (u["id"], u["id"], u["id"])).fetchone()[0]}


def _user(con, username):
    u = con.execute("SELECT * FROM users WHERE username=?", (username.lower(),)).fetchone()
    if u is None:
        raise HTTPException(404, f"Không có người dùng @{username}")
    return u


@router.get("/health")
def health():
    shared = security.EXTERNAL_AUTH is not None
    return {"ok": True, "places": len(places()), "allow_register": cfg.ALLOW_REGISTER and not shared, "shared_login": shared}


@router.get("/catalog/interests")
def catalog():
    return [{"id": k, "label": v[0], "group": v[1]} for k, v in INTERESTS.items()]


# ===== Tài khoản =====
@router.post("/auth/register", status_code=201)
def register(body: RegisterIn):
    if not cfg.ALLOW_REGISTER or security.EXTERNAL_AUTH is not None:
        raise HTTPException(403, "Đang tắt đăng ký")
    with session() as con:
        if con.execute("SELECT 1 FROM users WHERE username=?", (body.username,)).fetchone():
            raise HTTPException(409, f"@{body.username} đã có người dùng")
        cur = con.execute("INSERT INTO users(username, pw_hash, display_name) VALUES (?,?,?)",
                          (body.username, hash_password(body.password), body.display_name.strip()))
    return {"token": issue_token(cur.lastrowid), "username": body.username}


@router.post("/auth/login")
def login(body: LoginIn):
    if security.EXTERNAL_AUTH is not None:
        raise HTTPException(403, "Đăng nhập bằng tài khoản Couple Assistant")
    name = body.username.strip().lower()
    check_lock(name)
    with session() as con:
        u = con.execute("SELECT id, pw_hash FROM users WHERE username=?", (name,)).fetchone()
    ok = u is not None and check_password(body.password, u["pw_hash"])
    record_fail(name, ok)
    if not ok:
        raise HTTPException(401, "Sai tên đăng nhập hoặc mật khẩu")
    return {"token": issue_token(u["id"]), "username": name}


@router.get("/me")
def get_me(me=Depends(current_user)):
    with session() as con:
        return me_view(con, me)


@router.patch("/me")
def update_me(body: ProfileIn, me=Depends(current_user)):
    fields = body.model_dump(exclude_none=True)
    if "interests" in fields:
        fields["interests"] = json.dumps(fields["interests"])
    if "show_interests" in fields:
        fields["show_interests"] = int(fields["show_interests"])
    fields = {k: v.strip() if isinstance(v, str) else v for k, v in fields.items()}
    with session() as con:
        if fields:   # tên cột lấy từ model (cố định), giá trị qua tham số -> không có SQL injection
            con.execute(f"UPDATE users SET {', '.join(f'{k}=?' for k in fields)} WHERE id=?", (*fields.values(), me["id"]))
        return me_view(con, con.execute("SELECT * FROM users WHERE id=?", (me["id"],)).fetchone())


@router.delete("/me")
def delete_me(me=Depends(current_user)):
    """Xóa vĩnh viễn: tài khoản, bài viết, bình luận, lượt thích, kết nối, thông báo (ON DELETE CASCADE)."""
    with session() as con:
        imgs = [r["images"] for r in con.execute("SELECT images FROM posts WHERE author_id=?", (me["id"],))]
        con.execute("DELETE FROM users WHERE id=?", (me["id"],))
    media.delete_files(imgs)   # file ảnh không nằm trong CSDL nên xóa riêng
    return {"deleted": me["username"]}


# ===== Hồ sơ người khác =====
@router.get("/users/{username}")
def profile(username: str, me=Depends(current_user)):
    with session() as con:
        u = _user(con, username)
        rel = relation(con, me["id"], u["id"])
        mutual_ids = sorted(connection_ids(con, me["id"]) & connection_ids(con, u["id"])) if rel != "self" else []
        mutual = [con.execute("SELECT display_name FROM users WHERE id=?", (i,)).fetchone()[0] for i in mutual_ids[:3]]
        show = u["show_interests"] or rel == "self"
        posts = [p for p in con.execute("SELECT * FROM posts WHERE author_id=? ORDER BY id DESC LIMIT 30", (u["id"],))
                 if can_see(con, me["id"], p)]
        return {**card(u), "bio": u["bio"], "relation": rel, "joined": u["created_at"][:10],
                "interests": [{"id": i, "label": INTERESTS[i][0]} for i in suggest.interests_of(u)] if show else [],
                "shared_interests": suggest.shared_labels(me, u) if rel != "self" else [],
                "connections": len(connection_ids(con, u["id"])), "mutual": mutual, "n_mutual": len(mutual_ids),
                "posts": serialize(con, me["id"], posts[:20])}


# ===== Kết nối =====
@router.post("/connections/{username}")
def connect(username: str, me=Depends(current_user)):
    """Gửi lời mời; nếu người kia đã mời mình trước thì coi như chấp nhận."""
    with session() as con:
        u = _user(con, username)
        rel = relation(con, me["id"], u["id"])
        if rel == "self":
            raise HTTPException(422, "Không thể kết nối với chính mình")
        if rel == "received":
            con.execute("UPDATE connections SET status='accepted' WHERE a=? AND b=?", pair(me["id"], u["id"]))
            notify(con, u["id"], "connect_accepted", me["id"])
            rel = "connected"
        elif rel == "none":
            con.execute("INSERT INTO connections(a, b, status, requested_by) VALUES (?,?, 'pending', ?)", (*pair(me["id"], u["id"]), me["id"]))
            notify(con, u["id"], "connect_request", me["id"])
            rel = "sent"
    return {"relation": rel}


@router.post("/connections/{username}/accept")
def accept(username: str, me=Depends(current_user)):
    with session() as con:
        u = _user(con, username)
        if relation(con, me["id"], u["id"]) != "received":
            raise HTTPException(404, "Không có lời mời nào từ người này")
        con.execute("UPDATE connections SET status='accepted' WHERE a=? AND b=?", pair(me["id"], u["id"]))
        notify(con, u["id"], "connect_accepted", me["id"])
    return {"relation": "connected"}


@router.delete("/connections/{username}")
def disconnect(username: str, me=Depends(current_user)):
    """Hủy lời mời đã gửi, từ chối lời mời nhận được, hoặc gỡ kết nối."""
    with session() as con:
        u = _user(con, username)
        con.execute("DELETE FROM connections WHERE a=? AND b=?", pair(me["id"], u["id"]))
    return {"relation": "none"}


@router.get("/connections")
def my_connections(me=Depends(current_user)):
    with session() as con:
        ids = sorted(connection_ids(con, me["id"]))
        rows = [con.execute("SELECT * FROM users WHERE id=?", (i,)).fetchone() for i in ids]
        incoming = con.execute("SELECT u.* FROM connections c JOIN users u ON u.id = c.requested_by "
                               "WHERE (c.a=? OR c.b=?) AND c.status='pending' AND c.requested_by != ? ORDER BY c.created_at DESC",
                               (me["id"],) * 3).fetchall()
        sent = con.execute("SELECT u.* FROM connections c JOIN users u ON u.id = CASE WHEN c.a=? THEN c.b ELSE c.a END "
                           "WHERE (c.a=? OR c.b=?) AND c.status='pending' AND c.requested_by = ?", (me["id"],) * 4).fetchall()
    by_name = lambda r: fold(r["display_name"])  # noqa: E731
    return {"connections": [card(r) for r in sorted(rows, key=by_name)],
            "incoming": [{**card(r), "shared_interests": suggest.shared_labels(me, r)} for r in incoming],
            "sent": [card(r) for r in sent]}


# ===== Tìm kiếm & gợi ý =====
@router.get("/search")
def search(q: str = Query(..., min_length=1, max_length=80), me=Depends(current_user)):
    words = fold(q).split()
    with session() as con:
        people = [card(u) for u in con.execute("SELECT * FROM users ORDER BY display_name")
                  if all(w in fold(f"{u['username']} {u['display_name']} {u['headline']} {u['district']}") for w in words)][:8]
    return {"people": people, "places": search_places(q, limit=8)}


@router.get("/suggestions")
def suggestions(me=Depends(current_user)):
    with session() as con:
        return {"people": suggest.people(con, me), "places": suggest.places_for(con, me)}
