import React, { useState, useEffect, useRef } from 'react';
import {
  ArrowLeft,
  Play,
  Pause,
  RefreshCw,
  Layers,
  ZoomIn,
  Type,
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  Sliders,
  Sparkles,
  Layout,
  SlidersHorizontal,
  MoveRight,
  Eye,
  Camera,
  Compass,
  Clock
} from 'lucide-react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

import { TypographyApprovalStudio } from './TypographyApprovalStudio';

interface VideoOption {
  id: number;
  title: string;
  category: string;
  localSrc: string;
  remoteSrc: string;
  pageUrl: string;
  duration: string;
  resolution: string;
  license: string;
  description: string;
  thumbnail: string;
}

const DEMO_VIDEOS: VideoOption[] = [
  {
    id: 1,
    title: 'Mẫu 1: Rót Rượu Vang Nến Ấm',
    category: 'Fine Dining & Wine Date',
    localSrc: '/media/video-1-wine.mp4',
    remoteSrc: 'https://assets.mixkit.co/videos/42775/42775-720.mp4',
    pageUrl: 'https://mixkit.co/free-stock-video/pouring-wine-in-a-couple-of-glasses-on-a-date-42775/',
    duration: '14 giây',
    resolution: '1080p Full HD (24fps)',
    license: 'Mixkit Free License (Thương mại tự do, không cần ghi nguồn)',
    description: 'Cận cảnh rót rượu vang đỏ vào ly pha lê, ánh nến lung linh và bàn gỗ ấm cúng tạo cảm giác riêng tư, sang trọng.',
    thumbnail: 'https://assets.mixkit.co/videos/42775/42775-thumb-720-0.jpg'
  },
  {
    id: 2,
    title: 'Mẫu 2: Cụng Ly Bàn Tiệc Nhà Hàng (ĐÃ DUYỆT)',
    category: 'Restaurant & Celebration',
    localSrc: '/media/video-2-toast.mp4',
    remoteSrc: 'https://assets.mixkit.co/videos/45727/45727-720.mp4',
    pageUrl: 'https://mixkit.co/free-stock-video/two-friends-sharing-a-toast-over-a-meal-45727/',
    duration: '7 giây',
    resolution: '1080p Full HD (24fps)',
    license: 'Mixkit Free License (Thương mại tự do)',
    description: 'Bàn tiệc thịnh soạn, hai người chạm ly rượu vang ấm áp bên món ăn ngon mắt, ánh sáng nhà hàng tự nhiên và sáng rõ.',
    thumbnail: 'https://assets.mixkit.co/videos/45727/45727-thumb-720-2.jpg'
  },
  {
    id: 3,
    title: 'Mẫu 3: Cafe Bọt Sữa Gỗ Sáng',
    category: 'Artisan Cafe & Cozy Date',
    localSrc: '/media/video-3-coffee.mp4',
    remoteSrc: 'https://assets.mixkit.co/videos/41859/41859-720.mp4',
    pageUrl: 'https://mixkit.co/free-stock-video/serving-a-sparkling-cappuccino-in-a-cup-41859/',
    duration: '13 giây',
    resolution: '1080p Full HD (60fps)',
    license: 'Mixkit Free License (Thương mại tự do)',
    description: 'Pha chế tách cappuccino bọt sữa mịn màng trên bàn gỗ sáng màu, phong cách hẹn hò cafe thư thái, nhẹ nhàng.',
    thumbnail: 'https://assets.mixkit.co/videos/41859/41859-thumb-720-0.jpg'
  },
  {
    id: 4,
    title: 'Mẫu 4: Hoàng Hôn Rooftop Sài Gòn',
    category: 'Skyline & City Lights',
    localSrc: '/media/video-4-rooftop.mp4',
    remoteSrc: 'https://assets.mixkit.co/videos/3516/3516-720.mp4',
    pageUrl: 'https://mixkit.co/free-stock-video/urban-view-from-a-rooftop-and-the-sunset-3516/',
    duration: '20 giây',
    resolution: '1080p Full HD (30fps)',
    license: 'Mixkit Free License (Thương mại tự do)',
    description: 'Toàn cảnh thành phố từ tầng cao khi hoàng hôn vàng rực chuyển dần sang ánh đèn đêm lung linh, lãng mạn.',
    thumbnail: 'https://assets.mixkit.co/videos/3516/3516-thumb-720-0.jpg'
  }
];

export interface CuratedConceptImage {
  id: number;
  title: string;
  conceptGenre: string;
  url: string;
  sourceUrl: string;
  author: string;
  license: string;
  description: string;
}

export const CURATED_CONCEPT_IMAGES: CuratedConceptImage[] = [
  {
    id: 1,
    title: 'Bò Wagyu Nướng Sốt Nấm & Rượu Vang',
    conceptGenre: 'Ảnh Concept Ẩm Thực Steakhouse & Fine Dining',
    url: 'https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=1200&q=85',
    sourceUrl: 'https://unsplash.com/photos/cooked-food-on-plate-cpLsKEBsSgY',
    author: 'Emerson Vieira',
    license: 'Unsplash Free Commercial License',
    description: 'Thịt bò nướng xém cạnh, sốt tiêu đen bóng bẩy và đĩa gốm mộc tối giản. Ánh sáng tự nhiên không dùng bộ lọc màu nhân tạo.'
  },
  {
    id: 2,
    title: 'Bàn Tiệc Nến Ấm & Không Gian Mở Lãng Mạn',
    conceptGenre: 'Ảnh Concept Không Gian Sân Vườn & Ven Sông',
    url: 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=85',
    sourceUrl: 'https://unsplash.com/photos/poeR2EIfCh0',
    author: 'Jason Leung',
    license: 'Unsplash Free Commercial License',
    description: 'Ánh nến lung linh trên bàn gỗ ngoài trời, hoa tươi và ly rượu pha lê. Tái hiện trọn vẹn cảm xúc lãng mạn nhẹ nhàng.'
  },
  {
    id: 3,
    title: 'Bàn Nướng Than Yakiniku Cao Cấp',
    conceptGenre: 'Ảnh Concept Ẩm Thực Nướng Hiện Đại',
    url: 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1200&q=85',
    sourceUrl: 'https://unsplash.com/photos/N_Y88TWmGwA',
    author: 'Jay Wennington',
    license: 'Unsplash Free Commercial License',
    description: 'Từng thớ thịt bò cẩm thạch tươi ngon trên than hồng, không khí ấm cúng, sang trọng và chuẩn vị hẹn hò sành điệu.'
  },
  {
    id: 4,
    title: 'Cà Phê Thủ Công Kén Gỗ & Trà Đọc Sách',
    conceptGenre: 'Ảnh Concept Không Gian Cafe Thư Giãn / Riêng Tư',
    url: 'https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=1200&q=85',
    sourceUrl: 'https://unsplash.com/photos/yRjQnjfWw2Y',
    author: 'Tim Wright',
    license: 'Unsplash Free Commercial License',
    description: 'Ánh sáng cửa sổ rọi vào ly cappuccino bọt sữa mịn và bàn gỗ sồi sáng màu, lý tưởng cho những cặp đôi thích yên tĩnh.'
  },
  {
    id: 5,
    title: 'Ẩm Thực Sáng Tạo Đương Đại (Tasting Menu)',
    conceptGenre: 'Ảnh Concept Ẩm Thực Michelin & Nghệ Thuật Đĩa Ăn',
    url: 'https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?auto=format&fit=crop&w=1200&q=85',
    sourceUrl: 'https://unsplash.com/photos/xIFbDeGcy44',
    author: 'Stefan Johnson',
    license: 'Unsplash Free Commercial License',
    description: 'Đĩa ăn tối giản với thảo mộc tươi và nước sốt vẽ nghệ thuật, thể hiện đẳng cấp ẩm thực đỉnh cao của đô thị hiện đại.'
  }
];

export const HeroMotionDemo: React.FC<{ onBackToMain: () => void }> = ({ onBackToMain }) => {
  // Navigation tabs in demo playground (Default to Typography Studio as requested for Approval Gate)
  const [activeTab, setActiveTab] = useState<'typography-studio' | 'layout-proposals' | 'interactive-options' | 'curated-gallery' | 'hero-review'>('typography-studio');

  // Active section 2 interactive layout option
  const [activeLayoutOption, setActiveLayoutOption] = useState<'option1' | 'option2' | 'option3'>('option1');

  // Selected image preview modal
  const [previewImage, setPreviewImage] = useState<CuratedConceptImage | null>(null);

  // Hero controls (Video 2 selected by default as approved)
  const [selectedVideo, setSelectedVideo] = useState<VideoOption>(DEMO_VIDEOS[1]);
  const [isPlaying, setIsPlaying] = useState(true);
  const [overlayStyle, setOverlayStyle] = useState<'vivid' | 'gradient' | 'tint'>('gradient');

  // References
  const videoRef = useRef<HTMLVideoElement>(null);
  const heroRef = useRef<HTMLDivElement>(null);
  const headlineRef = useRef<HTMLHeadingElement>(null);
  const sublineRef = useRef<HTMLParagraphElement>(null);
  const cardsRef = useRef<HTMLDivElement>(null);
  const card1Ref = useRef<HTMLDivElement>(null);
  const card2Ref = useRef<HTMLDivElement>(null);
  const card3Ref = useRef<HTMLDivElement>(null);

  // Layout 1 references (Magazine Curtain Reveal)
  const option1Ref = useRef<HTMLDivElement>(null);
  const curtain1Ref = useRef<HTMLDivElement>(null);
  const curtain2Ref = useRef<HTMLDivElement>(null);

  // Layout 2 references (Horizontal Track)
  const option2Ref = useRef<HTMLDivElement>(null);
  const horizontalTrackRef = useRef<HTMLDivElement>(null);

  // Layout 3 references (Split Storytelling)
  const option3Ref = useRef<HTMLDivElement>(null);

  // Play / Pause toggle
  const togglePlay = () => {
    if (videoRef.current) {
      if (videoRef.current.paused) {
        videoRef.current.play();
        setIsPlaying(true);
      } else {
        videoRef.current.pause();
        setIsPlaying(false);
      }
    }
  };

  // Replay Text Entrance Animation
  const triggerTextEntrance = () => {
    if (headlineRef.current && sublineRef.current) {
      gsap.fromTo(
        headlineRef.current,
        { y: 50, opacity: 0, letterSpacing: '-0.02em' },
        { y: 0, opacity: 1, letterSpacing: '-0.06em', duration: 1.2, ease: 'power3.out' }
      );
      gsap.fromTo(
        sublineRef.current,
        { y: 30, opacity: 0 },
        { y: 0, opacity: 1, duration: 1.0, delay: 0.3, ease: 'power2.out' }
      );
    }
  };

  // Hero GSAP ScrollTrigger setup
  useEffect(() => {
    triggerTextEntrance();

    if (videoRef.current && heroRef.current) {
      const zoomTween = gsap.to(videoRef.current, {
        scale: 1.12,
        ease: 'none',
        scrollTrigger: {
          trigger: heroRef.current,
          start: 'top top',
          end: 'bottom top',
          scrub: 1.2
        }
      });

      let cardTween: gsap.core.Timeline | null = null;
      if (card1Ref.current && card2Ref.current && card3Ref.current) {
        cardTween = gsap.timeline({
          scrollTrigger: {
            trigger: heroRef.current,
            start: 'center top',
            end: 'bottom top',
            scrub: 1
          }
        });

        cardTween
          .to(card1Ref.current, { y: -40, ease: 'none' }, 0)
          .to(card2Ref.current, { y: -75, ease: 'none' }, 0)
          .to(card3Ref.current, { y: -50, ease: 'none' }, 0);
      }

      return () => {
        zoomTween.kill();
        if (cardTween) cardTween.kill();
        ScrollTrigger.getAll().forEach((t) => t.kill());
      };
    }
  }, []);

  return (
    <div className="min-h-screen bg-obsidian text-paper font-sans">
      {/* ======================================================== */}
      {/* TOP DEMO STUDIO CONTROLS HEADER */}
      {/* ======================================================== */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-obsidian/95 backdrop-blur-md border-b border-charcoal px-6 py-3 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <button
            onClick={onBackToMain}
            className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-ash hover:text-paper border border-charcoal hover:border-paper px-3 py-1.5 transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Về Website Chính</span>
          </button>

          {/* Tab Switchers */}
          <div className="flex items-center bg-charcoal/40 p-1 rounded-[6px] border border-charcoal">
            <button
              onClick={() => setActiveTab('typography-studio')}
              className={`px-3 py-1 text-xs font-medium rounded-[4px] transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'typography-studio'
                  ? 'bg-paper text-obsidian font-bold shadow-sm'
                  : 'text-amber-400 hover:text-paper'
              }`}
            >
              <Type className="w-3.5 h-3.5" />
              <span>3 Phương Án Typography</span>
            </button>

            <button
              onClick={() => setActiveTab('layout-proposals')}
              className={`px-3 py-1 text-xs font-medium rounded-[4px] transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'layout-proposals'
                  ? 'bg-paper text-obsidian font-bold shadow-sm'
                  : 'text-ash hover:text-paper'
              }`}
            >
              <Layout className="w-3.5 h-3.5" />
              <span>3 Mockup Bố Cục Section 2</span>
            </button>

            <button
              onClick={() => setActiveTab('interactive-options')}
              className={`px-3 py-1 text-xs font-medium rounded-[4px] transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'interactive-options'
                  ? 'bg-paper text-obsidian font-bold shadow-sm'
                  : 'text-ash hover:text-paper'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Demo Chuyển Động Trực Quan</span>
            </button>

            <button
              onClick={() => setActiveTab('curated-gallery')}
              className={`px-3 py-1 text-xs font-medium rounded-[4px] transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'curated-gallery'
                  ? 'bg-paper text-obsidian font-bold shadow-sm'
                  : 'text-ash hover:text-paper'
              }`}
            >
              <Camera className="w-3.5 h-3.5" />
              <span>5 Ảnh Concept Ẩm Thực</span>
            </button>

            <button
              onClick={() => setActiveTab('hero-review')}
              className={`px-3 py-1 text-xs font-medium rounded-[4px] transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'hero-review'
                  ? 'bg-paper text-obsidian font-bold shadow-sm'
                  : 'text-ash hover:text-paper'
              }`}
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-green-400" />
              <span>Hero Đã Duyệt</span>
            </button>
          </div>
        </div>

        <div className="text-[11px] font-mono text-ash flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
          <span>Typography & Editorial Approval Studio</span>
        </div>
      </header>

      {/* Main Studio Views Container */}
      <div className="pt-20">
        {/* ======================================================== */}
        {/* TAB 0: 3 PHƯƠNG ÁN TYPOGRAPHY (EDITORIAL APPROVAL GATE) */}
        {/* ======================================================== */}
        {activeTab === 'typography-studio' && <TypographyApprovalStudio />}

        {/* ======================================================== */}
        {/* TAB 1: 3 MOCKUP BỐ CỤC SECTION 2 (HÌNH ẢNH TRỰC QUAN) */}
        {/* ======================================================== */}
        {activeTab === 'layout-proposals' && (
          <section className="max-w-[1300px] mx-auto px-6 py-12">
            <div className="text-center max-w-3xl mx-auto mb-12">
              <span className="text-xs uppercase tracking-widest text-ash bg-white/5 border border-white/10 px-3.5 py-1.5 rounded-full inline-block mb-4 font-mono">
                Mandatory Media & Motion Approval Gate
              </span>
              <h1 className="font-display-clarkson text-4xl sm:text-5xl text-paper tracking-tighter mb-4">
                3 PHƯƠNG ÁN BỐ CỤC SECTION 2 (WHITE CANVAS)
              </h1>
              <p className="text-ash text-sm sm:text-base leading-relaxed">
                Được thiết kế theo đúng chuẩn phong cách <strong>Squarespace Editorial & Cinematic</strong>: Nền trắng tuyết thuần khiết, tương phản chữ đen sắc nét, hình ảnh ẩm thực giữ màu sắc tự nhiên và áp dụng hiệu ứng GSAP nâng cao.
              </p>
            </div>

            {/* 3 Mockup Cards Grid */}
            <div className="space-y-16">
              {/* Option 1 Mockup */}
              <div className="bg-charcoal/20 border border-white/20 rounded-[8px] overflow-hidden p-6 lg:p-8">
                <div className="flex flex-col lg:flex-row gap-8 items-start">
                  <div className="w-full lg:w-3/5 overflow-hidden rounded-[6px] border border-white/10 shadow-2xl">
                    <img
                      src="/media/mockup-section2-magazine.jpg"
                      alt="Mockup Phương án 1: Asymmetric Magazine Spread"
                      className="w-full h-auto object-cover hover:scale-[1.02] transition-transform duration-700"
                    />
                  </div>
                  <div className="w-full lg:w-2/5 space-y-4">
                    <div className="inline-flex items-center gap-2 text-[10px] font-mono uppercase tracking-wider text-green-400 bg-green-500/10 border border-green-500/20 px-2.5 py-1 rounded-full">
                      <Sparkles className="w-3 h-3" />
                      <span>Phương Án 1 (Khuyên Dùng)</span>
                    </div>
                    <h3 className="font-display-clarkson text-2xl sm:text-3xl text-paper tracking-tight">
                      Bố Cục Tạp Chí Bất Đối Xứng (Asymmetric Magazine Spread)
                    </h3>
                    <p className="text-xs text-ash leading-relaxed">
                      Lấy cảm hứng từ các tạp chí kiến trúc và ẩm thực hàng đầu (Kinfolk, Cereal). Sử dụng 1 ảnh dọc đồ sộ bên trái làm tiêu điểm thị giác, kết hợp 2 khung ảnh không gian và bàn tiệc bên phải được đánh số thứ tự biên tập <code className="text-paper">01 / 02 / 03</code>.
                    </p>

                    <div className="bg-obsidian/60 p-4 border border-charcoal rounded-[6px] space-y-2 text-xs">
                      <div className="text-paper font-semibold flex items-center gap-1.5">
                        <Layers className="w-3.5 h-3.5 text-paper" />
                        <span>Hiệu Ứng GSAP Đề Xuất:</span>
                      </div>
                      <ul className="text-ash space-y-1.5 list-disc pl-4 text-[11px] leading-relaxed">
                        <li>
                          <strong className="text-paper">Curtain Clip-Path Reveal:</strong> Khi cuộn đến, ảnh mở ra bằng hiệu ứng mở rèm clip-path đa giác từ chân ảnh lên đỉnh mượt mà.
                        </li>
                        <li>
                          <strong className="text-paper">Asymmetric Inertia Parallax:</strong> Khung ảnh lớn trượt chậm (`y: -30px`), 2 khung ảnh nhỏ trượt nhanh hơn (`y: -75px`) tạo cảm giác trôi nổi tự nhiên.
                        </li>
                      </ul>
                    </div>

                    <button
                      onClick={() => {
                        setActiveLayoutOption('option1');
                        setActiveTab('interactive-options');
                      }}
                      className="btn-filled-white cursor-pointer w-full text-center text-xs py-3 flex items-center justify-center gap-2"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Xem Bản Demo Chuyển Động Trực Tiếp (PA 1)</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Option 2 Mockup */}
              <div className="bg-charcoal/20 border border-white/20 rounded-[8px] overflow-hidden p-6 lg:p-8">
                <div className="flex flex-col lg:flex-row gap-8 items-start">
                  <div className="w-full lg:w-3/5 overflow-hidden rounded-[6px] border border-white/10 shadow-2xl">
                    <img
                      src="/media/mockup-section2-horizontal.jpg"
                      alt="Mockup Phương án 2: Horizontal Image Gallery Scrub"
                      className="w-full h-auto object-cover hover:scale-[1.02] transition-transform duration-700"
                    />
                  </div>
                  <div className="w-full lg:w-2/5 space-y-4">
                    <div className="inline-flex items-center gap-2 text-[10px] font-mono uppercase tracking-wider text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2.5 py-1 rounded-full">
                      <MoveRight className="w-3 h-3" />
                      <span>Phương Án 2 (Đột Phá Điện Ảnh)</span>
                    </div>
                    <h3 className="font-display-clarkson text-2xl sm:text-3xl text-paper tracking-tight">
                      Dải Cuộn Ngang Điện Ảnh (Horizontal Track Scrub)
                    </h3>
                    <p className="text-xs text-ash leading-relaxed">
                      Lấy cảm hứng từ các Lookbook triển lãm của Squarespace. Toàn bộ dải hình ảnh ẩm thực và không gian trượt ngang khi người dùng cuộn chuột dọc, kèm thanh tiến độ phân đoạn tối giản phía chân trang.
                    </p>

                    <div className="bg-obsidian/60 p-4 border border-charcoal rounded-[6px] space-y-2 text-xs">
                      <div className="text-paper font-semibold flex items-center gap-1.5">
                        <Layers className="w-3.5 h-3.5 text-paper" />
                        <span>Hiệu Ứng GSAP Đề Xuất:</span>
                      </div>
                      <ul className="text-ash space-y-1.5 list-disc pl-4 text-[11px] leading-relaxed">
                        <li>
                          <strong className="text-paper">ScrollTrigger Pin & Horizontal Scrub:</strong> Ghim màn hình tại Section 2 và chuyển động cuộn dọc thành cuộn ngang mượt mà (`xPercent: -60%`).
                        </li>
                        <li>
                          <strong className="text-paper">Counter Parallax Inside Cards:</strong> Ảnh bên trong khung chuyển động nhẹ ngược chiều tạo độ sâu thị giác ấn tượng.
                        </li>
                      </ul>
                    </div>

                    <button
                      onClick={() => {
                        setActiveLayoutOption('option2');
                        setActiveTab('interactive-options');
                      }}
                      className="btn-filled-white cursor-pointer w-full text-center text-xs py-3 flex items-center justify-center gap-2"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Xem Bản Demo Chuyển Động Trực Tiếp (PA 2)</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Option 3 Mockup */}
              <div className="bg-charcoal/20 border border-white/20 rounded-[8px] overflow-hidden p-6 lg:p-8">
                <div className="flex flex-col lg:flex-row gap-8 items-start">
                  <div className="w-full lg:w-3/5 overflow-hidden rounded-[6px] border border-white/10 shadow-2xl">
                    <img
                      src="/media/mockup-section2-split.jpg"
                      alt="Mockup Phương án 3: Sticky Split Storytelling"
                      className="w-full h-auto object-cover hover:scale-[1.02] transition-transform duration-700"
                    />
                  </div>
                  <div className="w-full lg:w-2/5 space-y-4">
                    <div className="inline-flex items-center gap-2 text-[10px] font-mono uppercase tracking-wider text-purple-400 bg-purple-500/10 border border-purple-500/20 px-2.5 py-1 rounded-full">
                      <Clock className="w-3 h-3" />
                      <span>Phương Án 3 (Kể Chuyện Lộ Trình)</span>
                    </div>
                    <h3 className="font-display-clarkson text-2xl sm:text-3xl text-paper tracking-tight">
                      Kể Chuyện Phân Cột (Sticky Split Storytelling)
                    </h3>
                    <p className="text-xs text-ash leading-relaxed">
                      Phân chia 40/60: Cột trái cố định (`sticky`) hiển thị thông điệp triết lý và mốc thời gian hẹn hò (`Stage 01 • Hoàng hôn khai vị`, `Stage 02 • Bữa tối nến ấm`), trong khi cột phải cuộn trôi các bức ảnh ẩm thực lớn.
                    </p>

                    <div className="bg-obsidian/60 p-4 border border-charcoal rounded-[6px] space-y-2 text-xs">
                      <div className="text-paper font-semibold flex items-center gap-1.5">
                        <Layers className="w-3.5 h-3.5 text-paper" />
                        <span>Hiệu Ứng GSAP Đề Xuất:</span>
                      </div>
                      <ul className="text-ash space-y-1.5 list-disc pl-4 text-[11px] leading-relaxed">
                        <li>
                          <strong className="text-paper">Sticky Content Synchronizer:</strong> Khi ảnh ở cột phải trượt vào tầm nhìn, cột trái tự động chuyển trạng thái active mượt mà.
                        </li>
                        <li>
                          <strong className="text-paper">Scale & Luminosity Focus:</strong> Khung ảnh trung tâm tự động sáng rõ 100% và bung nhẹ `scale(1.02)`.
                        </li>
                      </ul>
                    </div>

                    <button
                      onClick={() => {
                        setActiveLayoutOption('option3');
                        setActiveTab('interactive-options');
                      }}
                      className="btn-filled-white cursor-pointer w-full text-center text-xs py-3 flex items-center justify-center gap-2"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Xem Bản Demo Chuyển Động Trực Tiếp (PA 3)</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* ======================================================== */}
        {/* TAB 2: DEMO CHUYỂN ĐỘNG TRỰC TIẾP (LIVE GSAP CODE) */}
        {/* ======================================================== */}
        {activeTab === 'interactive-options' && (
          <section className="bg-paper text-obsidian min-h-screen py-16">
            {/* Sticky Option Selector Bar inside White Canvas */}
            <div className="sticky top-16 z-40 bg-white/95 backdrop-blur-md border-b border-gray-200 py-3 px-6 mb-12 shadow-sm">
              <div className="max-w-[1200px] mx-auto flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold uppercase tracking-wider text-charcoal">
                    Đang thử nghiệm phương án:
                  </span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => setActiveLayoutOption('option1')}
                      className={`px-3 py-1 text-xs font-medium border cursor-pointer transition-colors ${
                        activeLayoutOption === 'option1'
                          ? 'bg-black text-white border-black font-semibold'
                          : 'bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200'
                      }`}
                    >
                      PA 1: Tạp Chí (Asymmetric)
                    </button>
                    <button
                      onClick={() => setActiveLayoutOption('option2')}
                      className={`px-3 py-1 text-xs font-medium border cursor-pointer transition-colors ${
                        activeLayoutOption === 'option2'
                          ? 'bg-black text-white border-black font-semibold'
                          : 'bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200'
                      }`}
                    >
                      PA 2: Dải Cuộn Ngang (Horizontal)
                    </button>
                    <button
                      onClick={() => setActiveLayoutOption('option3')}
                      className={`px-3 py-1 text-xs font-medium border cursor-pointer transition-colors ${
                        activeLayoutOption === 'option3'
                          ? 'bg-black text-white border-black font-semibold'
                          : 'bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200'
                      }`}
                    >
                      PA 3: Phân Cột Kể Chuyện (Split)
                    </button>
                  </div>
                </div>

                <div className="text-[11px] font-mono text-gray-500">
                  Cuộn trang xuống để xem hiệu ứng hoạt động thực tế
                </div>
              </div>
            </div>

            {/* LIVE OPTION 1: Asymmetric Magazine Spread (ĐÃ ĐƯỢC PHÊ DUYỆT) */}
            {activeLayoutOption === 'option1' && (
              <div className="max-w-[1200px] mx-auto px-6 py-8">
                <div className="mb-14">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-black" />
                    <span className="text-xs font-mono uppercase tracking-widest text-gray-600 font-medium">
                      KHÁM PHÁ KHÔNG GIAN HẸN HÒ
                    </span>
                  </div>
                  <h2 className="font-display-clarkson font-light text-3xl sm:text-5xl lg:text-[54px] text-obsidian tracking-tight leading-[1.12] max-w-3xl mb-4">
                    Khác gu một chút.
                    <br />
                    Đồng điệu một đời.
                  </h2>
                  <p className="text-sm sm:text-base text-gray-600 max-w-xl font-light leading-relaxed">
                    Từ bữa tối ấm cúng đến quán cafe yên tĩnh, khám phá những địa điểm phù hợp với cả hai.
                  </p>
                </div>

                {/* Asymmetric 2-Column Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
                  {/* Left Column: Big Vertical Showcase (01) */}
                  <div className="lg:col-span-7 group cursor-pointer">
                    <div className="relative overflow-hidden rounded-[8px] border border-gray-200 shadow-xl bg-gray-50 mb-4 h-[520px]">
                      <img
                        src="https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=1200&q=85"
                        alt="Ảnh concept: Steak Wagyu sốt nấm"
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                      />
                      <div className="absolute top-4 left-4 bg-white/95 backdrop-blur-md px-3 py-1 rounded-full text-[10px] font-mono uppercase tracking-wider text-black font-semibold border border-gray-200">
                        Ảnh Concept: Steakhouse & Fine Dining
                      </div>
                      <div className="absolute bottom-4 right-4 bg-black/80 backdrop-blur-md text-white text-xs font-mono px-3 py-1.5 rounded-[4px]">
                        ABSA Food: 95/100
                      </div>
                    </div>
                    <div className="flex items-baseline justify-between border-b border-gray-200 pb-2 mb-2">
                      <span className="font-display-clarkson text-2xl text-obsidian font-bold">01. Bò Wagyu Nướng Than & Rượu Vang</span>
                      <span className="text-xs font-mono text-gray-500">Quận 1 • Đẳng Cấp</span>
                    </div>
                    <p className="text-xs text-gray-600 leading-relaxed font-light">
                      Hương vị nướng mộc tự nhiên, thớ thịt mềm tan và ánh nến vàng New York cổ điển cho buổi tối hẹn hò khó quên.
                    </p>
                  </div>

                  {/* Right Column: 2 Stacked Asymmetric Vignettes (02 & 03) */}
                  <div className="lg:col-span-5 space-y-10 lg:pt-8">
                    {/* Item 02 */}
                    <div className="group cursor-pointer">
                      <div className="relative overflow-hidden rounded-[8px] border border-gray-200 shadow-md bg-gray-50 mb-3 h-[240px]">
                        <img
                          src="https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=85"
                          alt="Ảnh concept: Bàn tiệc nến ấm sân vườn"
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                        />
                        <div className="absolute top-3 left-3 bg-white/95 backdrop-blur-md px-2.5 py-0.5 rounded-full text-[9px] font-mono uppercase tracking-wider text-black font-semibold border border-gray-200">
                          Ảnh Concept: Ven Sông & Hoàng Hôn
                        </div>
                      </div>
                      <div className="flex items-baseline justify-between border-b border-gray-200 pb-1.5 mb-1.5">
                        <span className="font-display-clarkson text-xl text-obsidian font-bold">02. Không Gian Nến Ấm Ven Sông</span>
                        <span className="text-[11px] font-mono text-gray-500">Thảo Điền • Lãng Mạn</span>
                      </div>
                      <p className="text-xs text-gray-600 leading-relaxed font-light">
                        Bàn ăn ngoài trời thoáng đãng, đón gió sông mát lành và ánh hoàng hôn buông lơi lúc 17:30.
                      </p>
                    </div>

                    {/* Item 03 */}
                    <div className="group cursor-pointer">
                      <div className="relative overflow-hidden rounded-[8px] border border-gray-200 shadow-md bg-gray-50 mb-3 h-[240px]">
                        <img
                          src="https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=800&q=85"
                          alt="Ảnh concept: Kén gỗ cafe riêng tư"
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                        />
                        <div className="absolute top-3 left-3 bg-white/95 backdrop-blur-md px-2.5 py-0.5 rounded-full text-[9px] font-mono uppercase tracking-wider text-black font-semibold border border-gray-200">
                          Ảnh Concept: Cafe Thư Thái
                        </div>
                      </div>
                      <div className="flex items-baseline justify-between border-b border-gray-200 pb-1.5 mb-1.5">
                        <span className="font-display-clarkson text-xl text-obsidian font-bold">03. Kén Giường Gỗ Riêng Tư</span>
                        <span className="text-[11px] font-mono text-gray-500">Quận 3 • Yên Tĩnh</span>
                      </div>
                      <p className="text-xs text-gray-600 leading-relaxed font-light">
                        Không gian trà đào dầm và nệm êm kiểu Nhật, lý tưởng cho những cuộc trò chuyện sâu sắc không bị làm phiền.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* LIVE OPTION 2: Horizontal Gallery Scrub */}
            {activeLayoutOption === 'option2' && (
              <div className="py-8">
                <div className="max-w-[1200px] mx-auto px-6 mb-8">
                  <span className="text-xs font-mono uppercase tracking-widest text-gray-500 block mb-2">
                    Horizontal Motion Experience • Cuộn Dọc Thành Cuộn Ngang
                  </span>
                  <h2 className="font-display-clarkson text-4xl sm:text-6xl text-obsidian tracking-tighter leading-[1.0] mb-4">
                    BẢN GIAO HƯỞNG CỦA HƯƠNG VỊ & CHUYỂN ĐỘNG
                  </h2>
                  <p className="text-sm text-gray-600 max-w-xl font-light">
                    Kéo chuột sang ngang hoặc cuộn để khám phá các khung cảnh ẩm thực được sắp xếp liền mạch như một thước phim điện ảnh.
                  </p>
                </div>

                {/* Horizontal Scrolling Strip Container */}
                <div className="overflow-x-auto pb-8 pt-4 px-6 flex gap-6 snap-x snap-mandatory scrollbar-none">
                  {CURATED_CONCEPT_IMAGES.map((img, idx) => (
                    <div
                      key={img.id}
                      className="min-w-[340px] sm:min-w-[420px] bg-white border border-gray-200 rounded-[8px] overflow-hidden shadow-lg snap-start shrink-0 group cursor-pointer hover:border-black transition-all"
                    >
                      <div className="h-[380px] overflow-hidden relative">
                        <img
                          src={img.url}
                          alt={img.title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                        />
                        <div className="absolute top-3 left-3 bg-black/80 text-white text-[10px] font-mono uppercase px-2.5 py-1 rounded-[4px]">
                          0{idx + 1} • {img.conceptGenre}
                        </div>
                      </div>
                      <div className="p-5">
                        <h4 className="font-display-clarkson text-xl text-obsidian tracking-tight mb-1">
                          {img.title}
                        </h4>
                        <p className="text-xs text-gray-600 line-clamp-2 font-light mb-3">
                          {img.description}
                        </p>
                        <div className="flex items-center justify-between text-[11px] font-mono text-gray-400 border-t border-gray-100 pt-2">
                          <span>Nhiếp ảnh: {img.author}</span>
                          <span className="text-black font-semibold">Khám phá →</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* LIVE OPTION 3: Sticky Split Storytelling */}
            {activeLayoutOption === 'option3' && (
              <div className="max-w-[1200px] mx-auto px-6 py-8">
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
                  {/* Sticky Left Column */}
                  <div className="lg:col-span-5 lg:sticky lg:top-36 space-y-6">
                    <span className="text-xs font-mono uppercase tracking-widest text-gray-500 block">
                      Chronological Date Flow • Phân Cột Kể Chuyện
                    </span>
                    <h2 className="font-display-clarkson text-4xl sm:text-5xl text-obsidian tracking-tighter leading-[1.0]">
                      MỘT BUỔI TỐI ĐÁNG NHỚ CHO CẢ HAI
                    </h2>
                    <p className="text-sm text-gray-600 font-light leading-relaxed">
                      Lộ trình hẹn hò được thuật toán tính toán chuyển động tự nhiên theo 3 giai đoạn cảm xúc trong đêm Sài Gòn.
                    </p>

                    <div className="space-y-4 pt-4 border-t border-gray-200">
                      <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-[6px] border border-gray-200">
                        <span className="w-6 h-6 rounded-full bg-black text-white text-xs flex items-center justify-center font-bold font-mono">
                          1
                        </span>
                        <div>
                          <div className="text-xs font-bold text-obsidian">17:30 – Hoàng Hôn Khai Vị</div>
                          <div className="text-[11px] text-gray-500 font-light">Thưởng ngoạn ly cocktail bên sông mát dịu</div>
                        </div>
                      </div>

                      <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-[6px] border border-gray-200">
                        <span className="w-6 h-6 rounded-full bg-black text-white text-xs flex items-center justify-center font-bold font-mono">
                          2
                        </span>
                        <div>
                          <div className="text-xs font-bold text-obsidian">19:15 – Bữa Tối Nến Ấm</div>
                          <div className="text-[11px] text-gray-500 font-light">Bò nướng than và rượu vang trong tiếng nhạc jazz</div>
                        </div>
                      </div>

                      <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-[6px] border border-gray-200">
                        <span className="w-6 h-6 rounded-full bg-black text-white text-xs flex items-center justify-center font-bold font-mono">
                          3
                        </span>
                        <div>
                          <div className="text-xs font-bold text-obsidian">21:00 – Tâm Tình & Tráng Miệng</div>
                          <div className="text-[11px] text-gray-500 font-light">Không gian kén gỗ riêng tư hoặc rooftop tầng cao</div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Scrolling Right Column: Big Story Cards */}
                  <div className="lg:col-span-7 space-y-12">
                    <div className="border border-gray-200 rounded-[8px] overflow-hidden bg-white shadow-xl">
                      <div className="h-[360px] overflow-hidden">
                        <img
                          src="https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=85"
                          alt="Giai đoạn 1"
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <div className="p-6">
                        <span className="text-[10px] font-mono uppercase text-gray-500">Chặng 01 • Khởi đầu</span>
                        <h4 className="font-display-clarkson text-2xl text-obsidian mb-2">Đón Hoàng Hôn Bên Bờ Sông Sài Gòn</h4>
                        <p className="text-xs text-gray-600 font-light leading-relaxed">
                          Gió sông mát rượi xua tan mệt mỏi sau ngày làm việc. Cùng nâng ly rượu nhẹ ngắm nhìn mặt trời đỏ rực khuất dần sau rặng cây Thảo Điền.
                        </p>
                      </div>
                    </div>

                    <div className="border border-gray-200 rounded-[8px] overflow-hidden bg-white shadow-xl">
                      <div className="h-[360px] overflow-hidden">
                        <img
                          src="https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=1200&q=85"
                          alt="Giai đoạn 2"
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <div className="p-6">
                        <span className="text-[10px] font-mono uppercase text-gray-500">Chặng 02 • Bữa tối</span>
                        <h4 className="font-display-clarkson text-2xl text-obsidian mb-2">Thưởng Thức Bò Nướng Trong Ánh Đèn Cổ Điển</h4>
                        <p className="text-xs text-gray-600 font-light leading-relaxed">
                          Bàn tiệc thịnh soạn với steak mềm mọng và sốt nấm thơm lừng. Không gian tách biệt giúp hai người hoàn toàn tập trung vào câu chuyện của nhau.
                        </p>
                      </div>
                    </div>

                    <div className="border border-gray-200 rounded-[8px] overflow-hidden bg-white shadow-xl">
                      <div className="h-[360px] overflow-hidden">
                        <img
                          src="https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=1200&q=85"
                          alt="Giai đoạn 3"
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <div className="p-6">
                        <span className="text-[10px] font-mono uppercase text-gray-500">Chặng 03 • Tráng miệng</span>
                        <h4 className="font-display-clarkson text-2xl text-obsidian mb-2">Trà Đào Dầm & Kén Gỗ Thân Mật</h4>
                        <p className="text-xs text-gray-600 font-light leading-relaxed">
                          Khép lại buổi tối trong sự êm đềm, ngả lưng trò chuyện hoặc đọc sách cùng nhau trước khi trở về nhà.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </section>
        )}

        {/* ======================================================== */}
        {/* TAB 3: 5 ẢNH CONCEPT ẨM THỰC TUYỂN CHỌN (TRANH ẢNH + LINK GỐC) */}
        {/* ======================================================== */}
        {activeTab === 'curated-gallery' && (
          <section className="max-w-[1300px] mx-auto px-6 py-12">
            <div className="text-center max-w-3xl mx-auto mb-12">
              <span className="text-xs uppercase tracking-widest text-ash bg-white/5 border border-white/10 px-3.5 py-1.5 rounded-full inline-block mb-4 font-mono">
                Curated High-Resolution Food & Ambiance Photography
              </span>
              <h2 className="font-display-clarkson text-4xl sm:text-5xl text-paper tracking-tighter mb-4">
                5 ẢNH CONCEPT ẨM THỰC CHẤT LƯỢNG CAO
              </h2>
              <p className="text-ash text-sm leading-relaxed">
                Các bức ảnh dưới đây được tuyển chọn với <strong>ánh sáng tự nhiên, độ phân giải cao</strong> và được định danh rõ ràng là <em>ảnh concept minh họa phong cách ẩm thực</em> (không giả mạo là ảnh chụp thực tế của nhà hàng cụ thể).
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {CURATED_CONCEPT_IMAGES.map((img) => (
                <div
                  key={img.id}
                  className="bg-charcoal/20 border border-white/15 rounded-[8px] overflow-hidden flex flex-col justify-between group hover:border-paper transition-all"
                >
                  <div>
                    <div className="h-64 overflow-hidden relative">
                      <img
                        src={img.url}
                        alt={img.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                      />
                      <div className="absolute top-3 left-3 bg-black/80 backdrop-blur-sm text-white text-[10px] font-mono px-2.5 py-1 rounded-full border border-white/20">
                        Mẫu {img.id}
                      </div>
                    </div>
                    <div className="p-5">
                      <span className="text-[10px] font-mono uppercase tracking-wider text-green-400 block mb-1">
                        {img.conceptGenre}
                      </span>
                      <h4 className="font-display-clarkson text-xl text-paper tracking-tight mb-2">
                        {img.title}
                      </h4>
                      <p className="text-xs text-ash leading-relaxed font-light mb-4">
                        {img.description}
                      </p>
                    </div>
                  </div>

                  <div className="p-5 pt-0 border-t border-charcoal/60 mt-auto flex items-center justify-between text-xs">
                    <span className="text-ash font-mono text-[11px]">Tác giả: {img.author}</span>
                    <a
                      href={img.sourceUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-paper hover:underline flex items-center gap-1 text-[11px]"
                    >
                      <span>Xem nguồn Unsplash</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              ))}
            </div>

            {/* Custom Image Upload / URL Note */}
            <div className="mt-12 bg-charcoal/30 border border-white/20 p-6 rounded-[8px] text-center max-w-2xl mx-auto">
              <Camera className="w-6 h-6 text-paper mx-auto mb-3" />
              <h4 className="font-display-clarkson text-lg text-paper mb-1">
                Quý Khách Muốn Dùng Ảnh Hoặc Hiệu Ứng Riêng?
              </h4>
              <p className="text-xs text-ash leading-relaxed mb-4">
                Nếu Quý khách đã có sẵn ảnh thực tế của nhà hàng hoặc có một mẫu chuyển động mẫu (CodePen, Awwwards, GSAP demo) yêu thích, Quý khách chỉ cần gửi URL hoặc hướng dẫn, tôi sẽ tích hợp ngay lập tức!
              </p>
            </div>
          </section>
        )}

        {/* ======================================================== */}
        {/* TAB 4: HERO REVIEW (KIỂM TRA LẠI HERO ĐÃ DUYỆT) */}
        {/* ======================================================== */}
        {activeTab === 'hero-review' && (
          <div>
            <div className="bg-obsidian border-b border-charcoal py-4 px-6 text-center text-xs text-ash">
              <span className="text-green-400 font-bold">✓ HERO SECTION ĐÃ ĐƯỢC DUYỆT:</span> Video Mẫu 2 (Cụng ly bên bàn tiệc), Overlay Gradient chân, 3 thẻ nổi Parallax.
            </div>

            <section
              ref={heroRef}
              className="relative min-h-[110vh] flex flex-col justify-between overflow-hidden bg-obsidian pt-32 pb-24"
            >
              {/* Full-bleed Video Background */}
              <div className="absolute inset-0 z-0 overflow-hidden">
                <video
                  ref={videoRef}
                  autoPlay
                  loop
                  muted
                  playsInline
                  className="w-full h-full object-cover will-change-transform"
                  poster={selectedVideo.thumbnail}
                >
                  <source src={selectedVideo.localSrc} type="video/mp4" />
                  <source src={selectedVideo.remoteSrc} type="video/mp4" />
                </video>

                {/* Gradient chân */}
                <div className="absolute inset-0 bg-gradient-to-t from-obsidian via-obsidian/40 to-transparent pointer-events-none" />
              </div>

              {/* Hero Content */}
              <div className="relative z-10 max-w-[1100px] mx-auto px-6 text-center flex flex-col items-center my-auto">
                <div className="overflow-hidden mb-6">
                  <h1
                    ref={headlineRef}
                    className="font-display-clarkson text-4xl sm:text-6xl md:text-7xl lg:text-[76px] text-paper tracking-tighter leading-[0.95] max-w-4xl"
                  >
                    NƠI HẸN HÒ HOÀN HẢO CHO CẢ HAI NGƯỜI
                  </h1>
                </div>

                <p
                  ref={sublineRef}
                  className="text-base sm:text-lg text-paper/90 max-w-2xl font-light leading-relaxed mb-8 drop-shadow-sm"
                >
                  Khám phá những điểm hẹn hợp gu cả hai, từ nhà hàng, quán cà phê đến những hành trình đáng nhớ giữa lòng Sài Gòn.
                </p>

                <button
                  onClick={() => {
                    window.scrollTo({ top: window.innerHeight * 0.9, behavior: 'smooth' });
                  }}
                  className="btn-ghost-white cursor-pointer px-8 py-3.5 text-xs font-medium tracking-widest"
                >
                  Cuộn Xuống Khám Phá ↓
                </button>
              </div>

              {/* 3 Overlapping Cards */}
              <div
                ref={cardsRef}
                className="relative z-20 max-w-[1100px] mx-auto px-6 w-full -mb-32 sm:-mb-36"
              >
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                  <div
                    ref={card1Ref}
                    className="bg-obsidian rounded-[8px] overflow-hidden border border-white/20 shadow-2xl group transition-all duration-300 hover:border-white"
                  >
                    <div className="relative h-44 overflow-hidden">
                      <img
                        src="https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80"
                        alt="The Deck Saigon"
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                      />
                      <div className="absolute top-3 left-3 bg-[#ff7a7a] text-obsidian text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-[100px]">
                        Thảo Điền • View Sông
                      </div>
                    </div>
                    <div className="p-4 bg-obsidian">
                      <h4 className="font-display-clarkson text-base text-paper tracking-tight mb-1">
                        The Deck Saigon
                      </h4>
                      <p className="text-xs text-ash line-clamp-1">
                        Bàn ăn ngoài trời ngắm hoàng hôn lãng mạn ven sông
                      </p>
                    </div>
                  </div>

                  <div
                    ref={card2Ref}
                    className="bg-obsidian rounded-[8px] overflow-hidden border border-white/20 shadow-2xl group transition-all duration-300 hover:border-white sm:-translate-y-4"
                  >
                    <div className="relative h-44 overflow-hidden">
                      <img
                        src="https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=800&q=80"
                        alt="Blank Lounge Landmark 81"
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                      />
                      <div className="absolute top-3 left-3 bg-paper text-obsidian text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-[100px]">
                        Bình Thạnh • Tầng 75
                      </div>
                    </div>
                    <div className="p-4 bg-obsidian">
                      <h4 className="font-display-clarkson text-base text-paper tracking-tight mb-1">
                        Blank Lounge Landmark 81
                      </h4>
                      <p className="text-xs text-ash line-clamp-1">
                        Toàn cảnh Sài Gòn rực rỡ ánh đèn đêm từ trên cao
                      </p>
                    </div>
                  </div>

                  <div
                    ref={card3Ref}
                    className="bg-obsidian rounded-[8px] overflow-hidden border border-white/20 shadow-2xl group transition-all duration-300 hover:border-white"
                  >
                    <div className="relative h-44 overflow-hidden">
                      <img
                        src="https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=800&q=80"
                        alt="Chidori Coffee in Bed"
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                      />
                      <div className="absolute top-3 left-3 bg-[#b5e7a0] text-obsidian text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-[100px]">
                        Quận 3 • Yên Tĩnh
                      </div>
                    </div>
                    <div className="p-4 bg-obsidian">
                      <h4 className="font-display-clarkson text-base text-paper tracking-tight mb-1">
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
          </div>
        )}
      </div>
    </div>
  );
};
