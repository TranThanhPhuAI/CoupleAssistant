# 💑 Couple Assistant

**Gợi ý quán ăn / cafe ở TP.HCM cho cặp đôi đi hẹn hò.** Quán được chọn phải vừa ngon vừa hợp hẹn hò, và cân bằng sở thích của cả hai người.

Bạn hỏi bằng tiếng Việt bình thường, hệ thống trả về 3–5 quán kèm lý do. Lý do lấy từ review thật, không bịa.
Có giao diện web để dùng ngay, và API JSON để gắn vào web / app Lovespot.

Dữ liệu kèm theo: **853 quán** và **20.924 review** (Foody / ShopeeFood). Dữ liệu đã xử lý sẵn, cài xong là dùng được ngay.

---

## Bắt đầu trong 3 bước

**1. Cài đặt** (cần Python 3.12 trở lên)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install torch --index-url https://download.pytorch.org/whl/cu128    # máy không có GPU NVIDIA: thay cu128 bằng cpu
pip install -r requirements.txt
```

**2. Kiểm tra**

```powershell
python run.py kiemtra --quick
```

Lần đầu chạy, máy sẽ tải model khoảng 2,3 GB. Thấy "ĐẠT" ở mọi dòng là xong.

**3. Mở giao diện web**

```powershell
python run.py web
```

Mở trình duyệt vào **http://127.0.0.1:8000**, bấm **Đăng ký** để tạo tài khoản (tài khoản quản trị:
`python run.py taikhoan tao admin --admin`). Giao diện có 4 tab:

| Tab | Làm gì |
|---|---|
| **Gợi ý quán** | Gõ mong muốn, chọn người đi cùng, giờ hẹn, ngân sách. Kết quả hiện thành thẻ quán kèm lý do, nhãn và nút "Chọn quán này" |
| **Lập plan** | Lịch trình ăn tối → cà phê theo dòng thời gian, đã kiểm tra giờ mở cửa, khoảng cách, ngân sách |
| **Hồ sơ sở thích** | Hồ sơ của bạn: tích chọn sở thích, bật / tắt chia sẻ với người đi cùng, xóa tài khoản |
| **Cộng đồng** | Mạng xã hội Lovespot (kiểu LinkedIn): hồ sơ gu ăn uống, kết nối, review và check-in quán thật, gợi ý người cùng gu. Dùng chung tài khoản, xem `social/README.md` |
| **Thống kê** | (chỉ admin) Tỷ lệ chọn quán AI gợi ý, số quán bịa bị chặn, độ trễ |
| **Phân quyền** | (chỉ admin) Danh sách tài khoản: đổi vai trò admin / thành viên, đổi gói AI, đặt lại mật khẩu (tự gỡ khóa), xóa tài khoản |

> 💡 **Nên cài thêm [Ollama](https://ollama.com)** rồi chạy `ollama pull qwen3:8b` để AI chọn quán và viết lý do.
> Không có Ollama: đặt `ANTHROPIC_API_KEY` để dùng Claude Haiku thay thế, hoặc bỏ tích "Dùng AI" (xếp theo điểm, lý do theo mẫu câu).

**Cho người khác dùng qua Internet (máy nhà + Cloudflare, gần như 0đ):** xem `docs/TRIEN_KHAI.md`.

**Gắn vào web / app Lovespot:** backend gọi API JSON (`POST /api/suggest`, `/api/plan`, `PUT /api/profiles/{id}`…).
Danh sách đầy đủ có thể thử trực tiếp ở **http://127.0.0.1:8000/docs**; chi tiết trong `docs/HUONG_DAN_SU_DUNG.md`.

---

## Các lệnh (dòng lệnh, cho người phát triển)

| Lệnh | Công dụng |
|---|---|
| `python run.py web` | Giao diện web + API (http://127.0.0.1:8000) |
| `python run.py taikhoan tao <tên> [--admin]` | Tạo tài khoản web (`ds` xem, `doimk` đổi mật khẩu, `quyen <tên> admin` nâng quyền, `xoa` xóa) |
| `python run.py saoluu` | Sao lưu dữ liệu ra `.zip` (giữ 14 bản gần nhất) |
| `python run.py hoso tao <tên>` | Tạo hồ sơ sở thích trên terminal (sửa: `hoso sua`, xem: `hoso xem`, xóa: `hoso xoa`) |
| `python run.py hoi "..."` | Hỏi gợi ý quán (thêm `--nguoi-a`, `--nguoi-b` để dùng hồ sơ) |
| `python run.py plan "..."` | Lập plan hẹn hò nhiều chặng |
| `python run.py thongke` | Chỉ số AI |
| `python run.py kiemtra` | Kiểm tra toàn bộ hệ thống (20 bài) |
| `python run.py nhap data/staging/<đợt>` | Nhập quán / review mới (mẫu file ở `data/staging/_template/`; `--tat-ca`: mọi đợt mới) |
| `python run.py tinhlai` | Tính lại điểm toàn bộ (nên chạy hằng tuần) |
| `python run.py danhgia` | Đo chất lượng gợi ý |
| `python run.py demo` | Xem demo từng phần |
| `python run.py` | Xem tất cả lệnh |

**Mẹo hỏi:** nói rõ quận ("Quận 3", "Bình Thạnh"), ngân sách ("200k/người", "1tr cho 2 người"), không khí ("yên tĩnh", "view đẹp") và món ("lẩu", "sushi").
Muốn tính khoảng cách cho từng người thì thêm vị trí: `--loc-a 10.77,106.70 --loc-b 10.85,106.75`.

---

## Trong thư mục có gì

```
CoupleAssistant/
├── README.md          ← bạn đang đọc
├── run.py             ← chạy mọi thứ từ đây
├── requirements.txt
├── docs/
│   ├── HUONG_DAN_SU_DUNG.md   ← hướng dẫn chi tiết, API, xử lý sự cố
│   ├── TRIEN_KHAI.md          ← đưa lên Internet: Cloudflare, lịch tự động, sao lưu
│   └── KY_THUAT.md            ← cách hệ thống chấm điểm, kết quả đánh giá, cấu hình
├── data/              ← dữ liệu quán, review, điểm đã tính sẵn (data/auth = tài khoản, không chia sẻ)
├── src/               ← mã nguồn (src/api.py = server, src/web/ = giao diện)
├── social/            ← mạng xã hội Lovespot (tab Cộng đồng; chạy riêng được: python social/server.py)
└── tools/             ← trien_khai.ps1 (Cloudflare Tunnel + lịch Windows), script phụ
```

---

## Điểm nổi bật

- **Công bằng cho hai người:** chấm điểm riêng cho từng người (vị trí, ngân sách, ưu tiên, sở thích), rồi chọn quán mà không ai phải chịu thiệt quá nhiều.
- **"Vừa ngon vừa hợp hẹn hò":** AI đọc review để đánh giá 8 khía cạnh: món ăn, không gian, yên tĩnh, lãng mạn, view, riêng tư, phục vụ, giá.
- **Sở thích cá nhân:** 24 sở thích (món, không khí, ngân sách). Sở thích chung của hai người được ưu tiên.
- **Plan hẹn hò:** xếp ăn tối → cà phê, code tự kiểm tra giờ mở cửa, khoảng cách và tổng tiền.
- **Lọc trước, AI chọn sau, code kiểm tra cuối:** LLM chỉ được chọn trong danh sách quán thật; chọn sai hoặc LLM lỗi thì dùng thứ tự chấm điểm.
- **Không bịa, chống chèn lệnh:** lời giải thích chỉ dùng dữ liệu thật; review được làm sạch trước khi đưa vào AI.
- **Chống review ảo:** phát hiện quán "bơm" điểm 10 hàng loạt.
- **Tôn trọng riêng tư:** hồ sơ chỉ lưu khi đồng ý, xóa được. Sở thích chỉ được dùng cho người kia khi bạn bật chia sẻ (mặc định tắt).
- **Hiệu quả đã đo:** chất lượng gợi ý (NDCG@10) đạt **0,76**, so với 0,39 nếu chỉ xếp theo rating; AI chọn quán tốt hơn chỉ dùng công thức (NDCG@3 0,83 so với 0,70). Xem `docs/KY_THUAT.md`.

---

*Dữ liệu: Foody / ShopeeFood Vietnam, dùng cho mục đích học tập và nghiên cứu. Review chủ yếu từ 2016–2024, nên quán có thể đã thay đổi.*
