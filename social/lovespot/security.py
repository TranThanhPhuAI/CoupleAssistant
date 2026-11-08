"""Mật khẩu (PBKDF2-SHA256), token JWT (HS256), khóa tạm khi sai mật khẩu nhiều lần, dependency người dùng hiện tại."""
import base64
import hashlib
import hmac
import os
import re
import secrets
import threading
import time

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import config as cfg
from .db import session

ITER = 200_000
_fails, _lock = {}, threading.Lock()
bearer = HTTPBearer(auto_error=False)

# Khi chạy chung trong web Couple Assistant: ứng dụng chủ gán hàm token -> (mã tài khoản, tên hiển thị)
# (ném lỗi nếu token sai). Khi đó Lovespot dùng chung đăng nhập, không có tài khoản riêng.
EXTERNAL_AUTH = None


def hash_password(pw):
    salt = secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, ITER)
    return f"pbkdf2_sha256${ITER}${base64.b64encode(salt).decode()}${base64.b64encode(h).decode()}"


def check_password(pw, stored):
    try:
        _, it, salt, h = stored.split("$")
        got = hashlib.pbkdf2_hmac("sha256", pw.encode(), base64.b64decode(salt), int(it))
        return hmac.compare_digest(got, base64.b64decode(h))
    except (ValueError, TypeError):
        return False


def _secret():
    env = os.environ.get("LOVESPOT_SOCIAL_JWT_SECRET")
    if env:
        return env
    f = cfg.SECRET_FILE
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(secrets.token_urlsafe(48), encoding="utf-8")
    return f.read_text(encoding="utf-8").strip()


def issue_token(user_id):
    now = int(time.time())
    return jwt.encode({"sub": str(user_id), "iat": now, "exp": now + cfg.TOKEN_DAYS * 86400}, _secret(), algorithm="HS256")


def check_lock(username):
    with _lock:
        recent = [t for t in _fails.get(username, []) if time.time() - t < cfg.LOCK_MINUTES * 60]
        _fails[username] = recent
        if len(recent) >= cfg.MAX_FAILS:
            raise HTTPException(429, f"Sai mật khẩu quá {cfg.MAX_FAILS} lần. Thử lại sau {cfg.LOCK_MINUTES} phút.")


def record_fail(username, ok):
    with _lock:
        if ok:
            _fails.pop(username, None)
        else:
            _fails.setdefault(username, []).append(time.time())


def current_user(cred: HTTPAuthorizationCredentials = Depends(bearer)):
    """Trả về dòng users của người đang đăng nhập; 401 nếu thiếu / sai / hết hạn token hoặc tài khoản đã xóa."""
    if cred is None:
        raise HTTPException(401, "Cần đăng nhập")
    if EXTERNAL_AUTH is not None:
        return _external_user(cred.credentials)
    try:
        sub = int(jwt.decode(cred.credentials, _secret(), algorithms=["HS256"], options={"require": ["sub", "exp"]})["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Phiên đăng nhập đã hết hạn")
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(401, "Token không hợp lệ")
    with session() as con:
        u = con.execute("SELECT * FROM users WHERE id=?", (sub,)).fetchone()
    if u is None:
        raise HTTPException(401, "Tài khoản không còn tồn tại")
    return u


def _username_from(ext_id, con):
    """Mã tài khoản Couple Assistant ('Minh-Tran') -> @tên hợp lệ, không trùng ('minh_tran', 'minh_tran2'…)."""
    base = re.sub(r"[^a-z0-9_]", "_", ext_id.lower())[:26].strip("_") or "ban"
    base = base.ljust(3, "_")
    name, n = base, 1
    while con.execute("SELECT 1 FROM users WHERE username=?", (name,)).fetchone():
        n += 1
        name = f"{base}{n}"
    return name


def _external_user(token):
    try:
        ext_id, display = EXTERNAL_AUTH(token)
    except Exception:
        raise HTTPException(401, "Phiên đăng nhập Couple Assistant không hợp lệ hoặc đã hết hạn")
    with session() as con:
        u = con.execute("SELECT * FROM users WHERE ext_id=?", (ext_id,)).fetchone()
        if u is None:   # lần đầu mở tab Cộng đồng: tạo hồ sơ từ tài khoản Couple Assistant (không có mật khẩu riêng)
            con.execute("INSERT INTO users(username, pw_hash, display_name, ext_id) VALUES (?, '!', ?, ?)",
                        (_username_from(ext_id, con), (display or ext_id)[:60], ext_id))
            u = con.execute("SELECT * FROM users WHERE ext_id=?", (ext_id,)).fetchone()
    return u
