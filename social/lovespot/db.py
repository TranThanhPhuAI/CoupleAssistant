"""SQLite: một file, không cần cài máy chủ CSDL. Mỗi request mở một kết nối riêng (an toàn đa luồng)."""
import sqlite3
from contextlib import contextmanager

from . import config as cfg

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  pw_hash TEXT NOT NULL,
  display_name TEXT NOT NULL,
  headline TEXT NOT NULL DEFAULT '',
  bio TEXT NOT NULL DEFAULT '',
  district TEXT NOT NULL DEFAULT '',
  interests TEXT NOT NULL DEFAULT '[]',          -- mã sở thích (danh mục 24 mục của Couple Assistant), JSON
  show_interests INTEGER NOT NULL DEFAULT 1,     -- người dùng tự chọn có hiện gu của mình không
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  ext_id TEXT,                                   -- mã tài khoản Couple Assistant khi chạy chung (đăng nhập một lần)
  is_demo INTEGER NOT NULL DEFAULT 0             -- tài khoản mẫu (seed_demo.py), luôn hiện nhãn "Tài khoản mẫu"
);
-- Kết nối hai chiều: lưu một dòng cho mỗi cặp với a < b
CREATE TABLE IF NOT EXISTS connections (
  a INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  b INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status TEXT NOT NULL CHECK (status IN ('pending', 'accepted')),
  requested_by INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (a, b), CHECK (a < b)
);
CREATE TABLE IF NOT EXISTS place_follows (
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  place_id TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (user_id, place_id)
);
CREATE TABLE IF NOT EXISTS posts (
  id INTEGER PRIMARY KEY,
  author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK (kind IN ('status', 'review', 'checkin')),
  body TEXT NOT NULL,
  place_id TEXT,
  rating INTEGER CHECK (rating BETWEEN 1 AND 5),
  visibility TEXT NOT NULL DEFAULT 'public' CHECK (visibility IN ('public', 'connections')),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  images TEXT NOT NULL DEFAULT '[]'   -- JSON: [{"upload": tên file}] hoặc [{"url": ..., "demo": true}] (ảnh minh họa)
);
CREATE INDEX IF NOT EXISTS posts_author ON posts(author_id, id);
CREATE INDEX IF NOT EXISTS posts_place ON posts(place_id, id);
CREATE TABLE IF NOT EXISTS likes (
  post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  PRIMARY KEY (post_id, user_id)
);
CREATE TABLE IF NOT EXISTS comments (
  id INTEGER PRIMARY KEY,
  post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  body TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS comments_post ON comments(post_id, id);
CREATE TABLE IF NOT EXISTS notifications (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,                              -- connect_request | connect_accepted | like | comment
  actor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
  is_read INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS notif_user ON notifications(user_id, id);
"""


_ready = set()   # CSDL đã tạo bảng (tạo ở lần kết nối đầu tiên, nên chỉ import module thì không ghi gì ra đĩa)


def connect(path=None):
    path = path or cfg.DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")
    if path not in _ready:
        _create(con)
        _ready.add(path)
    return con


def _create(con):
    con.executescript(SCHEMA)
    cols = {r["name"] for r in con.execute("PRAGMA table_info(users)")}   # CSDL tạo từ bản cũ -> thêm cột còn thiếu
    if "ext_id" not in cols:
        con.execute("ALTER TABLE users ADD COLUMN ext_id TEXT")
    if "is_demo" not in cols:
        con.execute("ALTER TABLE users ADD COLUMN is_demo INTEGER NOT NULL DEFAULT 0")
    if "images" not in {r["name"] for r in con.execute("PRAGMA table_info(posts)")}:
        con.execute("ALTER TABLE posts ADD COLUMN images TEXT NOT NULL DEFAULT '[]'")
    con.execute("CREATE UNIQUE INDEX IF NOT EXISTS users_ext ON users(ext_id) WHERE ext_id IS NOT NULL")
    con.commit()


def init(path=None):
    connect(path).close()


@contextmanager
def session():
    """Dùng trong route: with session() as con: ...  (tự commit khi xong, rollback khi lỗi)."""
    con = connect()
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def pair(x, y):
    """Khóa của một cặp kết nối: (nhỏ, lớn)."""
    return (x, y) if x < y else (y, x)


def relation(con, me, other):
    """'self' | 'none' | 'connected' | 'sent' (mình đã mời) | 'received' (họ mời mình)."""
    if me == other:
        return "self"
    r = con.execute("SELECT status, requested_by FROM connections WHERE a=? AND b=?", pair(me, other)).fetchone()
    if r is None:
        return "none"
    if r["status"] == "accepted":
        return "connected"
    return "sent" if r["requested_by"] == me else "received"


def connection_ids(con, uid):
    rows = con.execute("SELECT CASE WHEN a=? THEN b ELSE a END AS o FROM connections "
                       "WHERE (a=? OR b=?) AND status='accepted'", (uid, uid, uid)).fetchall()
    return {r["o"] for r in rows}


def notify(con, user_id, kind, actor_id, post_id=None):
    if user_id != actor_id:   # không tự báo cho chính mình
        con.execute("INSERT INTO notifications(user_id, kind, actor_id, post_id) VALUES (?,?,?,?)",
                    (user_id, kind, actor_id, post_id))
