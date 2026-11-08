"""Kiểm thử API Lovespot Social trên CSDL tạm (không đụng dữ liệu thật).   Chạy:  python social/tests/test_api.py"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

TMP = Path(tempfile.mkdtemp())
os.environ["LOVESPOT_SOCIAL_DATA"] = str(TMP)          # đặt TRƯỚC khi import ứng dụng
os.environ["LOVESPOT_SOCIAL_JWT_SECRET"] = "test-secret-only-not-for-production-0123456789"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient  # noqa: E402

import server  # noqa: E402
from lovespot.catalog import places  # noqa: E402

c = TestClient(server.app)
RESULTS = []


def test(fn):
    try:
        fn()
        RESULTS.append(("ĐẠT", fn.__doc__))
    except AssertionError as e:
        RESULTS.append(("LỖI", f"{fn.__doc__}: {e}"))
    return fn


def reg(name, display):
    r = c.post("/api/auth/register", json={"username": name, "password": "matkhau123", "display_name": display})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


A, B, C = reg("minh", "Minh"), reg("lan", "Lan"), reg("khoa", "Khoa")
PLACE = next(iter(places()))


@test
def _():
    """Đăng ký / đăng nhập / chặn khi thiếu token / khóa tạm sau 5 lần sai"""
    assert c.get("/api/me").status_code == 401
    assert c.get("/api/me", headers={"Authorization": "Bearer gia"}).status_code == 401
    assert c.post("/api/auth/register", json={"username": "minh", "password": "matkhau123", "display_name": "x"}).status_code == 409
    assert c.post("/api/auth/register", json={"username": "Có Dấu", "password": "matkhau123", "display_name": "x"}).status_code == 422
    codes = [c.post("/api/auth/login", json={"username": "khoa", "password": "sai"}).status_code for _ in range(6)]
    assert codes == [401] * 5 + [429], codes
    assert c.post("/api/auth/login", json={"username": "lan", "password": "matkhau123"}).status_code == 200


@test
def _():
    """Hồ sơ: sửa gu ăn uống, chặn sở thích ngoài danh mục, ẩn gu khi người dùng tắt"""
    r = c.patch("/api/me", headers=A, json={"headline": "Mê cà phê yên tĩnh", "district": "Quận 3", "interests": ["ca_phe", "yen_tinh", "lau"]})
    assert r.status_code == 200 and r.json()["interests"] == ["ca_phe", "yen_tinh", "lau"]
    assert c.patch("/api/me", headers=A, json={"interests": ["bay_len_troi"]}).status_code == 422
    c.patch("/api/me", headers=B, json={"district": "Quận 3", "interests": ["ca_phe", "yen_tinh"]})
    c.patch("/api/me", headers=C, json={"interests": ["ca_phe"], "show_interests": False})
    assert c.get("/api/users/khoa", headers=A).json()["interests"] == []
    assert c.get("/api/users/lan", headers=A).json()["shared_interests"] == ["Cà phê", "Yên tĩnh"]


@test
def _():
    """Gợi ý người cùng gu có lý do; người ẩn gu không bị lộ sở thích qua gợi ý"""
    s = c.get("/api/suggestions", headers=A).json()["people"]
    lan = next(p for p in s if p["username"] == "lan")
    assert "Cùng thích: Cà phê, Yên tĩnh" in lan["reason"] and "Cùng Quận 3" in lan["reason"], lan
    assert all(p["username"] != "khoa" for p in s), "lộ gu của người đã ẩn"


@test
def _():
    """Kết nối: mời -> chờ -> chấp nhận; mời ngược lại = chấp nhận; gỡ kết nối"""
    assert c.post("/api/connections/lan", headers=A).json()["relation"] == "sent"
    assert c.get("/api/users/minh", headers=B).json()["relation"] == "received"
    assert c.get("/api/connections", headers=B).json()["incoming"][0]["username"] == "minh"
    assert c.post("/api/connections/minh/accept", headers=B).json()["relation"] == "connected"
    assert c.post("/api/connections/minh", headers=C).json()["relation"] == "sent"
    assert c.post("/api/connections/khoa", headers=A).json()["relation"] == "connected"
    assert c.post("/api/connections/minh", headers=A).status_code == 422
    assert c.get("/api/users/khoa", headers=B).json()["n_mutual"] == 1
    c.delete("/api/connections/khoa", headers=A)
    assert c.get("/api/users/khoa", headers=A).json()["relation"] == "none"


@test
def _():
    """Bài viết: review phải có quán + sao; quán phải có thật; quyền xem 'connections'"""
    assert c.post("/api/posts", headers=A, json={"kind": "review", "body": "Ngon", "place_id": PLACE}).status_code == 422
    assert c.post("/api/posts", headers=A, json={"kind": "checkin", "body": "Đang ở đây"}).status_code == 422
    assert c.post("/api/posts", headers=A, json={"kind": "review", "body": "x", "place_id": "khong_co", "rating": 5}).status_code == 422
    r = c.post("/api/posts", headers=A, json={"kind": "review", "body": "Quán yên tĩnh, hợp hẹn hò", "place_id": PLACE, "rating": 5})
    assert r.status_code == 201 and r.json()["place"]["id"] == PLACE
    priv = c.post("/api/posts", headers=A, json={"body": "Chỉ bạn bè thấy", "visibility": "connections"}).json()["id"]
    assert any(p["id"] == priv for p in c.get("/api/feed", headers=B).json()["items"])       # Lan đã kết nối
    assert c.get(f"/api/posts/{priv}/comments", headers=C).status_code == 404                 # Khoa thì không
    assert all(p["id"] != priv for p in c.get("/api/users/minh", headers=C).json()["posts"])


@test
def _():
    """Thích / bình luận tạo thông báo; không xóa được bài của người khác"""
    pid = c.get("/api/feed", headers=B).json()["items"][-1]["id"]
    assert c.post(f"/api/posts/{pid}/like", headers=B).json() == {"liked": True, "likes": 1}
    assert c.post(f"/api/posts/{pid}/like", headers=B).json()["likes"] == 1          # bấm lại không cộng dồn
    assert c.post(f"/api/posts/{pid}/comments", headers=B, json={"body": "  "}).status_code == 422
    assert c.post(f"/api/posts/{pid}/comments", headers=B, json={"body": "Hôm nào đi chung!"}).status_code == 201
    n = c.get("/api/notifications", headers=A).json()
    assert n["unread"] >= 3 and {i["kind"] for i in n["items"]} >= {"like", "comment", "connect_accepted"}, n
    c.post("/api/notifications/read", headers=A)
    assert c.get("/api/notifications", headers=A).json()["unread"] == 0
    assert c.delete(f"/api/posts/{pid}", headers=B).status_code == 404


@test
def _():
    """Trang quán: theo dõi, điểm cộng đồng, bạn bè đã đến; bảng tin có bài về quán đang theo dõi"""
    assert c.post(f"/api/places/{PLACE}/follow", headers=C).json()["following"]
    p = c.get(f"/api/places/{PLACE}", headers=B).json()
    assert p["community_rating"] == 5 and p["friends_here"] == ["Minh"], p
    assert any(x["place"] and x["place"]["id"] == PLACE for x in c.get("/api/feed", headers=C).json()["items"])
    assert c.get("/api/places/khong_co", headers=C).status_code == 404


@test
def _():
    """Tìm kiếm không dấu: người và quán"""
    r = c.get("/api/search", params={"q": "minh"}, headers=B).json()
    assert r["people"][0]["username"] == "minh"
    name = places()[PLACE]["name"].split()[0]
    assert c.get("/api/search", params={"q": name}, headers=B).json()["places"]


@test
def _():
    """Ảnh: chỉ nhận ảnh thật (kiểm tra chữ ký file), bài gắn tối đa 4 ảnh đã tải lên, xóa bài thì xóa file"""
    from lovespot import config
    png = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    fake = "data:image/png;base64," + __import__("base64").b64encode(b"<script>alert(1)</script>").decode()
    assert c.post("/api/uploads", headers=B, json={"data": fake}).status_code == 422
    assert c.post("/api/uploads", headers=B, json={"data": "khong-phai-anh"}).status_code == 422
    name = c.post("/api/uploads", headers=B, json={"data": png}).json()["upload"]
    assert c.get(f"/api/uploads/{name}").status_code == 200 and c.get("/api/uploads/..%2Fsocial.db").status_code == 404
    assert c.post("/api/posts", headers=B, json={"body": "x", "images": ["https://example.com/a.jpg"]}).status_code == 422
    assert c.post("/api/posts", headers=B, json={"body": "", "images": []}).status_code == 422
    p = c.post("/api/posts", headers=B, json={"body": "", "images": [name]}).json()          # bài chỉ có ảnh
    assert p["images"] == [{"upload": name}], p
    c.delete(f"/api/posts/{p['id']}", headers=B)
    assert not (config.UPLOAD_DIR / name).exists(), "xóa bài nhưng còn file ảnh"


@test
def _():
    """Chạy chung trong Couple Assistant: nhận token bên ngoài, tự tạo hồ sơ, khóa đăng nhập/đăng ký riêng"""
    from lovespot import security

    def fake(t):
        if t != "ca-token-ok":
            raise ValueError("sai")
        return "Minh-Tran", "Minh Trần"
    security.EXTERNAL_AUTH = fake
    try:
        X = {"Authorization": "Bearer ca-token-ok"}
        assert c.get("/api/health").json()["shared_login"] is True
        me = c.get("/api/me", headers=X).json()
        assert me["username"] == "minh_tran" and me["display_name"] == "Minh Trần", me
        assert c.get("/api/me", headers=X).json()["username"] == "minh_tran"            # lần sau không tạo trùng
        assert c.get("/api/me", headers={"Authorization": "Bearer sai"}).status_code == 401
        assert c.post("/api/auth/login", json={"username": "lan", "password": "matkhau123"}).status_code == 403
        assert c.post("/api/auth/register", json={"username": "moi_moi", "password": "matkhau123", "display_name": "x"}).status_code == 403
    finally:
        security.EXTERNAL_AUTH = None


@test
def _():
    """Xóa tài khoản xóa sạch bài, bình luận, kết nối"""
    assert c.delete("/api/me", headers=A).status_code == 200
    assert c.get("/api/me", headers=A).status_code == 401
    assert c.get("/api/users/minh", headers=B).status_code == 404
    assert c.get("/api/connections", headers=B).json()["connections"] == []
    assert c.get(f"/api/places/{PLACE}", headers=B).json()["posts"] == []


if __name__ == "__main__":
    for status, name in RESULTS:
        print(f"[{status}] {name}")
    shutil.rmtree(TMP, ignore_errors=True)
    failed = sum(s == "LỖI" for s, _ in RESULTS)
    print(f"\n{len(RESULTS) - failed}/{len(RESULTS)} đạt")
    sys.exit(1 if failed else 0)
