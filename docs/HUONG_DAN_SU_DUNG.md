# Hướng dẫn sử dụng

[← Về README](../README.md)

1. [Cài đặt chi tiết](#1-cài-đặt-chi-tiết)
2. [Dùng qua giao diện web](#2-dùng-qua-giao-diện-web)
3. [Hồ sơ sở thích cá nhân](#3-hồ-sơ-sở-thích-cá-nhân)
4. [Hỏi gợi ý](#4-hỏi-gợi-ý)
5. [Lập plan hẹn hò](#5-lập-plan-hẹn-hò)
6. [Lượt AI và thống kê](#6-lượt-ai-và-thống-kê)
7. [Nhập quán / review mới](#7-nhập-quán--review-mới)
8. [Gắn vào web / app Lovespot (API)](#8-gắn-vào-web--app-lovespot-api)
9. [Xây lại dữ liệu từ đầu](#9-xây-lại-dữ-liệu-từ-đầu)
10. [Xử lý sự cố](#10-xử-lý-sự-cố)

---

## 1. Cài đặt chi tiết

**Yêu cầu:** Windows / macOS / Linux, Python 3.12 trở lên (đã chạy thử trên 3.14), khoảng 8 GB ổ trống, RAM 8 GB trở lên.
GPU NVIDIA giúp nhanh hơn nhưng không bắt buộc.

```powershell
cd CoupleAssistant
python -m venv .venv
.venv\Scripts\activate                 # macOS/Linux: source .venv/bin/activate

# PyTorch, chọn MỘT dòng:
pip install torch --index-url https://download.pytorch.org/whl/cu128   # có GPU NVIDIA
pip install torch --index-url https://download.pytorch.org/whl/cpu     # không có GPU

pip install -r requirements.txt
python run.py kiemtra
```

| Thành phần | Bắt buộc? | Ghi chú |
|---|---|---|
| Model embedding `BAAI/bge-m3` (khoảng 2,3 GB) | Có | Tự tải lần đầu vào `.cache/huggingface/` |
| Ollama + `qwen3:8b` (khoảng 5 GB) | Không, nhưng nên có | Hiểu câu hỏi tốt hơn và viết lời giải thích tự nhiên. Cài ở [ollama.com](https://ollama.com), sau đó chạy `ollama pull qwen3:8b` |

Không có Ollama thì thêm `--no-llm` vào lệnh. Khi đó quận và ngân sách được đọc bằng luật, còn lời giải thích dùng mẫu câu.

---

## 2. Dùng qua giao diện web

```powershell
python run.py web                       # http://127.0.0.1:8000   (thêm --port 8080 để đổi cổng)
```

0. **Đăng nhập:** lần đầu bấm **Đăng ký** (tên đăng nhập + mật khẩu ≥ 8 ký tự). Tài khoản quản trị tạo bằng
   `python run.py taikhoan tao admin --admin`. Sai mật khẩu 5 lần liền thì bị khóa 15 phút.
1. **Tab "Hồ sơ sở thích":** hồ sơ của chính bạn: tên, các sở thích, bật / tắt "Cho AI dùng sở thích của tôi khi người
   đi cùng hỏi", tích ô đồng ý rồi bấm **Lưu hồ sơ**. Nút **Xóa tài khoản** xóa cả tài khoản lẫn hồ sơ.
2. **Tab "Gợi ý quán":** gõ mong muốn (hoặc bấm một câu mẫu), chọn **Người đi cùng**, giờ hẹn, ngân sách, rồi bấm **Gợi ý**.
   Người hỏi luôn là bạn (tài khoản đang đăng nhập).
   - Mỗi quán hiện thành một thẻ: giá, giờ mở cửa, địa chỉ, nhãn AI và lý do.
   - Bấm **Chọn quán này** để ghi nhận lựa chọn; số liệu này dùng cho thống kê và cập nhật hồ sơ.
3. **Tab "Lập plan":** nhập mong muốn, giờ bắt đầu, ngân sách. Kết quả là dòng thời gian các chặng, kèm thời gian di chuyển và
   kết quả kiểm tra (giờ mở cửa, khoảng cách, ngân sách).
4. **Tab "Thống kê":** các chỉ số AI (chỉ tài khoản admin thấy).

- Có AI, mỗi lần gợi ý mất khoảng 20–50 giây. Bỏ tích "Dùng AI" thì có kết quả trong khoảng 1 giây (xếp theo điểm, lý do theo mẫu câu).
- Góc trên bên phải hiện trạng thái: số quán, và AI đang dùng (Ollama / Claude) đã sẵn sàng chưa.
- Server chỉ nghe ở 127.0.0.1. Muốn cho người khác dùng qua Internet: xem **[TRIEN_KHAI.md](TRIEN_KHAI.md)**
  (Cloudflare Tunnel + Access, lịch tự động, sao lưu, báo khi sập — gần như 0đ).
- Chỉ dùng một mình trên máy, không cần đăng nhập: `$env:LOVESPOT_AUTH="off"; python run.py web`.

---

## 3. Hồ sơ sở thích cá nhân

Mỗi người tạo một hồ sơ, bằng tab "Hồ sơ sở thích" trên web hoặc bằng lệnh dưới đây. Hồ sơ chỉ lưu trên máy (`data/profiles/`) và chỉ được tạo khi người đó đồng ý.

```powershell
python run.py hoso tao minh          # hỏi từng bước: đồng ý lưu -> tên -> chọn sở thích bằng số -> chia sẻ? -> tính cách?
python run.py hoso sua minh          # sửa, Enter để giữ nguyên
python run.py hoso xem minh
python run.py hoso ds                # danh sách hồ sơ
python run.py hoso danhmuc           # 24 sở thích có thể chọn
python run.py hoso xoa minh          # xóa vĩnh viễn

# Không hỏi từng bước (dùng cho kịch bản):
python run.py hoso tao lan --ten Lan --so-thich ca_phe,chup_anh,trang_mieng --chia-se --dong-y
```

**24 sở thích, chia 3 nhóm:**
- **Món:** cà phê, trà sữa, lẩu, nướng, Nhật, Hàn, Âu, Thái, Hoa, Việt, chay, hải sản, ăn vặt, tráng miệng.
- **Không khí:** yên tĩnh, lãng mạn, view đẹp, riêng tư, không gian đẹp, chụp ảnh, sôi động, sang trọng, sân vườn.
- **Ngân sách:** giá rẻ.

| Mục trong hồ sơ | Ý nghĩa |
|---|---|
| Sở thích | Quán khớp sở thích được cộng điểm. Sở thích **chung** của hai người được tính gấp đôi |
| `--chia-se` (mặc định TẮT) | Cho phép AI dùng sở thích của bạn khi **người đi cùng** hỏi gợi ý. Tắt thì AI chỉ dùng sở thích của người hỏi và báo rõ điều đó |
| Tính cách (tùy chọn) | Bảng hỏi 14 câu, điều chỉnh nhẹ kết quả |
| Gói AI | `free` 5 lượt/ngày, `plus` 30, `premium` 200 (sửa trong `src/config.py`) |

Độ khớp giữa quán và sở thích dựa trên bằng chứng thật: từ khóa trong tên hoặc loại quán, nhãn món, nhãn AI rút từ review, và tìm kiếm ngữ nghĩa trên review.

---

## 4. Hỏi gợi ý

Trên web: tab "Gợi ý quán". Trên dòng lệnh:

```powershell
python run.py hoi "chỗ ăn tối lãng mạn Quận 3 dưới 800k cho 2 người"            # chế độ khách (dùng thử)
python run.py hoi "tối thứ 7 đi cafe Quận 1 lúc 20h" --nguoi-a minh --nguoi-b lan  # dùng hồ sơ
python run.py hoi "lẩu ấm cúng ngày mưa" --loc-a 10.7769,106.7009 --loc-b 10.8494,106.7537
python run.py hoi                       # hỏi liên tục
```

| Tham số | Ý nghĩa |
|---|---|
| `--nguoi-a`, `--nguoi-b` | Mã hồ sơ của người hỏi và người đi cùng. Có hồ sơ thì dùng sở thích, tính lượt AI và ghi nhật ký |
| `--luc 19:30` | Giờ hẹn: chỉ gợi ý quán **đang mở cửa** lúc đó (hệ thống cũng hiểu "lúc 7 giờ tối", "tối nay") |
| `--loc-a`, `--loc-b` | Vị trí hai người (vĩ độ,kinh độ). Hệ thống ưu tiên quán không quá xa ai |
| `--budget 300000` | Ngân sách mỗi người, dùng khi câu hỏi không nói |
| `--k 3` | Số quán trả về khi không dùng LLM (có LLM thì AI tự chọn 3–5 quán) |
| `--no-llm` | Không dùng Ollama |

**Cách hệ thống chọn quán:**
1. Lọc quận, ngân sách, giờ mở cửa.
2. Chấm điểm và giữ 15 quán.
3. AI chọn 3–5 quán và viết lý do.
4. Code kiểm tra: AI chỉ được chọn quán có trong danh sách. Nếu AI chọn sai hoặc bị lỗi, hệ thống dùng thứ tự chấm điểm.

Nếu không có quán nào khớp, hệ thống **nới dần** điều kiện (ngân sách thêm 50%, mọi quận, bỏ điều kiện giờ) và **báo rõ đã nới gì**.

**Hệ thống hiểu được:**
- **Quận:** "Quận 1", "Q3", "q.10", "Bình Thạnh", "Thủ Đức", "Phú Nhuận"…
- **Ngân sách:** "dưới 400k", "300.000đ/người", "1tr cho 2 người", "mỗi người 250 nghìn".
  Nếu không nói rõ cho 1 hay 2 người, hệ thống hiểu là **tổng cho 2 người** và báo giả định này.
- **Giờ:** "19h30", "7 giờ tối", "lúc 20h", "tối nay", "trưa".
- **Mong muốn khác:** món, không khí, dịp (lãng mạn, yên tĩnh, view, kỷ niệm, sinh nhật…). Có Ollama thì còn tách được
  ý riêng của từng người, ví dụ "mình thích yên tĩnh, bạn gái mê đồ ăn ngon".

**Nhãn đi kèm mỗi quán:**
- "vừa ngon vừa hợp hẹn hò"
- "đúng yêu cầu, không gian hẹn hò chưa nổi bật"
- "đạt ở ngưỡng đã hạ (đánh đổi nhẹ)": xuất hiện khi khu vực hoặc ngân sách quá hẹp nên phải nới tiêu chí
- Nhãn AI rút từ review, ví dụ "lãng mạn", "yên tĩnh", "view đẹp", "ồn ào"

---

## 5. Lập plan hẹn hò

Trên web: tab "Lập plan". Trên dòng lệnh:

```powershell
python run.py plan "hẹn hò yên tĩnh" --luc 18:30 --ngan-sach 350000 --nguoi-a minh --nguoi-b lan
python run.py plan "tối nay Quận 3" --no-llm
```

Plan mặc định có 2 chặng: **ăn tối (90 phút) → cà phê / tráng miệng (60 phút)**. Muốn đổi chặng, sửa `PLAN_STOPS` trong `src/config.py`.

Hệ thống xếp plan bằng code, rồi **tự kiểm tra**:
- từng quán mở cửa đúng giờ của chặng đó;
- hai chặng liền nhau cách nhau không quá 5 km;
- tổng chi phí ước tính không vượt ngân sách.

Lỗi thì hệ thống tự đổi sang quán khác; vẫn lỗi thì báo ⚠ để bạn tự chỉnh. AI chỉ viết ghi chú cho từng chặng.

---

## 6. Lượt AI và thống kê

- Mỗi lần hỏi hoặc lập plan **có dùng hồ sơ** thì tính 1 lượt. Lượt reset lúc 0 giờ giờ Việt Nam.
- **Không tính lượt** khi hệ thống lỗi hoặc không tìm ra quán nào.
- Hết lượt thì hệ thống thông báo và đề nghị nâng gói.

```powershell
python run.py thongke
```

Lệnh này in các chỉ số: tỷ lệ chọn quán AI gợi ý, tỷ lệ dùng được LLM, số mã quán bịa bị chặn, tỷ lệ phải bù bằng thứ tự chấm điểm,
độ trễ (trung bình / p95), token mỗi lần, độ trùng giữa lựa chọn của AI và thứ tự chấm điểm, và các quán được gợi ý nhiều nhất.

Nhật ký nằm trong `data/ai_log/` (`ai_requests.jsonl`, `ai_suggestion_results.jsonl`, `date_plans.jsonl`), đặt tên theo bảng trong
tài liệu thiết kế. Nhật ký chỉ lưu mã người dùng đã băm.

---

## 7. Nhập quán / review mới

1. Chép thư mục mẫu `data/staging/_template/` thành thư mục mới, ví dụ `data/staging/dot_thang11/`.
2. Điền các file CSV (lưu dạng UTF-8):

**`restaurants.csv`**

| Cột | Bắt buộc | Ví dụ |
|---|---|---|
| `name` | ✅ | Nhà hàng ABC |
| `address` | ✅ | 12 Lê Lợi, Phường Bến Nghé, Quận 1, TP. HCM |
| `latitude`, `longitude` | nên có | 10.7769, 106.7009 |
| `price_min`, `price_max` hoặc `price_text` | nên có | 50000, 200000 hoặc "50.000đ - 200.000đ" |
| `category` | nên có | Nhà hàng, Món Âu |
| `opening_hours` | | 10:00 - 22:00 |
| `rating`, `review_count` | | điểm tổng hợp của nguồn (thang 10) |
| `website`, `source`, `source_url` | | |

**`reviews.csv`**

| Cột | Bắt buộc | Ghi chú |
|---|---|---|
| `review_text` | ✅ | |
| `restaurant_id` **hoặc** `restaurant_name` + `restaurant_address` | ✅ | tên và địa chỉ ghi giống `restaurants.csv` |
| `rating`, `rating_scale` | | `rating_scale` là 5 hoặc 10 (mặc định 10) |
| `review_date`, `author`, `source`, `source_url` | | |

3. Chạy lệnh:

```powershell
python run.py nhap data/staging/dot_thang11 --dry-run    # chỉ kiểm tra, chưa ghi
python run.py nhap data/staging/dot_thang11              # nhập thật
```

**Hệ thống tự bảo vệ dữ liệu:**
- Dòng lỗi (ngoài TP.HCM, thiếu tên, review rỗng, quán không tồn tại) bị bỏ qua và ghi vào `rejected.csv`.
- Nếu hơn 30% số dòng bị lỗi thì **hủy cả đợt**, không ghi gì.
- Chạy lại cùng đợt **không bị nhân đôi**.
- Có backup tự động trong `data/backup/`.
- Điểm của quán cũ giữ nguyên. Quán mới được cộng chút điểm "quán mới" trong 60 ngày đầu.
- Nhãn AI và độ khớp sở thích của quán mới được tính tự động.

Nên chạy `python run.py tinhlai` mỗi tuần (có thể đặt lịch bằng Task Scheduler) để tính lại điểm trên toàn bộ dữ liệu.

---

## 8. Gắn vào web / app Lovespot (API)

Chạy `python run.py web`. Backend Lovespot (viết bằng ngôn ngữ nào cũng được) gọi API JSON dưới đây.
Mọi endpoint đều có thể thử trực tiếp trên trình duyệt tại **http://127.0.0.1:8000/docs**.

| Phương thức | Đường dẫn | Việc làm |
|---|---|---|
| GET | `/api/health` | Trạng thái: số quán, LLM đang dùng, có bắt đăng nhập không (công khai, cho dịch vụ ping) |
| POST | `/api/auth/register` · `/api/auth/login` | Đăng ký / đăng nhập → `{"token": "..."}` (hạn 7 ngày) |
| GET / DELETE | `/api/auth/me` | Tài khoản hiện tại / xóa tài khoản + hồ sơ của mình |
| GET | `/api/interests` | Danh mục 24 sở thích (`id`, `label`, `group`) |
| GET | `/api/questions` | 14 câu bảng hỏi tính cách (tùy chọn) |
| GET | `/api/profiles` | Danh sách hồ sơ (mã + tên, để chọn người đi cùng) |
| GET / PUT / DELETE | `/api/profiles/{user_id}` | Hồ sơ **của chính mình** (admin: mọi hồ sơ). PUT bắt buộc `consent: true`; chỉ admin đổi được `plan` |
| POST | `/api/suggest` | Gợi ý quán; người hỏi = người đăng nhập, tính lượt AI |
| POST | `/api/plan` | Lập plan hẹn hò nhiều chặng |
| POST | `/api/choose` | Chọn quán từ gợi ý (ghi `chosen_at`, cập nhật hồ sơ) |
| GET | `/api/metrics` | Chỉ số AI (mục 5.3) — chỉ admin |

Mọi endpoint trừ health / interests / questions / register / login cần header `Authorization: Bearer <token>`.

**Ví dụ:**

```http
POST /api/auth/login
{"user_id": "minh", "password": "********"}         -> {"token": "eyJ...", "user_id": "minh", "role": "member"}

PUT /api/profiles/minh                               (kèm Authorization: Bearer eyJ...)
{"consent": true, "display_name": "Minh", "interests": ["ca_phe", "yen_tinh"], "share_interests_with_partner": false}

POST /api/suggest
{"query": "tối thứ 7 đi cafe Quận 1", "user_b": "lan", "at_time": "20:00",
 "budget": 150000, "loc_a": [10.7769, 106.7009], "loc_b": [10.7626, 106.6822], "use_llm": true}

-> {"status": "success", "request_id": "b2b5c77e...", "quota": {"used": 1, "limit": 5},
    "parsed": {...}, "notes": [...], "common_interests": ["Cà phê"],
    "items": [{"rank": 1, "restaurant_id": "r_...", "name": "...", "price_min": 50000, "tags": ["yên tĩnh", ...],
               "explanation": "...", "explanation_source": "llm", "score_breakdown": {...}}, ...]}

POST /api/choose
{"request_id": "b2b5c77e...", "place_id": "r_..."}
```

Mã lỗi: 401 chưa đăng nhập / token hết hạn; 403 không có quyền (hồ sơ người khác, chưa đồng ý, xem thống kê);
422 dữ liệu sai định dạng (giờ `25:99`, sở thích ngoài danh mục, mật khẩu < 8 ký tự); 429 sai mật khẩu quá 5 lần.

**Gọi trực tiếp từ Python** (cùng máy, không qua HTTP): `from ai_service import suggest, plan, choose_place, metrics`.
Các hàm này có cùng tham số và kết quả như API.

Trường `status` trong kết quả:

| `status` | Ý nghĩa |
|---|---|
| `success` | Có kết quả trong `items` (plan: `stops`) |
| `no_result` | Không có quán phù hợp (không tính lượt) |
| `quota_exceeded` | Hết lượt; `message` đề nghị nâng gói |
| `no_profile` | Người hỏi chưa có hồ sơ |
| `error` | Hệ thống lỗi (không tính lượt) |

**Các trường của mỗi quán:** `rank, restaurant_id, name, district, address, opening_hours, price_min, price_max,
group_score, tradeoff_label, tags, explanation, explanation_source (llm/template), llm_rank, score_breakdown`.

Không cần hạn mức và nhật ký (ví dụ chế độ khách) thì gọi thẳng `recommend.recommend(query, Person(...), Person(...), profiles=...)`.

**Phản hồi:**
- `choose_place(...)` ghi `chosen_at`, và nếu hồ sơ có phần tính cách thì cập nhật luôn.
- `feedback.log_event(...)` ghi sự kiện để sau này huấn luyện Learning-to-Rank.

---

## 9. Xây lại dữ liệu từ đầu

Chỉ cần khi thay đổi dữ liệu gốc trong `data/raw/` hoặc chỉnh thuật toán.

| Lệnh | Việc làm | Thời gian |
|---|---|---|
| `python run.py xaylai` | Làm sạch, tạo embedding, tính điểm, nhãn AI, tính chất quán, ma trận sở thích | khoảng 4 phút (GPU) / 30+ phút (CPU) |
| `python run.py gannhan` | AI gán nhãn 8 khía cạnh cho review (cần Ollama) | khoảng 2 giờ |
| `python run.py danhgia` | Chấm lại chất lượng | khoảng 20 phút (cần Ollama) |

Thứ tự đầy đủ khi làm lại từ đầu: `xaylai`, rồi `gannhan`, rồi `xaylai`, rồi `danhgia`.

---

## 10. Xử lý sự cố

| Hiện tượng | Cách xử lý |
|---|---|
| `LLM không trích được … -> dùng luật` | Ollama chưa chạy: mở ứng dụng Ollama hoặc chạy `ollama serve`. Hoặc thêm `--no-llm` |
| Chương trình tự tắt (mã `-1073741819`) khi nạp model | Thiếu RAM / VRAM (đang chơi game, mở nhiều ứng dụng). Đóng bớt ứng dụng, hoặc chạy `set EMBED_DEVICE=cpu` trước lệnh |
| Lần đầu chạy rất lâu | Đang tải model khoảng 2,3 GB, chỉ một lần |
| `Chưa có index` | Chạy `python run.py xaylai` |
| `ModuleNotFoundError` | Chưa kích hoạt môi trường: chạy `.venv\Scripts\activate` rồi `pip install -r requirements.txt` |
| Trang web báo "không kết nối được máy chủ" | Server chưa chạy hoặc đã tắt: chạy lại `python run.py web` |
| `address already in use` / cổng 8000 bận | Đổi cổng: `python run.py web --port 8080` |
| Bấm "Gợi ý" chờ rất lâu | Có AI mất 20–50 giây là bình thường. Nếu lâu hơn, kiểm tra Ollama, hoặc bỏ tích "Dùng AI" |
| Ổ C đầy | Model lưu trong `.cache/` của thư mục này. Với Ollama, đặt biến `OLLAMA_MODELS` sang ổ khác |
| Lỗi font tiếng Việt trên terminal | Chạy `chcp 65001` trước, hoặc dùng Windows Terminal |
