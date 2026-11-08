"""Giai đoạn 5: bảng hỏi tính cách (BFI-10 + 4 câu sở thích hẹn hò), hồ sơ p, tính chất quán q,
personality_fit = 1 - Σ w_k·|p_k - q_k|, điều chỉnh nhẹ trọng số TOPSIS, lưu trữ có xin phép.

Chỉ là TÍN HIỆU ĐIỀU CHỈNH (một tiêu chí TOPSIS), không dùng để loại quán; người dùng có thể bỏ qua.
Bản dịch BFI-10 dưới đây là bản dịch làm việc, CHƯA được chuẩn hóa/kiểm định cho người Việt.
"""
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config as cfg

# ======================= Bảng hỏi =======================
# Thang Likert 1-5: 1 = Hoàn toàn không đồng ý ... 5 = Hoàn toàn đồng ý
LIKERT = ["Hoàn toàn không đồng ý", "Không đồng ý", "Trung lập", "Đồng ý", "Hoàn toàn đồng ý"]
INTRO = "Tôi thấy mình là người..."
QUESTIONS = [
    # BFI-10 (Rammstedt & John, 2007): E hướng ngoại, A dễ chịu, C tận tâm, N bất ổn cảm xúc, O cởi mở
    {"id": "b1", "text": "dè dặt, kín đáo", "trait": "E", "reverse": True},
    {"id": "b2", "text": "nhìn chung dễ tin người", "trait": "A", "reverse": False},
    {"id": "b3", "text": "hay lười biếng", "trait": "C", "reverse": True},
    {"id": "b4", "text": "thoải mái, xử lý căng thẳng tốt", "trait": "N", "reverse": True},
    {"id": "b5", "text": "ít quan tâm đến nghệ thuật", "trait": "O", "reverse": True},
    {"id": "b6", "text": "hướng ngoại, hòa đồng", "trait": "E", "reverse": False},
    {"id": "b7", "text": "hay bắt lỗi người khác", "trait": "A", "reverse": True},
    {"id": "b8", "text": "làm việc chu đáo, kỹ lưỡng", "trait": "C", "reverse": False},
    {"id": "b9", "text": "dễ lo lắng, bồn chồn", "trait": "N", "reverse": False},
    {"id": "b10", "text": "giàu trí tưởng tượng", "trait": "O", "reverse": False},
    # Sở thích khi đi hẹn hò
    {"id": "p1", "text": "Khi hẹn hò, tôi thích chỗ sôi động, nhộn nhịp hơn là yên tĩnh", "trait": "lively_pref"},
    {"id": "p2", "text": "Tôi thích thử món lạ, quán mới hơn là món quen", "trait": "novelty_pref"},
    {"id": "p3", "text": "Tôi thích lên kế hoạch trước (chọn quán kỹ, đặt bàn) hơn là tùy hứng", "trait": "plan_pref"},
    {"id": "p4", "text": "Tôi thích quán đẹp, nhiều góc để chụp ảnh", "trait": "photo_pref"},
]
TRAITS = ["E", "A", "C", "N", "O"]
DIMENSIONS = ["lively", "novelty", "privacy", "aesthetic", "reliable"]
# Nhãn hai chiều (q thấp, q cao) để giải thích đúng hướng
DIM_LABEL = {"lively": ("yên tĩnh", "sôi động"), "novelty": ("món quen thuộc", "món lạ"),
             "privacy": ("thoáng, đông vui", "riêng tư"), "aesthetic": ("bình dị", "đẹp, nhiều góc chụp ảnh"),
             "reliable": ("quán mới, ít review", "được nhiều người kiểm chứng")}


def _scale(x):
    """Likert 1-5 -> 0-1."""
    return (float(x) - 1) / 4


def score_answers(answers):
    """answers: {question_id: 1..5}. Câu bỏ trống -> trung lập (3).
    Trả về (big5 {E,A,C,N,O} 0-1, prefs {..} 0-1, n_answered)."""
    big5, prefs, n = {t: [] for t in TRAITS}, {}, 0
    for q in QUESTIONS:
        v = answers.get(q["id"])
        if v is not None:
            if int(v) not in range(1, 6):
                raise ValueError(f"Câu {q['id']}: cần số 1-5, nhận {v!r}")
            n += 1
        x = _scale(v if v is not None else 3)
        if q["trait"] in TRAITS:
            big5[q["trait"]].append(1 - x if q["reverse"] else x)
        else:
            prefs[q["trait"]] = x
    return {t: float(np.mean(v)) for t, v in big5.items()}, prefs, n


def build_profile(answers):
    """Hồ sơ p ∈ [0,1] cho 5 chiều: kết hợp câu sở thích trực tiếp (nặng hơn) + nét Big Five liên quan."""
    b, pr, n = score_answers(answers)
    p = {
        "lively": 0.6 * pr["lively_pref"] + 0.4 * b["E"],
        "novelty": 0.6 * pr["novelty_pref"] + 0.4 * b["O"],
        "privacy": 0.6 * (1 - b["E"]) + 0.4 * (1 - pr["lively_pref"]),
        "aesthetic": 0.7 * pr["photo_pref"] + 0.3 * b["O"],
        "reliable": 0.6 * pr["plan_pref"] + 0.4 * b["C"],
    }
    return {"p": {k: round(v, 4) for k, v in p.items()}, "big5": b, "prefs": pr, "n_answered": n}


# ======================= Tính chất quán q =======================

def _sigmoid(z):
    return 1 / (1 + np.exp(-np.asarray(z, float)))


def restaurant_traits(restaurants, scores):
    """q ∈ [0,1] cho mỗi quán, cùng 5 chiều với hồ sơ người. Dùng z-score khía cạnh (GĐ3) qua sigmoid
    để quán không được nhắc tới nằm gần 0.5 (trung tính) thay vì bị đẩy ra hai đầu."""
    df = restaurants[["restaurant_id", "cuisines", "rating_n"]].merge(scores, on="restaurant_id", how="left")
    q = pd.DataFrame({"restaurant_id": df["restaurant_id"]})
    q["lively"] = _sigmoid(-df["quiet_z"].fillna(0))                       # ồn ào -> sôi động
    q["privacy"] = _sigmoid(df["privacy_z"].fillna(0))
    q["aesthetic"] = _sigmoid((df["view_z"].fillna(0) + df["ambience_z"].fillna(0)) / 2)
    # Độ lạ: món chính càng hiếm trong dữ liệu càng "lạ" (Món Việt phổ biến nhất -> thấp)
    primary = df["cuisines"].fillna("").str.split(";").str[0].str.strip()
    freq = primary[primary != ""].value_counts(normalize=True)
    q["novelty"] = np.where(primary == "", 0.5, 1 - primary.map(freq).fillna(0) / freq.max())
    q["novelty"] = 0.2 + 0.8 * q["novelty"]                               # quán món Việt vẫn ≥ 0.2
    # Độ "chắc ăn": nhiều review (phân vị)
    q["reliable"] = df["rating_n"].rank(pct=True).fillna(0.5)
    return q[["restaurant_id"] + DIMENSIONS].round(4)


# ======================= Độ phù hợp + trọng số =======================

def dimension_weights(p):
    """Chiều nào người dùng có sở thích rõ (xa 0.5) thì quan trọng hơn."""
    w = {k: cfg.PERSONALITY_WEIGHT_FLOOR + abs(v - 0.5) for k, v in p.items()}
    s = sum(w.values())
    return {k: v / s for k, v in w.items()}


def personality_fit(profile, traits):
    """personality_fit = 1 - Σ w_k·|p_k - q_k| (0-1). Trả về Series theo restaurant_id."""
    p = profile["p"]
    w = dimension_weights(p)
    dist = sum(w[k] * (traits[k] - p[k]).abs() for k in DIMENSIONS)
    return pd.Series((1 - dist).to_numpy(), index=traits["restaurant_id"], name="personality_fit")


def explain_fit(profile, traits_row, top=2):
    """Chiều khớp nhất của quán với một người (để giải thích, không lộ câu trả lời gốc)."""
    p, w = profile["p"], dimension_weights(profile["p"])
    gaps = sorted(DIMENSIONS, key=lambda k: w[k] * abs(traits_row[k] - p[k]))
    return [DIM_LABEL[k][int(traits_row[k] >= 0.5)] for k in gaps[:top]]


def adjust_weights(profile, base=None):
    """Hồ sơ chỉ chỉnh NHẸ trọng số TOPSIS (tối đa ±NUDGE), heuristic có thể giải thích:
    - thích lên kế hoạch / tận tâm -> coi trọng couple_score (quán đã được kiểm chứng)
    - tùy hứng -> coi trọng personality_fit hơn
    - dễ lo lắng -> coi trọng khoảng cách (đi lại ít phiền)
    - thích chụp ảnh -> coi trọng image_score (khi có dữ liệu ảnh)"""
    base = dict(base or cfg.DEFAULT_WEIGHTS)
    d, p, b = cfg.PERSONALITY_WEIGHT_NUDGE, profile["p"], profile["big5"]
    base["couple_score"] += d * (2 * p["reliable"] - 1)
    base["personality_fit"] += d * (1 - p["reliable"])
    base["distance_km"] += d * max(0.0, 2 * b["N"] - 1)
    base["image_score"] += d * max(0.0, 2 * profile["prefs"]["photo_pref"] - 1)
    return {k: max(v, 0.0) for k, v in base.items()}


# ======================= Lưu trữ có xin phép =======================

class ProfileStore:
    """Hồ sơ cá nhân: mỗi người một file data/profiles/<user_id>.json, gồm
    tên hiển thị, gói AI, sở thích (+ cờ chia sẻ với người kia) và tính cách (tùy chọn).
    - Chỉ lưu khi consent=True (người dùng đồng ý rõ ràng); delete() xóa vĩnh viễn.
    - share_interests_with_partner (mặc định TẮT, BR-AI-12): AI chỉ dùng sở thích của người này
      cho người kia khi bật. share_with_partner: cho người kia xem hồ sơ tính cách.
    - partner_view(): người kia chỉ thấy phần được phép."""

    def __init__(self, root=cfg.PROFILE_DIR):
        self.root = root

    def _path(self, user_id):
        if not str(user_id).replace("_", "").replace("-", "").isalnum():
            raise ValueError("user_id không hợp lệ")
        return self.root / f"{user_id}.json"

    def save(self, user_id, answers=None, consent=False, share_with_partner=False,
             interests=None, share_interests=False, display_name=None, plan="free"):
        """Tạo / ghi đè hồ sơ. answers (bảng hỏi tính cách) và interests đều tùy chọn."""
        from interests import validate_interests
        if not consent:
            raise PermissionError("Chưa có sự đồng ý lưu dữ liệu cá nhân -> không lưu.")
        if plan not in cfg.AI_PLANS:
            raise ValueError(f"Gói không hợp lệ: {plan} (có: {list(cfg.AI_PLANS)})")
        self.root.mkdir(parents=True, exist_ok=True)
        old = self.load(user_id) or {}
        rec = {"user_id": user_id, "display_name": display_name or old.get("display_name") or user_id,
               "plan": plan, "interests": validate_interests(interests or []),
               "share_interests_with_partner": bool(share_interests),
               "consent": {"personal_data": True, "share_with_partner": bool(share_with_partner),
                           "given_at": datetime.now(timezone.utc).isoformat(timespec="seconds")},
               "feedback": old.get("feedback", [])}
        if answers:
            rec.update({"answers": answers, **build_profile(answers)})
        self._path(user_id).write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        return rec

    def write(self, rec):
        """Ghi lại hồ sơ đã có (vd sau khi phản hồi cập nhật p)."""
        self._path(rec["user_id"]).write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")

    def list_users(self):
        return sorted(p.stem for p in self.root.glob("*.json")) if self.root.exists() else []

    def load(self, user_id):
        f = self._path(user_id)
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None

    def delete(self, user_id):
        f = self._path(user_id)
        existed = f.exists()
        f.unlink(missing_ok=True)
        return existed

    def partner_view(self, user_id):
        rec = self.load(user_id)
        if rec is None:
            return None
        view = {"user_id": user_id, "display_name": rec.get("display_name", user_id), "has_profile": True}
        if rec.get("share_interests_with_partner"):
            view["interests"] = rec.get("interests", [])
        if rec["consent"].get("share_with_partner") and "p" in rec:
            view["p"] = rec["p"]
        return view  # mặc định không lộ câu trả lời / Big Five / sở thích


def ask_in_terminal():
    """Hỏi trực tiếp trên terminal (python stage5_personality.py --ask)."""
    print("Bảng hỏi 14 câu (1-5). Bỏ trống = trung lập.")
    print("  " + " | ".join(f"{i + 1}={t}" for i, t in enumerate(LIKERT)))
    ans = {}
    for i, q in enumerate(QUESTIONS, 1):
        prefix = INTRO + " " if q["id"].startswith("b") else ""
        while True:
            s = input(f"{i:2d}. {prefix}{q['text']}: ").strip()
            if s == "":
                break
            if s in {"1", "2", "3", "4", "5"}:
                ans[q["id"]] = int(s)
                break
            print("   Nhập số 1-5 hoặc Enter để bỏ qua.")
    return ans
