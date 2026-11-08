"""Server web: API REST (JSON) + giao diện. Chạy:  python run.py web   -> http://127.0.0.1:8000

  GET  /api/health                 trạng thái (công khai, cho dịch vụ ping)
  POST /api/auth/register | login  đăng ký / đăng nhập -> token JWT (gửi kèm: Authorization: Bearer <token>)
  GET  /api/auth/me                tài khoản hiện tại        DELETE: xóa tài khoản + hồ sơ của mình
  GET  /api/interests | questions  danh mục 24 sở thích / bảng hỏi tính cách
  GET  /api/profiles               danh sách hồ sơ (mã + tên, để chọn người đi cùng)
  GET/PUT/DELETE /api/profiles/{id}   hồ sơ của CHÍNH MÌNH (admin: mọi hồ sơ)
  POST /api/suggest | plan         gợi ý quán / lập plan (người hỏi = người đang đăng nhập)
  POST /api/choose                 chọn quán từ gợi ý
  GET  /api/metrics                chỉ số AI (chỉ admin)
  /api/places/*, /api/admin/places/*   ảnh + menu quán (xem place_media.py)
  /docs                            tài liệu API tự sinh

Mặc định BẮT BUỘC đăng nhập (cfg.AUTH_REQUIRED). Server chỉ nghe ở 127.0.0.1; ra Internet qua Cloudflare Tunnel.
"""
import argparse
import math
import sys
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal, Optional

import jwt
import numpy as np
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import config as cfg
import place_media
from ai_service import AiLog, choose_place, metrics, plan, quota, suggest, unchoose_place
from auth import AccountStore, decode_token, issue_token
from interests import CATALOG
from personality import QUESTIONS, ProfileStore
from ranker import Person

WEB_DIR = Path(__file__).resolve().parent / "web"
HHMM = r"^([01]\d|2[0-3]):[0-5]\d$"
USER_ID = r"^[A-Za-z0-9_\-]{1,40}$"
@asynccontextmanager
async def lifespan(_app):
    warm_up()
    yield


app = FastAPI(title="Couple Assistant API", version="1.1", lifespan=lifespan,
              description="AI gợi ý quán hẹn hò và lập plan cho cặp đôi ở TP.HCM (module AI của Lovespot).")
store, log, accounts = ProfileStore(), AiLog(), AccountStore()  # đổi được khi kiểm thử (thư mục tạm)
bearer = HTTPBearer(auto_error=False)


_DATA_FILES = [cfg.INDEX_DIR / "CURRENT", cfg.RESTAURANTS_CLEAN, cfg.SCORES, cfg.RESTAURANT_TRAITS,
               cfg.PLACE_TAGS, cfg.ABSA_REVIEW_PRED, cfg.CLEAN_DIR / "place_interests.csv"]
_data_sig, _data_lock = None, threading.Lock()


def fresh_data():
    """Lịch tự động (run.py nhap / tinhlai) ghi dữ liệu mới khi server đang chạy -> bỏ bộ nhớ đệm để nạp lại,
    không cần khởi động lại server. Chỉ tốn vài lệnh stat mỗi request."""
    global _data_sig
    sig = tuple(p.stat().st_mtime_ns if p.exists() else 0 for p in _DATA_FILES)
    with _data_lock:
        if _data_sig is not None and sig != _data_sig:
            import explainer, interests, ranker, recommend, semantic
            with semantic._model_lock:
                semantic._searcher = None
            ranker._cache.clear()
            explainer._cache.clear()
            recommend._traits = interests._matrix = None
        _data_sig = sig


def jsonable(o):
    """Chuyển kết quả nội bộ (numpy, NaN, DataFrame) thành JSON; bỏ trường nội bộ ranked_frame."""
    if isinstance(o, dict):
        return {k: jsonable(v) for k, v in o.items() if k != "ranked_frame"}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if math.isnan(o) else float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def _loc(v):
    return tuple(v) if v else None


# ======================= Đăng nhập =======================

def current_user(cred: Optional[HTTPAuthorizationCredentials] = Depends(bearer)):
    """{"sub": mã tài khoản, "role": member|admin}. Khi tắt đăng nhập (chạy thử trên máy): sub=None, role=admin."""
    if not cfg.AUTH_REQUIRED:
        return {"sub": None, "role": "admin"}
    if cred is None:
        raise HTTPException(401, "Chưa đăng nhập", headers={"WWW-Authenticate": "Bearer"})
    try:
        claims = decode_token(cred.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Phiên đăng nhập đã hết hạn, hãy đăng nhập lại")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Token không hợp lệ")
    role = accounts.role(claims["sub"])
    if role is None:
        raise HTTPException(401, "Tài khoản không còn tồn tại")
    return {"sub": claims["sub"], "role": role}


def require_admin(me=Depends(current_user)):
    if me["role"] != "admin":
        raise HTTPException(403, "Chỉ quản trị viên được xem mục này")
    return me


def _check_owner(me, user_id):
    if me["role"] != "admin" and me["sub"] != user_id:
        raise HTTPException(403, "Bạn chỉ xem / sửa được hồ sơ của chính mình")


def _asker(me, body_user_a):
    """Người hỏi = người đang đăng nhập (không cho hỏi thay người khác)."""
    if me["sub"] is None:  # đã tắt đăng nhập
        return body_user_a
    if body_user_a and body_user_a != me["sub"] and me["role"] != "admin":
        raise HTTPException(403, "Chỉ hỏi được bằng hồ sơ của chính mình")
    return body_user_a or me["sub"]


# ======================= Mô hình dữ liệu vào =======================

class RegisterIn(BaseModel):
    user_id: str = Field(..., pattern=USER_ID, description="chữ, số, _ hoặc -")
    password: str = Field(..., min_length=cfg.AUTH_MIN_PASSWORD, max_length=128)


class LoginIn(BaseModel):
    user_id: str = Field(..., max_length=40)
    password: str = Field(..., max_length=128)


class ProfileIn(BaseModel):
    consent: bool = Field(..., description="Người dùng đồng ý lưu dữ liệu cá nhân (bắt buộc true)")
    display_name: Optional[str] = Field(None, max_length=60)
    interests: list[str] = Field(default_factory=list, description="id trong /api/interests")
    share_interests_with_partner: bool = Field(False, description="BR-AI-12: cho AI dùng sở thích khi người đi cùng hỏi")
    plan: str = Field("free", description=f"gói AI: {', '.join(cfg.AI_PLANS)}")
    answers: Optional[dict[str, int]] = Field(None, description="bảng hỏi tính cách (tùy chọn), xem /api/questions")
    share_personality_with_partner: bool = False


class AskIn(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, examples=["tối thứ 7 đi cafe Quận 1 lúc 20h, tầm 150k/người"])
    user_a: Optional[str] = Field(None, description="mã hồ sơ người hỏi (mặc định: người đang đăng nhập)")
    user_b: Optional[str] = Field(None, description="mã hồ sơ người đi cùng")
    loc_a: Optional[list[float]] = Field(None, min_length=2, max_length=2, description="[vĩ độ, kinh độ]")
    loc_b: Optional[list[float]] = Field(None, min_length=2, max_length=2)
    budget: Optional[float] = Field(None, gt=0, description="ngân sách mỗi người (VNĐ)")
    use_llm: bool = True


class SuggestIn(AskIn):
    at_time: Optional[str] = Field(None, pattern=HHMM, description="giờ hẹn HH:MM")


class PlanIn(AskIn):
    start: Optional[str] = Field(None, pattern=HHMM, description="giờ bắt đầu HH:MM")
    walk: bool = Field(True, description="thêm chặng đi dạo (phố đi bộ, công viên, bờ sông) sau cà phê")


class ChooseIn(BaseModel):
    request_id: str
    place_id: str
    user_id: Optional[str] = None
    liked: bool = True
    chosen: bool = Field(True, description="false = bỏ chọn quán đã chọn")


# ======================= Endpoint công khai =======================

@app.get("/api/health")
def health():
    from llm import active_provider, ollama_up
    import pandas as pd
    n = len(pd.read_csv(cfg.RESTAURANTS_CLEAN, encoding="utf-8-sig", usecols=["restaurant_id"]))
    return {"ok": True, "restaurants": n, "ollama": ollama_up(), "llm_provider": active_provider(),
            "auth_required": cfg.AUTH_REQUIRED, "allow_register": cfg.AUTH_ALLOW_REGISTER, "ai_plans": cfg.AI_PLANS,
            "social": SOCIAL_ON and cfg.AUTH_REQUIRED}   # tab Cộng đồng cần đăng nhập để biết ai là ai


@app.get("/api/interests")
def interests():
    return [{"id": k, "label": v[0], "group": v[1]} for k, v in CATALOG.items()]


@app.get("/api/questions")
def questions():
    return {"scale": "1 = Hoàn toàn không đồng ý ... 5 = Hoàn toàn đồng ý",
            "items": [{"id": q["id"], "text": q["text"]} for q in QUESTIONS]}


@app.post("/api/auth/register")
def register(body: RegisterIn):
    if not cfg.AUTH_ALLOW_REGISTER:
        raise HTTPException(403, "Đăng ký đang tắt, hãy nhờ quản trị viên tạo tài khoản")
    try:
        accounts.create(body.user_id, body.password, "member")
    except ValueError as e:
        raise HTTPException(409 if "đã tồn tại" in str(e) else 422, str(e))
    return {"token": issue_token(body.user_id, "member"), "user_id": body.user_id, "role": "member"}


@app.post("/api/auth/login")
def login(body: LoginIn):
    try:
        role = accounts.verify(body.user_id, body.password)
    except PermissionError as e:
        raise HTTPException(429, str(e))
    if role is None:
        raise HTTPException(401, "Sai tên đăng nhập hoặc mật khẩu")
    return {"token": issue_token(body.user_id, role), "user_id": body.user_id, "role": role}


# ======================= Endpoint cần đăng nhập =======================

@app.get("/api/auth/me")
def me_info(me=Depends(current_user)):
    has_profile = bool(me["sub"]) and store.load(me["sub"]) is not None
    return {"user_id": me["sub"], "role": me["role"], "has_profile": has_profile}


@app.delete("/api/auth/me")
def delete_me(me=Depends(current_user)):
    """Quyền xóa dữ liệu: xóa vĩnh viễn tài khoản + hồ sơ của chính mình."""
    if me["sub"] is None:
        raise HTTPException(400, "Đăng nhập đang tắt")
    store.delete(me["sub"])
    accounts.delete(me["sub"])
    return {"deleted": me["sub"]}


@app.get("/api/profiles")
def list_profiles(me=Depends(current_user)):
    out = []
    for uid in store.list_users():
        rec = store.load(uid)
        out.append({"user_id": uid, "display_name": rec.get("display_name", uid)})
    return out


def _owner_view(rec):
    return {"user_id": rec["user_id"], "display_name": rec.get("display_name"), "plan": rec.get("plan", "free"),
            "interests": rec.get("interests", []),
            "share_interests_with_partner": rec.get("share_interests_with_partner", False),
            "has_personality": "p" in rec, "share_personality_with_partner": rec["consent"].get("share_with_partner", False)}


@app.get("/api/profiles/{user_id}")
def get_profile(user_id: str, me=Depends(current_user)):
    _check_owner(me, user_id)
    try:
        rec = store.load(user_id)
    except ValueError as e:
        raise HTTPException(422, str(e))
    if rec is None:
        raise HTTPException(404, f"Không có hồ sơ '{user_id}'")
    return _owner_view(rec)


@app.put("/api/profiles/{user_id}")
def put_profile(user_id: str, body: ProfileIn, me=Depends(current_user)):
    _check_owner(me, user_id)
    if me["role"] != "admin" and body.plan != (store.load(user_id) or {}).get("plan", "free"):
        raise HTTPException(403, "Chỉ quản trị viên được đổi gói AI")
    try:
        rec = store.save(user_id, answers=body.answers, consent=body.consent,
                         share_with_partner=body.share_personality_with_partner, interests=body.interests,
                         share_interests=body.share_interests_with_partner, display_name=body.display_name, plan=body.plan)
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(422, str(e))
    return _owner_view(rec)


@app.delete("/api/profiles/{user_id}")
def delete_profile(user_id: str, me=Depends(current_user)):
    _check_owner(me, user_id)
    try:
        if not store.delete(user_id):
            raise HTTPException(404, f"Không có hồ sơ '{user_id}'")
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"deleted": user_id}


@app.post("/api/suggest")
def api_suggest(body: SuggestIn, me=Depends(current_user), _=Depends(fresh_data)):
    user_a = _asker(me, body.user_a)
    if user_a:
        res = suggest(body.query, user_a, body.user_b, _loc(body.loc_a), _loc(body.loc_b), body.budget,
                      body.at_time, body.use_llm, store=store, log=log, unlimited=me["role"] == "admin")
    else:  # chỉ khi tắt đăng nhập: chế độ khách, không hồ sơ, không tính lượt, không ghi nhật ký
        from recommend import recommend
        res = {"status": "success", **recommend(body.query, Person("A", _loc(body.loc_a), body.budget),
                                                Person("B", _loc(body.loc_b), body.budget),
                                                use_llm=body.use_llm, at_time=body.at_time)}
        if not res["items"]:
            res["status"] = "no_result"
    place_media.attach(res.get("items") or [])
    return jsonable(res)


@app.post("/api/plan")
def api_plan(body: PlanIn, me=Depends(current_user), _=Depends(fresh_data)):
    user_a = _asker(me, body.user_a)
    if user_a:
        res = plan(body.query, user_a, body.user_b, _loc(body.loc_a), _loc(body.loc_b), body.budget,
                   body.start, body.use_llm, store=store, log=log, unlimited=me["role"] == "admin", walk=body.walk)
    else:
        from planner import make_plan
        p = make_plan(Person("A", _loc(body.loc_a), body.budget), Person("B", _loc(body.loc_b), body.budget),
                      query=body.query, start=body.start, budget=body.budget, use_llm=body.use_llm, walk=body.walk)
        res = {"status": "success" if p.get("stops") else "no_result", **p}
    place_media.attach(res.get("stops") or [])
    return jsonable(res)


@app.post("/api/choose")
def api_choose(body: ChooseIn, me=Depends(current_user)):
    user_id = _asker(me, body.user_id)
    ok = user_id and (choose_place(body.request_id, body.place_id, user_id, body.liked, store=store, log=log) if body.chosen
                      else unchoose_place(body.request_id, body.place_id, user_id, store=store, log=log))
    if not ok:
        raise HTTPException(404, "Không tìm thấy gợi ý này của bạn (request_id / place_id)")
    return {"ok": True, "chosen": body.chosen}


@app.get("/api/metrics")
def api_metrics(me=Depends(require_admin)):
    return jsonable(metrics(log))


# ======================= Phân quyền (chỉ quản trị viên) =======================
class AccountPatch(BaseModel):
    role: Optional[Literal["admin", "member"]] = None
    plan: Optional[str] = Field(None, description=f"gói AI: {', '.join(cfg.AI_PLANS)}")


class PasswordIn(BaseModel):
    password: str = Field(..., min_length=cfg.AUTH_MIN_PASSWORD, max_length=128)


def _target(user_id):
    role = accounts.role(user_id)
    if role is None:
        raise HTTPException(404, f"Không có tài khoản '{user_id}'")
    return role


def _keep_one_admin(user_id, role):
    """Không cho hạ quyền / xóa quản trị viên cuối cùng (sẽ không còn ai vào được trang này)."""
    if role == "admin" and sum(r == "admin" for r in accounts.list().values()) <= 1:
        raise HTTPException(400, "Phải còn ít nhất một quản trị viên")


@app.get("/api/admin/accounts")
def admin_accounts(me=Depends(require_admin)):
    out = []
    for uid, acc in accounts.details().items():
        prof = store.load(uid)
        plan_id = (prof or {}).get("plan", "free")
        used, limit = quota(uid, plan_id, log)
        out.append({"user_id": uid, "role": acc["role"], "created_at": acc["created_at"], "is_me": uid == me["sub"],
                    "has_profile": prof is not None, "display_name": (prof or {}).get("display_name"),
                    "plan": plan_id, "used_today": used, "limit": None if acc["role"] == "admin" else limit})
    return {"accounts": out, "plans": cfg.AI_PLANS}


@app.patch("/api/admin/accounts/{user_id}")
def admin_update(user_id: str, body: AccountPatch, me=Depends(require_admin)):
    role = _target(user_id)
    if body.role and body.role != role:
        if role == "admin":
            _keep_one_admin(user_id, role)
        accounts.set_role(user_id, body.role)
    if body.plan is not None:
        if body.plan not in cfg.AI_PLANS:
            raise HTTPException(422, f"Gói không hợp lệ (chọn: {', '.join(cfg.AI_PLANS)})")
        rec = store.load(user_id)
        if rec is None:
            raise HTTPException(409, "Người này chưa có hồ sơ sở thích nên chưa có gói AI để đổi")
        rec["plan"] = body.plan
        store.write(rec)
    return {"user_id": user_id, "role": accounts.role(user_id), "plan": (store.load(user_id) or {}).get("plan")}


@app.post("/api/admin/accounts/{user_id}/password")
def admin_password(user_id: str, body: PasswordIn, me=Depends(require_admin)):
    _target(user_id)
    accounts.set_password(user_id, body.password)   # đồng thời gỡ khóa tạm do gõ sai mật khẩu
    return {"ok": True}


@app.delete("/api/admin/accounts/{user_id}")
def admin_delete(user_id: str, me=Depends(require_admin)):
    role = _target(user_id)
    if user_id == me["sub"]:
        raise HTTPException(400, "Không tự xóa ở đây. Dùng 'Xóa tài khoản' trong Hồ sơ của tôi.")
    _keep_one_admin(user_id, role)
    store.delete(user_id)
    accounts.delete(user_id)
    if SOCIAL_ON:   # xóa luôn hồ sơ Cộng đồng (bài viết, kết nối, ảnh) của người này
        from lovespot import media as social_media_files
        from lovespot.db import session as social_session
        with social_session() as con:
            imgs = [r["images"] for r in con.execute("SELECT p.images FROM posts p JOIN users u ON u.id = p.author_id WHERE u.ext_id=?", (user_id,))]
            con.execute("DELETE FROM users WHERE ext_id=?", (user_id,))
        social_media_files.delete_files(imgs)
    return {"deleted": user_id}


app.include_router(place_media.public, dependencies=[Depends(current_user)])
app.include_router(place_media.admin, dependencies=[Depends(require_admin)])
app.include_router(place_media.files)


# ======================= Giao diện web =======================

@app.get("/", include_in_schema=False)
def index():
    return FileResponse(WEB_DIR / "index.html")


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


# ======================= Tab "Cộng đồng": mạng xã hội Lovespot (thư mục social/) =======================
# Chạy chung một server, dùng chung đăng nhập: token Couple Assistant được chấp nhận ở /social/api/*.
# Thiếu thư mục social/ thì bỏ qua, web chính vẫn chạy bình thường.
SOCIAL_DIR = cfg.BASE / "social"
SOCIAL_ON = (SOCIAL_DIR / "lovespot").is_dir()
if SOCIAL_ON:
    sys.path.insert(0, str(SOCIAL_DIR))
    from lovespot import security as social_security  # noqa: E402
    from lovespot.routes_people import router as social_people  # noqa: E402
    from lovespot.routes_posts import router as social_posts  # noqa: E402
    from lovespot.media import router as social_media  # noqa: E402

    def _social_identity(token):
        """Token Couple Assistant -> (mã tài khoản, tên hiển thị). Ném lỗi nếu token sai / tài khoản đã xóa."""
        sub = decode_token(token)["sub"]
        if accounts.role(sub) is None:
            raise PermissionError("tài khoản đã bị xóa")
        prof = store.load(sub) or {}
        return sub, prof.get("display_name") or sub

    social_security.EXTERNAL_AUTH = _social_identity   # CSDL Lovespot tự tạo ở request đầu tiên
    place_media.COMMUNITY = place_media.social_photos
    app.include_router(social_people, prefix="/social")
    app.include_router(social_posts, prefix="/social")
    app.include_router(social_media, prefix="/social")
    app.mount("/social/static", StaticFiles(directory=SOCIAL_DIR / "web"), name="social_static")

    @app.get("/social/", include_in_schema=False)
    def social_index():
        return FileResponse(SOCIAL_DIR / "web" / "index.html")


def warm_up():
    """Nạp model embedding sẵn ở nền để request đầu tiên không phải chờ."""
    def _load():
        from semantic import search
        search("khởi động", k=1, evidence=0)
    threading.Thread(target=_load, daemon=True).start()


if __name__ == "__main__":
    import uvicorn
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Chạy server web Couple Assistant")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    a = ap.parse_args()
    print(f"Giao diện:   http://{a.host}:{a.port}\nTài liệu API: http://{a.host}:{a.port}/docs"
          f"\nĐăng nhập: {'BẬT' if cfg.AUTH_REQUIRED else 'TẮT (chỉ dùng trên máy này)'}\n(Ctrl+C để dừng)")
    uvicorn.run(app, host=a.host, port=a.port, log_level="warning")
