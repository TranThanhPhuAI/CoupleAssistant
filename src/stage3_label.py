"""Giai đoạn 3a: chọn mẫu ~2.000 review -> LLM local gán nhãn ABSA -> xuất 200 dòng kiểm tra tay.

Chạy:  python stage3_label.py              (chọn mẫu nếu chưa có, gán nhãn tiếp phần còn thiếu)
       python stage3_label.py --limit 20   (thử nhanh 20 review)
       python stage3_label.py --expand     (gán thêm mọi review chứa từ khóa hẹn hò/không gian)
Có thể Ctrl+C rồi chạy lại: nhãn đã gán được cache trong llm_labels.jsonl.
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd

import config as cfg
from absa import ASPECTS, label_review

sys.stdout.reconfigure(encoding="utf-8")

# Truy vấn để lấy mẫu có chủ đích: đảm bảo đủ ví dụ cho khía cạnh hiếm (lãng mạn, view, riêng tư, ồn)
TARGET_QUERIES = [
    "không gian lãng mạn, hợp hẹn hò với người yêu",
    "quán yên tĩnh, riêng tư, nói chuyện thoải mái",
    "view đẹp, nhiều góc chụp ảnh sống ảo",
    "quán ồn ào, chật chội, bàn ghế sát nhau",
    "không gian đẹp, decor xinh xắn, ấm cúng",
    "nhà hàng sang trọng có phòng riêng",
]


def make_sample():
    from semantic import embed_query
    from vector_store import VectorStore

    rev = pd.read_csv(cfg.REVIEWS_CLEAN, encoding="utf-8-sig")
    rev = rev[rev["text_len"] >= 20]
    meta, emb, _ = VectorStore(cfg.INDEX_DIR).load()
    is_rev = (meta["doc_type"] == "review").to_numpy()
    rmeta = meta[is_rev].reset_index(drop=True)
    remb = emb[is_rev]
    rng = np.random.default_rng(42)
    per_rest = {}
    chosen = []

    def take(review_ids, stratum, limit):
        n = 0
        for rv in review_ids:
            if n >= limit:
                break
            rid = rest_of.get(rv)
            if rid is None or rv in chosen_set or per_rest.get(rid, 0) >= cfg.ABSA_MAX_PER_RESTAURANT:
                continue
            chosen.append((rv, stratum))
            chosen_set.add(rv)
            per_rest[rid] = per_rest.get(rid, 0) + 1
            n += 1

    rest_of = dict(zip(rev["review_id"], rev["restaurant_id"]))
    chosen_set = set()
    n_target = int(cfg.ABSA_SAMPLE_SIZE * cfg.ABSA_TARGETED_SHARE)
    per_q = n_target // len(TARGET_QUERIES)
    for q in TARGET_QUERIES:
        sims = remb @ embed_query(q)
        order = rmeta.iloc[np.argsort(-sims)]["review_id"].drop_duplicates()
        take(order, f"targeted:{q[:25]}", per_q)
    rest_ids = rev["review_id"].to_numpy().copy()
    rng.shuffle(rest_ids)
    take(rest_ids, "random", cfg.ABSA_SAMPLE_SIZE - len(chosen))

    s = pd.DataFrame(chosen, columns=["review_id", "stratum"]).merge(
        rev[["review_id", "restaurant_id", "review_text", "rating"]], on="review_id")
    cfg.ABSA_DIR.mkdir(parents=True, exist_ok=True)
    s.to_csv(cfg.ABSA_SAMPLE, index=False, encoding="utf-8-sig")
    print(f"Đã chọn mẫu: {len(s)} review, {s['restaurant_id'].nunique()} quán")
    print(s["stratum"].str.split(":").str[0].value_counts().to_dict())
    return s


# Từ khóa (đã bỏ dấu) cho khía cạnh hẹn hò: bộ phân loại embedding bắt kém các khía cạnh hiếm,
# nên mọi review nhắc tới những từ này đều được LLM gán nhãn trực tiếp.
DATE_KEYWORDS = (r"\b(?:lang man|hen ho|cap doi|nguoi yeu|di date|yen tinh|on ao|dong duc|chat choi|rieng tu|"
                 r"phong rieng|kin dao|view|veiw|song ao|chup anh|chup hinh|check in|checkin|rooftop|san thuong|"
                 r"ban cong|sang trong|nhac nhe|nhac to|am cung|decor|khong gian)\b")


def make_extra_sample(sample):
    from common import fold
    rev = pd.read_csv(cfg.REVIEWS_CLEAN, encoding="utf-8-sig")
    m = rev["review_text"].map(fold).str.contains(DATE_KEYWORDS, regex=True) & ~rev["review_id"].isin(sample["review_id"])
    extra = rev.loc[m, ["review_id", "restaurant_id", "review_text", "rating"]].assign(stratum="keyword")
    extra.to_csv(cfg.ABSA_SAMPLE_EXTRA, index=False, encoding="utf-8-sig")
    print(f"Mẫu bổ sung theo từ khóa: {len(extra)} review, {extra['restaurant_id'].nunique()} quán")
    return extra


def load_cache():
    done = {}
    if cfg.ABSA_LLM_LABELS.exists():
        for line in cfg.ABSA_LLM_LABELS.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                done[d["review_id"]] = d
    return done


def run_labeling(sample, limit=None):
    done = load_cache()
    todo = sample[~sample["review_id"].isin(done)]
    if limit:
        todo = todo.head(limit)
    print(f"Đã có nhãn: {len(done)} | cần gán: {len(todo)} (model {cfg.OLLAMA_MODEL})")
    if todo.empty:
        return
    t0, n_ok, n_err = time.time(), 0, 0
    with open(cfg.ABSA_LLM_LABELS, "a", encoding="utf-8") as f, \
            ThreadPoolExecutor(cfg.OLLAMA_WORKERS) as pool:
        futs = {pool.submit(label_review, t): rv for rv, t in zip(todo["review_id"], todo["review_text"])}
        for fut in as_completed(futs):
            rv = futs[fut]
            try:
                lab = fut.result()
            except Exception as e:  # lỗi schema/timeout -> bỏ qua, lần chạy sau thử lại
                n_err += 1
                print(f"  lỗi {rv}: {e}")
                continue
            f.write(json.dumps({"review_id": rv, **lab}, ensure_ascii=False) + "\n")
            f.flush()
            n_ok += 1
            if n_ok % 50 == 0:
                rate = n_ok / (time.time() - t0)
                print(f"  {n_ok}/{len(todo)} | {rate:.2f} review/s | còn ~{(len(todo) - n_ok) / rate / 60:.0f} phút")
    print(f"Xong: {n_ok} nhãn mới, {n_err} lỗi, {time.time() - t0:.0f}s")


def report_and_manual_check(sample):
    done = load_cache()
    lab = pd.DataFrame(done.values())
    if lab.empty:
        return
    print(f"\nPhân bố nhãn LLM ({len(lab)} review):")
    dist = pd.DataFrame({a: lab[a].value_counts(normalize=True) for a in ASPECTS}).T.fillna(0)
    print((dist[["pos", "neg", "none"]] * 100).round(1).to_string())

    # 200 dòng kiểm tra tay: cột *_llm là nhãn máy, cột *_human để bạn sửa (để trống = đồng ý)
    if not cfg.ABSA_MANUAL_CHECK.exists() and len(lab) >= cfg.ABSA_MANUAL_N:
        m = sample.merge(lab, on="review_id").sample(cfg.ABSA_MANUAL_N, random_state=7)
        out = m[["review_id", "review_text"]].copy()
        for a in ASPECTS:
            out[f"{a}_llm"] = m[a].to_numpy()
            out[f"{a}_human"] = ""
        out.to_csv(cfg.ABSA_MANUAL_CHECK, index=False, encoding="utf-8-sig")
        print(f"\nĐã xuất file kiểm tra tay: {cfg.ABSA_MANUAL_CHECK.relative_to(cfg.BASE)}")


if __name__ == "__main__":
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    sample = pd.read_csv(cfg.ABSA_SAMPLE, encoding="utf-8-sig") if cfg.ABSA_SAMPLE.exists() else make_sample()
    if "--expand" in sys.argv:  # gán thêm review chứa từ khóa hẹn hò/không gian
        extra = (pd.read_csv(cfg.ABSA_SAMPLE_EXTRA, encoding="utf-8-sig") if cfg.ABSA_SAMPLE_EXTRA.exists()
                 else make_extra_sample(sample))
        target = extra
    else:
        target = sample
    for _ in range(3):  # vòng sau thử lại các review bị timeout/lỗi schema
        run_labeling(target, limit)
        if limit or target["review_id"].isin(load_cache()).all():
            break
    report_and_manual_check(sample)
