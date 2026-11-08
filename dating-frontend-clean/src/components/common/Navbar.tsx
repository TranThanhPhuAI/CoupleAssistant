import React, { useState, useEffect } from 'react';
import { Compass, Calendar, Sparkles, HeartHandshake, MapPin } from 'lucide-react';

interface NavbarProps {
  currentView: 'home' | 'recommendation' | 'itinerary';
  onNavigate: (view: 'home' | 'recommendation' | 'itinerary') => void;
  onOpenPersonality: () => void;
  onOpenDemo?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentView, onNavigate, onOpenPersonality, onOpenDemo }) => {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 40);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'bg-obsidian/95 backdrop-blur-md border-b border-charcoal py-4'
          : 'bg-transparent py-6'
      }`}
    >
      <div className="max-w-[1240px] mx-auto px-6 flex items-center justify-between">
        {/* Logo Brand */}
        <button
          onClick={() => onNavigate('home')}
          className="flex items-center gap-3 text-left group cursor-pointer focus:outline-none"
        >
          <div className="w-8 h-8 bg-paper text-obsidian flex items-center justify-center font-bold text-xs tracking-tighter">
            CA
          </div>
          <div>
            <span className="text-sm font-medium tracking-widest uppercase text-paper block">
              Couple Assistant
            </span>
            <span className="text-[10px] text-ash tracking-wider uppercase block">
              TP. Hồ Chí Minh
            </span>
          </div>
        </button>

        {/* Center Nav Items */}
        <nav className="hidden md:flex items-center gap-8">
          <button
            onClick={() => onNavigate('home')}
            className={`text-xs uppercase tracking-wider transition-colors py-1 cursor-pointer ${
              currentView === 'home'
                ? 'text-paper border-b border-paper font-medium'
                : 'text-ash hover:text-paper'
            }`}
          >
            Trang Chủ
          </button>
          <button
            onClick={() => onNavigate('recommendation')}
            className={`text-xs uppercase tracking-wider transition-colors py-1 cursor-pointer flex items-center gap-1.5 ${
              currentView === 'recommendation'
                ? 'text-paper border-b border-paper font-medium'
                : 'text-ash hover:text-paper'
            }`}
          >
            <Compass className="w-3.5 h-3.5" />
            Gợi Ý Quán Ăn
          </button>
          <button
            onClick={() => onNavigate('itinerary')}
            className={`text-xs uppercase tracking-wider transition-colors py-1 cursor-pointer flex items-center gap-1.5 ${
              currentView === 'itinerary'
                ? 'text-paper border-b border-paper font-medium'
                : 'text-ash hover:text-paper'
            }`}
          >
            <Calendar className="w-3.5 h-3.5" />
            Lịch Trình Hẹn Hò
          </button>
          <button
            onClick={onOpenPersonality}
            className="text-xs uppercase tracking-wider text-ash hover:text-paper transition-colors py-1 cursor-pointer flex items-center gap-1.5"
          >
            <HeartHandshake className="w-3.5 h-3.5 text-fog" />
            Trắc Nghiệm Tính Cách
          </button>
        </nav>

        {/* Right CTA */}
        <div className="flex items-center gap-3">
          {onOpenDemo && (
            <button
              onClick={onOpenDemo}
              className="hidden sm:flex items-center gap-1.5 text-xs text-fog hover:text-paper border border-white/20 hover:border-paper px-3 py-1.5 transition-colors cursor-pointer"
              title="Mở phòng thử nghiệm 4 video và 3 hiệu ứng GSAP độc lập"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
              <span>Phòng Thử Nghiệm /demo</span>
            </button>
          )}
          <div className="hidden lg:flex items-center gap-1.5 text-xs text-ash border border-charcoal px-3 py-1.5 rounded-none">
            <MapPin className="w-3 h-3 text-paper" />
            <span>853 Quán TP.HCM</span>
          </div>
          <button
            onClick={() => onNavigate('itinerary')}
            className="btn-filled-white cursor-pointer flex items-center gap-2"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Lên Lịch Trình</span>
          </button>
        </div>
      </div>
    </header>
  );
};
