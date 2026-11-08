# Lovespot Social

Mạng xã hội kiểu LinkedIn cho người mê ăn và mê hẹn hò ở TP.HCM. Đây là ứng dụng riêng, chạy độc lập với Couple Assistant: có cổng, cơ sở dữ liệu và tài khoản riêng. Nó dùng lại danh sách 853 quán thật và 24 sở thích của dự án.

| LinkedIn | Lovespot |
|---|---|
| Hồ sơ: chức danh, kinh nghiệm | Hồ sơ: một dòng về gu, quận hay lui tới, **gu ăn uống** (24 sở thích) |
| Kết nối, lời mời | Như LinkedIn: mời, chấp nhận, bỏ qua, gỡ kết nối |
| Trang công ty | **Trang quán** (853 quán thật): theo dõi, điểm review của cộng đồng, bạn bè đã đến |
| Bài viết | Chia sẻ, **review quán** (chấm 1–5 sao) và **check-in**, luôn gắn với quán thật. **Tối đa 4 ảnh** mỗi bài (trình duyệt thu nhỏ ảnh trước khi tải lên). Chọn người xem: mọi người hoặc chỉ kết nối |
| People you may know | **Người cùng gu**: 2 điểm mỗi bạn chung, 1 điểm mỗi sở thích chung, 1 điểm nếu cùng quận. Mỗi gợi ý kèm lý do |
| Thông báo | Lời mời kết nối, chấp nhận, thích, bình luận |

## Chạy

**Cách 1: chạy chung với Couple Assistant (khuyên dùng).** Chạy `python run.py web`, đăng nhập, rồi mở tab **Cộng đồng**.
- Dùng chung tài khoản: lần đầu mở tab, hồ sơ cộng đồng được tạo từ tài khoản Couple Assistant (`@tên` lấy theo mã tài khoản).
- API nằm ở `/social/api/*`. Cần bật đăng nhập (mặc định là bật) thì tab mới hiện.

**Cách 2: chạy riêng.** Lovespot có tài khoản riêng:

```powershell
.venv\Scripts\activate
python social/server.py                 # http://127.0.0.1:8100   (tài liệu API: /docs)
python social/tests/test_api.py         # kiểm thử, dùng CSDL tạm
```

- Dữ liệu nằm trong `social/data/` (gồm `social.db` và khóa ký token). Thư mục này không đưa lên git.
- Biến môi trường:
  - `LOVESPOT_SOCIAL_DATA`: đổi nơi lưu dữ liệu.
  - `LOVESPOT_PLACES_CSV`: đổi file danh sách quán.
  - `LOVESPOT_SOCIAL_REGISTER=off`: tắt tự đăng ký.

## Dữ liệu mẫu (cho giao diện có nội dung khi chưa có người dùng)

```powershell
python social/seed_demo.py          # 12 tài khoản mẫu, khoảng 48 bài, kết nối, lượt thích, bình luận
python social/seed_demo.py --xoa    # xóa sạch, nên chạy trước khi mở cho người dùng thật
```

- Mọi tài khoản mẫu luôn có nhãn **"Tài khoản mẫu"** trên giao diện.
- Nội dung review lấy **nguyên văn từ review thật của chính quán đó** (dữ liệu Foody). Số sao đổi từ điểm của review đó: thang 10 sang 5 sao.
- Không bịa nhận xét về quán thật.
- Ảnh của bài mẫu là **ảnh minh họa** theo loại món (Unsplash, giấy phép miễn phí), không phải ảnh chụp tại quán. Ảnh luôn có nhãn "Ảnh minh họa".

## Cấu trúc

```
server.py                  khởi động FastAPI, phục vụ giao diện
lovespot/config.py         cấu hình, giới hạn độ dài
lovespot/db.py             SQLite: bảng, quan hệ kết nối, thông báo
lovespot/security.py       mật khẩu PBKDF2, JWT, khóa 15 phút sau 5 lần sai
lovespot/catalog.py        24 sở thích (cùng mã với Couple Assistant), đọc danh sách quán, tìm không dấu
lovespot/suggest.py        gợi ý người cùng gu, quán đang được nhắc tới
lovespot/routes_people.py  tài khoản, hồ sơ, kết nối, tìm kiếm, gợi ý
lovespot/routes_posts.py   bài viết, bảng tin, thích, bình luận, trang quán, thông báo
web/                       giao diện JS thuần, phong cách đen trắng giống Couple Assistant
tests/test_api.py          10 nhóm kiểm thử (có cả chế độ dùng chung đăng nhập)
```

## Quyền riêng tư
- Tắt "Hiện gu ăn uống" thì người khác không thấy sở thích của bạn, và chúng cũng không được dùng để gợi ý bạn cho ai.
- Bài "chỉ kết nối" chỉ hiện với bạn và những người đã kết nối với bạn.
- Xóa tài khoản là xóa vĩnh viễn hồ sơ, bài viết, bình luận, lượt thích, kết nối và thông báo.

## Chưa có (nên làm tiếp)
- Nhắn tin riêng.
- Ảnh đại diện.
- Liên kết "cặp đôi" giữa hai hồ sơ.
- Nút "Lên plan hẹn hò cho hai đứa": gọi API `/api/plan` của Couple Assistant với hai hồ sơ.
- Báo cáo nội dung xấu.
