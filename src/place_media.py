"""Ảnh và menu của quán, hiện trên thẻ gợi ý và chặng plan.

Nguồn (không lấy ảnh / menu của Foody về, chỉ dẫn link sang trang gốc):
  - Ảnh + menu do quản trị viên nhập ở tab Phân quyền -> data/place_media/ (media.json + photos/)
  - Ảnh thật người dùng đăng trong tab Cộng đồng khi gắn quán (bỏ bài mẫu / ảnh minh họa)
  - Link "Xem trên Foody" (source_url) và "Đặt món ShopeeFood" (website) có sẵn trong dữ liệu

  GET    /api/places/{id}/media                   ảnh, menu, link của một quán (cần đăng nhập)
  GET    /api/place-photos/{tên file}             file ảnh (công khai: thẻ <img> không gửi được token, tên ngẫu nhiên)
  GET    /api/admin/places?q=...                  tìm quán để thêm ảnh / menu (chỉ quản trị viên)
  PUT    /api/admin/places/{id}/menu              lưu menu [{name, price}]
  POST   /api/admin/places/{id}/photos            tải ảnh lên (data URL JPEG/PNG/WebP)
  DELETE /api/admin/places/{id}/photos/{tên file} xóa ảnh
"""
import base64
import binascii
import json
import re
import secrets
import threading
import time
import unicodedata
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import config as cfg

DIR = cfg.BASE / "data" / "place_media"
PHOTOS = DIR / "photos"
INDEX = DIR / "media.json"
MAX_PHOTOS, MAX_MENU, MAX_BYTES = 8, 40, 3 * 1024 * 1024
NAME = re.compile(r"^[0-9a-f]{32}\.(jpg|png|webp)$")
PLACE_ID = r"^[A-Za-z0-9_\-]{1,64}$"
LINK_OK = re.compile(r"^https://(www\.)?(foody|shopeefood)\.vn/")   # chỉ dẫn link sang hai trang nguồn của dữ liệu

COMMUNITY = None   # api.py gắn khi có tab Cộng đồng: hàm (danh sách mã quán) -> {mã quán: [url ảnh]}

public = APIRouter()   # cần đăng nhập (api.py gắn dependency)
admin = APIRouter()    # chỉ quản trị viên
files = APIRouter()    # công khai
_lock = threading.Lock()
_cat, _cat_sig = None, None


def _plain(s):
    """Bỏ dấu + chữ thường để tìm "phuc long" ra "Phúc Long"."""
    s = unicodedata.normalize("NFD", str(s).replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def catalog():
    """{mã quán: {name, district, address, foody, order, key}}; nạp lại khi file dữ liệu đổi."""
    global _cat, _cat_sig
    sig = cfg.RESTAURANTS_CLEAN.stat().st_mtime_ns if cfg.RESTAURANTS_CLEAN.exists() else 0
    if _cat is None or sig != _cat_sig:
        out = {}
        if sig:
            df = pd.read_csv(cfg.RESTAURANTS_CLEAN, encoding="utf-8-sig",
                             usecols=["restaurant_id", "name", "district", "address", "website", "source_url"]).fillna("")
            for r in df.itertuples(index=False):
                links = [u for u in (r.source_url, r.website) if LINK_OK.match(u)]
                out[r.restaurant_id] = {"name": r.name, "district": r.district, "address": r.address,
                                        "foody": next((u for u in links if "foody.vn" in u), None),
                                        "order": next((u for u in links if "shopeefood.vn" in u), None),
                                        "key": _plain(f"{r.name} {r.district} {r.address}")}
        _cat, _cat_sig = out, sig
    return _cat


def _load():
    try:
        return json.loads(INDEX.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


def _save(data):
    DIR.mkdir(parents=True, exist_ok=True)
    tmp = INDEX.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(INDEX)


def _photo_url(name):
    return f"/api/place-photos/{name}"


FOODY_IMG = re.compile(r"^https://down-vn\.img\.susercontent\.com/[A-Za-z0-9_\-]+$")
_foody_cache, _foody_sig = {}, None


def foody_photos():
    """{mã quán: [link ảnh gốc]} do lệnh `python run.py anhfoody` lấy (foody_photos.py); nạp lại khi file đổi."""
    global _foody_cache, _foody_sig
    f = DIR / "foody.json"
    sig = (str(f), f.stat().st_mtime_ns) if f.exists() else None
    if sig != _foody_sig:
        try:
            raw = json.loads(f.read_text(encoding="utf-8")) if sig else {}
        except ValueError:
            raw = {}
        _foody_cache = {pid: [u for u in v.get("photos", []) if FOODY_IMG.match(u)] for pid, v in raw.items() if isinstance(v, dict)}
        _foody_sig = sig
    return _foody_cache


def media_of(pid, saved=None, community=None):
    c = catalog().get(pid) or {}
    m = (saved if saved is not None else _load()).get(pid, {})
    return {"photos": [_photo_url(n) for n in m.get("photos", [])], "menu": m.get("menu", []),
            "foody_photos": foody_photos().get(pid, []) if c.get("foody") else [],
            "community_photos": (community or {}).get(pid, [])[:6],
            "foody": c.get("foody"), "order": c.get("order")}


def social_photos(place_ids):
    """Ảnh thật người dùng đăng kèm quán ở tab Cộng đồng (bài công khai, bỏ tài khoản mẫu và ảnh minh họa).
    api.py gắn vào COMMUNITY sau khi đã nạp được gói lovespot (thư mục social/)."""
    from lovespot import media as social_media
    from lovespot.db import session
    marks, out = ",".join("?" * len(place_ids)), {}
    with session() as con:
        for r in con.execute(f"SELECT p.place_id, p.images FROM posts p JOIN users u ON u.id = p.author_id "
                             f"WHERE p.place_id IN ({marks}) AND p.visibility='public' AND u.is_demo=0 AND p.images != '[]' "
                             "ORDER BY p.id DESC", list(place_ids)):
            out.setdefault(r["place_id"], []).extend(
                f"/social/api/uploads/{i['upload']}" for i in social_media.public(r["images"]) if "upload" in i)
    return out


def attach(items):
    """Gắn "media" vào mỗi quán trong kết quả gợi ý / plan (bỏ qua chặng đi dạo)."""
    ids = [it["restaurant_id"] for it in items if it.get("kind") != "walk" and it.get("restaurant_id") in catalog()]
    if not ids:
        return items
    saved, community = _load(), {}
    if COMMUNITY:
        try:
            community = COMMUNITY(ids)
        except Exception:   # Cộng đồng lỗi không được làm hỏng kết quả gợi ý
            community = {}
    for it in items:
        if it.get("restaurant_id") in ids:
            it["media"] = media_of(it["restaurant_id"], saved, community)
    return items


def _place(pid):
    if not re.match(PLACE_ID, pid) or pid not in catalog():
        raise HTTPException(404, "Không có quán này")
    return pid


# ======================= Xem =======================

@public.get("/api/places/{pid}/media")
def get_media(pid: str):
    _place(pid)
    community = {}
    if COMMUNITY:
        try:
            community = COMMUNITY([pid])
        except Exception:
            community = {}
    return media_of(pid, community=community)


@files.get("/api/place-photos/{name}", include_in_schema=False)
def serve(name: str):
    f = PHOTOS / name
    if not NAME.match(name) or not f.is_file():
        raise HTTPException(404, "Không có ảnh này")
    return FileResponse(f, headers={"Cache-Control": "public, max-age=31536000, immutable", "X-Content-Type-Options": "nosniff"})


# ======================= Quản trị viên nhập =======================

class MenuItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    price: Optional[int] = Field(None, ge=0, le=50_000_000, description="VNĐ")


class MenuIn(BaseModel):
    items: list[MenuItem] = Field(default_factory=list, max_length=MAX_MENU)


class PhotoIn(BaseModel):
    data: str = Field(..., max_length=MAX_BYTES * 4 // 3 + 100)   # data:image/...;base64,...


@admin.get("/api/admin/places")
def search(q: str = "", limit: int = 20):
    words = _plain(q).split()
    saved = _load()
    rows = [(pid, c) for pid, c in catalog().items() if all(w in c["key"] for w in words)] if words \
        else [(pid, catalog()[pid]) for pid in saved if pid in catalog()]   # ô tìm trống: các quán đã có ảnh / menu
    rows = sorted(rows, key=lambda x: (-len(saved.get(x[0], {}).get("photos", [])) - len(saved.get(x[0], {}).get("menu", [])), x[1]["name"]))
    return [{"id": pid, "name": c["name"], "district": c["district"], "address": c["address"],
             "photos": len(saved.get(pid, {}).get("photos", [])), "menu": len(saved.get(pid, {}).get("menu", []))}
            for pid, c in rows[:max(1, min(limit, 50))]]


@admin.put("/api/admin/places/{pid}/menu")
def put_menu(pid: str, body: MenuIn):
    _place(pid)
    items = [{"name": " ".join(i.name.split()), "price": i.price} for i in body.items if i.name.strip()]
    with _lock:
        data = _load()
        rec = data.setdefault(pid, {})
        rec["menu"], rec["updated_at"] = items, int(time.time())
        _save(data)
    return media_of(pid)


def _kind(raw):
    if raw.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "webp"
    return None


@admin.post("/api/admin/places/{pid}/photos", status_code=201)
def add_photo(pid: str, body: PhotoIn):
    _place(pid)
    head, _, b64 = body.data.partition(",")
    if not head.startswith("data:image/") or ";base64" not in head:
        raise HTTPException(422, "Ảnh không đúng định dạng")
    try:
        raw = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(422, "Dữ liệu ảnh hỏng")
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, f"Ảnh quá lớn (tối đa {MAX_BYTES // 1024 // 1024} MB)")
    ext = _kind(raw)   # kiểm tra chữ ký đầu file, không tin khai báo của trình duyệt
    if ext is None:
        raise HTTPException(422, "Chỉ nhận ảnh JPEG, PNG hoặc WebP")
    with _lock:
        data = _load()
        rec = data.setdefault(pid, {})
        if len(rec.get("photos", [])) >= MAX_PHOTOS:
            raise HTTPException(409, f"Mỗi quán tối đa {MAX_PHOTOS} ảnh, hãy xóa bớt")
        PHOTOS.mkdir(parents=True, exist_ok=True)
        name = f"{secrets.token_hex(16)}.{ext}"
        (PHOTOS / name).write_bytes(raw)
        rec.setdefault("photos", []).append(name)
        rec["updated_at"] = int(time.time())
        _save(data)
    return media_of(pid)


@admin.delete("/api/admin/places/{pid}/photos/{name}")
def delete_photo(pid: str, name: str):
    _place(pid)
    with _lock:
        data = _load()
        rec = data.get(pid, {})
        if not NAME.match(name) or name not in rec.get("photos", []):
            raise HTTPException(404, "Không có ảnh này")
        rec["photos"].remove(name)
        _save(data)
    (PHOTOS / name).unlink(missing_ok=True)
    return media_of(pid)
