import React, { useState } from 'react';
import { X, Star, MapPin, DollarSign, Clock, ShieldCheck, Heart, Plus, Check } from 'lucide-react';
import { Restaurant } from '../../types';

interface DetailModalProps {
  restaurant: Restaurant | null;
  onClose: () => void;
  onAddToItinerary: (restaurant: Restaurant) => void;
}

export const DetailModal: React.FC<DetailModalProps> = ({
  restaurant,
  onClose,
  onAddToItinerary
}) => {
  const [activeImageIdx, setActiveImageIdx] = useState(0);
  const [added, setAdded] = useState(false);

  if (!restaurant) return null;

  const handleAdd = () => {
    onAddToItinerary(restaurant);
    setAdded(true);
    setTimeout(() => setAdded(false), 2000);
  };

  const galleryImages = restaurant.gallery?.length ? restaurant.gallery : [restaurant.image_url];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto bg-black/80 backdrop-blur-md">
      <div className="relative w-full max-w-4xl bg-obsidian border border-charcoal rounded-[8px] overflow-hidden my-8 shadow-2xl flex flex-col">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-20 w-9 h-9 bg-obsidian/80 hover:bg-white text-paper hover:text-obsidian flex items-center justify-center border border-charcoal transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Gallery Hero Section */}
        <div className="relative h-[340px] sm:h-[420px] bg-charcoal">
          <img
            src={galleryImages[activeImageIdx]}
            alt={restaurant.name}
            className="w-full h-full object-cover filter brightness-85"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-obsidian via-transparent to-black/30" />

          {/* Thumbnail Strip */}
          {galleryImages.length > 1 && (
            <div className="absolute bottom-4 left-6 flex items-center gap-2 z-10">
              {galleryImages.map((img, idx) => (
                <button
                  key={idx}
                  onClick={() => setActiveImageIdx(idx)}
                  className={`w-14 h-10 border transition-all cursor-pointer overflow-hidden ${
                    activeImageIdx === idx ? 'border-paper scale-105' : 'border-white/30 opacity-70'
                  }`}
                >
                  <img src={img} alt="thumb" className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          )}

          {/* District & Category */}
          <div className="absolute top-6 left-6 z-10 flex items-center gap-2">
            <span className="text-xs font-mono uppercase bg-obsidian/90 text-paper px-3 py-1 border border-white/20 rounded-[100px]">
              {restaurant.district}
            </span>
            <span className="text-xs font-mono uppercase bg-paper text-obsidian px-3 py-1 font-semibold rounded-[100px]">
              {restaurant.category}
            </span>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-6 sm:p-8 space-y-8">
          {/* Header Title & Scores */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-charcoal">
            <div>
              <h2 className="font-display-clarkson text-3xl sm:text-4xl text-paper tracking-tight mb-2">
                {restaurant.name}
              </h2>
              <div className="flex flex-wrap items-center gap-4 text-xs text-ash">
                <span className="flex items-center gap-1.5 text-paper">
                  <MapPin className="w-3.5 h-3.5 text-ash" />
                  {restaurant.address}
                </span>
                <span className="flex items-center gap-1.5 text-paper font-mono">
                  <DollarSign className="w-3.5 h-3.5 text-ash" />
                  {restaurant.price_text}
                </span>
                <span className="flex items-center gap-1.5 text-ash">
                  <Clock className="w-3.5 h-3.5" />
                  {restaurant.opening_hours}
                </span>
              </div>
            </div>

            {/* Scores Pill Group */}
            <div className="flex items-center gap-3 bg-charcoal/30 p-3 border border-charcoal self-start lg:self-auto">
              <div className="text-center px-3 border-r border-charcoal">
                <span className="text-[10px] text-ash block uppercase">FOOD SCORE</span>
                <span className="text-lg font-mono font-bold text-paper">
                  {restaurant.food_score.toFixed(2)}
                </span>
              </div>
              <div className="text-center px-3 border-r border-charcoal">
                <span className="text-[10px] text-ash block uppercase">DATE SCORE</span>
                <span className="text-lg font-mono font-bold text-paper">
                  {restaurant.date_score.toFixed(2)}
                </span>
              </div>
              <div className="text-center px-3">
                <span className="text-[10px] text-ash block uppercase">COUPLE SCORE</span>
                <span className="text-lg font-mono font-bold text-paper">
                  {restaurant.couple_score.toFixed(2)}
                </span>
              </div>
            </div>
          </div>

          {/* AI Hallucination-free Explanation */}
          <div className="bg-charcoal/20 border border-charcoal p-6 rounded-[8px]">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-paper mb-2">
              <ShieldCheck className="w-4 h-4 text-paper" />
              <span>Tại sao quán này lý tưởng cho hẹn hò?</span>
            </div>
            <p className="text-sm text-fog leading-relaxed">
              {restaurant.explanation}
            </p>
          </div>

          {/* 8-Aspect ABSA Breakdown */}
          <div>
            <h3 className="text-xs uppercase tracking-widest text-ash mb-4">
              PHÂN TÍCH 8 KHÍA CẠNH CẢM XÚC (ABSA TỪ REVIEW THẬT)
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {Object.entries({
                'Món ăn': restaurant.absa_scores.food,
                'Không gian': restaurant.absa_scores.ambiance,
                'Yên tĩnh': restaurant.absa_scores.quiet,
                'Lãng mạn': restaurant.absa_scores.romantic,
                'View đẹp': restaurant.absa_scores.view,
                'Riêng tư': restaurant.absa_scores.privacy,
                'Phục vụ': restaurant.absa_scores.service,
                'Giá hợp lý': restaurant.absa_scores.price
              }).map(([label, score]) => (
                <div key={label} className="bg-obsidian border border-charcoal p-3 rounded-[4px]">
                  <div className="flex justify-between items-center text-xs mb-1.5">
                    <span className="text-ash">{label}</span>
                    <span className="font-mono text-paper font-medium">{score}%</span>
                  </div>
                  <div className="w-full bg-charcoal h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-paper h-full transition-all duration-700"
                      style={{ width: `${score}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Verified Real Reviews */}
          <div>
            <h3 className="text-xs uppercase tracking-widest text-ash mb-4">
              ĐÁNH GIÁ THỰC TẾ ĐÃ LÀM SẠCH ({restaurant.review_count} REVIEWS)
            </h3>
            <div className="space-y-3">
              {restaurant.highlight_reviews.map((rev) => (
                <div key={rev.id} className="p-4 bg-charcoal/15 border border-charcoal text-xs">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-paper">{rev.author}</span>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-ash">{rev.date}</span>
                      <span className="font-mono text-paper bg-charcoal px-2 py-0.5 rounded-[100px]">
                        ★ {rev.rating} / 10
                      </span>
                    </div>
                  </div>
                  <p className="text-ash leading-relaxed mb-2">"{rev.comment}"</p>
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {rev.sentimentAspects.map((asp, i) => (
                      <span
                        key={i}
                        className="text-[10px] text-fog/80 bg-black/40 border border-charcoal px-2 py-0.5"
                      >
                        ✓ {asp}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Footer CTA */}
          <div className="flex items-center justify-end gap-4 pt-4 border-t border-charcoal">
            <button onClick={onClose} className="btn-ghost-white py-2.5 px-6 text-xs cursor-pointer">
              Đóng
            </button>
            <button
              onClick={handleAdd}
              className={`py-2.5 px-6 text-xs font-medium uppercase tracking-wider transition-colors cursor-pointer flex items-center gap-2 ${
                added ? 'bg-green-600 text-white' : 'btn-filled-white'
              }`}
            >
              {added ? (
                <>
                  <Check className="w-3.5 h-3.5" />
                  <span>Đã Thêm Vào Lịch Trình</span>
                </>
              ) : (
                <>
                  <Plus className="w-3.5 h-3.5" />
                  <span>Thêm Vào Lịch Trình Hẹn Hò</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
