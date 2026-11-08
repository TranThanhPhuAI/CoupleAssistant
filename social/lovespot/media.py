"""Ảnh trong bài viết: tải lên (JSON base64, trình duyệt đã thu nhỏ ảnh trước), phục vụ, xóa.

- Chỉ nhận JPEG / PNG / WebP, kiểm tra bằng chữ ký đầu file (không tin đuôi tên hay khai báo của trình duyệt).
- Tên file ngẫu nhiên 32 ký tự hex -> không đoán được; thẻ <img> không gửi được token nên ảnh không cần đăng nhập để xem.
"""
import base64
import binascii
import json
import re
import secrets

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from . import config as cfg
from .security import current_user

router = APIRouter(prefix="/api")
NAME = re.compile(r"^[0-9a-f]{32}\.(jpg|png|webp)$")
SIGNATURES = [(b"\xff\xd8\xff", "jpg"), (b"\x89PNG\r\n\x1a\n", "png")]


class UploadIn(BaseModel):
    data: str = Field(..., max_length=cfg.MAX_IMAGE_BYTES * 4 // 3 + 100)   # data:image/...;base64,....


def _kind(raw):
    for sig, ext in SIGNATURES:
        if raw.startswith(sig):
            return ext
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "webp"
    return None


@router.post("/uploads", status_code=201)
def upload(body: UploadIn, me=Depends(current_user)):
    head, _, b64 = body.data.partition(",")
    if not head.startswith("data:image/") or ";base64" not in head:
        raise HTTPException(422, "Ảnh không đúng định dạng")
    try:
        raw = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(422, "Dữ liệu ảnh hỏng")
    if len(raw) > cfg.MAX_IMAGE_BYTES:
        raise HTTPException(413, f"Ảnh quá lớn (tối đa {cfg.MAX_IMAGE_BYTES // 1024 // 1024} MB)")
    ext = _kind(raw)
    if ext is None:
        raise HTTPException(422, "Chỉ nhận ảnh JPEG, PNG hoặc WebP")
    cfg.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{secrets.token_hex(16)}.{ext}"
    (cfg.UPLOAD_DIR / name).write_bytes(raw)
    return {"upload": name}


@router.get("/uploads/{name}", include_in_schema=False)
def serve(name: str):
    f = cfg.UPLOAD_DIR / name
    if not NAME.match(name) or not f.is_file():
        raise HTTPException(404, "Không có ảnh này")
    return FileResponse(f, headers={"Cache-Control": "public, max-age=31536000, immutable", "X-Content-Type-Options": "nosniff"})


def check_uploads(names):
    """Ảnh gắn vào bài phải là file đã tải lên qua /api/uploads."""
    if len(names) > cfg.MAX_IMAGES:
        raise HTTPException(422, f"Tối đa {cfg.MAX_IMAGES} ảnh mỗi bài")
    for n in names:
        if not NAME.match(n) or not (cfg.UPLOAD_DIR / n).is_file():
            raise HTTPException(422, "Ảnh chưa được tải lên hoặc đã bị xóa")
    return [{"upload": n} for n in dict.fromkeys(names)]


def public(images_json):
    """Cho giao diện: [{"upload": tên}] hoặc [{"url": ..., "demo": true}] (ảnh minh họa của bài mẫu)."""
    try:
        items = json.loads(images_json or "[]")
    except ValueError:
        return []
    return [i for i in items if isinstance(i, dict) and (NAME.match(str(i.get("upload", ""))) or str(i.get("url", "")).startswith("https://"))]


def delete_files(images_json_list):
    for js in images_json_list:
        for i in public(js):
            if "upload" in i:
                (cfg.UPLOAD_DIR / i["upload"]).unlink(missing_ok=True)
