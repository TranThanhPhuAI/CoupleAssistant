import React, { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Restaurant } from '../../types';
import { MOCK_RESTAURANTS } from '../../data/mockRestaurants';
import { ArrowDown } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

interface HeroSectionProps {
  onSearch?: (query: string) => void;
  onExplore: () => void;
  onOpenStudio?: () => void;
  onSelectRestaurant?: (restaurant: Restaurant) => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({
  onExplore,
  onSelectRestaurant
}) => {
  const heroRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const headlineLine1Ref = useRef<HTMLParagraphElement>(null);
  const headlineLine2Ref = useRef<HTMLHeadingElement>(null);
  const sublineRef = useRef<HTMLParagraphElement>(null);
  const cardsRef = useRef<HTMLDivElement>(null);
  const card1Ref = useRef<HTMLDivElement>(null);
  const card2Ref = useRef<HTMLDivElement>(null);
  const card3Ref = useRef<HTMLDivElement>(null);

  // Map 3 approved venues from MOCK_RESTAURANTS for interactive modal click
  const theDeck = MOCK_RESTAURANTS.find((r) => r.id === 'res-the-deck');
  const blankLounge = MOCK_RESTAURANTS.find((r) => r.id === 'res-blank-lounge');
  const chidori = MOCK_RESTAURANTS.find((r) => r.id === 'res-chidori-bed');

  const handleCardClick = (res?: Restaurant) => {
    if (res && onSelectRestaurant) {
      onSelectRestaurant(res);
    } else {
      onExplore();
    }
  };

  useEffect(() => {
    const ctx = gsap.context(() => {
      // 1. Text Entrance Animation (Editorial Stagger Reveal for Option A)
      if (headlineLine1Ref.current && headlineLine2Ref.current) {
        gsap.fromTo(
          headlineLine1Ref.current,
          { y: 35, opacity: 0, letterSpacing: '0.06em' },
          { y: 0, opacity: 1, letterSpacing: '0.14em', duration: 1.0, ease: 'power3.out' }
        );
        gsap.fromTo(
          headlineLine2Ref.current,
          { y: 50, opacity: 0, filter: 'blur(4px)' },
          { y: 0, opacity: 1, filter: 'blur(0px)', duration: 1.2, delay: 0.15, ease: 'power3.out' }
        );
      }

      if (sublineRef.current) {
        gsap.fromTo(
          sublineRef.current,
          { y: 30, opacity: 0 },
          { y: 0, opacity: 1, duration: 1.0, delay: 0.4, ease: 'power2.out' }
        );
      }

      // 2. Video Zoom on Scroll (Gentle scrub scale from 1.0 to 1.12)
      if (videoRef.current && heroRef.current) {
        gsap.to(videoRef.current, {
          scale: 1.12,
          ease: 'none',
          scrollTrigger: {
            trigger: heroRef.current,
            start: 'top top',
            end: 'bottom top',
            scrub: 1.2
          }
        });
      }

      // 3. Overlapping Cards Parallax Scrub (Staggered parallax speeds)
      if (card1Ref.current && card2Ref.current && card3Ref.current && heroRef.current) {
        const cardTimeline = gsap.timeline({
          scrollTrigger: {
            trigger: heroRef.current,
            start: 'center top',
            end: 'bottom top',
            scrub: 1
          }
        });

        cardTimeline
          .to(card1Ref.current, { y: -40, ease: 'none' }, 0)
          .to(card2Ref.current, { y: -75, ease: 'none' }, 0)
          .to(card3Ref.current, { y: -50, ease: 'none' }, 0);
      }
    }, heroRef);

    return () => {
      ctx.revert(); // Perfectly cleans up GSAP tweens and ScrollTriggers
    };
  }, []);

  return (
    <section
      ref={heroRef}
      className="relative min-h-[110vh] flex flex-col justify-between overflow-hidden bg-obsidian pt-32 pb-24"
    >
      {/* Full-bleed Video Background with Live Zoom on Scroll */}
      <div className="absolute inset-0 z-0 overflow-hidden">
        <video
          ref={videoRef}
          autoPlay
          loop
          muted
          playsInline
          preload="auto"
          className="w-full h-full object-cover will-change-transform"
          poster="https://assets.mixkit.co/videos/45727/45727-thumb-720-2.jpg"
        >
          {/* Mẫu 2 – Cụng ly bên bàn tiệc nhà hàng (Đã được phê duyệt) */}
          <source src="/media/video-2-toast.mp4" type="video/mp4" />
          <source src="https://assets.mixkit.co/videos/45727/45727-720.mp4" type="video/mp4" />
        </video>

        {/* Chế độ Overlay Gradient Chân đã được phê duyệt (Không làm mất màu sắc tự nhiên của video) */}
        <div className="absolute inset-0 bg-gradient-to-t from-obsidian via-obsidian/40 to-transparent pointer-events-none" />
      </div>

      {/* Hero Content (Squarespace Minimalist • Editorial Typography) */}
      <div className="relative z-10 max-w-[1100px] mx-auto px-6 text-center flex flex-col items-center my-auto">
        {/* Monumental Editorial Headline with Luxury Dual Typography (Phương án A) */}
        <div className="overflow-hidden mb-6 text-center max-w-4xl space-y-2">
          {/* Dòng 1: Modern Sans-serif, thanh mảnh, hiện đại */}
          <p
            ref={headlineLine1Ref}
            className="font-jakarta font-light text-2xl sm:text-4xl md:text-5xl lg:text-[46px] text-paper uppercase tracking-[0.14em] leading-tight"
          >
            MỘT ĐIỂM HẸN.
          </p>

          {/* Dòng 2: Elegant Serif Italic nghệ thuật, lãng mạn */}
          <h1
            ref={headlineLine2Ref}
            className="font-playfair italic font-normal text-4xl sm:text-6xl md:text-7xl lg:text-[76px] text-paper tracking-tight leading-[1.08]"
          >
            VẠN KHOẢNH KHẮC.
          </h1>
        </div>

        {/* Editorial Subline */}
        <p
          ref={sublineRef}
          className="text-base sm:text-lg text-paper/90 max-w-2xl font-light leading-relaxed mb-8 drop-shadow-sm"
        >
          Khám phá những điểm hẹn hợp gu cả hai, từ nhà hàng, quán cà phê đến những hành trình đáng nhớ giữa lòng Sài Gòn.
        </p>

        {/* Ghost Button (0px sharp radius) */}
        <button
          onClick={() => {
            window.scrollTo({ top: window.innerHeight * 0.9, behavior: 'smooth' });
          }}
          className="btn-ghost-white cursor-pointer px-8 py-3.5 text-xs font-medium tracking-widest flex items-center gap-2 group transition-all"
        >
          <span>Cuộn Xuống Khám Phá</span>
          <ArrowDown className="w-3.5 h-3.5 group-hover:translate-y-0.5 transition-transform" />
        </button>
      </div>

      {/* ======================================================== */}
      {/* 3 THẺ HÌNH ẢNH CHỒNG LỚP (OVERLAPPING CARDS PARALLAX) */}
      {/* 50% nằm trên video Hero và 50% trồi xuống Section tiếp theo */}
      {/* ======================================================== */}
      <div
        ref={cardsRef}
        className="relative z-20 max-w-[1100px] mx-auto px-6 w-full -mb-32 sm:-mb-36"
      >
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {/* Card 1: The Deck Saigon (Thảo Điền • View Sông) */}
          <div
            ref={card1Ref}
            onClick={() => handleCardClick(theDeck)}
            className="bg-obsidian rounded-[8px] overflow-hidden border border-white/20 shadow-2xl group transition-all duration-300 hover:border-white cursor-pointer will-change-transform"
          >
            <div className="relative h-44 overflow-hidden">
              <img
                src="https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80"
                alt="Ven sông Thảo Điền"
                loading="eager"
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
              />
              <div className="absolute top-3 left-3 bg-[#ff7a7a] text-obsidian text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-[100px]">
                Thảo Điền • View Sông
              </div>
            </div>
            <div className="p-4 bg-obsidian">
              <h4 className="font-display-clarkson text-base text-paper tracking-tight mb-1 group-hover:text-white transition-colors">
                The Deck Saigon
              </h4>
              <p className="text-xs text-ash line-clamp-1">
                Bàn ăn ngoài trời ngắm hoàng hôn lãng mạn ven sông
              </p>
            </div>
          </div>

          {/* Card 2: Blank Lounge Landmark 81 (Bình Thạnh • Tầng 75) */}
          <div
            ref={card2Ref}
            onClick={() => handleCardClick(blankLounge)}
            className="bg-obsidian rounded-[8px] overflow-hidden border border-white/20 shadow-2xl group transition-all duration-300 hover:border-white sm:-translate-y-4 cursor-pointer will-change-transform"
          >
            <div className="relative h-44 overflow-hidden">
              <img
                src="https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=800&q=80"
                alt="Landmark 81 Sky view"
                loading="eager"
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
              />
              <div className="absolute top-3 left-3 bg-paper text-obsidian text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-[100px]">
                Bình Thạnh • Tầng 75
              </div>
            </div>
            <div className="p-4 bg-obsidian">
              <h4 className="font-display-clarkson text-base text-paper tracking-tight mb-1 group-hover:text-white transition-colors">
                Blank Lounge Landmark 81
              </h4>
              <p className="text-xs text-ash line-clamp-1">
                Toàn cảnh Sài Gòn rực rỡ ánh đèn đêm từ trên cao
              </p>
            </div>
          </div>

          {/* Card 3: Chidori Coffee in Bed (Quận 3 • Yên Tĩnh) */}
          <div
            ref={card3Ref}
            onClick={() => handleCardClick(chidori)}
            className="bg-obsidian rounded-[8px] overflow-hidden border border-white/20 shadow-2xl group transition-all duration-300 hover:border-white cursor-pointer will-change-transform"
          >
            <div className="relative h-44 overflow-hidden">
              <img
                src="https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=800&q=80"
                alt="Chidori coffee in bed"
                loading="eager"
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
              />
              <div className="absolute top-3 left-3 bg-[#b5e7a0] text-obsidian text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-[100px]">
                Quận 3 • Yên Tĩnh
              </div>
            </div>
            <div className="p-4 bg-obsidian">
              <h4 className="font-display-clarkson text-base text-paper tracking-tight mb-1 group-hover:text-white transition-colors">
                Chidori Coffee in Bed
              </h4>
              <p className="text-xs text-ash line-clamp-1">
                Kén gỗ riêng tư, nệm êm đọc sách và uống trà đào
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
