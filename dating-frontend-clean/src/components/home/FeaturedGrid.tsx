import React from 'react';
import { ArrowUpRight, Star } from 'lucide-react';
import { Restaurant } from '../../types';

interface FeaturedGridProps {
  restaurants: Restaurant[];
  onSelectRestaurant: (restaurant: Restaurant) => void;
  onViewAll: () => void;
}

export const FeaturedGrid: React.FC<FeaturedGridProps> = ({
  restaurants,
  onSelectRestaurant,
  onViewAll
}) => {
  return (
    <section className="bg-obsidian py-24 border-b border-charcoal">
      <div className="max-w-[1200px] mx-auto px-6">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-14">
          <div>
            <p className="text-xs uppercase tracking-widest text-ash mb-3">Bộ Sưu Tập Tuyển Chọn</p>
            <h2 className="font-display-clarkson text-3xl sm:text-5xl text-paper tracking-tighter">
              ĐỊA ĐIỂM HẸN HÒ BIỂU TƯỢNG
            </h2>
          </div>
          <button
            onClick={onViewAll}
            className="mt-6 md:mt-0 text-xs uppercase tracking-widest text-paper hover:text-fog flex items-center gap-2 cursor-pointer pb-1 border-b border-paper"
          >
            <span>Xem Toàn Bộ 853 Quán</span>
            <ArrowUpRight className="w-4 h-4" />
          </button>
        </div>

        {/* 4-Column Grid of Dark Feature Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {restaurants.slice(0, 4).map((res) => (
            <div
              key={res.id}
              onClick={() => onSelectRestaurant(res)}
              className="group relative h-[380px] rounded-[8px] overflow-hidden border border-charcoal hover:border-white/50 transition-all duration-300 cursor-pointer flex flex-col justify-end p-6 bg-charcoal"
            >
              {/* Background Image with Dark Vignette */}
              <img
                src={res.image_url}
                alt={res.name}
                className="absolute inset-0 w-full h-full object-cover filter brightness-60 contrast-110 group-hover:scale-105 transition-transform duration-700"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-obsidian via-obsidian/40 to-transparent opacity-90" />

              {/* Top Badges */}
              <div className="absolute top-4 left-4 right-4 flex items-center justify-between z-10">
                <span className="text-[10px] font-mono tracking-wider uppercase bg-black/60 backdrop-blur-sm border border-white/20 text-paper px-2.5 py-1 rounded-[100px]">
                  {res.district}
                </span>
                <div className="flex items-center gap-1 text-xs text-paper bg-black/60 backdrop-blur-sm border border-white/20 px-2 py-0.5 rounded-[100px]">
                  <Star className="w-3 h-3 fill-paper text-paper" />
                  <span className="font-mono">{res.couple_score.toFixed(2)}</span>
                </div>
              </div>

              {/* Bottom Content */}
              <div className="relative z-10">
                <p className="text-[11px] text-ash tracking-wide uppercase mb-1">
                  {res.category}
                </p>
                <h3 className="font-display-clarkson text-xl text-paper tracking-tight mb-2 group-hover:text-fog transition-colors line-clamp-1">
                  {res.name}
                </h3>
                <p className="text-xs text-ash/90 line-clamp-2 leading-relaxed mb-4">
                  {res.explanation}
                </p>
                <div className="flex items-center justify-between pt-3 border-t border-white/15">
                  <span className="text-xs font-mono text-paper font-medium">
                    {res.price_text}
                  </span>
                  <div className="w-7 h-7 rounded-full bg-white/10 group-hover:bg-white text-paper group-hover:text-obsidian flex items-center justify-center transition-all">
                    <ArrowUpRight className="w-4 h-4" />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
