"""Tài khoản + đăng nhập JWT cho server web (cần khi mở ra Internet qua Cloudflare Tunnel).

- Mật khẩu băm PBKDF2-SHA256 (thư viện chuẩn), không bao giờ lưu mật khẩu gốc.
- Token JWT HS256, hết hạn sau AUTH_TOKEN_DAYS ngày; khóa ký tự sinh, lưu ở data/auth/jwt_secret.
- Sai mật khẩu AUTH_MAX_FAILS lần trong AUTH_LOCK_MINUTES phút -> khóa tạm tài khoản đó.

Quản lý từ dòng lệnh:
    python run.py taikhoan tao admin --admin      (hỏi mật khẩu)
    python run.py taikhoan doimk minh | xoa minh | ds
"""
import argparse
import base64
import getpass
import hashlib
import hmac
import json
import os
import secrets
import sys
import threading
import time

import jwt

import config as cfg

ROLES = ("member", "admin")
_lock = threading.Lock()
_fails = {}  # user_id -> [thời điểm sai]


def _valid_id(user_id):
    return bool(user_id) and len(user_id) <= 40 and str(user_id).replace("_", "").replace("-", "").isalnum()


def _hash_password(password, salt=None, iterations=200_000):
    salt = salt or secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def _check_password(password, stored):
    _, it, salt, _ = stored.split("$")
    return hmac.compare_digest(_hash_password(password, base64.b64decode(salt), int(it)), stored)


class AccountStore:
    """Tài khoản trong data/auth/accounts.json (ghi atomic). Hồ sơ sở thích vẫn nằm ở ProfileStore."""

    def __init__(self, root=cfg.AUTH_DIR):
        self.root = root
        self.path = root / "accounts.json"

    def _load(self):
        return json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}

    def _save(self, data):
        self.root.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)

    def create(self, user_id, password, role="member"):
        if not _valid_id(user_id):
            raise ValueError("Mã tài khoản chỉ gồm chữ, số, '_' hoặc '-' (tối đa 40 ký tự)")
        if len(password) < cfg.AUTH_MIN_PASSWORD:
            raise ValueError(f"Mật khẩu cần ít nhất {cfg.AUTH_MIN_PASSWORD} ký tự")
        if role not in ROLES:
            raise ValueError(f"Vai trò không hợp lệ: {role}")
        with _lock:
            data = self._load()
            if user_id in data:
                raise ValueError(f"Tài khoản '{user_id}' đã tồn tại")
            data[user_id] = {"password": _hash_password(password), "role": role, "created_at": int(time.time())}
            self._save(data)

    def set_password(self, user_id, password):
        if len(password) < cfg.AUTH_MIN_PASSWORD:
            raise ValueError(f"Mật khẩu cần ít nhất {cfg.AUTH_MIN_PASSWORD} ký tự")
        with _lock:
            data = self._load()
            if user_id not in data:
                raise KeyError(user_id)
            data[user_id]["password"] = _hash_password(password)
            data[user_id]["password_set_at"] = time.time()   # gỡ khóa tạm do gõ sai trước đó (kể cả khi server đang chạy)
            self._save(data)

    def set_role(self, user_id, role):
        if role not in ROLES:
            raise ValueError(f"Vai trò không hợp lệ: {role} (chọn: {', '.join(ROLES)})")
        with _lock:
            data = self._load()
            if user_id not in data:
                raise KeyError(user_id)
            data[user_id]["role"] = role
            self._save(data)

    def delete(self, user_id):
        with _lock:
            data = self._load()
            existed = data.pop(user_id, None) is not None
            self._save(data)
        return existed

    def role(self, user_id):
        acc = self._load().get(user_id)
        return acc["role"] if acc else None

    def list(self):
        return {u: a["role"] for u, a in sorted(self._load().items())}

    def details(self):
        """{mã: {role, created_at}} — KHÔNG kèm mật khẩu đã băm (cho trang Phân quyền)."""
        return {u: {"role": a["role"], "created_at": a.get("created_at")} for u, a in sorted(self._load().items())}

    def verify(self, user_id, password):
        """Trả về vai trò nếu đúng; None nếu sai. Raise PermissionError khi đang bị khóa tạm."""
        now = time.time()
        window = cfg.AUTH_LOCK_MINUTES * 60
        acc = self._load().get(user_id)
        reset_at = (acc or {}).get("password_set_at", 0)   # đổi mật khẩu (run.py taikhoan doimk) -> xóa các lần sai trước đó
        with _lock:
            recent = [t for t in _fails.get(user_id, []) if now - t < window and t > reset_at]
            _fails[user_id] = recent
            if len(recent) >= cfg.AUTH_MAX_FAILS:
                wait = int((window - (now - recent[0])) / 60) + 1
                raise PermissionError(f"Sai mật khẩu quá {cfg.AUTH_MAX_FAILS} lần. Thử lại sau khoảng {wait} phút, "
                                      "hoặc nhờ quản trị đặt lại mật khẩu.")
        if acc and _check_password(password, acc["password"]):
            _fails.pop(user_id, None)
            return acc["role"]
        with _lock:
            _fails.setdefault(user_id, []).append(now)
        return None


def _secret():
    """Khóa ký JWT: biến môi trường LOVESPOT_JWT_SECRET, nếu không có thì tự sinh và lưu một lần."""
    env = os.environ.get("LOVESPOT_JWT_SECRET")
    if env:
        return env
    path = cfg.AUTH_DIR / "jwt_secret"
    if not path.exists():
        cfg.AUTH_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(secrets.token_urlsafe(48), encoding="utf-8")
    return path.read_text(encoding="utf-8").strip()


def issue_token(user_id, role):
    now = int(time.time())
    return jwt.encode({"sub": user_id, "role": role, "iat": now, "exp": now + cfg.AUTH_TOKEN_DAYS * 86400},
                      _secret(), algorithm="HS256")


def decode_token(token):
    """Trả về {"sub", "role", ...}; raise jwt.InvalidTokenError nếu sai chữ ký / hết hạn."""
    return jwt.decode(token, _secret(), algorithms=["HS256"], options={"require": ["sub", "exp"]})


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="run.py taikhoan", description="Quản lý tài khoản đăng nhập web")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("tao")
    p.add_argument("user_id")
    p.add_argument("--admin", action="store_true", help="tài khoản quản trị (xem thống kê, sửa mọi hồ sơ)")
    sub.add_parser("doimk").add_argument("user_id")
    q = sub.add_parser("quyen", help="đổi vai trò tài khoản có sẵn, vd: quyen phu admin")
    q.add_argument("user_id")
    q.add_argument("role", choices=sorted(ROLES))
    sub.add_parser("xoa").add_argument("user_id")
    sub.add_parser("ds")
    a = ap.parse_args()
    store = AccountStore()
    try:
        if a.cmd == "tao":
            pw = getpass.getpass("Mật khẩu: ")
            if pw != getpass.getpass("Nhập lại: "):
                sys.exit("Hai lần nhập không khớp.")
            store.create(a.user_id, pw, "admin" if a.admin else "member")
            print(f"Đã tạo tài khoản '{a.user_id}' ({'admin' if a.admin else 'member'}).")
        elif a.cmd == "doimk":
            pw = getpass.getpass("Mật khẩu mới: ")
            store.set_password(a.user_id, pw)
            print("Đã đổi mật khẩu.")
        elif a.cmd == "quyen":
            store.set_role(a.user_id, a.role)
            print(f"Đã đổi '{a.user_id}' thành {a.role}. Người đó tải lại trang web (Ctrl+F5) là thấy quyền mới.")
        elif a.cmd == "xoa":
            print("Đã xóa tài khoản." if store.delete(a.user_id) else "Không có tài khoản này.")
        else:
            accs = store.list()
            print("\n".join(f"  {u:20s} {r}" for u, r in accs.items()) if accs else "Chưa có tài khoản nào.")
    except (ValueError, KeyError) as e:
        sys.exit(f"Lỗi: {e}")


if __name__ == "__main__":
    main()
