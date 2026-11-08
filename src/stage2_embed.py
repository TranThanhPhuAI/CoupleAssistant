"""Giai đoạn 2: build index embedding (chỉ embed doc mới) + chạy truy vấn kiểm tra.

Chạy:  python stage2_embed.py            (build/cập nhật index + demo)
       python stage2_embed.py --demo     (chỉ demo, không build)
"""
import sys
import time

import numpy as np
import pandas as pd

import config as cfg
from semantic import Searcher, build_docs, embed_docs
from vector_store import VectorStore

sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 220)
pd.set_option("display.max_colwidth", 60)


def build():
    rest = pd.read_csv(cfg.RESTAURANTS_CLEAN, encoding="utf-8-sig")
    rev = pd.read_csv(cfg.REVIEWS_CLEAN, encoding="utf-8-sig")
    docs = build_docs(rest, rev)
    n_rev = (docs["doc_type"] == "review").sum()
    print(f"Review: {len(rev)} -> {n_rev} chunk (review bị cắt: {(docs[docs.doc_type=='review'].review_id.value_counts() > 1).sum()})")
    print(f"Doc hồ sơ quán: {(docs['doc_type'] == 'profile').sum()} | Tổng doc: {len(docs)}")
    print("Ví dụ doc hồ sơ:", docs[docs.doc_type == "profile"]["text"].iloc[0])

    t = time.time()
    stats = VectorStore(cfg.INDEX_DIR).build(docs, embed_docs, cfg.EMBED_MODEL, keep=cfg.INDEX_KEEP_VERSIONS)
    print(f"Build xong trong {time.time() - t:.0f}s:", stats)


# Truy vấn kiểm tra + từ khóa "đúng" để đo nhanh precision@10 (proxy, không thay cho bộ đánh giá GĐ cuối)
DEMO = [
    ("cafe yên tĩnh để trò chuyện", {}, r"cafe|coffee|cà phê|caphe|trà"),
    ("nhà hàng lãng mạn cho buổi hẹn hò tối", {}, None),
    ("quán có view đẹp chụp ảnh sống ảo", {}, None),
    ("lẩu ngon ăn tối mùa mưa", {}, r"lẩu"),
    ("pizza mì Ý kiểu Tây", {}, r"pizza|pasta|ý|ita"),
    ("đồ Hàn Quốc nướng BBQ", {}, r"hàn|gogi|bbq|nướng|korea"),
    ("ăn chay thanh đạm", {}, r"chay|vegetarian|veggie"),
    ("chỗ ăn tối lãng mạn Quận 3 dưới 400k", {"districts": ["Quận 3"], "budget_max": 400_000}, None),
]


def demo():
    t = time.time()
    s = Searcher()
    print(f"\nNạp index: {len(s.meta)} doc, model {s.manifest['model']} ({time.time() - t:.1f}s)")
    s.search("khởi động")  # nạp model
    for q, f, pat in DEMO:
        t = time.time()
        res = s.search(q, k=10, **f)
        dt = time.time() - t
        line = f"\n### '{q}' {f if f else ''} ({dt*1000:.0f} ms)"
        if pat:
            # Proxy: tên/loại/món của quán chứa từ khóa
            info = res["restaurant_id"].map(s.rest["name"].fillna("") + " " + s.rest["cuisines"].fillna("")
                                            + " " + s.rest["place_type"].fillna(""))
            p = info.str.contains(pat, case=False, regex=True).mean()
            line += f"  | proxy P@10 = {p:.0%}"
        print(line)
        show = res.head(5).copy()
        show["name"] = show["name"].str.slice(0, 40)
        show["ev"] = show["evidence"].map(lambda e: e[0][1][:90].replace("\n", " ") if e else "")
        print(show[["name", "district", "place_type", "semantic_match", "n_hit_reviews", "bayes_rating", "ev"]]
              .round(3).to_string(index=False))

    # Phân bố điểm semantic_match trên toàn bộ quán cho 1 truy vấn
    allr = s.search("cafe yên tĩnh để trò chuyện", k=10_000, evidence=0)
    print("\nPhân bố semantic_match ('cafe yên tĩnh...', toàn bộ quán):",
          allr["semantic_match"].describe()[["min", "25%", "50%", "75%", "max"]].round(3).to_dict())


if __name__ == "__main__":
    if "--demo" not in sys.argv:
        build()
    demo()
