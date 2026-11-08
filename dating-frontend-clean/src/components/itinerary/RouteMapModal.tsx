import React from 'react';
import { X, MapPin, Navigation, Clock, DollarSign, Check } from 'lucide-react';
import { Itinerary } from '../../types';

interface RouteMapModalProps {
  itinerary: Itinerary | null;
  onClose: () => void;
}

export const RouteMapModal: React.FC<RouteMapModalProps> = ({ itinerary, onClose }) => {
  if (!itinerary) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/85 backdrop-blur-md overflow-y-auto">
      <div className="relative w-full max-w-4xl bg-obsidian border border-charcoal rounded-[8px] overflow-hidden my-8 shadow-2xl flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-charcoal flex items-center justify-between">
          <div>
            <span className="text-[10px] font-mono text-ash uppercase tracking-wider block">
              BẢN ĐỒ LỘ TRÌNH HẸN HÒ MÔ PHỎNG TP.HCM
            </span>
            <h2 className="font-display-clarkson text-2xl text-paper tracking-tight">
              {itinerary.title}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 bg-charcoal hover:bg-white text-paper hover:text-obsidian flex items-center justify-center transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Simulated Saigon Interactive Map View */}
        <div className="relative h-[320px] sm:h-[400px] bg-[#0d0d0d] border-b border-charcoal overflow-hidden flex items-center justify-center">
          {/* Subtle City Grid Map SVG */}
          <svg className="absolute inset-0 w-full h-full opacity-30" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#2f2f2f" strokeWidth="0.5" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
            {/* Curved Saigon River representation */}
            <path
              d="M 50 400 Q 250 200 450 300 T 850 100"
              fill="none"
              stroke="#444444"
              strokeWidth="16"
              strokeLinecap="round"
              opacity="0.6"
            />
            {/* Route connecting line */}
            <path
              d="M 220 280 L 440 210 L 680 160"
              fill="none"
              stroke="#ffffff"
              strokeWidth="2.5"
              strokeDasharray="6,6"
            />
          </svg>

          {/* Interactive Stop Pins on Map */}
          <div className="relative z-10 w-full max-w-2xl px-6 flex items-center justify-between">
            {itinerary.stops.map((stop, idx) => (
              <div key={stop.order} className="flex flex-col items-center text-center group">
                <div className="w-10 h-10 rounded-full bg-obsidian border-2 border-paper flex items-center justify-center text-paper font-mono font-bold text-xs shadow-lg mb-2 group-hover:scale-110 transition-transform">
                  {stop.order}
                </div>
                <div className="bg-obsidian/95 border border-white/20 p-2.5 rounded-[4px] max-w-[160px] text-left">
                  <span className="text-[9px] font-mono text-ash block">{stop.time_slot}</span>
                  <span className="text-xs text-paper font-medium block truncate">
                    {stop.restaurant.name}
                  </span>
                  <span className="text-[10px] text-fog/80 block">
                    {stop.restaurant.district}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Map Watermark */}
          <div className="absolute bottom-3 left-4 text-[10px] font-mono text-ash/60">
            SIMULATED SAIGON GEO-COORDINATES (10.7769° N, 106.7009° E)
          </div>
        </div>

        {/* Summary Breakdown */}
        <div className="p-6 sm:p-8 space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div className="bg-charcoal/20 border border-charcoal p-4 rounded-[4px]">
              <span className="text-ash block uppercase mb-1">Thời gian buổi hẹn</span>
              <span className="font-mono text-paper text-base font-bold flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-ash" />
                {itinerary.duration}
              </span>
            </div>
            <div className="bg-charcoal/20 border border-charcoal p-4 rounded-[4px]">
              <span className="text-ash block uppercase mb-1">Dự toán chi phí 2 người</span>
              <span className="font-mono text-paper text-base font-bold flex items-center gap-1.5">
                <DollarSign className="w-4 h-4 text-ash" />
                {itinerary.estimated_cost.toLocaleString('vi-VN')} đ
              </span>
            </div>
            <div className="bg-charcoal/20 border border-charcoal p-4 rounded-[4px]">
              <span className="text-ash block uppercase mb-1">Độ công bằng sở thích</span>
              <span className="font-mono text-paper text-base font-bold flex items-center gap-1.5">
                <Navigation className="w-4 h-4 text-ash" />
                {itinerary.fairness_rating}% (TOPSIS Match)
              </span>
            </div>
          </div>

          {/* Stops List */}
          <div>
            <h3 className="text-xs uppercase tracking-widest text-ash mb-3">
              CHI TIẾT CÁC ĐIỂM DỪNG
            </h3>
            <div className="space-y-3">
              {itinerary.stops.map((stop) => (
                <div
                  key={stop.order}
                  className="p-4 bg-charcoal/15 border border-charcoal flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-full bg-paper text-obsidian flex items-center justify-center font-mono font-bold text-xs shrink-0">
                      {stop.order}
                    </span>
                    <div>
                      <span className="font-medium text-paper text-sm block">
                        {stop.restaurant.name}
                      </span>
                      <span className="text-ash">{stop.restaurant.address}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-6 sm:justify-end text-right">
                    <span className="font-mono text-fog">{stop.time_slot}</span>
                    <span className="font-mono text-paper font-semibold">
                      ~{stop.cost_estimate.toLocaleString('vi-VN')} đ
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Close button */}
          <div className="pt-4 border-t border-charcoal flex justify-end">
            <button onClick={onClose} className="btn-filled-white text-xs cursor-pointer">
              Đóng Bản Đồ
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
