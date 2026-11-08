import React, { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { ArrowUpRight, Sparkles, Utensils, HeartHandshake } from 'lucide-react';
import { Restaurant } from '../../types';

gsap.registerPlugin(ScrollTrigger);

interface CuratedDiningSectionProps {
  onExplore: () => void;
  onSelectRestaurant?: (restaurant: Restaurant) => void;
}

export const CuratedDiningSection: React.FC<CuratedDiningSectionProps> = ({
  onExplore,
  onSelectRestaurant
}) => {
  const sectionRef = useRef<HTMLDivElement>(null);
  const headlineRef = useRef<HTMLHeadingElement>(null);
  const sublineRef = useRef<HTMLParagraphElement>(null);

  // Image wrapper refs for Curtain Clip-Path Reveal
  const imageWrapper1Ref = useRef<HTMLDivElement>(null);
  const imageWrapper2Ref = useRef<HTMLDivElement>(null);
  const imageWrapper3Ref = useRef<HTMLDivElement>(null);

  // Parallax targets
  const parallaxImg1Ref = useRef<HTMLImageElement>(null);
  const parallaxImg2Ref = useRef<HTMLImageElement>(null);
  const parallaxImg3Ref = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // 1. Headline & Subline Entrance
      if (headlineRef.current && sublineRef.current) {
        gsap.fromTo(
          headlineRef.current,
          { y: 40, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            duration: 1.0,
            ease: 'power3.out',
            scrollTrigger: {
              trigger: headlineRef.current,
              start: 'top 85%',
              toggleActions: 'play none none none'
            }
          }
        );

        gsap.fromTo(
          sublineRef.current,
          { y: 20, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            duration: 0.9,
            delay: 0.2,
            ease: 'power2.out',
            scrollTrigger: {
              trigger: headlineRef.current,
              start: 'top 85%',
              toggleActions: 'play none none none'
            }
          }
        );
      }

      // 2. Curtain Clip-Path Reveal on Scroll (Hiệu ứng mở màn rèm cuốn mượt mà)
      const wrappers = [
        imageWrapper1Ref.current,
        imageWrapper2Ref.current,
        imageWrapper3Ref.current
      ].filter(Boolean) as HTMLDivElement[];

      wrappers.forEach((wrapper, idx) => {
        gsap.fromTo(
          wrapper,
          {
            clipPath: 'polygon(0% 100%, 100% 100%, 100% 100%, 0% 100%)',
            opacity: 0.8
          },
          {
            clipPath: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)',
            opacity: 1,
            duration: 1.2,
            delay: idx * 0.15,
            ease: 'power3.inOut',
            scrollTrigger: {
              trigger: wrapper,
              start: 'top 80%',
              toggleActions: 'play none none none'
            }
          }
        );
      });

      // 3. Asymmetric Inertia Parallax (Trượt lệch tốc độ tinh tế khi cuộn)
      if (sectionRef.current) {
        // Ảnh lớn bên trái: trượt chậm (-35px)
        if (parallaxImg1Ref.current) {
          gsap.to(parallaxImg1Ref.current, {
            y: -35,
            ease: 'none',
            scrollTrigger: {
              trigger: sectionRef.current,
              start: 'top bottom',
              end: 'bottom top',
              scrub: 1.2
            }
          });
        }

        // Ảnh nhỏ trên bên phải: trượt vừa (-65px)
        if (parallaxImg2Ref.current) {
          gsap.to(parallaxImg2Ref.current, {
            y: -65,
            ease: 'none',
            scrollTrigger: {
              trigger: sectionRef.current,
              start: 'top bottom',
              end: 'bottom top',
              scrub: 1.2
            }
          });
        }

        // Ảnh nhỏ dưới bên phải: trượt nhanh hơn (-90px)
        if (parallaxImg3Ref.current) {
          gsap.to(parallaxImg3Ref.current, {
            y: -90,
            ease: 'none',
            scrollTrigger: {
              trigger: sectionRef.current,
              start: 'top bottom',
              end: 'bottom top',
              scrub: 1.2
            }
          });
        }
      }
    }, sectionRef);

    return () => {
      ctx.revert();
    };
  }, []);

  return (
    <section
      ref={sectionRef}
      className="bg-paper text-obsidian pt-44 sm:pt-48 pb-28 border-b border-gray-200 transition-colors"
    >
      <div className="max-w-[1240px] mx-auto px-6">
        {/* Editorial Section Header */}
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-8 mb-16 border-b border-gray-200 pb-10">
          <div>
            {/* Slogan chính thức với Typography Option A: Modern Sans + Elegant Serif Italic */}
            <div ref={headlineRef} className="max-w-2xl space-y-1">
              <p className="font-jakarta font-light text-2xl sm:text-4xl lg:text-[44px] text-obsidian tracking-[0.03em] leading-tight block">
                Khác gu một chút.
              </p>
              <h2 className="font-playfair italic font-medium text-4xl sm:text-6xl lg:text-[68px] text-obsidian tracking-tight leading-[1.08] block">
                Đồng điệu một đời.
              </h2>
            </div>
          </div>

          <div className="max-w-md">
            <p
              ref={sublineRef}
              className="text-sm sm:text-base text-charcoal/80 font-light leading-relaxed mb-6"
            >
              Từ bữa tối ấm cúng đến quán cafe yên tĩnh, khám phá những địa điểm phù hợp với cả hai.
            </p>

            {/* Pill Category Tags (100px radius, 0% color saturation for chrome) */}
            <div className="flex flex-wrap gap-2 text-xs">
              <span className="px-3 py-1 bg-obsidian text-paper rounded-full text-[11px] font-medium">
                Tất Cả Không Gian
              </span>
              <span className="px-3 py-1 bg-gray-100 text-charcoal hover:bg-gray-200 rounded-full text-[11px] font-medium transition-colors">
                Fine Dining & Steak
              </span>
              <span className="px-3 py-1 bg-gray-100 text-charcoal hover:bg-gray-200 rounded-full text-[11px] font-medium transition-colors">
                Bàn Tiệc Nến Ấm
              </span>
              <span className="px-3 py-1 bg-gray-100 text-charcoal hover:bg-gray-200 rounded-full text-[11px] font-medium transition-colors">
                Cafe Thư Giãn
              </span>
            </div>
          </div>
        </div>

        {/* ======================================================== */}
        {/* ASYMMETRIC MAGAZINE SPREAD GRID (PHƯƠNG ÁN 1) */}
        {/* ======================================================== */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-start">
          {/* CỘT TRÁI (7 CỘT): ẢNH DỌC ĐỒ SỘ (01 - FINE DINING & STEAKHOUSE) */}
          <div className="lg:col-span-7 group cursor-pointer" onClick={onExplore}>
            <div
              ref={imageWrapper1Ref}
              className="relative overflow-hidden rounded-[8px] border border-gray-200 shadow-xl bg-gray-50 mb-6 h-[460px] sm:h-[560px] will-change-transform"
            >
              <img
                ref={parallaxImg1Ref}
                src="https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=1400&q=85"
                alt="Ảnh Concept: Bò Wagyu nướng sốt nấm & Rượu vang"
                loading="eager"
                className="w-full h-[115%] object-cover group-hover:scale-105 transition-transform duration-700"
              />

              {/* Discreet Concept Label (Ảnh minh họa ngắn gọn theo yêu cầu) */}
              <div className="absolute top-4 left-4 bg-white/95 backdrop-blur-md px-3 py-1 rounded-full text-[10px] font-mono uppercase tracking-wider text-obsidian font-semibold border border-gray-200 shadow-sm flex items-center gap-1.5">
                <Utensils className="w-3 h-3 text-obsidian" />
                <span>Ảnh minh họa • Steakhouse</span>
              </div>

              {/* Experience Highlights Overlay (Tập trung trải nghiệm, không hiển thị thuật toán kỹ thuật) */}
              <div className="absolute bottom-4 left-4 right-4 bg-white/95 backdrop-blur-md p-3.5 rounded-[6px] border border-gray-200 shadow-lg flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-mono uppercase text-charcoal/60 block">
                    Trải Nghiệm Ẩm Thực
                  </span>
                  <span className="font-display-clarkson text-base sm:text-lg text-obsidian font-semibold">
                    Steakhouse & Wine Bar
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] font-mono uppercase text-charcoal/60 block">
                    Không Gian
                  </span>
                  <span className="text-xs font-medium text-obsidian">
                    Ấm Cúng & Riêng Tư
                  </span>
                </div>
              </div>
            </div>

            {/* Editorial Caption & Details */}
            <div className="flex items-baseline justify-between border-b border-gray-200 pb-2 mb-2">
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm text-charcoal/50 font-bold">[01]</span>
                <h3 className="font-display-clarkson text-2xl sm:text-3xl text-obsidian font-bold tracking-tight group-hover:text-black transition-colors">
                  Bò Wagyu Nướng Than & Rượu Vang Đỏ
                </h3>
              </div>
              <span className="text-xs font-mono text-charcoal/60 shrink-0">Quận 1 • Trung Tâm</span>
            </div>
            <p className="text-xs sm:text-sm text-charcoal/80 leading-relaxed font-light">
              Món bò Wagyu nướng xém cạnh thơm phức sốt tiêu đen trong ánh đèn vàng cổ điển, mang lại sự riêng tư cho những dịp kỷ niệm quan trọng.
            </p>
          </div>

          {/* CỘT PHẢI (5 CỘT): 2 KHUNG ẢNH XẾP SO LE (02 & 03) */}
          <div className="lg:col-span-5 space-y-10 lg:pt-6">
            {/* ITEM 02: BÀN TIỆC NẾN ẤM SÂN VƯỜN / VEN SÔNG */}
            <div className="group cursor-pointer" onClick={onExplore}>
              <div
                ref={imageWrapper2Ref}
                className="relative overflow-hidden rounded-[8px] border border-gray-200 shadow-md bg-gray-50 mb-4 h-[260px] sm:h-[280px] will-change-transform"
              >
                <img
                  ref={parallaxImg2Ref}
                  src="https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1000&q=85"
                  alt="Ảnh minh họa: Bàn tiệc nến ấm sân vườn"
                  loading="eager"
                  className="w-full h-[120%] object-cover group-hover:scale-105 transition-transform duration-700"
                />
                <div className="absolute top-3 left-3 bg-white/95 backdrop-blur-md px-2.5 py-0.5 rounded-full text-[9px] font-mono uppercase tracking-wider text-obsidian font-semibold border border-gray-200 shadow-sm flex items-center gap-1">
                  <Sparkles className="w-2.5 h-2.5 text-obsidian" />
                  <span>Ảnh minh họa • Ven Sông</span>
                </div>
              </div>

              <div className="flex items-baseline justify-between border-b border-gray-200 pb-1.5 mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs text-charcoal/50 font-bold">[02]</span>
                  <h4 className="font-display-clarkson text-xl text-obsidian font-bold tracking-tight group-hover:text-black transition-colors">
                    Bàn Ăn Hoàng Hôn Ven Sông
                  </h4>
                </div>
                <span className="text-[11px] font-mono text-charcoal/60">Thảo Điền • Lãng Mạn</span>
              </div>
              <p className="text-xs text-charcoal/80 leading-relaxed font-light">
                Gió sông mát rượi, ánh hoàng hôn buông lơi lúc 17:30 và bàn tiệc ngoài trời nến lung linh giúp cảm xúc thăng hoa.
              </p>
            </div>

            {/* ITEM 03: CÀ PHÊ THỦ CÔNG KÉN GỖ THƯ THÁI */}
            <div className="group cursor-pointer" onClick={onExplore}>
              <div
                ref={imageWrapper3Ref}
                className="relative overflow-hidden rounded-[8px] border border-gray-200 shadow-md bg-gray-50 mb-4 h-[260px] sm:h-[280px] will-change-transform"
              >
                <img
                  ref={parallaxImg3Ref}
                  src="https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=1000&q=85"
                  alt="Ảnh minh họa: Kén gỗ cafe riêng tư"
                  loading="eager"
                  className="w-full h-[120%] object-cover group-hover:scale-105 transition-transform duration-700"
                />
                <div className="absolute top-3 left-3 bg-white/95 backdrop-blur-md px-2.5 py-0.5 rounded-full text-[9px] font-mono uppercase tracking-wider text-obsidian font-semibold border border-gray-200 shadow-sm flex items-center gap-1">
                  <HeartHandshake className="w-2.5 h-2.5 text-obsidian" />
                  <span>Ảnh minh họa • Cafe Thư Thái</span>
                </div>
              </div>

              <div className="flex items-baseline justify-between border-b border-gray-200 pb-1.5 mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs text-charcoal/50 font-bold">[03]</span>
                  <h4 className="font-display-clarkson text-xl text-obsidian font-bold tracking-tight group-hover:text-black transition-colors">
                    Kén Giường Gỗ Riêng Tư
                  </h4>
                </div>
                <span className="text-[11px] font-mono text-charcoal/60">Quận 3 • Yên Tĩnh</span>
              </div>
              <p className="text-xs text-charcoal/80 leading-relaxed font-light">
                Không gian trà đào dầm và nệm êm kiểu Nhật, lý tưởng cho những cuộc tâm tình sâu sắc sau bữa tối.
              </p>
            </div>
          </div>
        </div>

        {/* Bottom Editorial Action */}
        <div className="mt-16 pt-8 border-t border-gray-200 flex justify-end">
          <button
            onClick={onExplore}
            className="btn-ghost-black cursor-pointer text-xs flex items-center gap-1.5 py-2.5 px-6"
          >
            <span>Khám Phá Toàn Bộ Quán Tuyển Chọn</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </section>
  );
};
