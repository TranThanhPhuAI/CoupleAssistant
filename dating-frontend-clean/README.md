# Couple Assistant — Frontend Prototype

Ứng dụng web đề xuất địa điểm hẹn hò và lập lịch trình lãng mạn tại TP.HCM (AI Date Recommendation & Itinerary Planner).

---

## 🛠️ Công Nghệ (Tech Stack)

- **Core**: React 19 + TypeScript + Vite
- **Styling**: Tailwind CSS v4
- **Animation & Motion**: GSAP 3 + ScrollTrigger + Lenis Smooth Scroll + Motion
- **Icons**: Lucide React
- **Design Tokens**: Xem chi tiết tại [DESIGN.md](./DESIGN.md)

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Ứng Dụng

### 1. Cài đặt dependencies
Yêu cầu Node.js phiên bản 18 trở lên (khuyến nghị Node 20+):
```bash
npm install
```

### 2. Khởi chạy môi trường phát triển (Local Development)
```bash
npm run dev
```
Truy cập ứng dụng tại: `http://localhost:5173/`

### 3. Build kiểm tra Production
```bash
npm run build
```

### 4. Xem trước bản build Production
```bash
npm run preview
```

---

## 📁 Cấu Trúc Thư Mục

```
.
├── public/                # Media tĩnh (video nền Hero, ảnh mockup độ phân giải cao)
├── src/                   # Toàn bộ mã nguồn giao diện, components, hooks, utils
│   ├── assets/            # Static assets
│   ├── components/        # UI components (Hero, Navbar, Restaurant Details, Layout...)
│   ├── data/              # Mock data (danh sách quán, reviews, tags)
│   ├── hooks/             # Custom React hooks (Smooth scroll, viewport, animation)
│   ├── types/             # TypeScript definitions
│   ├── utils/             # Helper functions
│   ├── App.tsx            # Main application root
│   ├── index.css          # Design system CSS tokens & styles
│   └── main.tsx           # Entry point
├── index.html             # HTML Shell (Google Fonts: Plus Jakarta Sans, Playfair Display)
├── package.json           # Dependencies và scripts
├── tsconfig.json          # Cấu hình TypeScript
├── vercel.json            # Cấu hình SPA rewrites & cache headers cho Vercel
├── vite.config.ts         # Cấu hình Vite & Tailwind v4
├── DESIGN.md              # Luxury Editorial Design System Tokens
└── README.md              # Tài liệu hướng dẫn phát triển
```
