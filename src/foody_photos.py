"""Lấy link ảnh quán từ trang Foody của từng quán (ảnh bìa + album ảnh món) để thẻ gợi ý hiện ảnh ngay trên web.

Chỉ lưu ĐƯỜNG LINK vào data/place_media/foody.json: ảnh vẫn nằm trên máy chủ ảnh của Foody/Shopee, không tải file về.
Thẻ quán ghi nguồn "Ảnh: Foody" và có link về trang gốc. Chạy chậm (mặc định 1 trang / 1,2 giây) để không làm phiền họ.

  python run.py anhfoody                 lấy cho các quán chưa có (bị ngắt thì chạy lại, làm tiếp chỗ cũ)
  python run.py anhfoody --lam-moi 30    lấy lại cả các quán đã lấy quá 30 ngày
  python run.py anhfoody --gioi-han 20   chỉ lấy 20 quán (chạy thử)
"""
import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request

import place_media as pm

IMG = r"https://down-vn\.img\.susercontent\.com/[A-Za-z0-9_\-]+"
OG = re.compile(rf'<meta property="og:image" content="({IMG})"')          # ảnh bìa của quán
GALLERY = re.compile(rf'<img[^>]+src="({IMG})@resize_ss180x180"')          # album ảnh (avatar người review cỡ khác, không khớp)
MAX = 8


def parse(html):
    return list(dict.fromkeys(OG.findall(html)[:1] + GALLERY.findall(html)))[:MAX]


def load():
    try:
        return json.loads((pm.DIR / "foody.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


def save(data):
    pm.DIR.mkdir(parents=True, exist_ok=True)
    tmp = pm.DIR / "foody.json.tmp"
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    tmp.replace(pm.DIR / "foody.json")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept-Language": "vi"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read(4_000_000).decode("utf-8", "replace")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Lấy link ảnh quán từ Foody")
    ap.add_argument("--lam-moi", type=int, default=0, help="lấy lại quán đã lấy quá N ngày")
    ap.add_argument("--gioi-han", type=int, default=0, help="chỉ lấy N quán")
    ap.add_argument("--cho", type=float, default=1.2, help="số giây chờ giữa hai trang")
    a = ap.parse_args()
    cat, data, now = pm.catalog(), load(), time.time()
    todo = [pid for pid, c in cat.items() if c["foody"] and
            (pid not in data or (a.lam_moi and now - data[pid]["at"] > a.lam_moi * 86400))]
    if a.gioi_han:
        todo = todo[:a.gioi_han]
    print(f"Cần lấy ảnh cho {len(todo)} quán (đã có {len(data)}), khoảng {len(todo) * (a.cho + 0.6) / 60:.0f} phút.")
    ok = fail = 0
    for i, pid in enumerate(todo, 1):
        try:
            data[pid] = {"photos": parse(fetch(cat[pid]["foody"])), "at": int(time.time())}
            ok += 1
        except urllib.error.HTTPError as e:
            if e.code == 404:   # trang đã gỡ: ghi rỗng để lần sau không thử lại
                data[pid] = {"photos": [], "at": int(time.time())}
            fail += 1
            print(f"  lỗi {e.code}: {cat[pid]['name'][:50]}")
        except Exception as e:  # mạng chập chờn: bỏ qua, lần chạy sau thử lại
            fail += 1
            print(f"  lỗi: {cat[pid]['name'][:50]}: {e}")
        if fail >= 15 and ok == 0:
            print("Dừng: không lấy được trang nào (mất mạng hoặc Foody chặn). Thử lại sau.")
            break
        if i % 20 == 0 or i == len(todo):
            save(data)
            print(f"  {i}/{len(todo)}  được {ok}, lỗi {fail}")
        time.sleep(a.cho)
    save(data)
    have = sum(1 for v in data.values() if v["photos"])
    print(f"Xong. {have} quán có ảnh Foody.")


if __name__ == "__main__":
    main()
