"""Giai đoạn 2: tạo doc, embedding (bge-m3) và tìm kiếm ngữ nghĩa mức review -> gộp lên quán.

Dùng:
    from semantic import search
    search("cafe yên tĩnh để trò chuyện", k=10, districts=["Quận 3"], budget_max=200_000)
"""
import re
import threading

import numpy as np
import pandas as pd

import config as cfg  # đặt HF_HOME trước khi import sentence_transformers
from vector_store import VectorStore

# ======================= Tạo doc =======================

def chunk_text(text, max_chars=cfg.CHUNK_MAX_CHARS):
    """Cắt review dài theo câu thành các đoạn <= max_chars (review ngắn giữ nguyên)."""
    if len(text) <= max_chars * 1.2:
        return [text]
    chunks, cur = [], ""
    for s in re.split(r"(?<=[.!?…])\s+|\n+", text):
        if cur and len(cur) + len(s) + 1 > max_chars:
            chunks.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        chunks.append(cur)
    out = []
    for c in chunks:  # câu quá dài -> cắt cứng
        out += [c[i:i + max_chars] for i in range(0, len(c), max_chars)]
    return out


def _fmt_price(lo, hi):
    if pd.isna(lo):
        return ""
    lo, hi = int(lo) // 1000, int(hi) // 1000
    return f" Giá {lo}k" + (f" - {hi}k." if hi != lo else ".")


def profile_text(r):
    """Doc 'hồ sơ quán': giúp khớp truy vấn theo tên/món/loại hình, và cho quán không có review."""
    parts = [str(r["name"]) + "."]
    if isinstance(r.get("place_types"), str) and r["place_types"]:
        parts.append(f"Loại hình: {r['place_types']}.")
    if isinstance(r.get("cuisines"), str) and r["cuisines"]:
        parts.append(f"Món: {r['cuisines']}.")
    if isinstance(r.get("district"), str):
        parts.append(f"{r['district']}, TP. HCM.")
    return " ".join(parts) + _fmt_price(r.get("price_min"), r.get("price_max"))


def build_docs(restaurants, reviews):
    """Trả về DataFrame doc: doc_id, restaurant_id, review_id, doc_type (review|profile), text."""
    rows = []
    for rid, revid, text in zip(reviews["restaurant_id"], reviews["review_id"], reviews["review_text"]):
        for i, c in enumerate(chunk_text(str(text))):
            rows.append((f"{revid}#{i}", rid, revid, "review", c))
    for _, r in restaurants.iterrows():
        rows.append((f"{r['restaurant_id']}#profile", r["restaurant_id"], "", "profile", profile_text(r)))
    return pd.DataFrame(rows, columns=["doc_id", "restaurant_id", "review_id", "doc_type", "text"])


# ======================= Embedding =======================

_model = None
_model_lock = threading.RLock()  # server web: nhiều request dùng chung 1 model


def get_model():
    global _model
    with _model_lock:
        return _model if _model is not None else _load_model()


def _load_model():
    global _model
    if _model is None:
        import torch
        from sentence_transformers import SentenceTransformer
        device = cfg.EMBED_DEVICE
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        if device == "cuda":  # nạp thẳng fp16 để tiết kiệm VRAM
            _model = SentenceTransformer(cfg.EMBED_MODEL, device="cuda", model_kwargs={"torch_dtype": torch.float16})
        else:  # CPU: bfloat16 tốn ~nửa RAM, đủ nhanh để embed câu hỏi (dùng khi GPU đang bận)
            _model = SentenceTransformer(cfg.EMBED_MODEL, device="cpu", model_kwargs={"torch_dtype": torch.bfloat16})
        _model.max_seq_length = cfg.EMBED_MAX_SEQ
    return _model


def embed_docs(texts):
    texts = [cfg.EMBED_DOC_PREFIX + t for t in texts]
    return get_model().encode(texts, batch_size=cfg.EMBED_BATCH, normalize_embeddings=True,
                              show_progress_bar=True, convert_to_numpy=True)


def embed_query(q):
    model = get_model()
    with _model_lock:
        v = model.encode([cfg.EMBED_QUERY_PREFIX + q], normalize_embeddings=True, convert_to_tensor=True)[0]
    return v.float().cpu().numpy()  # bfloat16 không chuyển thẳng sang numpy được


# ======================= Tìm kiếm =======================

class Searcher:
    """Nạp index hiện hành (CURRENT) + bảng quán một lần, tìm kiếm nhiều lần."""

    def __init__(self, index_dir=None, restaurants_path=None):
        loaded = VectorStore(index_dir or cfg.INDEX_DIR).load()
        if loaded is None:
            raise RuntimeError("Chưa có index. Chạy: python stage2_embed.py")
        self.meta, self.emb, self.manifest = loaded
        self.rest = pd.read_csv(restaurants_path or cfg.RESTAURANTS_CLEAN, encoding="utf-8-sig").set_index("restaurant_id")
        self.is_review = (self.meta["doc_type"] == "review").to_numpy()
        # mã số nguyên cho quán/review để gộp nhanh bằng pandas
        self.rest_codes, self.rest_index = pd.factorize(self.meta["restaurant_id"])

    def search(self, query, k=10, districts=None, budget_max=None, place_types=None, evidence=2):
        """Trả về DataFrame top-k quán, cột semantic_match (cosine, chưa chuẩn hóa) + bằng chứng review.

        Điểm quán = (1-w)·review_agg + w·profile_sim
          review_agg = trung bình top-3 review gần nhất (mỗi review lấy chunk tốt nhất);
          quán có < 3 review được bù bằng mức nền (trung vị độ tương đồng của truy vấn) -> làm mượt.
        Bộ lọc: giá thiếu / quận thiếu KHÔNG bị loại (trung tính).
        """
        q = embed_query(query)
        sims = self.emb @ q
        m = self.meta

        rv = pd.DataFrame({"rest": self.rest_codes[self.is_review], "review_id": m.loc[self.is_review, "review_id"].to_numpy(),
                           "doc_i": np.flatnonzero(self.is_review), "sim": sims[self.is_review]})
        baseline = float(np.median(rv["sim"]))
        best = rv.sort_values("sim", ascending=False).drop_duplicates("review_id")  # chunk tốt nhất mỗi review
        best["rank"] = best.groupby("rest").cumcount()
        top = best[best["rank"] < cfg.SEM_TOP_REVIEWS]
        agg = top.groupby("rest")["sim"].agg(["sum", "count"])

        n_rest = len(self.rest_index)
        s_sum = np.zeros(n_rest)
        s_cnt = np.zeros(n_rest)
        s_sum[agg.index] = agg["sum"]
        s_cnt[agg.index] = agg["count"]
        review_agg = (s_sum + (cfg.SEM_TOP_REVIEWS - s_cnt) * baseline) / cfg.SEM_TOP_REVIEWS

        prof = np.full(n_rest, baseline)
        pmask = ~self.is_review
        prof[self.rest_codes[pmask]] = sims[pmask]
        w = cfg.SEM_PROFILE_WEIGHT
        score = (1 - w) * review_agg + w * prof

        res = pd.DataFrame({"restaurant_id": self.rest_index, "semantic_match": score,
                            "review_agg": review_agg, "profile_sim": prof, "n_hit_reviews": s_cnt.astype(int)})
        res = res[res["restaurant_id"].isin(self.rest.index)]  # index có thể mới hơn/cũ hơn bảng quán trong lúc ingest
        res = res.join(self.rest[["name", "district", "place_type", "price_min", "price_max",
                                  "bayes_rating", "rating_suspect"]], on="restaurant_id")

        # Bộ lọc cứng (người dùng chỉ định rõ); dữ liệu thiếu -> giữ lại
        if districts:
            res = res[res["district"].isna() | res["district"].isin(districts)]
        if budget_max is not None:
            res = res[res["price_min"].isna() | (res["price_min"] <= budget_max)]
        if place_types:
            res = res[res["place_type"].isin(place_types)]

        res = res.sort_values("semantic_match", ascending=False).head(k).reset_index(drop=True)

        # Bằng chứng: các review khớp nhất của từng quán (dùng cho RAG giai đoạn 6)
        if evidence:
            code_of = {r: i for i, r in enumerate(self.rest_index)}
            ev = top[top["rank"] < evidence]
            texts = m["text"].to_numpy()
            res["evidence"] = [
                [(round(float(s), 3), texts[d]) for s, d in
                 ev.loc[ev["rest"] == code_of[rid], ["sim", "doc_i"]].itertuples(index=False)]
                for rid in res["restaurant_id"]]
        return res


_searcher = None


def search(query, k=10, **filters):
    """Hàm tiện dụng: search(query, k=10, districts=[...], budget_max=..., place_types=[...])."""
    global _searcher
    with _model_lock:
        if _searcher is None:
            _searcher = Searcher()
    return _searcher.search(query, k=k, **filters)
