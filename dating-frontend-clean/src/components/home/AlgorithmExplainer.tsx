import React from 'react';
import { Scale, Utensils, Heart, ShieldCheck, Zap } from 'lucide-react';

export const AlgorithmExplainer: React.FC = () => {
  return (
    <section className="bg-obsidian py-24 border-b border-charcoal">
      <div className="max-w-[1200px] mx-auto px-6">
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto mb-20">
          <p className="text-xs uppercase tracking-widest text-ash mb-3">Hệ Thống Độc Bản</p>
          <h2 className="font-display-clarkson text-3xl sm:text-5xl text-paper tracking-tighter mb-4">
            VỪA NGON VỪA HỢP HẸN HÒ
          </h2>
          <p className="text-sm text-ash leading-relaxed">
            Hầu hết các ứng dụng ẩm thực chỉ chấm điểm đồ ăn hoặc chỉ xếp hạng theo review ngẫu nhiên.
            Couple Assistant giải quyết tận gốc mâu thuẫn sở thích của hai người.
          </p>
        </div>

        {/* 3 Pillar Cards - 8px radius according to DESIGN.md */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Pillar 1 */}
          <div className="border border-charcoal bg-charcoal/20 p-8 rounded-[8px] flex flex-col justify-between hover:border-white/40 transition-colors">
            <div>
              <div className="w-10 h-10 bg-white/10 flex items-center justify-center mb-6">
                <Utensils className="w-5 h-5 text-paper" />
              </div>
              <h3 className="font-display-clarkson text-2xl text-paper tracking-tight mb-2">
                Hệ Thống Chấm Điểm Kép
              </h3>
              <p className="text-xs text-ash leading-relaxed mb-6">
                Mỗi quán có hai chỉ số độc lập: <span className="text-paper">food_score</span> (chất lượng món) và{' '}
                <span className="text-paper">date_score</span> (lãng mạn, yên tĩnh, view, riêng tư). Chỉ giữ quán đạt chuẩn cả hai:
              </p>
            </div>
            <div className="bg-obsidian border border-charcoal p-4 text-xs font-mono text-fog">
              couple_score = food<sup>0.5</sup> × date<sup>0.5</sup>
              <div className="text-[10px] text-ash mt-1">Điều kiện: food ≥ 0.55 & date ≥ 0.50</div>
            </div>
          </div>

          {/* Pillar 2 */}
          <div className="border border-charcoal bg-charcoal/20 p-8 rounded-[8px] flex flex-col justify-between hover:border-white/40 transition-colors">
            <div>
              <div className="w-10 h-10 bg-white/10 flex items-center justify-center mb-6">
                <Scale className="w-5 h-5 text-paper" />
              </div>
              <h3 className="font-display-clarkson text-2xl text-paper tracking-tight mb-2">
                Công Bằng Cho Cả Hai (TOPSIS)
              </h3>
              <p className="text-xs text-ash leading-relaxed mb-6">
                Xếp hạng riêng cho từng người theo vị trí, ngân sách và ưu tiên cá nhân, sau đó gộp điểm bằng công thức công bằng:
              </p>
            </div>
            <div className="bg-obsidian border border-charcoal p-4 text-xs font-mono text-fog">
              Điểm gộp = 0.5 × TB + 0.5 × min(A, B)
              <div className="text-[10px] text-ash mt-1">Đảm bảo người kém hài lòng hơn không bị thiệt</div>
            </div>
          </div>

          {/* Pillar 3 */}
          <div className="border border-charcoal bg-charcoal/20 p-8 rounded-[8px] flex flex-col justify-between hover:border-white/40 transition-colors">
            <div>
              <div className="w-10 h-10 bg-white/10 flex items-center justify-center mb-6">
                <ShieldCheck className="w-5 h-5 text-paper" />
              </div>
              <h3 className="font-display-clarkson text-2xl text-paper tracking-tight mb-2">
                Chống Ảo & Không Bịa Đặt
              </h3>
              <p className="text-xs text-ash leading-relaxed mb-6">
                Áp dụng Bayesian Rating xử lý quán ít review, hạ trọng số quán bơm điểm ảo. Lời giải thích tạo từ review thật đã được kiểm chứng.
              </p>
            </div>
            <div className="bg-obsidian border border-charcoal p-4 text-xs font-mono text-fog flex items-center gap-2">
              <Zap className="w-3.5 h-3.5 text-paper" />
              <span>Phân tích 8 khía cạnh cảm xúc ABSA</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
