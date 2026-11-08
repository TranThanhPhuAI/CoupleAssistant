# Triển khai trên máy nhà + Cloudflare (gần như 0đ)

```
Người dùng ──HTTPS──> Cloudflare (DNS + HTTPS + Access chặn người lạ)
                          │  Tunnel (máy nhà không mở cổng router)
                          ▼
              Máy Windows: 127.0.0.1:8000  python run.py web  (đăng nhập JWT)
                 ├─ model bge-m3 + index trong RAM
                 ├─ LLM: Ollama qwen3:8b  ──(tắt / máy yếu)──> Claude Haiku (API, tùy chọn)
                 ├─ data\  (quán, hồ sơ, tài khoản, nhật ký AI)
                 └─ Task Scheduler: sao lưu 02:00, nhập quán mới 02:30, tính lại Chủ nhật 03:00
```

Chi phí: Cloudflare gói Free, UptimeRobot gói Free, điện máy nhà. Claude Haiku chỉ tốn tiền khi bật (vài USD/tháng với lượng nhỏ).

## Bước 1. Tài khoản quản trị

```powershell
python run.py taikhoan tao admin --admin      # nhập mật khẩu (≥ 8 ký tự), không hiện trên màn hình
python run.py taikhoan ds                      # xem danh sách
python run.py taikhoan doimk admin             # đổi mật khẩu
```

Người dùng khác tự bấm **Đăng ký** trên web. Muốn tắt đăng ký (chỉ admin tạo tài khoản): `setx LOVESPOT_REGISTER off` (rồi chạy lại `-CaiLich` ở bước 4).
Khóa ký token nằm trong `data\auth\` — không gửi thư mục này cho ai.

## Bước 2. Cloudflare Tunnel

Tên miền phải đang dùng DNS của Cloudflare. Mở PowerShell **Run as administrator** tại thư mục dự án:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\tools\trien_khai.ps1 -Tunnel hen.tenmien.com
```

Script cài `cloudflared`, mở trình duyệt để bạn đăng nhập Cloudflare (1 lần), tạo tunnel `couple-assistant`,
trỏ `hen.tenmien.com` về `http://127.0.0.1:8000`. Server chỉ nghe ở 127.0.0.1 nên không ai vào thẳng được máy.

## Bước 3. Cloudflare Access (lớp khóa thứ hai)

Trên [one.dash.cloudflare.com](https://one.dash.cloudflare.com) → **Access → Applications → Add → Self-hosted**:

| Ứng dụng | Domain | Policy |
|---|---|---|
| `Couple Assistant` | `hen.tenmien.com` | **Allow** — Emails: email của bạn và người được mời (đăng nhập bằng mã gửi email) |
| `Health check` | `hen.tenmien.com/api/health` | **Bypass** — Everyone |

Ứng dụng thứ hai bắt buộc phải có: nếu thiếu, dịch vụ ping ở bước 5 bị Access chặn và luôn báo "sập".
`/api/health` chỉ trả số quán và trạng thái, không có dữ liệu cá nhân.

## Bước 4. Lịch chạy tự động

```powershell
.\tools\trien_khai.ps1 -CaiLich          # thêm -CPU nếu hay chơi game (model embedding chạy CPU, nhường GPU)
.\tools\trien_khai.ps1                   # xem trạng thái + server có phản hồi không
.\tools\trien_khai.ps1 -GoLich           # gỡ hết
```

| Tác vụ | Khi nào | Việc |
|---|---|---|
| Web, Ollama, Tunnel | Khi bật máy (chưa cần đăng nhập Windows), tự chạy lại nếu dừng | Server, LLM, đường hầm |
| SaoLuu | 02:00 hằng ngày | `run.py saoluu` → `.zip`, giữ 14 bản gần nhất |
| NhapMoi | 02:30 hằng ngày | `run.py nhap --tat-ca`: nhập mọi thư mục mới trong `data\staging\`, xong thì đánh dấu `.done` |
| TinhLai | 03:00 Chủ nhật | `run.py tinhlai`: tính lại tham số chấm điểm |

Server tự nạp lại dữ liệu sau khi nhập / tính lại, không cần khởi động lại. Log ở `data\logs\`.

**Sao lưu ra ngoài máy:** trỏ nơi lưu sang thư mục OneDrive / Google Drive / ổ ngoài, rồi chạy lại `-CaiLich`:
`setx LOVESPOT_BACKUP_DIR "D:\OneDrive\CoupleAssistant_backup"`. Khôi phục: giải nén file `.zip` vào thư mục dự án.

## Bước 5. Báo khi sập (miễn phí)

[UptimeRobot](https://uptimerobot.com) → **New monitor → HTTP(s)** → URL `https://hen.tenmien.com/api/health`,
5 phút/lần → nhận email khi máy tắt, mất mạng hoặc server lỗi.

## Bước 6. Claude Haiku dự phòng (tùy chọn)

Khi Ollama tắt hoặc máy đang bận (chơi game), AI tự chuyển sang Claude Haiku nếu có khóa API:

```powershell
setx ANTHROPIC_API_KEY "sk-ant-..."      # lấy ở console.anthropic.com
setx LLM_PROVIDER auto                   # auto (mặc định): Ollama trước, Claude khi Ollama không chạy
                                         # anthropic: luôn dùng Claude (máy yếu)   ollama: chỉ dùng local
```

Chạy lại `-CaiLich` sau khi đổi biến. Lưu ý: với Claude, câu hỏi + review của quán được gửi tới Anthropic
(hồ sơ không bị gửi; chỉ gửi cờ "hợp cả hai" của từng quán và tên sở thích liên quan). Trạng thái hiện ở góc phải trang web và trong `/api/health`.

## Tùy chọn: đưa giao diện lên Vercel

Vercel chỉ chứa **giao diện**. Backend (AI, model khoảng 2,3 GB, dữ liệu) vẫn chạy trên máy nhà. Vercel và các gói miễn phí của Render / Railway không đủ dung lượng và RAM cho phần này.

1. Làm xong bước 2 (Tunnel). Server trên máy nhà phải mở được qua `https://hen.tenmien.com`.
2. **Bỏ Cloudflare Access** của tên miền backend, hoặc thêm Bypass cho `/api/*`, `/social/api/*` và `/docs`. Lý do: Vercel chuyển tiếp yêu cầu từ máy chủ của nó, không đăng nhập Access thay người dùng được. Bảo vệ lúc này là đăng nhập của chính ứng dụng (mật khẩu + JWT).
3. Đóng gói, chỉ lấy file giao diện (khoảng 8 MB), không có dữ liệu hay khóa:
   ```powershell
   python tools/vercel_build.py https://hen.tenmien.com     # -> dist/vercel/
   ```
4. Vào vercel.com, chọn **Add New → Project**, kéo thả **thư mục `dist/vercel`** (không phải cả thư mục dự án). Framework: **Other**, không có Build Command.

Vercel chuyển tiếp `/api/*`, `/social/api/*`, `/docs` về backend, nên trình duyệt chỉ thấy một tên miền: đăng nhập và tab Cộng đồng chạy như cũ. Đổi tên miền backend thì chạy lại bước 3 rồi tải lên lại.
Lưu ý: gợi ý có AI mất 20–50 giây. Nếu Vercel báo hết thời gian chờ, hãy bỏ tích "Dùng AI" hoặc dùng Claude Haiku (bước 6) cho nhanh hơn.

## Kiểm tra sau khi xong

1. `https://hen.tenmien.com` → trang Cloudflare Access hỏi email → trang đăng nhập Couple Assistant.
2. Đăng nhập `admin` → tab **Thống kê** xuất hiện (chỉ admin thấy).
3. UptimeRobot báo **Up**.

| Sự cố | Cách xử lý |
|---|---|
| Web báo 502 / "Bad gateway" | Server chưa chạy: `.\tools\trien_khai.ps1` xem trạng thái, đọc `data\logs\web.log` |
| Error 1033 (Cloudflare) | Tunnel chưa chạy: xem `data\logs\tunnel.log` |
| Đăng nhập báo khóa 15 phút | Sai mật khẩu 5 lần liền; chờ 15 phút. Quên mật khẩu: admin chạy `run.py taikhoan doimk <tên>` |
| Mọi người bị đăng xuất | Khóa ký `data\auth\jwt_secret` bị xóa / đổi — đăng nhập lại là được |
