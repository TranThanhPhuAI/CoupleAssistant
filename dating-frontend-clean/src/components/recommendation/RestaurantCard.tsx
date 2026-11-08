import React from 'react';
import { Star, MapPin, DollarSign, Clock, ArrowRight, Heart, Plus } from 'lucide-react';
import { Restaurant } from '../../types';

interface RestaurantCardProps {
  restaurant: Restaurant;
  onSelect: (restaurant: Restaurant) => void;
  onAddToItinerary: (restaurant: Restaurant) => void;
}

export const RestaurantCard: React.FC<RestaurantCardProps> = ({
  restaurant,
  onSelect,
  onAddToItinerary
}) => {
  return (
    <div className="bg-charcoal/25 border border-charcoal hover:border-white/40 transition-all duration-300 rounded-[8px] overflow-hidden flex flex-col group">
      {/* Top Media with High-Contrast Overlay */}
      <div className="relative h-56 overflow-hidden cursor-pointer" onClick={() => onSelect(restaurant)}>
        <img
          src={restaurant.image_url}
          alt={restaurant.name}
          className="w-full h-full object-cover filter brightness-75 group-hover:scale-105 transition-transform duration-700"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-obsidian via-transparent to-black/30" />

        {/* District & Category Badge */}
        <div className="absolute top-3 left-3 flex items-center gap-2">
          <span className="text-[10px] font-mono tracking-wider uppercase bg-obsidian/85 text-paper px-2.5 py-1 border border-white/20 rounded-[100px]">
            {restaurant.district}
          </span>
          {restaurant.is_balanced && (
            <span className="text-[10px] font-mono tracking-wider uppercase bg-paper text-obsidian px-2.5 py-1 font-semibold rounded-[100px]">
              Vừa ngon vừa hợp
            </span>
          )}
        </div>

        {/* Triple Score Pill */}
        <div className="absolute bottom-3 right-3 flex items-center gap-1.5 bg-obsidian/90 border border-white/30 backdrop-blur-md px-3 py-1.5 rounded-[100px]">
          <div className="text-center pr-2 border-r border-white/20">
            <span className="text-[9px] text-ash block leading-none">FOOD</span>
            <span className="text-xs font-mono font-bold text-paper">
              {restaurant.food_score.toFixed(2)}
            </span>
          </div>
          <div className="text-center pr-2 border-r border-white/20">
            <span className="text-[9px] text-ash block leading-none">DATE</span>
            <span className="text-xs font-mono font-bold text-paper">
              {restaurant.date_score.toFixed(2)}
            </span>
          </div>
          <div className="text-center">
            <span className="text-[9px] text-ash block leading-none">COUPLE</span>
            <span className="text-xs font-mono font-bold text-paper">
              {restaurant.couple_score.toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      {/* Body Info */}
      <div className="p-6 flex-1 flex flex-col justify-between">
        <div>
          <div className="text-[11px] text-ash uppercase tracking-wider mb-1 font-medium">
            {restaurant.category}
          </div>
          <h3
            onClick={() => onSelect(restaurant)}
            className="font-display-clarkson text-xl text-paper tracking-tight mb-2 hover:text-fog cursor-pointer transition-colors line-clamp-1"
          >
            {restaurant.name}
          </h3>

          <div className="flex items-center gap-4 text-xs text-ash mb-4">
            <span className="flex items-center gap-1 font-mono text-paper">
              <DollarSign className="w-3.5 h-3.5 text-ash" />
              {restaurant.price_text}
            </span>
            <span className="flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5 text-ash" />
              {restaurant.district}
            </span>
          </div>

          {/* AI Hallucination-free Explanation based on real reviews */}
          <p className="text-xs text-ash/90 leading-relaxed line-clamp-2 mb-4 bg-obsidian/60 p-3 border border-charcoal/80">
            <span className="text-paper font-medium">Lý do phù hợp: </span>
            {restaurant.explanation}
          </p>

          {/* Mini ABSA bars */}
          <div className="grid grid-cols-4 gap-2 mb-6">
            <div className="bg-obsidian border border-charcoal p-1.5 text-center">
              <span className="text-[9px] text-ash block">Món ăn</span>
              <span className="text-xs font-mono text-paper">{restaurant.absa_scores.food}%</span>
            </div>
            <div className="bg-obsidian border border-charcoal p-1.5 text-center">
              <span className="text-[9px] text-ash block">Không gian</span>
              <span className="text-xs font-mono text-paper">{restaurant.absa_scores.ambiance}%</span>
            </div>
            <div className="bg-obsidian border border-charcoal p-1.5 text-center">
              <span className="text-[9px] text-ash block">Yên tĩnh</span>
              <span className="text-xs font-mono text-paper">{restaurant.absa_scores.quiet}%</span>
            </div>
            <div className="bg-obsidian border border-charcoal p-1.5 text-center">
              <span className="text-[9px] text-ash block">Lãng mạn</span>
              <span className="text-xs font-mono text-paper">{restaurant.absa_scores.romantic}%</span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3 pt-4 border-t border-charcoal">
          <button
            onClick={() => onSelect(restaurant)}
            className="flex-1 text-center py-2.5 px-3 border border-white/20 hover:border-paper text-paper text-xs uppercase tracking-wider transition-colors cursor-pointer"
          >
            Chi Tiết
          </button>
          <button
            onClick={() => onAddToItinerary(restaurant)}
            className="py-2.5 px-3 bg-paper text-obsidian hover:bg-fog text-xs font-medium uppercase tracking-wider transition-colors cursor-pointer flex items-center justify-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Thêm Lộ Trình</span>
          </button>
        </div>
      </div>
    </div>
  );
};
