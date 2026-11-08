import React, { useState } from 'react';
import { Calendar, Clock, DollarSign, MapPin, Sparkles, ArrowRight, RotateCw, CheckCircle, Navigation } from 'lucide-react';
import { Itinerary, Restaurant } from '../../types';
import { MOCK_ITINERARIES } from '../../data/mockItineraries';
import { MOCK_RESTAURANTS } from '../../data/mockRestaurants';
import confetti from 'canvas-confetti';

interface ItineraryPlannerProps {
  onOpenRouteMap: (itinerary: Itinerary) => void;
  onSelectRestaurant: (restaurant: Restaurant) => void;
}

export const ItineraryPlanner: React.FC<ItineraryPlannerProps> = ({
  onOpenRouteMap,
  onSelectRestaurant
}) => {
  const [selectedTheme, setSelectedTheme] = useState<string>('Lãng mạn & Tinh tế');
  const [activeItinerary, setActiveItinerary] = useState<Itinerary>(MOCK_ITINERARIES[0]);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Filter or switch itinerary based on theme
  const handleSelectTheme = (theme: string) => {
    setSelectedTheme(theme);
    const found = MOCK_ITINERARIES.find((itin) => itin.theme === theme);
    if (found) {
      setActiveItinerary(found);
    }
  };

  const handleRegenerate = () => {
    setIsRegenerating(true);
    setTimeout(() => {
      setIsRegenerating(false);
      // Shuffle or toggle
      const currentIndex = MOCK_ITINERARIES.findIndex((i) => i.id === activeItinerary.id);
      const nextItin = MOCK_ITINERARIES[(currentIndex + 1) % MOCK_ITINERARIES.length];
      setActiveItinerary(nextItin);
      setSelectedTheme(nextItin.theme);
    }, 600);
  };

  const handleSaveItinerary = () => {
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 },
      colors: ['#ffffff', '#dddddd', '#898989', '#2f2f2f']
    });
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <section className="bg-obsidian py-24 min-h-screen">
      <div className="max-w-[1200px] mx-auto px-6">
        {/* Header */}
        <div className="text-center max-w-2xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 border border-white/20 bg-black/40 rounded-full text-xs text-fog uppercase tracking-widest mb-4">
            <Sparkles className="w-3.5 h-3.5 text-paper" />
            <span>AI Itinerary Generator</span>
          </div>
          <h1 className="font-display-clarkson text-4xl sm:text-6xl text-paper tracking-tighter mb-4">
            LẬP LỊCH TRÌNH HẸN HÒ TRỌN GÓI
          </h1>
          <p className="text-sm text-ash leading-relaxed">
            Hệ thống tự động liên kết 3 chặng hẹn hò buổi tối tại TP.HCM: Ăn tối lãng mạn, ngắm cảnh tráng miệng và cocktail kết thúc ngày, tối ưu hóa quãng đường di chuyển.
          </p>
        </div>

        {/* Theme Selector Pills */}
        <div className="flex items-center justify-center gap-2 flex-wrap mb-12">
          {MOCK_ITINERARIES.map((itin) => (
            <button
              key={itin.id}
              onClick={() => handleSelectTheme(itin.theme)}
              className={`pill-tab cursor-pointer ${
                selectedTheme === itin.theme ? 'pill-tab-active' : 'pill-tab-inactive'
              }`}
            >
              {itin.theme}
            </button>
          ))}
        </div>

        {/* Itinerary Banner Card */}
        <div className="bg-charcoal/20 border border-charcoal p-8 rounded-[8px] mb-12 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h2 className="font-display-clarkson text-2xl sm:text-3xl text-paper tracking-tight">
                {activeItinerary.title}
              </h2>
              <span className="text-xs font-mono bg-paper text-obsidian px-2.5 py-0.5 font-bold rounded-[100px]">
                {activeItinerary.fairness_rating}% Công Bằng
              </span>
            </div>
            <p className="text-xs sm:text-sm text-ash mb-4">
              {activeItinerary.tagline}
            </p>
            <div className="flex flex-wrap items-center gap-6 text-xs text-fog">
              <span className="flex items-center gap-1.5 font-mono">
                <Clock className="w-4 h-4 text-ash" />
                {activeItinerary.duration}
              </span>
              <span className="flex items-center gap-1.5 font-mono text-paper font-semibold">
                <DollarSign className="w-4 h-4 text-ash" />
                Ước tính: {activeItinerary.estimated_cost.toLocaleString('vi-VN')} đ cho 2 người
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3 self-start md:self-auto shrink-0">
            <button
              onClick={handleRegenerate}
              disabled={isRegenerating}
              className="btn-ghost-white py-2.5 px-4 text-xs flex items-center gap-2 cursor-pointer"
            >
              <RotateCw className={`w-3.5 h-3.5 ${isRegenerating ? 'animate-spin' : ''}`} />
              <span>Đổi Lịch Trình Khác</span>
            </button>
            <button
              onClick={() => onOpenRouteMap(activeItinerary)}
              className="btn-filled-white py-2.5 px-5 text-xs flex items-center gap-2 cursor-pointer"
            >
              <Navigation className="w-3.5 h-3.5" />
              <span>Xem Bản Đồ Lộ Trình</span>
            </button>
          </div>
        </div>

        {/* 3-Step Animated Timeline */}
        <div className="relative pl-6 md:pl-0 space-y-8 before:absolute before:left-2.5 md:before:left-1/2 before:top-4 before:bottom-4 before:w-[1px] before:bg-charcoal">
          {activeItinerary.stops.map((stop, idx) => (
            <div
              key={stop.order}
              className={`relative flex flex-col md:flex-row items-center gap-8 ${
                idx % 2 === 0 ? 'md:flex-row-reverse' : ''
              }`}
            >
              {/* Timeline Center Dot */}
              <div className="absolute left-[-24px] md:left-1/2 md:-translate-x-1/2 w-5 h-5 rounded-full bg-obsidian border-2 border-paper flex items-center justify-center z-10">
                <span className="w-1.5 h-1.5 rounded-full bg-paper block" />
              </div>

              {/* Stop Card */}
              <div className="w-full md:w-[46%] bg-obsidian border border-charcoal hover:border-white/40 transition-all duration-300 p-6 rounded-[8px] flex flex-col justify-between">
                <div className="flex items-center justify-between text-xs pb-3 mb-4 border-b border-charcoal">
                  <span className="font-mono text-paper font-semibold tracking-wider uppercase">
                    {stop.stage_name}
                  </span>
                  <span className="font-mono text-ash bg-charcoal/50 px-2.5 py-1">
                    {stop.time_slot}
                  </span>
                </div>

                <div className="flex gap-4 mb-4">
                  <img
                    src={stop.restaurant.image_url}
                    alt={stop.restaurant.name}
                    className="w-24 h-24 object-cover rounded-[4px] filter brightness-85 shrink-0"
                  />
                  <div>
                    <h3
                      onClick={() => onSelectRestaurant(stop.restaurant)}
                      className="font-display-clarkson text-lg text-paper tracking-tight hover:text-fog cursor-pointer transition-colors mb-1"
                    >
                      {stop.restaurant.name}
                    </h3>
                    <p className="text-xs text-ash flex items-center gap-1 mb-2">
                      <MapPin className="w-3 h-3 text-paper" />
                      {stop.restaurant.district}
                    </p>
                    <p className="text-xs text-fog/90 italic">
                      "{stop.suggested_action}"
                    </p>
                  </div>
                </div>

                {stop.transit_note && (
                  <div className="bg-charcoal/30 border border-charcoal p-2.5 text-[11px] text-ash flex items-center gap-2 mb-4">
                    <Navigation className="w-3.5 h-3.5 text-paper shrink-0" />
                    <span>{stop.transit_note}</span>
                  </div>
                )}

                <div className="flex items-center justify-between pt-3 border-t border-charcoal text-xs">
                  <span className="font-mono text-paper font-medium">
                    Chi phí: ~{stop.cost_estimate.toLocaleString('vi-VN')} đ
                  </span>
                  <button
                    onClick={() => onSelectRestaurant(stop.restaurant)}
                    className="text-paper hover:text-fog flex items-center gap-1 uppercase tracking-wider text-[11px] cursor-pointer"
                  >
                    <span>Xem Quán</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>

              {/* Empty placeholder to balance layout on desktop */}
              <div className="hidden md:block md:w-[46%]" />
            </div>
          ))}
        </div>

        {/* Footer Actions */}
        <div className="mt-16 text-center">
          <button
            onClick={handleSaveItinerary}
            className={`btn-filled-white px-8 py-3.5 text-xs font-medium cursor-pointer transition-all ${
              savedSuccess ? 'bg-green-600 text-white border-green-600' : ''
            }`}
          >
            {savedSuccess ? (
              <span className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                Lịch Trình Đã Được Lưu Thành Công!
              </span>
            ) : (
              <span>Lưu Lịch Trình Này Cho Hai Bạn</span>
            )}
          </button>
        </div>
      </div>
    </section>
  );
};
