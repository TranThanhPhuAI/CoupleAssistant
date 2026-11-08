"""Đánh giá: Recall@10 và NDCG@10 cho 4 phiên bản xếp hạng trên data/eval/queries.json.

    V1 chỉ rating | V2 + text (ngữ nghĩa) | V3 + ABSA (hệ thống đầy đủ) | V4 + tính cách
    + so sánh "có AI chọn" (V5_llm: LLM chọn 3–5 trong 15 quán của V3) với "chỉ chấm điểm" (n quán đầu của V3,
      n = số quán AI chọn) bằng NDCG@n, điểm liên quan trung bình, tỷ lệ quán "rất phù hợp" (Lovespot 5.3).

Nhãn liên quan: pooling top-10 của mọi phiên bản -> LLM chấm 0/1/2 dựa trên dữ liệu quán
(ràng buộc cứng quận/giá kiểm tra bằng code -> vi phạm = 0). Nhãn được cache; nếu có
data/eval/judgments_human.csv (qid, restaurant_id, grade) thì nhãn người GHI ĐÈ nhãn LLM.
Lựa chọn của LLM (V5) cũng được cache ở data/eval/llm_picks.json.

Chạy:  python evaluate.py              (chấm phần còn thiếu + tính chỉ số)
       python evaluate.py --no-judge   (chỉ tính chỉ số từ nhãn đã có)
"""
import json
import sys

import numpy as np
import pandas as pd

import config as cfg
from explainer import _review_evidence, _strengths, _fmt_price
from personality import adjust_weights, build_profile, personality_fit
from query_parser import parse_budget, parse_districts
from ranker import Person, load_candidates, rank_for_couple
from scoring import pct_from_ref
from semantic import search

sys.stdout.reconfigure(encoding="utf-8")
EVAL_DIR = cfg.BASE / "data" / "eval"
JUDGE_CACHE = EVAL_DIR / "judgments.jsonl"
HUMAN = EVAL_DIR / "judgments_human.csv"
RESULTS = EVAL_DIR / "eval_results.csv"
PICKS_CACHE = EVAL_DIR / "llm_picks.json"
K = 10
VARIANTS = ["V1_rating", "V2_text", "V3_absa", "V4_persona"]


# ======================= Chạy 4 phiên bản =======================

def hard_filter(C, q):
    if q.get("districts"):
        C = C[C["district"].isna() | C["district"].isin(q["districts"])]
    if q.get("budget_per_person"):
        C = C[C["price_min"].isna() | (C["price_min"] <= q["budget_per_person"])]
    return C


def llm_pick(q, ranked, picks_cache, allow_llm):
    """V5: LLM chọn trong danh sách ngắn của V3 (cache theo truy vấn để không gọi lại mỗi lần đánh giá)."""
    key = f"{q['id']}|{'|'.join(ranked['restaurant_id'])}"
    if key not in picks_cache and allow_llm:
        from explainer import choose
        picks, stats = choose(ranked, {"mong_muon": q["text"]}, use_llm=True)
        if stats.get("llm_used"):
            picks_cache[key] = {"picks": [p["restaurant_id"] for p in picks], "n_invalid_id": stats.get("n_invalid_id", 0)}
    return picks_cache.get(key)


def run_variants(q, personas, traits, picks_cache=None, allow_llm=False):
    sem = search(q["semantic"], k=10_000, evidence=2)
    base = hard_filter(load_candidates(), q)
    out = {}
    out["V1_rating"] = base.sort_values(["bayes_rating", "restaurant_id"], ascending=[False, True])["restaurant_id"].head(K).tolist()
    b = base.merge(sem[["restaurant_id", "semantic_match"]], on="restaurant_id", how="left")
    b["s"] = 0.5 * pct_from_ref(b["bayes_rating"], b["bayes_rating"]) + 0.5 * pct_from_ref(b["semantic_match"], b["semantic_match"])
    out["V2_text"] = b.sort_values(["s", "restaurant_id"], ascending=[False, True])["restaurant_id"].head(K).tolist()
    budget = q.get("budget_per_person")
    a, bb = Person("A", None, budget), Person("B", None, budget)
    ranked = rank_for_couple(a, bb, query=q["semantic"], k=cfg.AI_SHORTLIST, districts=q.get("districts"))
    out["V3_absa"] = ranked["restaurant_id"].tolist()[:K]
    if picks_cache is not None:
        v5 = llm_pick(q, ranked, picks_cache, allow_llm)
        if v5:
            out["V5_llm"] = v5["picks"]
    if q.get("persona"):
        pr = personas[q["persona"]]
        pa, pb = build_profile(pr["a"]), build_profile(pr["b"])
        a = Person("A", None, budget, weights=adjust_weights(pa))
        bb = Person("B", None, budget, weights=adjust_weights(pb))
        out["V4_persona"] = rank_for_couple(a, bb, query=q["semantic"], k=K, districts=q.get("districts"),
                                            personality_fit={"A": personality_fit(pa, traits),
                                                             "B": personality_fit(pb, traits)})["restaurant_id"].tolist()
    else:
        out["V4_persona"] = out["V3_absa"]  # không có hồ sơ tính cách -> giống V3
    return out, sem


# ======================= Chấm nhãn (LLM) =======================

JUDGE_SCHEMA = {"type": "object", "properties": {"grades": {"type": "array", "items": {
    "type": "object", "properties": {"restaurant_id": {"type": "string"}, "grade": {"type": "integer", "minimum": 0, "maximum": 2}},
    "required": ["restaurant_id", "grade"]}}}, "required": ["grades"]}
JUDGE_SYSTEM = (
    "Bạn là giám khảo đánh giá hệ thống gợi ý quán hẹn hò ở TP.HCM. Với yêu cầu của cặp đôi và dữ liệu từng quán, "
    "chấm: 2 = rất phù hợp (đúng yêu cầu chính VÀ hợp để hẹn hò), 1 = phù hợp một phần, 0 = không phù hợp. "
    "Chỉ dựa vào dữ liệu được cung cấp, không dựa vào hiểu biết bên ngoài. Trả JSON {\"grades\": [...]} cho MỌI quán."
)


def load_judgments():
    J = {}
    if JUDGE_CACHE.exists():
        for line in JUDGE_CACHE.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                J[(d["qid"], d["restaurant_id"])] = d["grade"]
    if HUMAN.exists():
        h = pd.read_csv(HUMAN, encoding="utf-8-sig")
        for qid, rid, g in h[["qid", "restaurant_id", "grade"]].dropna().itertuples(index=False):
            J[(qid, rid)] = int(g)
    return J


def judge(q, rids, sem, personas, J):
    from llm import llm_json
    R = load_candidates().set_index("restaurant_id")
    ev = dict(zip(sem["restaurant_id"], sem["evidence"]))
    todo = [r for r in rids if (q["id"], r) not in J]
    new = []
    for r in list(todo):  # ràng buộc cứng: kiểm tra bằng code
        row = R.loc[r]
        bad_d = q.get("districts") and pd.notna(row["district"]) and row["district"] not in q["districts"]
        bad_p = q.get("budget_per_person") and pd.notna(row["price_min"]) and row["price_min"] > q["budget_per_person"]
        if bad_d or bad_p:
            new.append({"qid": q["id"], "restaurant_id": r, "grade": 0, "source": "rule"})
            todo.remove(r)
    req = q["text"] + (f" | Cặp đôi: {personas[q['persona']]['desc']}" if q.get("persona") else "")
    # Lô 8 quán; quán bị sót (lỗi/LLM bỏ qua) -> chấm lại riêng từng quán
    chunks = [todo[i:i + 8] for i in range(0, len(todo), 8)]
    done = set()
    while chunks:
        chunk = chunks.pop(0)
        items = []
        for r in chunk:
            row = R.loc[r]
            items.append({"restaurant_id": r, "ten": row["name"], "loai_hinh": row["place_types"],
                          "mon": row["cuisines"] if isinstance(row["cuisines"], str) else "",
                          "quan": row["district"], "gia": _fmt_price(row["price_min"], row["price_max"]),
                          "diem_danh_gia_10": round(float(row["bayes_rating"]), 1), "diem_noi_bat": _strengths(r),
                          "review_lien_quan": [t[:200] for _, t in (ev.get(r) or [])][:2],
                          "review_khac": _review_evidence(r, 1)})
        msg = json.dumps({"yeu_cau": req, "quan": items}, ensure_ascii=False)
        try:
            obj = llm_json([{"role": "system", "content": JUDGE_SYSTEM}, {"role": "user", "content": msg}],
                              JUDGE_SCHEMA, timeout=300, num_ctx=8192)
            got = {str(g["restaurant_id"]): int(g["grade"]) for g in obj.get("grades", [])}
        except Exception as e:
            print(f"  [{q['id']}] lỗi chấm: {e}")
            got = {}
        new += [{"qid": q["id"], "restaurant_id": r, "grade": got[r], "source": "llm"} for r in chunk if r in got]
        missed = [r for r in chunk if r not in got]
        if len(chunk) > 1:
            chunks += [[r] for r in missed]
        done |= set(chunk)
    if new:
        with open(JUDGE_CACHE, "a", encoding="utf-8") as f:
            for d in new:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
                J[(d["qid"], d["restaurant_id"])] = d["grade"]
    return J


# ======================= Chỉ số =======================

def ndcg_at_k(ranked, grades, k=K):
    gains = [2 ** grades.get(r, 0) - 1 for r in ranked[:k]]
    dcg = sum(g / np.log2(i + 2) for i, g in enumerate(gains))
    ideal = sorted((2 ** g - 1 for g in grades.values()), reverse=True)[:k]
    idcg = sum(g / np.log2(i + 2) for i, g in enumerate(ideal))
    return dcg / idcg if idcg > 0 else np.nan


def recall_at_k(ranked, grades, k=K):
    rel = {r for r, g in grades.items() if g >= 1}
    return len(set(ranked[:k]) & rel) / min(len(rel), k) if rel else np.nan


def main():
    spec = json.loads((EVAL_DIR / "queries.json").read_text(encoding="utf-8"))
    personas, queries = spec["personas"], spec["queries"]
    traits = pd.read_csv(cfg.RESTAURANT_TRAITS, encoding="utf-8-sig")
    J = load_judgments()
    do_judge = "--no-judge" not in sys.argv

    # Độ chính xác parser (luật) so với ràng buộc chuẩn
    ok_d = ok_b = 0
    for q in queries:
        ok_d += sorted(parse_districts(q["text"])) == sorted(q.get("districts", []))
        ok_b += parse_budget(q["text"])[0] == q.get("budget_per_person")
    print(f"Parser luật: quận đúng {ok_d}/{len(queries)}, ngân sách đúng {ok_b}/{len(queries)}")

    picks_cache = json.loads(PICKS_CACHE.read_text(encoding="utf-8")) if PICKS_CACHE.exists() else {}
    rows, ai_rows = [], []
    for q in queries:
        runs, sem = run_variants(q, personas, traits, picks_cache, allow_llm=do_judge)
        pool = list(dict.fromkeys(r for v in VARIANTS + ["V5_llm"] for r in runs.get(v, [])))
        if do_judge:
            J = judge(q, pool, sem, personas, J)
        grades = {r: J[(q["id"], r)] for r in pool if (q["id"], r) in J}
        if len(grades) < len(pool):
            print(f"  [{q['id']}] thiếu nhãn {len(pool) - len(grades)}/{len(pool)}")
        for v in VARIANTS:
            rows.append({"qid": q["id"], "variant": v, "persona": bool(q.get("persona")),
                         "recall@10": recall_at_k(runs[v], grades), "ndcg@10": ndcg_at_k(runs[v], grades),
                         "n_returned": len(runs[v]), "n_relevant_pool": sum(g >= 1 for g in grades.values())})
        print(f"  {q['id']} pool={len(pool)} relevant={rows[-1]['n_relevant_pool']} | " +
              " ".join(f"{v.split('_')[0]}:{r['ndcg@10']:.2f}" for v, r in zip(VARIANTS, rows[-4:])))
        if runs.get("V5_llm"):  # có AI chọn vs chỉ chấm điểm: cùng 15 ứng viên, CÙNG số quán hiển thị (n = số AI chọn)
            n = len(runs["V5_llm"])
            for name, lst in (("chỉ chấm điểm (top-n V3)", runs["V3_absa"][:n]), ("có AI chọn (V5)", runs["V5_llm"])):
                ai_rows.append({"qid": q["id"], "variant": name, "ndcg@n": ndcg_at_k(lst, grades, n),
                                "mean_grade": np.mean([grades.get(r, 0) for r in lst]),
                                "share_grade2": np.mean([grades.get(r, 0) == 2 for r in lst]), "n_shown": n})
    PICKS_CACHE.write_text(json.dumps(picks_cache, ensure_ascii=False, indent=1), encoding="utf-8")
    df = pd.DataFrame(rows)
    df.to_csv(RESULTS, index=False, encoding="utf-8-sig")
    print("\n=== TRUNG BÌNH (40 truy vấn) ===")
    print(df.groupby("variant")[["recall@10", "ndcg@10"]].mean().reindex(VARIANTS).round(3).to_string())
    print("\n=== CHỈ CÁC TRUY VẤN CÓ HỒ SƠ TÍNH CÁCH ===")
    print(df[df["persona"]].groupby("variant")[["recall@10", "ndcg@10"]].mean().reindex(VARIANTS).round(3).to_string())
    pv = df.pivot(index="qid", columns="variant", values="ndcg@10")
    print(f"\nV3 tốt hơn V2 ở {(pv['V3_absa'] > pv['V2_text']).sum()} truy vấn, kém hơn ở {(pv['V3_absa'] < pv['V2_text']).sum()}")
    if ai_rows:
        ai = pd.DataFrame(ai_rows)
        print(f"\n=== CÓ AI CHỌN vs CHỈ CHẤM ĐIỂM ({ai['qid'].nunique()} truy vấn, Lovespot 5.3) ===")
        print(ai.groupby("variant")[["ndcg@n", "mean_grade", "share_grade2", "n_shown"]].mean().round(3).to_string())
        pa = ai.pivot(index="qid", columns="variant", values="mean_grade")
        better = (pa["có AI chọn (V5)"] > pa["chỉ chấm điểm (top-n V3)"]).sum()
        worse = (pa["có AI chọn (V5)"] < pa["chỉ chấm điểm (top-n V3)"]).sum()
        print(f"AI chọn tốt hơn ở {better} truy vấn, kém hơn ở {worse} | mã quán bịa bị chặn: "
              f"{sum(v.get('n_invalid_id', 0) for v in picks_cache.values())}")
    print(f"Đã lưu: {RESULTS.relative_to(cfg.BASE)} | nhãn: {JUDGE_CACHE.relative_to(cfg.BASE)}")


if __name__ == "__main__":
    main()
