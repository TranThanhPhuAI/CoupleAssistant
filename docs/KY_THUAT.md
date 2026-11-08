# Tài liệu kỹ thuật

[← Về README](../README.md)

1. [Tổng quan kiến trúc](#1-tổng-quan-kiến-trúc)
2. [Cách chấm điểm](#2-cách-chấm-điểm)
3. [Module AI theo tài liệu Lovespot](#3-module-ai-theo-tài-liệu-lovespot)
4. [Kết quả đánh giá](#4-kết-quả-đánh-giá)
5. [Cấu hình](#5-cấu-hình)
6. [Quyền riêng tư](#6-quyền-riêng-tư)
7. [Hạn chế đã biết](#7-hạn-chế-đã-biết)
8. [Bản đồ mã nguồn](#8-bản-đồ-mã-nguồn)

---

## 1. Tổng quan kiến trúc

```
 kiểm tra lượt AI ─► hiểu câu hỏi ─► lọc cứng ─────────► chấm điểm xác định ─────────► LLM chọn 3–5 ─► code kiểm tra ─► lưu nhật ký
 (hồ sơ, gói)        (luật + LLM)    quận, ngân sách,    ngữ nghĩa + ngưỡng "ngon +     + viết lý do    quán bịa? lý do   ai_requests,
                                     đang mở cửa;        hẹn hò" + TOPSIS từng người                    bịa? -> bù bằng   ai_suggestion_
                                     trống -> nới dần    + gộp 2 người -> 15 quán                       thứ tự điểm       results
```

**Nguyên tắc thiết kế:**
- **Lọc trước, AI chọn sau, code kiểm tra cuối:** phần cần đúng / sai giao cho dữ liệu, công thức và code; LLM chỉ hiểu câu hỏi,
  chọn trong danh sách đã lọc và viết lý do. Thứ tự hiển thị luôn theo điểm công thức, nên cùng đầu vào luôn cho cùng thứ tự.
- **Tách dữ liệu / chỉ mục / API:** `data/clean/*.csv`, rồi `data/index/` (có phiên bản, tráo atomic), rồi lõi
  `recommend.py` / `planner.py`, rồi lớp dịch vụ `ai_service.py`, rồi server `api.py` (REST JSON + giao diện web).
  Backend Lovespot chỉ cần gọi HTTP.
- **Thêm dữ liệu không phải huấn luyện lại:** quán mới chỉ cần embedding cho phần mới và chấm theo tham chiếu đã lưu.
- **LLM chạy local** (Ollama `qwen3:8b`), nên không tốn phí API và dữ liệu không rời khỏi máy.
  Dự phòng tùy chọn: Claude Haiku (`claude-haiku-5-5`) khi Ollama tắt (`LLM_PROVIDER=auto`) hoặc máy yếu (`anthropic`).
- **Triển khai máy nhà:** server chỉ nghe 127.0.0.1, ra Internet qua Cloudflare Tunnel + Access; đăng nhập JWT;
  lịch Windows sao lưu / nhập / tính lại; server tự nạp lại dữ liệu khi file thay đổi (`api.fresh_data`). Xem `TRIEN_KHAI.md`.

---

## 2. Cách chấm điểm

### 2.1 Rating Bayes

`bayes = (n·v + m·C) / (n + m)`, với m = 10 và C ≈ 6,97 là trung bình theo quán. Quán ít review bị kéo về C.
- **Chống review ảo:** mỗi quán chỉ tính tối đa 3 review/ngày. Quán có hơn 90% review đạt 10 điểm và các review dồn vào ít
  ngày bị gắn cờ `rating_suspect`, khi đó n bị giới hạn ≤ m.
- **Ba nguồn rating, theo thứ tự ưu tiên:** review trong dữ liệu, điểm tổng hợp của nguồn, rồi prior C (quán chưa có gì).

### 2.2 Phân tích cảm xúc theo khía cạnh (ABSA)

- **8 khía cạnh:** món ăn, không gian, yên tĩnh, lãng mạn, view, riêng tư, phục vụ, giá. Mỗi khía cạnh nhận pos / neg / none.
- LLM gán nhãn trực tiếp **5.634 review**: 2.000 review mẫu (một nửa chọn có chủ đích) cộng mọi review chứa từ khóa về
  không gian / hẹn hò.
- Phần còn lại dùng hồi quy logistic trên embedding bge-m3. Bộ phân loại này huấn luyện một lần, review mới chỉ cần dự đoán.

### 2.3 food_score, date_score, couple_score (0–1)

- **Khía cạnh dạng tỉ lệ** (món ăn, phục vụ, giá) = khen / (khen + chê), làm mượt Bayes với α = 5.
- **Khía cạnh hẹn hò** = (khen − chê) / số review, làm mượt với α = 20, rồi đổi sang z-score (cắt ±3).
  Đa số quán không được ai nhắc tới các khía cạnh này, nên dùng phân vị sẽ khuếch đại nhiễu.
- `food_score` = phân vị của (0,5 × phân vị rating Bayes + 0,5 × phân vị khía cạnh món ăn).
- `date_score` = phân vị của tổng có trọng số: không gian 0,30, lãng mạn 0,25, yên tĩnh 0,15, view 0,15, riêng tư 0,15.
- `couple_score` = food^0,5 × date^0,5, kèm ngưỡng food ≥ 0,55 và date ≥ 0,5.
  Nếu dưới 10 quán qua ngưỡng thì hạ cả hai ngưỡng từng bước 0,05 và gắn nhãn "đánh đổi".

### 2.4 Tìm kiếm ngữ nghĩa

- Embedding `BAAI/bge-m3` cho từng review; review dài trên khoảng 1.200 ký tự được cắt thành đoạn. Mỗi quán có thêm 1 doc "hồ sơ" (tên, loại, món, quận, giá).
- Điểm của quán = 0,8 × trung bình 3 review khớp nhất + 0,2 × độ khớp của doc hồ sơ.
- Quán dưới 3 review được bù bằng mức nền, để một review tình cờ khớp không đẩy quán lên đầu.

### 2.5 Xếp hạng cho hai người

1. **Lọc cứng:** quận, ngân sách, và **đang mở cửa vào giờ hẹn** (còn mở thêm đủ thời gian ở lại; xử lý cả khung qua nửa đêm).
   Quán thiếu dữ liệu vẫn được giữ. Không còn quán nào thì nới dần: ngân sách +50%, mọi quận, bỏ điều kiện giờ; mỗi lần nới đều được báo.
2. **Ngữ nghĩa:** lấy top 80 quán liên quan tới câu hỏi.
3. **Ngưỡng couple:** áp ngưỡng, và luôn giữ thêm 5 quán khớp câu hỏi nhất kèm nhãn đánh đổi.
4. **TOPSIS cho từng người**, tối đa 7 tiêu chí:

| Tiêu chí | Loại | Trọng số mặc định |
|---|---|---|
| couple_score (+ điểm cộng quán mới) | lợi ích | 0,35 |
| interest_match: khớp sở thích, sở thích chung ×2 (chỉ khi có hồ sơ) | lợi ích | 0,30 |
| semantic_match | lợi ích | 0,25 |
| price_fit (tỉ lệ thực đơn nằm trong ngân sách chung = mức thấp hơn của hai người) | lợi ích | 0,15 |
| khoảng cách Haversine từ vị trí của người đó | chi phí | 0,15 |
| personality_fit | lợi ích | 0,10 |
| bookable: có Shop đã duyệt (BR-AI-13; chờ dữ liệu Shop từ backend) | lợi ích | 0,10 |

   Mỗi tiêu chí được đưa về [0,1] bằng min-max trước khi chuẩn hóa vector. Nếu bỏ bước này, tiêu chí có biên độ hẹp gần như mất tác dụng.
   Giá trị thiếu được điền trung vị (mức trung tính); tiêu chí trống toàn bộ thì bỏ qua và chia lại trọng số.
   Vì vậy khi không có sở thích hay dữ liệu Shop, kết quả giống hệt bản trước.
5. **Gộp hai người:** `0,5 × trung bình + 0,5 × min` (least-misery).

### 2.6 Tính cách (tùy chọn)

- **Bảng hỏi 14 câu:** BFI-10 (Rammstedt & John, 2007) + 4 câu sở thích (sôi động / yên tĩnh, món lạ, lên kế hoạch, chụp ảnh).
- **Hồ sơ p ∈ [0,1]** có 5 chiều: sôi động, món lạ, riêng tư, thẩm mỹ, "chắc ăn". Mỗi quán có vector tính chất q cùng 5 chiều.
- `personality_fit = 1 − Σ w_k·|p_k − q_k|`, với w_k tỉ lệ với độ "rõ" của sở thích (|p_k − 0,5|).
- Hồ sơ chỉnh trọng số TOPSIS tối đa ±0,05 mỗi tiêu chí. Hồ sơ **không bao giờ dùng để loại quán**.
- **Phản hồi:** mỗi chiều cập nhật theo Beta pseudo-count. Một lượt thích kéo p về phía q của quán; một lượt không thích có tác dụng bằng nửa.

### 2.7 Sở thích cá nhân

- **24 sở thích** (món / không khí / ngân sách). Độ khớp quán × sở thích (0–1) lấy giá trị lớn nhất trong các bằng chứng:
  - từ khóa trong tên / loại quán (1,0);
  - nhãn món có sẵn (1,0);
  - nhãn AI từ review (độ tin 0,5–1,0);
  - tìm kiếm ngữ nghĩa trên review (tối đa 0,5, chỉ để phân hạng).
- **"Khớp rõ"** (≥ 0,6, dùng trong lời giải thích) bắt buộc phải có bằng chứng cụ thể; ví dụ món Thái chỉ có 12 quán khớp rõ.
- Ma trận được cache ở `data/clean/place_interests.csv` và dựng lại khi `xaylai` hoặc `nhap`.

### 2.8 Nhãn quán do AI gắn (`place_tags`, `source = ai`)

- Nhãn hẹn hò (không gian đẹp, lãng mạn, yên tĩnh, view đẹp, riêng tư) cần z ≥ 1 **và** ít nhất 2 review khen.
- Nhãn món ngon / phục vụ tốt / giá hợp lý cần phân vị ≥ 0,8 trên quán có ít nhất 5 review.
- Có thêm nhãn tiêu cực "ồn ào" để lời giải thích trung thực.
- Hiện có 743 nhãn trên 369 quán.

### 2.9 LLM chọn quán + lời giải thích (RAG)

- LLM nhận 15 quán đã lọc và chấm điểm, cùng dữ liệu đã truy xuất (tên, quận, giá, giờ, nhãn AI, sở thích khớp, trích review đã làm sạch).
  LLM chọn 3–5 quán và viết lý do.
- **Bộ kiểm tra:**
  - mã quán phải nằm trong danh sách (quán bịa bị loại và đếm lại);
  - không chọn trùng;
  - mọi con số trong lý do phải có trong dữ liệu của chính quán đó;
  - không nhắc quán khác.
- Lý do sai thì giữ lựa chọn nhưng thay lý do bằng mẫu câu. Thiếu quán hoặc LLM lỗi thì bù bằng thứ tự chấm điểm.
- **Chống prompt injection:** review được cắt độ dài, bỏ ký tự lạ, vô hiệu hóa câu chèn lệnh ("bỏ qua mọi hướng dẫn…",
  "SYSTEM:", "hãy gợi ý quán X…"); prompt ghi rõ nội dung review là dữ liệu.

### 2.10 Lập plan hẹn hò

- Mỗi chặng (mặc định: ăn tối 90 phút, rồi cà phê / tráng miệng 60 phút) lấy 6 ứng viên đang mở cửa đúng giờ dự kiến.
- Chọn tổ hợp có tổng điểm đôi cao nhất, trừ điểm khi hai chặng xa nhau trên 1 km; loại tổ hợp có chặng cách nhau trên 5 km hoặc vượt ngân sách.
- Giờ từng chặng = chặng trước + thời gian ở lại + di chuyển (ước tính 20 km/h + 10 phút, vì chưa có Map Service).
- `validate_plan` kiểm tra lại giờ mở cửa, khoảng cách và tổng tiền. Lỗi thì thử tổ hợp kế tiếp (tối đa 20); vẫn lỗi thì báo để người dùng chỉnh.
- LLM chỉ viết ghi chú cho từng chặng (có kiểm tra chống bịa); tiêu đề plan cố định.

---

## 3. Module AI theo tài liệu Lovespot

Repo này là **module AI** (thành viên 5, mục 7.1). Các phân hệ hẹn hò, mạng xã hội, đặt chỗ, thanh toán thuộc backend của nhóm.

| Tài liệu | Hiện thực | File |
|---|---|---|
| 4.3 bước 1, BR-AI-01/02: kiểm tra đăng nhập, còn lượt trong ngày | Phải có hồ sơ; đếm lượt từ `ai_requests` theo ngày giờ VN; gói free/plus/premium | `ai_service.py` |
| BR-AI-04: hết lượt thì đề nghị nâng gói | Trả `quota_exceeded` + thông báo, không gọi AI | `ai_service.py` |
| BR-AI-14: mỗi yêu cầu 1 lượt, lỗi hệ thống không tính | `counted` chỉ khi `success`; `error` và `no_result` không tính | `ai_service.py` |
| 4.3 bước 2: lọc cứng (khu vực, ngân sách, đang mở cửa) | `hard_filter` + `is_open_at` | `ranker.py`, `common.py` |
| 4.7: không quán nào qua lọc thì nới dần và báo | `RELAX_STEPS`, ghi chú trong kết quả | `ranker.py` |
| 4.3 bước 3: chấm điểm, giữ khoảng 15 quán (sở thích chung, review, hợp hẹn hò, khoảng cách, đặt chỗ được) | TOPSIS: `interest_match`, `couple_score` (rating + ABSA), khoảng cách, `bookable` | `ranker.py`, `interests.py` |
| 4.3 bước 4–5, BR-AI-11: LLM chọn 3–5, code kiểm tra, dự phòng | `choose` + `validate_picks` | `explainer.py` |
| 4.3 bước 6, 4.5: lưu `ai_requests`, `ai_suggestion_results` | JSONL đúng tên trường của tài liệu (`input_json`, `status`, `counted`, `score_breakdown_json`, `chosen_at`…) | `ai_service.py` |
| BR-AI-12, `profiles.share_interests_with_partner` | Sở thích người kia chỉ dùng khi họ bật; mặc định tắt; báo khi không dùng | `personality.py`, `interests.py` |
| BR-AI-15: chọn quán từ gợi ý | `choose_place` ghi `chosen_at` + cập nhật hồ sơ | `ai_service.py` |
| BR-AI-06, 5.1: plan nhiều chặng + kiểm tra bằng code | `make_plan`, `validate_plan`, log `date_plans` | `planner.py` |
| 4.1: gắn nhãn quán từ review | `derive_tags` cho ra `place_tags.csv` (`source = ai`) | `scoring.py` |
| 5.2: chống prompt injection | `clean_text` + `DATA_RULE` | `llm.py` |
| 5.3: chỉ số (tỷ lệ chọn, quán bịa bị chặn, độ trễ, token, có AI so với chỉ công thức) | `python run.py thongke` + so sánh V5 trong `danhgia` | `ai_service.py`, `evaluate.py` |
| 4.2: lớp bọc AiProvider | `llm.llm_json` là điểm duy nhất gọi LLM: Ollama hoặc Claude Haiku (JSON theo schema), ghi `provider` vào nhật ký | `llm.py` |
| 4.3 bước 1: đăng nhập | JWT HS256 (7 ngày), mật khẩu PBKDF2-SHA256 200k vòng, khóa 15 phút sau 5 lần sai; chỉ sửa hồ sơ của mình, chỉ admin xem chỉ số / đổi gói | `auth.py`, `api.py` |

**Chưa làm vì cần dữ liệu từ backend:**
- `bookable` (Shop đã duyệt);
- tỷ lệ gợi ý dẫn tới đặt chỗ done (`bookings`);
- Map Service (khoảng cách đi đường thật, hiện dùng đường chim bay);
- đánh dấu chặng cần đổi khi quán bị ẩn hoặc Shop bị khóa.

Các cột này đã chừa sẵn chỗ: điền dữ liệu vào là dùng được, không phải sửa thuật toán.

---

## 4. Kết quả đánh giá

- **Cách đo:** 40 câu hỏi mẫu (12 câu có hồ sơ tính cách). Top 10 của mọi phiên bản được gộp lại, LLM chấm từng quán 0/1/2,
  còn ràng buộc quận / giá được kiểm tra bằng code.

| Phiên bản | Recall@10 | NDCG@10 |
|---|---|---|
| V1 chỉ rating | 0,478 | 0,392 |
| V2 + tìm kiếm ngữ nghĩa | 0,663 | 0,556 |
| V3 + ABSA (hệ thống đầy đủ) | **0,848** | **0,760** |
| V4 + tính cách | 0,848 | 0,763 |
| *Riêng 12 câu có hồ sơ: V3 → V4* | 0,891 → 0,891 | 0,742 → 0,752 |

- V3 tốt hơn V2 ở 33/40 câu.

**Có AI chọn so với chỉ chấm điểm công thức** (mục 5.3 của tài liệu):
- Cùng 15 ứng viên, cùng số quán hiển thị: AI chọn 3 quán, đối chứng là 3 quán đầu của công thức.

| | NDCG@3 | Điểm liên quan TB (0–2) | Tỷ lệ quán "rất phù hợp" |
|---|---|---|---|
| Chỉ chấm điểm | 0,702 | 1,40 | 62,5% |
| Có AI chọn | **0,830** | **1,63** | **77,5%** |

- AI chọn tốt hơn ở 19/40 câu, kém hơn ở 4/40 câu. Không có mã quán bịa nào (code vẫn kiểm tra mọi lựa chọn).
- Bản prompt đầu tiên của bước chọn quán thua ở 7 câu: ví dụ hỏi "cafe" nhưng LLM chọn nhà hàng. Đã sửa bằng cách gửi thêm
  `loai_quan`, `mon`, `hang_he_thong` và dặn LLM ưu tiên quán đúng loại hoặc món được hỏi.

⚠️ **Lưu ý thiên lệch:**
- Nhãn do cùng LLM (qwen3) chấm, và LLM đọc cùng loại review mà hệ thống dùng, nên các con số có thể lạc quan.
- Riêng phép so sánh AI với công thức có thể nghiêng về AI, vì người chấm và người chọn là cùng một model.
- Nên thêm nhãn của người bằng file `data/eval/judgments_human.csv` (cột `qid, restaurant_id, grade`); `evaluate.py` sẽ ưu tiên nhãn của người.
- Bộ số liệu này đổi nhẹ so với lần trước (0,766 thành 0,760) vì tập quán được chấm đã có thêm các quán do AI chọn.

---

## 5. Cấu hình

Mọi tham số nằm trong `src/config.py`.

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `DEFAULT_WEIGHTS` | xem bảng 2.5 | Trọng số TOPSIS |
| `GROUP_MEAN_WEIGHT` | 0,5 | 1,0 = chỉ trung bình; càng nhỏ càng ưu tiên người kém hài lòng hơn |
| `COUPLE_FOOD_MIN` / `COUPLE_DATE_MIN` | 0,55 / 0,5 | Ngưỡng "vừa ngon vừa hợp hẹn hò" |
| `DATE_WEIGHTS` | 0,30 / 0,25 / 0,15 / 0,15 / 0,15 | Thành phần date_score |
| `BAYES_M`, `BAYES_DAILY_CAP` | 10, 3 | Bayes và chống seeding |
| `SEMANTIC_PRESELECT`, `SEMANTIC_ALWAYS_KEEP` | 80, 5 | Số quán lấy theo ngữ nghĩa / luôn giữ dù chưa qua ngưỡng |
| `NEW_RESTAURANT_DAYS`, `NEW_RESTAURANT_BONUS` | 60, 0,05 | Cold-start |
| `BUDGET_UNSPECIFIED_SCOPE` | `"total"` | Câu "dưới 400k" được hiểu là tổng cho 2 người |
| `OLLAMA_MODEL`, `OLLAMA_URL` | `qwen3:8b`, `127.0.0.1:11434` | Không dùng `localhost` (Windows chậm khoảng 2 giây/lần) |
| `EMBED_DEVICE` (biến môi trường) | `auto` | `cpu` khi GPU bận |
| `LLM_PROVIDER`, `ANTHROPIC_MODEL` (biến môi trường) | `auto`, `claude-haiku-5-5` | `auto` / `ollama` / `anthropic`; Claude cần `ANTHROPIC_API_KEY` |
| `LOVESPOT_AUTH`, `LOVESPOT_REGISTER` (biến môi trường) | `on`, `on` | `off` = tắt đăng nhập (chỉ dùng trên máy) / tắt tự đăng ký |
| `LOVESPOT_JWT_SECRET` (biến môi trường) | tự sinh `data/auth/jwt_secret` | Khóa ký token |
| `LOVESPOT_BACKUP_DIR`, `BACKUP_KEEP` | `data/backups`, 14 | Nơi lưu bản sao lưu, số bản giữ lại |
| `AI_PLANS` | free 5 / plus 30 / premium 200 | Lượt AI mỗi ngày theo gói |
| `AI_SHORTLIST`, `AI_PICK_MIN` / `AI_PICK_MAX` | 15, 3 / 5 | Số quán gửi LLM / LLM được chọn |
| `PLAN_STOPS`, `PLAN_MAX_HOP_KM` | ăn tối → cà phê, 5 km | Mẫu plan, khoảng cách tối đa giữa hai chặng |
| `REVIEW_SNIPPET_MAX` | 220 | Độ dài tối đa đoạn review đưa vào prompt |

---

## 6. Quyền riêng tư

- Hồ sơ (sở thích, tính cách) là dữ liệu cá nhân.
  - `ProfileStore.save` từ chối lưu khi `consent=False`; `delete` xóa vĩnh viễn.
  - `share_interests_with_partner` **mặc định tắt**: AI không dùng sở thích của người này khi người kia hỏi (BR-AI-12).
  - `partner_view` mặc định chỉ trả `has_profile`; sở thích và vector tính cách chỉ hiện khi chủ hồ sơ bật chia sẻ.
- Chỉ gửi cho LLM sở thích dạng nhãn chung và thông tin quán; không gửi tên, mã người dùng hay câu trả lời bảng hỏi.
- Lời giải thích chỉ nói "hợp với cả hai" ở mức chung.
- Nhật ký AI và nhật ký phản hồi lưu mã người dùng đã băm SHA-256.
- Gói chia sẻ **không chứa** hồ sơ, nhật ký, tài khoản hay phản hồi của ai.
- Trên web: mỗi người chỉ xem / sửa / xóa hồ sơ của mình; xóa tài khoản thì xóa luôn hồ sơ. Khi dùng Claude Haiku,
  câu hỏi và review quán được gửi tới Anthropic (không gửi hồ sơ). Nên bật BitLocker cho ổ chứa `data/`.

---

## 7. Hạn chế đã biết

- Nhãn đánh giá và nhãn ABSA đều do LLM tạo. 200 dòng kiểm tra tay (`data/absa/absa_manual_check.csv`) **chưa được người duyệt**.
- Bộ phân loại embedding nhận ra khía cạnh hiếm còn yếu (recall: lãng mạn 0,32, view 0,41, riêng tư khoảng 0). Phần được LLM gán trực tiếp thì đáng tin hơn.
- 42 quán chưa có tọa độ, nên khoảng cách được tính ở mức trung tính.
- Tính cách mới cải thiện rất nhẹ và cần dữ liệu phản hồi thật. Bản dịch BFI-10 sang tiếng Việt chưa được kiểm định.
- Bộ luật đọc quận / ngân sách không hiểu phủ định ("không phải Quận 10").
- Chưa có `image_score` từ ảnh quán (dự kiến dùng CLIP / SigLIP); đã chừa sẵn cột.
- Dữ liệu review chủ yếu từ 2016–2024.
- Giờ mở cửa chỉ có một khung chung cho mọi ngày (không theo thứ trong tuần); 26 quán chưa có giờ nên được giữ ở mức trung tính.
- Khoảng cách giữa các chặng là đường chim bay; thời gian di chuyển chỉ là ước tính.
- Mỗi lần LLM chọn quán mất khoảng 20–40 giây trên GPU laptop (qwen3:8b, 15 quán).
- **Hướng phát triển:** khi có đủ dữ liệu phản hồi trong `data/feedback/events.jsonl`, thay công thức gộp bằng Learning-to-Rank (LightGBM lambdarank).

---

## 8. Bản đồ mã nguồn

Tất cả nằm trong `src/`.

| File | Vai trò |
|---|---|
| `config.py` | Đường dẫn và tham số |
| `common.py` | Chuẩn hóa chuỗi, mã quán (hash), giá, giờ, category |
| `ratings.py` | Bayes, giới hạn review/ngày, cờ seeding |
| `vector_store.py` | Lưu trữ vector có phiên bản, tráo atomic, chỉ embed doc mới |
| `semantic.py` | bge-m3, hàm `search()` |
| `absa.py` | Prompt ABSA |
| `llm.py` | Điểm duy nhất gọi LLM (AiProvider), làm sạch review chống prompt injection |
| `scoring.py` | Điểm khía cạnh, food / date / couple, ngưỡng hạ dần, nhãn AI `place_tags` |
| `ranker.py` | Lọc cứng (giờ mở cửa, nới dần), TOPSIS, gộp hai người, cold-start |
| `interests.py` | Danh mục 24 sở thích, ma trận quán × sở thích, điểm sở thích chung |
| `personality.py` | Bảng hỏi, hồ sơ, personality_fit, `ProfileStore` (sở thích + quyền chia sẻ) |
| `query_parser.py` | Trích quận / ngân sách / giờ (luật) và mức quan tâm (LLM) |
| `explainer.py` | LLM chọn 3–5 quán + lý do, kiểm tra chống bịa |
| `recommend.py` | Lõi gợi ý: câu hỏi → 15 quán → LLM chọn → kết quả |
| `planner.py` | Plan nhiều chặng + `validate_plan` |
| `ai_service.py` | Hạn mức lượt AI, nhật ký `ai_requests` / `ai_suggestion_results` / `date_plans`, chỉ số (lớp backend gọi) |
| `auth.py` | Tài khoản, băm mật khẩu, khóa tạm, phát / kiểm tra JWT; CLI `run.py taikhoan` |
| `backup.py` | Sao lưu `.zip` (`run.py saoluu`) |
| `feedback.py` | Cập nhật hồ sơ, nhật ký cho Learning-to-Rank |
| `ingest.py` | Nhập dữ liệu mới: staging, upsert, embedding, chấm điểm, nhãn, sở thích |
| `api.py` | Server web (FastAPI): API REST JSON + phục vụ giao diện; `/docs` tự sinh |
| `web/` | Giao diện dùng thử: `index.html`, `style.css`, `app.js` (HTML/JS thuần, không cần build) |
| `app_cli.py`, `profile_cli.py` | Giao diện dòng lệnh: hỏi / plan, hồ sơ |
| `smoke_test.py`, `evaluate.py` | Kiểm tra (19 bài), đánh giá |
| `stage1_clean.py` … `stage7_test_ingest.py` | Các bước xây dựng / demo theo giai đoạn |
