import React from 'react';
import { Heart } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-obsidian border-t border-charcoal py-16 text-xs text-ash">
      <div className="max-w-[1200px] mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-8">
        <div>
          <div className="flex items-center gap-2 text-paper font-semibold tracking-wider uppercase mb-2">
            <span>Couple Assistant</span>
            <span className="text-ash">•</span>
            <span className="text-ash font-normal">TP. Hồ Chí Minh</span>
          </div>
          <p className="text-ash/80 max-w-md leading-relaxed">
            Nền tảng gợi ý quán hẹn hò & lập lịch trình tối ưu cho cặp đôi. Công thức chấm điểm kép food_score & date_score, thuật toán cân bằng TOPSIS từ 853 quán và 20.924 review thực tế.
          </p>
        </div>

        <div className="flex flex-col md:items-end gap-2 text-center md:text-right">
          <div className="flex items-center gap-6 text-paper font-medium uppercase tracking-wider text-[11px]">
            <a href="#hero" className="hover:text-fog transition-colors">Trang Chủ</a>
            <a href="#recommend" className="hover:text-fog transition-colors">Gợi Ý Quán</a>
            <a href="#itinerary" className="hover:text-fog transition-colors">Lộ Trình</a>
            <a href="#privacy" className="hover:text-fog transition-colors">Quyền Riêng Tư</a>
          </div>
          <p className="text-ash/60 text-[10px] tracking-wide mt-2">
            © 2026 Couple Assistant. Thiết kế theo phong cách Cinematic Monochrome Gallery.
          </p>
        </div>
      </div>
    </footer>
  );
};
