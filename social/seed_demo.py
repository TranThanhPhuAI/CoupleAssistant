"""Dữ liệu MẪU cho tab Cộng đồng, để giao diện có nội dung khi chưa có người dùng thật.

    python social/seed_demo.py            tạo 12 tài khoản mẫu + bài viết, kết nối, thích, bình luận
    python social/seed_demo.py --xoa      xóa sạch mọi tài khoản mẫu (và mọi thứ của họ)

Nguyên tắc để không đánh lừa người xem:
- Mọi tài khoản mẫu có cờ is_demo -> giao diện luôn hiện nhãn "Tài khoản mẫu".
- Nội dung review lấy NGUYÊN VĂN từ review thật của chính quán đó (dữ liệu Foody), số sao đổi từ điểm của review đó
  (thang 10 -> 5 sao). Không bịa nhận xét về quán thật.
- Ảnh của bài mẫu là ảnh MINH HỌA theo loại món (Unsplash), không phải ảnh chụp tại quán: luôn có nhãn "Ảnh minh họa".
- Nên chạy --xoa trước khi mở cho người dùng thật.
"""
import csv
import json
import random
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lovespot import config as cfg  # noqa: E402
from lovespot.catalog import fold, places  # noqa: E402
from lovespot.db import pair, session  # noqa: E402

REVIEWS_CSV = cfg.PLACES_CSV.parent / "reviews_clean.csv"
VI_MARKS = re.compile(r"[ăâđêôơưàáạảãằắặẳẵầấậẩẫèéẹẻẽềếệểễìíịỉĩòóọỏõồốộổỗờớợởỡùúụủũừứựửữỳýỵỷỹ]", re.I)

USERS = [  # (tên người dùng, tên hiển thị, một dòng về gu, quận, sở thích)
    ("ngoc_han", "Ngọc Hân", "Săn quán cà phê yên tĩnh để đọc sách", "Quận 3", ["ca_phe", "yen_tinh", "trang_mieng"]),
    ("tuan_kiet", "Tuấn Kiệt", "Mê lẩu nướng, đi đâu cũng rủ cả nhóm", "Quận Bình Thạnh", ["lau", "nuong", "soi_dong"]),
    ("bao_anh", "Bảo Anh", "Hẹn hò là phải có view", "Quận 1", ["view_dep", "lang_man", "chup_anh"]),
    ("minh_khoi", "Minh Khôi", "Fine dining cuối tuần, steak là chân ái", "Quận 1", ["au", "sang_trong", "lang_man"]),
    ("thu_trang", "Thu Trang", "Ăn chay và yêu những quán có sân vườn", "Quận Phú Nhuận", ["chay", "san_vuon", "yen_tinh"]),
    ("gia_huy", "Gia Huy", "Sushi, ramen và mọi thứ Nhật Bản", "Quận 3", ["nhat", "yen_tinh", "khong_gian"]),
    ("my_linh", "Mỹ Linh", "Trà sữa mỗi ngày, bánh ngọt cuối tuần", "Quận 10", ["tra_sua", "trang_mieng", "chup_anh"]),
    ("duc_anh", "Đức Anh", "Quán ngon giá sinh viên khắp Sài Gòn", "Quận 4", ["an_vat", "gia_re", "viet"]),
    ("khanh_vy", "Khánh Vy", "Hẹn hò thích chỗ riêng tư, ấm cúng", "Quận 7", ["rieng_tu", "lang_man", "au"]),
    ("hoang_nam", "Hoàng Nam", "Hải sản và đồ nướng cuối tuần", "Quận 4", ["hai_san", "nuong", "soi_dong"]),
    ("phuong_thao", "Phương Thảo", "Cà phê decor xinh để chụp ảnh", "Quận Phú Nhuận", ["ca_phe", "khong_gian", "chup_anh"]),
    ("quoc_bao", "Quốc Bảo", "Món Hàn, lẩu Thái, càng cay càng vui", "Quận Tân Bình", ["han", "thai", "lau"]),
]
# Từ khóa trong tên / loại quán ứng với từng sở thích (để mỗi người review đúng gu của mình)
KEYS = {"ca_phe": ["cafe", "coffee", "ca phe"], "lau": ["lau"], "nuong": ["nuong", "bbq", "grill"], "nhat": ["sushi", "ramen", "nhat"],
        "au": ["steak", "pizza", "bistro", "pasta"], "tra_sua": ["tra sua", "tea", "the"], "chay": ["chay", "vegan"],
        "hai_san": ["hai san", "oc ", "seafood", "cua"], "han": ["han quoc", "korean", "gogi", "kimchi"], "thai": ["thai"],
        "trang_mieng": ["banh", "kem", "dessert", "cake"], "an_vat": ["an vat", "banh trang", "xien"], "viet": ["pho", "bun", "com"]}
# Ảnh MINH HỌA (Unsplash, giấy phép miễn phí) theo loại món / không gian. Đã xem từng ảnh để đúng loại.
# KHÔNG phải ảnh chụp tại quán: giao diện luôn gắn nhãn "Ảnh minh họa".
DEMO_IMAGES = {
    "ca_phe": ["1495474472287-4d71bcdd2085", "1509042239860-f550ce710b93", "1442512595331-e89e73853f31",
               "1501339847302-ac426a4a7cbb", "1554118811-1e0d58224f24", "1445116572660-236099ec97a0", "1541167760496-1628856ab772"],
    "lau": ["1617093727343-374698b1b08d", "1604908176997-125f25cc6f3d"],
    "nuong": ["1555939594-58d7cb561ad1", "1529193591184-b1d58069ecdd", "1558030006-450675393462", "1544025162-d76694265947"],
    "nhat": ["1579871494447-9811cf80d66c", "1553621042-f6e147245754", "1569718212165-3a8278d5f624", "1611143669185-af224c5e3252"],
    "au": ["1414235077428-338989a2e8c0", "1565299624946-b28f40a0ae38", "1621996346565-e3dbc646d9a9"],
    "trang_mieng": ["1551024601-bec78aea704b", "1488477181946-6428a0291777", "1563729784474-d77dbb933a9e", "1578985545062-69928b1d9587"],
    "tra_sua": ["1558857563-b371033873b8", "1525803377221-4f6ccdaa5133"],
    "hai_san": ["1565680018434-b513d5e5fd47", "1615141982883-c7ad0e69fd62", "1559737558-2f5a35f4523b"],
    "chay": ["1512621776951-a57141f2eefd", "1540189549336-e6e99c3679fe"],
    "han": ["1590301157890-4810ed352733", "1498654896293-37aacf113fd9"],
    "viet": ["1582878826629-29b7ad1cdc43", "1503764654157-72d979d9af2f", "1576577445504-6af96477db52"],
    "khong_gian": ["1517248135467-4c7edcad34c4", "1514933651103-005eec06c04b", "1552566626-52f8b828add9",
                   "1559339352-11d035aa65de", "1424847651672-bf20a4b0982b"],
}


def _image(cat, rng):
    return {"url": f"https://images.unsplash.com/photo-{rng.choice(DEMO_IMAGES[cat])}?w=1200&q=70&auto=format&fit=crop",
            "demo": True, "credit": "Unsplash"}


def _images_for(pid, rng):
    """1–2 ảnh minh họa theo loại quán (tên quán chứa từ khóa món), thêm ảnh không gian; ~15% bài không có ảnh."""
    key = places()[pid]["_key"]
    cat = next((c for c in DEMO_IMAGES if c in KEYS and any(k in key for k in KEYS[c])), "khong_gian")
    roll = rng.random()
    if roll < 0.15:
        return []
    imgs = [_image(cat, rng)]
    if roll > 0.7:
        imgs.append(_image("khong_gian" if cat != "khong_gian" else "ca_phe", rng))
    return imgs


STATUS = ["Ai biết quán cà phê nào mở tới 23h, ngồi yên để trò chuyện không? Đang tìm chỗ cho tối thứ 6.",
          "Cuối tuần này mưa, có ai gợi ý quán lẩu ấm cúng cho hai người không?",
          "Kỷ niệm 1 năm muốn tìm chỗ có view đẹp mà không quá ồn. Mọi người gợi ý giúp với!",
          "Lần đầu hẹn hò nên chọn cà phê hay đi ăn tối luôn? Mọi người hay chọn kiểu nào?",
          "Đang gom danh sách quán chay ngon ở Phú Nhuận, ai có quán ruột thì cho xin tên nhé.",
          "Hôm nay thử lập plan bằng Couple Assistant: ăn tối rồi cà phê, đi bộ chỉ 10 phút. Tiện thật."]
COMMENTS = ["Lưu lại cuối tuần đi thử!", "Quán này mình đi rồi, đồng ý nha.", "Nhìn hấp dẫn quá, tag người yêu liền.",
            "Có cần đặt bàn trước không bạn?", "Hôm nào đi chung không?", "Cảm ơn review chi tiết!", "Giá vậy là ổn đó.",
            "Mình thích chỗ này vì yên, ngồi nói chuyện được lâu."]


def _clean(text, place_name):
    """Bỏ tên quán lặp ở đầu review, gọn khoảng trắng, cắt ở cuối câu (tối đa ~320 ký tự)."""
    t = re.sub(r"\s+", " ", text or "").strip()
    if fold(t).startswith(fold(place_name)[:20]):
        t = t.split(". ", 1)[1] if ". " in t else t
    if len(t) > 320:
        cut = max(t.rfind(". ", 0, 320), t.rfind("! ", 0, 320))
        t = t[:cut + 1] if cut > 120 else t[:317].rsplit(" ", 1)[0] + "…"
    return t


def _reviews():
    """{restaurant_id: [(text, stars)]} — chỉ review tiếng Việt dài vừa phải, có điểm."""
    out = {}
    if not REVIEWS_CSV.exists():
        return out
    with open(REVIEWS_CSV, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            try:
                score = float(r["rating"])
            except (TypeError, ValueError):
                continue
            text = r["review_text"] or ""
            # nhãn ngôn ngữ của dữ liệu gốc có chỗ sai -> chỉ lấy review có đủ chữ có dấu tiếng Việt
            if (r.get("language") == "vi" and 80 <= len(text) <= 900 and r["restaurant_id"] in places()
                    and len(VI_MARKS.findall(text)) >= len(text) / 25):
                out.setdefault(r["restaurant_id"], []).append((r["review_text"], max(1, min(5, round(score / 2)))))
    return out


def _places_for(interests, reviewed, rng):
    keys = [k for i in interests for k in KEYS.get(i, [])]
    hits = [pid for pid in reviewed if any(k in places()[pid]["_key"] for k in keys)]
    return hits or list(reviewed)


def seed(n_posts=48, rng=None):
    rng = rng or random.Random(7)
    reviewed = _reviews()
    if not places() or not reviewed:
        sys.exit("Không thấy dữ liệu quán / review (data/clean/). Chạy Couple Assistant 'python run.py xaylai' trước.")
    now = datetime.now(timezone.utc)
    with session() as con:
        ids = {}
        for u, name, head, dist, ints in USERS:
            if con.execute("SELECT 1 FROM users WHERE username=?", (u,)).fetchone():
                continue   # trùng tên với tài khoản đã có -> bỏ qua, không ghi đè
            joined = (now - timedelta(days=rng.randint(25, 60))).strftime("%Y-%m-%d %H:%M:%S")
            ids[u] = con.execute("INSERT INTO users(username, pw_hash, display_name, headline, district, interests, is_demo, created_at) "
                                 "VALUES (?, '!', ?, ?, ?, ?, 1, ?)", (u, name, head, dist, json.dumps(ints), joined)).lastrowid
        if not ids:
            return print("Tài khoản mẫu đã có sẵn. Muốn tạo lại: python social/seed_demo.py --xoa  rồi chạy lại.")
        uids = list(ids.values())
        for u in uids:   # mỗi người kết nối với 2–4 người mẫu khác
            for v in rng.sample([x for x in uids if x != u], rng.randint(2, 4)):
                con.execute("INSERT OR IGNORE INTO connections(a, b, status, requested_by) VALUES (?,?, 'accepted', ?)", (*pair(u, v), u))
        # Bài viết, xếp theo thời gian trong 3 tuần gần đây (id tăng dần theo thời gian để bảng tin đúng thứ tự)
        times = sorted(now - timedelta(minutes=rng.randint(20, 21 * 24 * 60)) for _ in range(n_posts))
        posts, used = [], set()
        for t in times:
            uname, _, _, _, ints = rng.choice([x for x in USERS if x[0] in ids])
            roll = rng.random()
            ts = t.strftime("%Y-%m-%d %H:%M:%S")
            if roll < 0.12:
                kind, body, pid, stars, imgs = "status", rng.choice(STATUS), None, None, []
            else:
                pid = rng.choice([p for p in _places_for(ints, reviewed, rng) if p not in used] or list(reviewed))
                used.add(pid)
                text, stars = rng.choice(reviewed[pid])
                kind, body = ("review" if roll < 0.85 else "checkin"), _clean(text, places()[pid]["name"])
                if kind == "checkin":
                    stars = None
                imgs = _images_for(pid, rng)
            posts.append(con.execute("INSERT INTO posts(author_id, kind, body, place_id, rating, created_at, images) VALUES (?,?,?,?,?,?,?)",
                                     (ids[uname], kind, body, pid, stars, ts, json.dumps(imgs))).lastrowid)
            for liker in rng.sample(uids, rng.randint(0, 6)):
                con.execute("INSERT OR IGNORE INTO likes(post_id, user_id) VALUES (?,?)", (posts[-1], liker))
            for _ in range(rng.choice([0, 0, 1, 1, 2, 3])):
                when = (t + timedelta(minutes=rng.randint(5, 600))).strftime("%Y-%m-%d %H:%M:%S")
                con.execute("INSERT INTO comments(post_id, author_id, body, created_at) VALUES (?,?,?,?)",
                            (posts[-1], rng.choice(uids), rng.choice(COMMENTS), when))
        for u in uids:   # theo dõi vài quán đã được nhắc tới
            for pid in rng.sample(sorted(used), min(3, len(used))):
                con.execute("INSERT OR IGNORE INTO place_follows(user_id, place_id) VALUES (?,?)", (u, pid))
    print(f"Đã tạo {len(ids)} tài khoản mẫu, {len(posts)} bài viết (review lấy từ review thật của {len(used)} quán).")
    print("Xóa khi không cần nữa:  python social/seed_demo.py --xoa")


def remove():
    with session() as con:
        n = con.execute("DELETE FROM users WHERE is_demo=1").rowcount   # bài viết, bình luận, kết nối… xóa theo (CASCADE)
    print(f"Đã xóa {n} tài khoản mẫu cùng bài viết, bình luận, kết nối của họ.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    remove() if "--xoa" in sys.argv else seed()
