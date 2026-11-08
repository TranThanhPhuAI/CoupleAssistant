"""Giai đoạn 7: nhập quán / review mới mà KHÔNG làm hỏng hệ thống đang chạy.

    staging (kiểm tra schema, từ chối dòng lỗi) -> upsert theo restaurant_id (không nhân đôi)
    -> rating (giữ tham số Bayes cũ) -> ghi file atomic (có backup)
    -> embedding CHỈ cho doc mới -> tráo index -> ABSA cho review mới -> chấm điểm theo tham chiếu cũ

Chạy:
    python ingest.py data/staging/<batch>              nhập một đợt
    python ingest.py data/staging/<batch> --dry-run    chỉ kiểm tra, không ghi
    python ingest.py --recompute                       (theo lịch) tính lại tham số Bayes + tham chiếu điểm cho toàn bộ
Tùy chọn: --data-root DIR (chạy trên bản sao dữ liệu), --max-reject 0.3, --llm (LLM gán ABSA cho review mới có từ khóa)

File staging:
    restaurants.csv  bắt buộc: name, address
                     tùy chọn: category, district, latitude, longitude, price_min, price_max, price_text,
                               opening_hours, rating, review_count, website, source, source_url
    reviews.csv      bắt buộc: review_text + (restaurant_id hoặc restaurant_name + restaurant_address)
                     tùy chọn: rating, rating_scale (5 hoặc 10, mặc định 10), review_date, author, source, source_url
"""
import json
import os
import pickle
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import config as cfg
from common import (fold, infer_type_from_name, make_restaurant_id, make_review_id, nfc, parse_category,
                    parse_city, parse_hours, parse_old_district_ward, parse_price_text)
from ratings import compute_rating_stats

REST_REQUIRED = ["name", "address"]
REST_OPTIONAL = ["category", "district", "latitude", "longitude", "price_min", "price_max", "price_text",
                 "opening_hours", "rating", "review_count", "website", "source", "source_url"]
REV_OPTIONAL = ["rating", "rating_scale", "review_date", "author", "source", "source_url"]
OTHER_CITIES = r"\b(?:ha noi|da nang|hai phong|can tho|nha trang|da lat|hue|vung tau|bien hoa|binh duong)\b"


@dataclass
class Paths:
    """Mọi đường dẫn dữ liệu tính từ một gốc -> chạy được trên bản sao (sandbox) để thử."""
    root: Path

    @property
    def clean(self): return self.root / "clean"
    @property
    def restaurants(self): return self.clean / "restaurants_clean.csv"
    @property
    def reviews(self): return self.clean / "reviews_clean.csv"
    @property
    def bayes(self): return self.clean / "bayes_params.json"
    @property
    def scores(self): return self.clean / "restaurant_scores.csv"
    @property
    def traits(self): return self.clean / "restaurant_traits.csv"
    @property
    def index(self): return self.root / "index"
    @property
    def absa(self): return self.root / "absa"
    @property
    def aspects(self): return self.absa / "review_aspects.csv"
    @property
    def probe(self): return self.absa / "aspect_probe.pkl"
    @property
    def score_ref(self): return self.absa / "score_reference.json"
    @property
    def log_dir(self): return self.root / "ingest_log"


def say(*a):
    print(*a, flush=True)


# ======================= 1. Staging: kiểm tra schema =======================

def _num(s):
    return pd.to_numeric(s, errors="coerce")


def validate_restaurants(df):
    """Trả về (bảng hợp lệ đã chuẩn hóa, bảng bị từ chối có cột reason, cảnh báo)."""
    warns = []
    missing = [c for c in REST_REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"restaurants.csv thiếu cột bắt buộc: {missing}")
    unknown = set(df.columns) - set(REST_REQUIRED + REST_OPTIONAL)
    if unknown:
        warns.append(f"bỏ qua cột lạ: {sorted(unknown)}")
    df = df.reindex(columns=REST_REQUIRED + REST_OPTIONAL).copy()
    for c in ["name", "address", "category", "district", "price_text", "opening_hours", "website", "source", "source_url"]:
        df[c] = df[c].map(nfc)
    reason = pd.Series("", index=df.index)
    reason[df["name"].isna()] += "thiếu tên; "
    reason[df["address"].isna()] += "thiếu địa chỉ; "
    other = df["address"].fillna("").map(fold).str.contains(OTHER_CITIES, regex=True)
    city = df["address"].map(parse_city)
    other |= city.notna() & ~city.fillna("").str.contains("Hồ Chí Minh|HCM", regex=True)
    reason[other] += "ngoài TP.HCM; "

    for c in ["latitude", "longitude", "price_min", "price_max", "rating", "review_count"]:
        df[c] = _num(df[c])
    lat0, lat1, lon0, lon1 = cfg.HCM_BBOX
    bad_xy = df["latitude"].notna() & ~(df["latitude"].between(lat0, lat1) & df["longitude"].between(lon0, lon1))
    if bad_xy.any():
        warns.append(f"{bad_xy.sum()} dòng tọa độ ngoài TP.HCM -> bỏ tọa độ (giữ quán, khoảng cách = trung tính)")
        df.loc[bad_xy, ["latitude", "longitude"]] = np.nan
    bad_r = df["rating"].notna() & ~df["rating"].between(0, 10)
    df.loc[bad_r, "rating"] = np.nan
    if bad_r.any():
        warns.append(f"{bad_r.sum()} dòng rating ngoài 0-10 -> bỏ rating")

    ok = df[reason == ""].copy()
    rej = df[reason != ""].assign(reason=reason[reason != ""].str.rstrip("; "))
    ok["restaurant_id"] = [make_restaurant_id(n, a) for n, a in zip(ok["name"], ok["address"])]
    dup = ok["restaurant_id"].duplicated(keep="last")
    if dup.any():
        warns.append(f"{dup.sum()} dòng trùng quán trong cùng đợt -> giữ dòng cuối")
        ok = ok[~dup]
    return ok, rej, warns


def validate_reviews(df, known_ids):
    warns = []
    if "review_text" not in df.columns:
        raise ValueError("reviews.csv thiếu cột review_text")
    df = df.copy()
    has_name = {"restaurant_name", "restaurant_address"} <= set(df.columns)
    if "restaurant_id" not in df.columns and not has_name:
        raise ValueError("reviews.csv cần restaurant_id hoặc restaurant_name + restaurant_address")
    if "restaurant_id" not in df.columns:
        df["restaurant_id"] = np.nan
    if has_name:  # từng dòng: thiếu restaurant_id -> suy từ tên + địa chỉ (cùng hàm băm với bảng quán)
        derived = pd.Series([make_restaurant_id(nfc(n), nfc(a)) if pd.notna(n) and pd.notna(a) else np.nan
                             for n, a in zip(df["restaurant_name"], df["restaurant_address"])], index=df.index)
        df["restaurant_id"] = df["restaurant_id"].fillna(derived)
    df = df.reindex(columns=["restaurant_id", "review_text"] + REV_OPTIONAL)
    df["review_text"] = df["review_text"].map(nfc)
    df["author"] = df["author"].map(nfc)
    reason = pd.Series("", index=df.index)
    reason[df["review_text"].fillna("").str.len() < 5] += "review rỗng/quá ngắn; "
    reason[~df["restaurant_id"].isin(known_ids)] += "không tìm thấy quán; "

    scale = _num(df["rating_scale"]).fillna(10)
    df["rating"] = _num(df["rating"]) * np.where(scale == 5, 2.0, 1.0)  # thang 5 -> thang 10
    bad = df["rating"].notna() & ~df["rating"].between(1, 10)
    df.loc[bad, "rating"] = np.nan
    if bad.any():
        warns.append(f"{bad.sum()} review rating ngoài 1-10 -> bỏ rating")
    df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce")
    future = df["review_date"] > pd.Timestamp.now()
    df.loc[future, "review_date"] = pd.NaT
    ok = df[reason == ""].copy()
    rej = df[reason != ""].assign(reason=reason[reason != ""].str.rstrip("; "))
    return ok, rej, warns


# ======================= 2. Upsert =======================

def enrich_restaurants(new):
    """Trường dẫn xuất cho dòng staging (cùng hàm chuẩn hóa với giai đoạn 1)."""
    out = new.copy()
    dw = out["address"].map(parse_old_district_ward)
    parsed_d = pd.Series([d for d, _ in dw], index=out.index)
    direct = out["address"].str.extract(r"(Quận\s+[\wÀ-ỹ]+(?:\s+[\wÀ-ỹ]+)?|Huyện\s+[\wÀ-ỹ]+(?:\s+[\wÀ-ỹ]+)?|TP\.\s*Thủ Đức)")[0]
    out["district"] = out["district"].fillna(parsed_d).fillna(direct.str.replace(r"\s+", " ", regex=True))
    out["ward"] = [w for _, w in dw]
    pm = out["price_text"].map(lambda t: parse_price_text(t, cfg.PRICE_MIN_VALID, cfg.PRICE_MAX_VALID))
    out["price_min"] = out["price_min"].fillna(pd.Series([a for a, _ in pm], index=out.index))
    out["price_max"] = out["price_max"].fillna(pd.Series([b for _, b in pm], index=out.index))
    out["price_source"] = np.where(out["price_min"].notna(), "ingest", None)
    out["price_mid"] = (out["price_min"] + out["price_max"]) / 2
    out["price_suspect"] = out["price_max"] > cfg.PRICE_SUSPECT_MAX
    out["opening_hours_raw"] = out["opening_hours"]
    out["opening_hours"] = out["opening_hours"].map(parse_hours)
    cats = out["category"].map(parse_category)
    types = [t if t else [infer_type_from_name(n) if isinstance(infer_type_from_name(n), str) else "Quán ăn"]
             for (t, _, _), n in zip(cats, out["name"])]
    out["place_types"] = ["; ".join(t) for t in types]
    out["place_type"] = [t[0] for t in types]
    out["cuisines"] = ["; ".join(c) for _, c, _ in cats]
    out["category_raw"] = out["category"]
    out["category_source"] = np.where(out["category"].notna(), "source", "inferred_name")
    out["curated_tag"] = [g for _, _, g in cats]
    out["address_new"] = out["address"]
    out["city"] = "TP. HCM"
    out["has_coords"] = out["latitude"].notna() & out["longitude"].notna()
    return out.rename(columns={"rating": "source_rating", "review_count": "source_review_count"})


def upsert_restaurants(R, staged, today):
    """Quán mới -> thêm (first_seen = hôm nay); quán đã có -> chỉ cập nhật trường staging có giá trị."""
    staged = enrich_restaurants(staged).set_index("restaurant_id")
    R = R.set_index("restaurant_id")
    is_new = ~staged.index.isin(R.index)
    upd = staged[~is_new]
    changed = 0
    for col in upd.columns:
        if col not in R.columns:
            continue
        vals = upd[col].dropna()
        if col in {"place_types", "place_type", "category_source", "address_new", "city", "has_coords",
                   "price_source", "price_suspect", "price_mid"}:
            continue  # trường dẫn xuất: chỉ đặt cho quán mới
        vals = vals[vals.astype(str) != ""]
        diff = vals[R.loc[vals.index, col].astype(str) != vals.astype(str)]
        if len(diff):
            R.loc[diff.index, col] = diff
            changed += len(diff)
    new = staged[is_new].copy()
    new["first_seen"] = today
    new["legacy_id"] = np.nan
    new["source"] = new["source"].fillna("ingest")  # mặc định chỉ cho quán mới, không ghi đè nguồn của quán cũ
    R = pd.concat([R, new.reindex(columns=R.columns)])
    R.loc[upd.index, "has_coords"] = R.loc[upd.index, "latitude"].notna() & R.loc[upd.index, "longitude"].notna()
    return R.reset_index(), int(is_new.sum()), len(upd), changed


def upsert_reviews(V, staged):
    staged = staged.copy()
    staged["review_id"] = [make_review_id(r, a, d, t) for r, a, d, t in
                           zip(staged["restaurant_id"], staged["author"],
                               staged["review_date"].dt.strftime("%Y-%m-%d").where(staged["review_date"].notna(), "NaT"),
                               staged["review_text"])]
    key_old = set(zip(V["restaurant_id"], V["review_text"].map(fold)))
    dup = staged["review_id"].isin(V["review_id"]) | pd.Series(
        [(r, fold(t)) in key_old for r, t in zip(staged["restaurant_id"], staged["review_text"])], index=staged.index)
    dup |= staged.assign(_k=staged["review_text"].map(fold)).duplicated(["restaurant_id", "_k"])  # trùng trong đợt
    new = staged[~dup].copy()
    new["text_len"] = new["review_text"].str.len()
    new["legacy_review_id"] = np.nan
    new["language"] = "vi"
    new["source_file"] = "ingest"
    new["review_date"] = new["review_date"].dt.strftime("%Y-%m-%d")
    V = pd.concat([V, new.reindex(columns=V.columns)], ignore_index=True)
    return V, new, int(dup.sum())


# ======================= 3. Ghi file atomic =======================

def atomic_write_csv(df, path, backup_dir):
    if path.exists():
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup_dir / path.name)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False, encoding="utf-8-sig")
    os.replace(tmp, path)


# ======================= 4. ABSA cho review mới =======================

def absa_for_new(P, new_reviews, use_llm=False):
    """Bộ phân loại (đã huấn luyện ở GĐ3) dự đoán khía cạnh cho review mới, không huấn luyện lại.
    --llm: review có từ khóa hẹn hò được LLM gán trực tiếp (ghi đè)."""
    from vector_store import VectorStore
    if new_reviews.empty:
        return pd.DataFrame()
    meta, emb, _ = VectorStore(P.index).load()
    probe = pickle.load(open(P.probe, "rb"))
    m = meta[(meta["doc_type"] == "review") & meta["review_id"].isin(new_reviews["review_id"])]
    codes, ids = pd.factorize(m["review_id"])
    X = np.zeros((len(ids), emb.shape[1]), dtype=np.float32)
    np.add.at(X, codes, emb[m.index.to_numpy()])
    X /= np.linalg.norm(X, axis=1, keepdims=True)
    out = pd.DataFrame({"review_id": ids})
    out["restaurant_id"] = out["review_id"].map(new_reviews.set_index("review_id")["restaurant_id"])
    for a, clf in probe["probes"].items():
        Pr = clf.predict_proba(X)
        cls = list(clf.classes_)
        out[f"{a}_pos"] = Pr[:, cls.index("pos")] if "pos" in cls else 0.0
        out[f"{a}_neg"] = Pr[:, cls.index("neg")] if "neg" in cls else 0.0
    out["label_source"] = "probe"
    if use_llm:
        from absa import label_review
        from stage3_label import DATE_KEYWORDS
        text = new_reviews.set_index("review_id")["review_text"]
        for i, rv in enumerate(out["review_id"]):
            if re.search(DATE_KEYWORDS, fold(text[rv])):
                try:
                    lab = label_review(text[rv])
                    for a, v in lab.items():
                        out.loc[i, f"{a}_pos"], out.loc[i, f"{a}_neg"] = float(v == "pos"), float(v == "neg")
                    out.loc[i, "label_source"] = "llm"
                except Exception as e:
                    say(f"  LLM lỗi với {rv}: {e} -> giữ dự đoán của bộ phân loại")
    return out.round(4)


# ======================= Chạy một đợt =======================

def ingest(batch_dir, P, dry_run=False, max_reject=cfg.INGEST_MAX_REJECT_SHARE, use_llm=False):
    batch_dir = Path(batch_dir)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    today = date.today().isoformat()
    report = {"batch": str(batch_dir), "started": ts, "dry_run": dry_run}
    R = pd.read_csv(P.restaurants, encoding="utf-8-sig")
    V = pd.read_csv(P.reviews, encoding="utf-8-sig")
    say(f"Hiện có: {len(R)} quán, {len(V)} review")

    # ---- Staging ----
    rest_ok = rest_rej = pd.DataFrame()
    warns = []
    if (batch_dir / "restaurants.csv").exists():
        rest_ok, rest_rej, w = validate_restaurants(pd.read_csv(batch_dir / "restaurants.csv", encoding="utf-8-sig"))
        warns += w
    known = set(R["restaurant_id"]) | set(rest_ok.get("restaurant_id", []))
    rev_ok = rev_rej = pd.DataFrame()
    if (batch_dir / "reviews.csv").exists():
        rev_ok, rev_rej, w = validate_reviews(pd.read_csv(batch_dir / "reviews.csv", encoding="utf-8-sig"), known)
        warns += w
    n_in = len(rest_ok) + len(rest_rej) + len(rev_ok) + len(rev_rej)
    n_rej = len(rest_rej) + len(rev_rej)
    report.update(rest_ok=len(rest_ok), rest_rejected=len(rest_rej), rev_ok=len(rev_ok),
                  rev_rejected=len(rev_rej), warnings=warns)
    say(f"Staging: quán hợp lệ {len(rest_ok)}, từ chối {len(rest_rej)} | review hợp lệ {len(rev_ok)}, từ chối {len(rev_rej)}")
    for w in warns:
        say("  cảnh báo:", w)
    for _, r in pd.concat([rest_rej, rev_rej]).iterrows():
        label = r.get("name") if pd.notna(r.get("name")) else r.get("review_text")
        say(f"  từ chối: {str(label)[:40]!r} -> {r['reason']}")
    if n_rej:
        pd.concat([rest_rej, rev_rej]).to_csv(batch_dir / "rejected.csv", index=False, encoding="utf-8-sig")
    if n_in and n_rej / n_in > max_reject:
        say(f"HỦY ĐỢT: {n_rej}/{n_in} dòng lỗi > {max_reject:.0%}. Không ghi gì. Sửa file rồi chạy lại "
            f"(hoặc --max-reject).")
        report["status"] = "aborted"
        return report
    if dry_run:
        say("Dry-run: dừng ở đây, không ghi.")
        report["status"] = "dry_run"
        return report

    # ---- Upsert ----
    n_r0, n_v0 = len(R), len(V)
    if len(rest_ok):
        R, n_new, n_upd, n_changed = upsert_restaurants(R, rest_ok, today)
        say(f"Upsert quán: +{n_new} mới, {n_upd} đã có ({n_changed} trường được cập nhật)")
        report.update(rest_new=n_new, rest_in_batch_existing=n_upd, fields_changed=n_changed)
    new_rev = pd.DataFrame()
    if len(rev_ok):
        V, new_rev, n_dup = upsert_reviews(V, rev_ok)
        say(f"Upsert review: +{len(new_rev)} mới, {n_dup} trùng bị bỏ qua")
        report.update(rev_new=len(new_rev), rev_duplicates=n_dup)
    assert R["restaurant_id"].is_unique and V["review_id"].is_unique, "Upsert sinh trùng khóa!"
    if len(R) == n_r0 and len(V) == n_v0 and report.get("fields_changed", 0) == 0:
        say("Không có gì mới -> dừng (chạy lại cùng đợt là an toàn).")
        report["status"] = "no_change"
        return report

    # ---- Rating: giữ tham số Bayes cũ (C, m) -> quán cũ không bị xê dịch ----
    bp = json.loads(P.bayes.read_text(encoding="utf-8"))
    Vd = V.assign(review_date=pd.to_datetime(V["review_date"], errors="coerce"))
    R, _, _ = compute_rating_stats(R, Vd, C=bp["C"], m=bp["m"])
    R["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # ---- Ghi dữ liệu (atomic + backup) TRƯỚC index: index thiếu doc mới chỉ làm quán mới trung tính ----
    backup = P.root / "backup" / ts
    cols_R = pd.read_csv(P.restaurants, encoding="utf-8-sig", nrows=0).columns
    atomic_write_csv(R.reindex(columns=cols_R), P.restaurants, backup)
    atomic_write_csv(V, P.reviews, backup)
    say(f"Đã ghi dữ liệu: {len(R)} quán, {len(V)} review (backup: {backup.relative_to(P.root)})")

    # ---- Embedding: chỉ doc mới/đổi nội dung ----
    from semantic import build_docs, embed_docs
    from vector_store import VectorStore
    stats = VectorStore(P.index).build(build_docs(R, V), embed_docs, cfg.EMBED_MODEL, keep=cfg.INDEX_KEEP_VERSIONS)
    say(f"Index: {stats['n_embedded_new']} doc embed mới, {stats['n_reused']} dùng lại")
    report["index"] = stats

    # ---- ABSA + chấm điểm theo tham chiếu cũ ----
    from scoring import SCORE_COLS, score_restaurants
    A = pd.read_csv(P.aspects, encoding="utf-8-sig")
    A_new = absa_for_new(P, new_rev, use_llm=use_llm)
    if len(A_new):
        A = pd.concat([A[~A["review_id"].isin(A_new["review_id"])], A_new], ignore_index=True)
        atomic_write_csv(A, P.aspects, backup)
    ref = json.loads(P.score_ref.read_text(encoding="utf-8"))
    S, _ = score_restaurants(R, A, reference=ref)
    atomic_write_csv(S[SCORE_COLS].round(4), P.scores, backup)
    refresh_derived(P, R, S, backup)
    say(f"ABSA review mới: {len(A_new)} | chấm điểm lại {len(S)} quán theo tham chiếu cũ")

    report["status"] = "ok"
    P.log_dir.mkdir(parents=True, exist_ok=True)
    (P.log_dir / f"{ts}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return report


def refresh_derived(P, R, S, backup):
    """Dữ liệu suy ra từ điểm: tính chất quán (tính cách), nhãn AI (place_tags), ma trận sở thích."""
    from interests import build_matrix
    from personality import restaurant_traits
    from scoring import SCORE_COLS, derive_tags
    atomic_write_csv(restaurant_traits(R, S[SCORE_COLS]), P.traits, backup)
    atomic_write_csv(derive_tags(S), P.clean / cfg.PLACE_TAGS.name, backup)
    build_matrix(clean_dir=P.clean, index_dir=P.index)


def recompute(P):
    """Chạy theo lịch (vd hằng tuần): tính lại C của Bayes + prior/tham chiếu điểm trên TOÀN BỘ dữ liệu."""
    from scoring import SCORE_COLS, score_restaurants
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = P.root / "backup" / ts
    R = pd.read_csv(P.restaurants, encoding="utf-8-sig")
    V = pd.read_csv(P.reviews, encoding="utf-8-sig")
    Vd = V.assign(review_date=pd.to_datetime(V["review_date"], errors="coerce"))
    old = json.loads(P.bayes.read_text(encoding="utf-8"))
    R, C, _ = compute_rating_stats(R, Vd, C=None, m=old["m"])
    atomic_write_csv(R, P.restaurants, backup)
    bp = {**old, "C": C, "n_restaurants": len(R), "n_reviews": len(V),
          "computed_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    P.bayes.write_text(json.dumps(bp, indent=2), encoding="utf-8")
    A = pd.read_csv(P.aspects, encoding="utf-8-sig")
    S, ref = score_restaurants(R, A, reference=None)
    atomic_write_csv(S[SCORE_COLS].round(4), P.scores, backup)
    ref["computed_at"] = bp["computed_at"]
    P.score_ref.write_text(json.dumps(ref), encoding="utf-8")
    refresh_derived(P, R, S, backup)
    say(f"Tính lại: C {old['C']} -> {C:.4f}, {len(R)} quán, tham chiếu điểm mới")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    root = Path(args[args.index("--data-root") + 1]) if "--data-root" in args else cfg.BASE / "data"
    P = Paths(root)
    mr = float(args[args.index("--max-reject") + 1]) if "--max-reject" in args else cfg.INGEST_MAX_REJECT_SHARE
    if "--recompute" in args:
        recompute(P)
    elif "--tat-ca" in args:  # chạy theo lịch: nhập mọi đợt mới trong staging/, đánh dấu .done khi xong
        pending = sorted(d for d in (root / "staging").iterdir()
                         if d.is_dir() and not d.name.startswith("_") and not (d / ".done").exists()) \
            if (root / "staging").exists() else []
        say(f"Có {len(pending)} đợt mới trong staging/")
        for d in pending:
            say(f"\n=== Đợt {d.name} ===")
            rep = ingest(d, P, max_reject=mr, use_llm="--llm" in args)
            say("Kết quả:", rep["status"])
            if rep["status"] in {"ok", "no_change"}:  # đợt bị hủy giữ nguyên để sửa file rồi chạy lại
                (d / ".done").write_text(json.dumps(rep, ensure_ascii=False, default=str), encoding="utf-8")
    else:
        with_value = {"--data-root", "--max-reject"}
        skip = {args[i + 1] for i, a in enumerate(args[:-1]) if a in with_value}
        batch = next(a for a in args if not a.startswith("--") and a not in skip)
        rep = ingest(batch, P, dry_run="--dry-run" in args, max_reject=mr, use_llm="--llm" in args)
        say("Kết quả:", rep["status"])
