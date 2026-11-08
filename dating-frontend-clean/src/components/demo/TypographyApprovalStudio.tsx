import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  CheckCircle2,
  Layers,
  ArrowRight,
  RotateCcw,
  ExternalLink,
  ShieldCheck,
  Eye,
  Columns,
  Monitor,
  Smartphone,
  Tablet,
  BookOpen,
  Info,
  Flame,
  Check
} from 'lucide-react';
import gsap from 'gsap';

export type TypographyOptionId = 'option-a' | 'option-b' | 'option-c';

interface LuxuryWebsiteDossier {
  id: string;
  name: string;
  domain: string;
  category: string;
  originalFonts: string;
  googleFontEquivalent: string;
  styleDescription: string;
  metrics: {
    heroLine1: string;
    heroLine2: string;
    section2: string;
    letterSpacing: string;
    lineHeight: string;
  };
  rationale: string;
  licenseAndVietnamese: string;
  screenshotUrl: string;
}

const LUXURY_WEBSITES: LuxuryWebsiteDossier[] = [
  {
    id: 'emp',
    name: 'Eleven Madison Park',
    domain: 'https://www.elevenmadisonpark.com',
    category: 'Haute Cuisine & 3 Michelin Stars (New York)',
    originalFonts: 'Canela / GT America / Custom Grotesque',
    googleFontEquivalent: 'Plus Jakarta Sans (Light) + Playfair Display / Cormorant Garamond',
    styleDescription: 'Modern Sans-serif tối giản kết hợp điểm nhấn Serif cổ điển tinh tế, mang lại cảm giác tĩnh lặng, sang trọng bậc nhất thế giới.',
    metrics: {
      heroLine1: 'Font-weight 300, 36–48px, Tracking +0.14em',
      heroLine2: 'Font-weight 400 Italic, 64–76px, Tracking -0.01em',
      section2: 'Font-weight 300 + 400 Italic, 48–56px',
      letterSpacing: 'Rộng ở dòng Sans (+0.14em) và vừa vặn ở dòng Serif (-0.01em)',
      lineHeight: '1.15 – 1.25'
    },
    rationale: 'Rất phù hợp cho định vị "Một điểm hẹn. Vạn khoảnh khắc." vì tạo sự cân bằng giữa trải nghiệm ăn uống hiện đại và tính xúc cảm lãng mạn.',
    licenseAndVietnamese: 'Google Fonts SIL Open Font License (Tự do thương mại). Hỗ trợ 100% tiếng Việt Extended với đầy đủ dấu thanh.',
    screenshotUrl: 'https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=800&q=80'
  },
  {
    id: 'aman',
    name: 'Aman Resorts & Hotels',
    domain: 'https://www.aman.com',
    category: 'Ultra-Luxury Hospitality & Quiet Luxury (Global)',
    originalFonts: 'Aman Custom Grotesk + Classical Book Serif',
    googleFontEquivalent: 'Plus Jakarta Sans (300) + Cormorant Garamond (Italic 400)',
    styleDescription: 'Triết lý "Quiet Luxury" tôn vinh sự bình yên và không gian thanh khiết. Khoảng trắng mênh mông, chữ thanh mảnh và sắc sảo.',
    metrics: {
      heroLine1: 'Font-weight 300 Uppercase, 32–42px, Tracking +0.18em',
      heroLine2: 'Font-weight 300/400 Italic, 58–72px, Tracking 0.02em',
      section2: 'Font-weight 300 + 400 Italic, 42–52px',
      letterSpacing: 'Rất thoáng (+0.16em đến +0.20em)',
      lineHeight: '1.20 – 1.30'
    },
    rationale: 'Thích hợp tuyệt đối cho các cặp đôi tìm kiếm không gian hẹn hò kín đáo, thư thái và đẳng cấp không ồn ào.',
    licenseAndVietnamese: 'OFL 1.1 100% Free. Cormorant Garamond và Plus Jakarta Sans kiểm tra dấu tiếng Việt chuẩn xác không xô lệch.',
    screenshotUrl: 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80'
  },
  {
    id: 'singlethread',
    name: 'SingleThread Farm - Restaurant - Inn',
    domain: 'https://www.singlethreadfarms.com',
    category: 'Boutique Luxury & 3 Michelin Stars (Sonoma, CA)',
    originalFonts: 'Ogg / Garamond Premier Pro',
    googleFontEquivalent: 'Cormorant Garamond (300/400/500 Serif & Italic)',
    styleDescription: 'Thuần chất Editorial Tạp Chí Cổ Điển (Full Luxury Serif). Nét chữ như được khắc trên giấy mỹ thuật, giàu chất thơ và tôn vinh nguyên bản.',
    metrics: {
      heroLine1: 'Font-weight 400 Uppercase, 38–50px, Tracking +0.10em',
      heroLine2: 'Font-weight 500 Semi-Italic, 62–78px, Tracking 0.00em',
      section2: 'Font-weight 400 + 500 Italic, 46–58px',
      letterSpacing: 'Tinh tế (+0.08em cho tiêu đề)',
      lineHeight: '1.18 – 1.28'
    },
    rationale: 'Tạo nên ấn tượng sang trọng hoàng gia, biến trải nghiệm hẹn hò thành một bữa tiệc nghệ thuật có chiều sâu.',
    licenseAndVietnamese: 'OFL License 100%. Cormorant Garamond có bộ ký tự tiếng Việt đầy đủ do tác giả Christian Thalmann chau chuốt.',
    screenshotUrl: 'https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?auto=format&fit=crop&w=800&q=80'
  },
  {
    id: 'lebernardin',
    name: 'Le Bernardin',
    domain: 'https://www.le-bernardin.com',
    category: 'Iconic 3 Michelin Stars French Fine Dining (NYC)',
    originalFonts: 'Baskerville / Monotype Didot / Bauer Bodoni',
    googleFontEquivalent: 'Playfair Display (400 Regular & 500 Italic)',
    styleDescription: 'High-contrast Didone/Transitional Serif với độ tương phản nét thanh nét đậm cực kỳ ấn tượng, mang phong thái quý tộc Paris & New York.',
    metrics: {
      heroLine1: 'Font-weight 400 Uppercase, 36–46px, Tracking +0.12em',
      heroLine2: 'Font-weight 600 Italic, 66–82px, Tracking -0.02em',
      section2: 'Font-weight 400 + 500 Italic, 48–60px',
      letterSpacing: '+0.10em đến -0.02em',
      lineHeight: '1.12 – 1.22'
    },
    rationale: 'Tạo cảm giác xa hoa, uy tín và chuẩn mực, khiến mỗi gợi ý nhà hàng trên Couple Assistant như một lựa chọn được chọn lọc khắt khe.',
    licenseAndVietnamese: 'OFL License 100%. Playfair Display hỗ trợ trọn vẹn bộ gõ tiếng Việt Unicode.',
    screenshotUrl: 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80'
  },
  {
    id: 'chevalblanc',
    name: 'Cheval Blanc Paris (LVMH Hotel & Plénitude)',
    domain: 'https://www.chevalblanc.com/en/maison/paris/',
    category: 'Palace Hotel & Ultra-Luxury Hospitality (Paris)',
    originalFonts: 'Cheval Blanc Proprietary Grotesk + French Didot',
    googleFontEquivalent: 'Plus Jakarta Sans (Caps Minimal) + Playfair Display Italic',
    styleDescription: 'Phong cách thời trang xa xỉ Pháp (LVMH Haute Couture Hospitality). Sự kết hợp giữa nét chữ Sans gọn gàng hiện đại và nét uốn lượn lãng mạn.',
    metrics: {
      heroLine1: 'Font-weight 400 Uppercase, 30–40px, Tracking +0.22em',
      heroLine2: 'Font-weight 500 Italic, 68–84px, Tracking 0.00em',
      section2: 'Font-weight 400 + 500 Italic, 44–56px',
      letterSpacing: 'Rất rộng dòng đầu (+0.22em), uyển chuyển dòng sau',
      lineHeight: '1.20'
    },
    rationale: 'Rất hợp với các cặp đôi trẻ yêu thích phong cách thời thượng, thanh lịch, sành điệu.',
    licenseAndVietnamese: 'OFL 100% Free. Bộ font chuẩn Google Fonts tối ưu tải nhanh và hiển thị mượt mà trên mọi thiết bị.',
    screenshotUrl: 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80'
  },
  {
    id: 'cloveclub',
    name: 'The Clove Club',
    domain: 'https://thecloveclub.com',
    category: '2 Michelin Stars & Awwwards Design Winner (London)',
    originalFonts: 'Monument Grotesk + Larish Alte',
    googleFontEquivalent: 'Plus Jakarta Sans (Medium Condensed Tracking) + Cormorant Garamond',
    styleDescription: 'Độ tương phản mạnh mẽ (Minimal Luxury Contrast): Dòng đầu nhỏ gọn, giãn ký tự rộng như một lời thì thầm biên tập; dòng thứ hai to bản, nghệ thuật bùng nổ thị giác.',
    metrics: {
      heroLine1: 'Font-weight 500 Uppercase, 22–30px, Tracking +0.26em',
      heroLine2: 'Font-weight 600 Serif, 72–88px, Tracking -0.03em',
      section2: 'Dòng 1 Sans nhỏ tracking rộng + Dòng 2 Serif lớn tương phản',
      letterSpacing: '+0.26em (Dòng 1) vs -0.03em (Dòng 2)',
      lineHeight: '1.10 – 1.18'
    },
    rationale: 'Tạo dấu ấn nhận diện độc bản, khác biệt hoàn toàn với các website hẹn hò đại trà trên thị trường.',
    licenseAndVietnamese: 'OFL 100% Free. Tương thích hoàn hảo mọi hệ điều hành iOS/macOS/Windows/Android.',
    screenshotUrl: 'https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=800&q=80'
  }
];

export const TypographyApprovalStudio: React.FC = () => {
  const [selectedOption, setSelectedOption] = useState<TypographyOptionId>('option-a');
  const [previewMode, setPreviewMode] = useState<'hero' | 'section2' | 'compare-all' | 'dossier' | 'diacritics'>('hero');
  const [deviceView, setDeviceView] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');
  const [isAnimationPlaying, setIsAnimationPlaying] = useState(false);

  // Animation refs
  const heroTextContainerRef = useRef<HTMLDivElement>(null);
  const heroLine1Ref = useRef<HTMLParagraphElement>(null);
  const heroLine2Ref = useRef<HTMLHeadingElement>(null);

  // Play entrance animation
  const replayHeroAnimation = () => {
    if (heroLine1Ref.current && heroLine2Ref.current) {
      setIsAnimationPlaying(true);
      const tl = gsap.timeline({
        onComplete: () => setIsAnimationPlaying(false)
      });

      tl.fromTo(
        heroLine1Ref.current,
        { y: 35, opacity: 0, letterSpacing: '0.05em' },
        { y: 0, opacity: 1, letterSpacing: selectedOption === 'option-c' ? '0.24em' : '0.14em', duration: 0.9, ease: 'power3.out' }
      ).fromTo(
        heroLine2Ref.current,
        { y: 50, opacity: 0, filter: 'blur(4px)' },
        { y: 0, opacity: 1, filter: 'blur(0px)', duration: 1.1, ease: 'power3.out' },
        '-=0.55'
      );
    }
  };

  useEffect(() => {
    replayHeroAnimation();
  }, [selectedOption, previewMode]);

  return (
    <div className="space-y-12 pb-24">
      {/* ======================================================== */}
      {/* 1. TOP HEADER & MANDATORY APPROVAL BANNER */}
      {/* ======================================================== */}
      <div className="max-w-[1300px] mx-auto px-6 pt-4">
        <div className="bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-500/30 rounded-[8px] p-6 mb-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-amber-500/20 text-amber-400 rounded-full mt-0.5">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-mono uppercase tracking-wider text-amber-400 font-bold">
                  Giai Đoạn A: Typography Preview & Approval Gate
                </span>
                <span className="text-[10px] bg-white/10 text-paper px-2 py-0.5 rounded-full font-mono">
                  Bắt buộc xem trước
                </span>
              </div>
              <h2 className="text-lg font-medium text-paper">
                So Sánh Trực Quan 3 Phong Cách Luxury Editorial Cho Hero & Section 2
              </h2>
              <p className="text-xs text-ash mt-1 max-w-2xl leading-relaxed">
                Theo đúng chỉ đạo nghiêm ngặt: <strong>Homepage chính (/) được bảo vệ nguyên vẹn</strong>. Bạn hãy thử nghiệm và so sánh cả 3 phương án dưới đây trên nền video Hero và nền trắng Section 2 trước khi quyết định phương án chốt cho Giai đoạn B.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-[4px] flex items-center gap-1.5">
              <Check className="w-3.5 h-3.5" />
              <span>Tiếng Việt 100% Hỗ Trợ Đầy Đủ</span>
            </span>
          </div>
        </div>

        {/* ======================================================== */}
        {/* 2. OPTION SELECTOR TABS (PA A, PA B, PA C) */}
        {/* ======================================================== */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          {/* Option A */}
          <button
            onClick={() => setSelectedOption('option-a')}
            className={`p-4 rounded-[8px] text-left transition-all border cursor-pointer relative ${
              selectedOption === 'option-a'
                ? 'bg-charcoal/40 border-paper ring-1 ring-paper shadow-2xl'
                : 'bg-charcoal/20 border-white/10 hover:border-white/30 text-ash'
            }`}
          >
            {selectedOption === 'option-a' && (
              <span className="absolute top-6 right-6 z-10 text-[10px] font-mono text-paper bg-obsidian/80 backdrop-blur-sm border border-white/30 px-2 py-0.5 rounded-full flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                <span>Đang Xem</span>
              </span>
            )}
            <div className="aspect-[16/9] mb-3 overflow-hidden rounded-[4px] border border-white/10 shadow">
              <img src="/media/typography-option-a.jpg" alt="Preview Phương Án A" className="w-full h-full object-cover" />
            </div>
            <div className="text-[11px] font-mono uppercase tracking-wider text-emerald-400 mb-1 flex items-center gap-1">
              <Sparkles className="w-3 h-3" />
              <span>Phương Án A (Khuyên Dùng)</span>
            </div>
            <h3 className="text-base font-semibold text-paper mb-1">
              Modern Sans + Elegant Serif Italic
            </h3>
            <p className="text-xs text-ash mb-3 line-clamp-2">
              Dòng đầu Sans-serif thanh mảnh, hiện đại; dòng thứ hai Serif Italic uốn lượn nghệ thuật, giàu chất thơ.
            </p>
            <div className="text-[11px] font-mono text-paper/70 bg-obsidian/60 p-2.5 rounded-[4px] border border-white/5 space-y-1">
              <div>• Dòng 1: <strong className="text-paper">Plus Jakarta Sans</strong> (300)</div>
              <div>• Dòng 2: <strong className="text-paper">Playfair Display / Cormorant</strong> (Italic)</div>
              <div className="text-[10px] text-ash pt-1 border-t border-white/5">
                Tham chiếu: Eleven Madison Park, Aman Resorts, Kinfolk
              </div>
            </div>
          </button>

          {/* Option B */}
          <button
            onClick={() => setSelectedOption('option-b')}
            className={`p-4 rounded-[8px] text-left transition-all border cursor-pointer relative ${
              selectedOption === 'option-b'
                ? 'bg-charcoal/40 border-paper ring-1 ring-paper shadow-2xl'
                : 'bg-charcoal/20 border-white/10 hover:border-white/30 text-ash'
            }`}
          >
            {selectedOption === 'option-b' && (
              <span className="absolute top-6 right-6 z-10 text-[10px] font-mono text-paper bg-obsidian/80 backdrop-blur-sm border border-white/30 px-2 py-0.5 rounded-full flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                <span>Đang Xem</span>
              </span>
            )}
            <div className="aspect-[16/9] mb-3 overflow-hidden rounded-[4px] border border-white/10 shadow">
              <img src="/media/typography-option-b.jpg" alt="Preview Phương Án B" className="w-full h-full object-cover" />
            </div>
            <div className="text-[11px] font-mono uppercase tracking-wider text-blue-400 mb-1 flex items-center gap-1">
              <BookOpen className="w-3 h-3" />
              <span>Phương Án B</span>
            </div>
            <h3 className="text-base font-semibold text-paper mb-1">
              Full Luxury Serif (Editorial Haute)
            </h3>
            <p className="text-xs text-ash mb-3 line-clamp-2">
              Cả hai dòng thuần Serif cao cấp, nhấn mạnh phong cách tạp chí biên tập cổ điển và ẩm thực Michelin đỉnh cao.
            </p>
            <div className="text-[11px] font-mono text-paper/70 bg-obsidian/60 p-2.5 rounded-[4px] border border-white/5 space-y-1">
              <div>• Dòng 1: <strong className="text-paper">Cormorant Garamond</strong> (Caps, 400)</div>
              <div>• Dòng 2: <strong className="text-paper">Cormorant Garamond</strong> (Italic, 500)</div>
              <div className="text-[10px] text-ash pt-1 border-t border-white/5">
                Tham chiếu: SingleThread Farm, Le Bernardin, Cereal
              </div>
            </div>
          </button>

          {/* Option C */}
          <button
            onClick={() => setSelectedOption('option-c')}
            className={`p-4 rounded-[8px] text-left transition-all border cursor-pointer relative ${
              selectedOption === 'option-c'
                ? 'bg-charcoal/40 border-paper ring-1 ring-paper shadow-2xl'
                : 'bg-charcoal/20 border-white/10 hover:border-white/30 text-ash'
            }`}
          >
            {selectedOption === 'option-c' && (
              <span className="absolute top-6 right-6 z-10 text-[10px] font-mono text-paper bg-obsidian/80 backdrop-blur-sm border border-white/30 px-2 py-0.5 rounded-full flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                <span>Đang Xem</span>
              </span>
            )}
            <div className="aspect-[16/9] mb-3 overflow-hidden rounded-[4px] border border-white/10 shadow">
              <img src="/media/typography-option-c.jpg" alt="Preview Phương Án C" className="w-full h-full object-cover" />
            </div>
            <div className="text-[11px] font-mono uppercase tracking-wider text-purple-400 mb-1 flex items-center gap-1">
              <Flame className="w-3 h-3" />
              <span>Phương Án C</span>
            </div>
            <h3 className="text-base font-semibold text-paper mb-1">
              Minimal Luxury Contrast
            </h3>
            <p className="text-xs text-ash mb-3 line-clamp-2">
              Tương phản tối đa: Dòng đầu Sans nhỏ gọn với tracking cực rộng; dòng thứ hai Serif khổng lồ nổi bật.
            </p>
            <div className="text-[11px] font-mono text-paper/70 bg-obsidian/60 p-2.5 rounded-[4px] border border-white/5 space-y-1">
              <div>• Dòng 1: <strong className="text-paper">Plus Jakarta Sans</strong> (500 Caps, Spacing +0.26em)</div>
              <div>• Dòng 2: <strong className="text-paper">Playfair Display</strong> (600 Bold Serif)</div>
              <div className="text-[10px] text-ash pt-1 border-t border-white/5">
                Tham chiếu: The Clove Club, Cheval Blanc Paris, Awwwards
              </div>
            </div>
          </button>
        </div>

        {/* ======================================================== */}
        {/* 3. VIEW MODE SWITCHER & DEVICE SIMULATOR */}
        {/* ======================================================== */}
        <div className="flex flex-wrap items-center justify-between gap-4 bg-charcoal/30 p-2 rounded-[6px] border border-white/10 mb-8">
          <div className="flex items-center gap-1 flex-wrap">
            <button
              onClick={() => setPreviewMode('hero')}
              className={`px-3 py-1.5 text-xs font-medium rounded-[4px] transition-all cursor-pointer flex items-center gap-1.5 ${
                previewMode === 'hero'
                  ? 'bg-paper text-obsidian font-bold shadow-sm'
                  : 'text-ash hover:text-paper'
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              <span>Bối Cảnh Hero Video (Nền Tối)</span>
            </button>

            <button
              onClick={() => setPreviewMode('section2')}
              className={`px-3 py-1.5 text-xs font-medium rounded-[4px] transition-all cursor-pointer flex items-center gap-1.5 ${
                previewMode === 'section2'
                  ? 'bg-paper text-obsidian font-bold shadow-sm'
                  : 'text-ash hover:text-paper'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Bối Cảnh Section 2 (White Canvas)</span>
            </button>

            <button
              onClick={() => setPreviewMode('compare-all')}
              className={`px-3 py-1.5 text-xs font-medium rounded-[4px] transition-all cursor-pointer flex items-center gap-1.5 ${
                previewMode === 'compare-all'
                  ? 'bg-paper text-obsidian font-bold shadow-sm'
                  : 'text-ash hover:text-paper'
              }`}
            >
              <Columns className="w-3.5 h-3.5" />
              <span>So Sánh 3 Cột (Side-by-Side Matrix)</span>
            </button>

            <button
              onClick={() => setPreviewMode('dossier')}
              className={`px-3 py-1.5 text-xs font-medium rounded-[4px] transition-all cursor-pointer flex items-center gap-1.5 ${
                previewMode === 'dossier'
                  ? 'bg-paper text-obsidian font-bold shadow-sm'
                  : 'text-ash hover:text-paper'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>Nghiên Cứu 6 Website Thực Tế (Dossier)</span>
            </button>

            <button
              onClick={() => setPreviewMode('diacritics')}
              className={`px-3 py-1.5 text-xs font-medium rounded-[4px] transition-all cursor-pointer flex items-center gap-1.5 ${
                previewMode === 'diacritics'
                  ? 'bg-paper text-obsidian font-bold shadow-sm'
                  : 'text-ash hover:text-paper'
              }`}
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Kiểm Thử Dấu Tiếng Việt (Stress-Test)</span>
            </button>
          </div>

          {/* Viewport simulation */}
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono text-ash hidden sm:inline">Khổ màn hình:</span>
            <div className="flex items-center bg-obsidian/70 rounded-[4px] p-0.5 border border-white/10">
              <button
                onClick={() => setDeviceView('desktop')}
                title="Desktop (100% width)"
                className={`p-1.5 rounded-[3px] transition-all cursor-pointer ${
                  deviceView === 'desktop' ? 'bg-white/20 text-paper' : 'text-ash hover:text-paper'
                }`}
              >
                <Monitor className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setDeviceView('tablet')}
                title="Tablet View (768px)"
                className={`p-1.5 rounded-[3px] transition-all cursor-pointer ${
                  deviceView === 'tablet' ? 'bg-white/20 text-paper' : 'text-ash hover:text-paper'
                }`}
              >
                <Tablet className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setDeviceView('mobile')}
                title="Mobile View (390px)"
                className={`p-1.5 rounded-[3px] transition-all cursor-pointer ${
                  deviceView === 'mobile' ? 'bg-white/20 text-paper' : 'text-ash hover:text-paper'
                }`}
              >
                <Smartphone className="w-3.5 h-3.5" />
              </button>
            </div>

            {previewMode === 'hero' && (
              <button
                onClick={replayHeroAnimation}
                disabled={isAnimationPlaying}
                className="text-xs font-mono text-paper bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-[4px] border border-white/20 transition-all cursor-pointer flex items-center gap-1.5"
              >
                <RotateCcw className={`w-3.5 h-3.5 ${isAnimationPlaying ? 'animate-spin' : ''}`} />
                <span>Chạy Animation Lại</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* ======================================================== */}
      {/* 4. MAIN PREVIEW CONTAINER (ADAPTIVE VIEWPORT) */}
      {/* ======================================================== */}
      <div className="max-w-[1400px] mx-auto px-4 flex justify-center">
        <div
          className={`transition-all duration-500 overflow-hidden ${
            deviceView === 'desktop'
              ? 'w-full'
              : deviceView === 'tablet'
              ? 'w-[768px] border-x border-white/20 shadow-2xl'
              : 'w-[390px] border-x border-white/20 shadow-2xl rounded-t-[20px]'
          }`}
        >
          {/* ======================================================== */}
          {/* VIEW 1: HERO SECTION CONTEXT PREVIEW */}
          {/* ======================================================== */}
          {previewMode === 'hero' && (
            <div className="relative min-h-[85vh] flex flex-col justify-between overflow-hidden bg-obsidian border border-white/10 rounded-[8px]">
              {/* Background Video (Mẫu 2 Toast đã duyệt) */}
              <div className="absolute inset-0 z-0">
                <video
                  autoPlay
                  loop
                  muted
                  playsInline
                  className="w-full h-full object-cover"
                >
                  <source src="/media/video-2-toast.mp4" type="video/mp4" />
                  <source src="https://assets.mixkit.co/videos/45727/45727-720.mp4" type="video/mp4" />
                </video>
                {/* Gradient Overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-obsidian via-obsidian/60 to-obsidian/30" />
              </div>

              {/* Top Watermark / Spec Details */}
              <div className="relative z-10 p-6 flex items-center justify-between">
                <div className="inline-flex items-center gap-2 bg-obsidian/80 backdrop-blur-md border border-white/20 px-3 py-1 rounded-full text-xs font-mono">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span>
                    Bối Cảnh Hero Video • {selectedOption === 'option-a' ? 'Phương Án A' : selectedOption === 'option-b' ? 'Phương Án B' : 'Phương Án C'}
                  </span>
                </div>
                <div className="text-[11px] font-mono text-white/60 bg-black/60 px-2.5 py-1 rounded">
                  {deviceView.toUpperCase()} MODE
                </div>
              </div>

              {/* Central Headline Display */}
              <div
                ref={heroTextContainerRef}
                className="relative z-10 text-center max-w-4xl mx-auto px-6 py-12 space-y-4"
              >
                {/* LINE 1 */}
                <p
                  ref={heroLine1Ref}
                  className={`text-paper uppercase transition-all duration-300 ${
                    selectedOption === 'option-a'
                      ? 'font-jakarta font-light text-2xl sm:text-4xl lg:text-[46px] tracking-[0.14em]'
                      : selectedOption === 'option-b'
                      ? 'font-cormorant font-normal text-2xl sm:text-4xl lg:text-[48px] tracking-[0.08em]'
                      : 'font-jakarta font-semibold text-lg sm:text-2xl lg:text-[28px] tracking-[0.24em] text-white/90'
                  }`}
                >
                  MỘT ĐIỂM HẸN.
                </p>

                {/* LINE 2 */}
                <h1
                  ref={heroLine2Ref}
                  className={`text-paper transition-all duration-300 ${
                    selectedOption === 'option-a'
                      ? 'font-playfair italic font-normal text-4xl sm:text-6xl lg:text-[76px] tracking-tight leading-[1.08]'
                      : selectedOption === 'option-b'
                      ? 'font-cormorant italic font-medium text-4xl sm:text-6xl lg:text-[82px] tracking-tight leading-[1.05]'
                      : 'font-playfair font-bold text-4xl sm:text-6xl lg:text-[84px] tracking-tight leading-[1.05]'
                  }`}
                >
                  VẠN KHOẢNH KHẮC.
                </h1>

                {/* Approved Subtitle Description */}
                <p className="font-sans text-xs sm:text-sm lg:text-base text-paper/85 max-w-2xl mx-auto leading-relaxed pt-2 font-light">
                  Khám phá những điểm hẹn hợp gu cả hai, từ nhà hàng, quán cafe đến rooftop bar tại TP.HCM. Thuật toán thông minh giúp cặp đôi luôn tìm thấy trải nghiệm trọn vẹn mà không cần thỏa hiệp.
                </p>

                {/* CTA Buttons */}
                <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
                  <button className="btn-filled-white text-xs px-7 py-3 tracking-widest cursor-pointer">
                    Khám Phá Điểm Hẹn
                  </button>
                  <button className="btn-ghost-white text-xs px-7 py-3 tracking-widest cursor-pointer">
                    Xem Lịch Trình Mẫu
                  </button>
                </div>
              </div>

              {/* 3 Overlapping Cards at Hero Base */}
              <div className="relative z-10 max-w-4xl mx-auto px-6 pb-6 w-full opacity-90">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="bg-obsidian/85 backdrop-blur-md rounded-[6px] p-3 border border-white/15 flex items-center gap-3">
                    <img
                      src="https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=200&q=80"
                      alt="Steakhouse"
                      className="w-12 h-12 rounded-[4px] object-cover"
                    />
                    <div>
                      <span className="text-[10px] font-mono text-emerald-400 block">01 / Fine Dining</span>
                      <p className="text-xs font-medium text-paper">Steakhouse & Wine</p>
                    </div>
                  </div>

                  <div className="bg-obsidian/85 backdrop-blur-md rounded-[6px] p-3 border border-white/15 flex items-center gap-3">
                    <img
                      src="https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=200&q=80"
                      alt="Ven Song"
                      className="w-12 h-12 rounded-[4px] object-cover"
                    />
                    <div>
                      <span className="text-[10px] font-mono text-amber-400 block">02 / Không Gian Mở</span>
                      <p className="text-xs font-medium text-paper">Bàn Tiệc Nến Ấm</p>
                    </div>
                  </div>

                  <div className="bg-obsidian/85 backdrop-blur-md rounded-[6px] p-3 border border-white/15 flex items-center gap-3">
                    <img
                      src="https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=200&q=80"
                      alt="Artisan Cafe"
                      className="w-12 h-12 rounded-[4px] object-cover"
                    />
                    <div>
                      <span className="text-[10px] font-mono text-purple-400 block">03 / Thư Giãn</span>
                      <p className="text-xs font-medium text-paper">Kén Gỗ Cafe Yên Tĩnh</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* VIEW 2: SECTION 2 CONTEXT PREVIEW (WHITE CANVAS) */}
          {/* ======================================================== */}
          {previewMode === 'section2' && (
            <div className="bg-[#ffffff] text-[#000000] p-8 sm:p-14 lg:p-20 rounded-[8px] border border-white/20">
              <div className="max-w-[1200px] mx-auto space-y-12">
                {/* Editorial Slogan with Selected Typography */}
                <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6 border-b border-black/10 pb-8">
                  <div>
                    {/* Notice: Label "KHÁM PHÁ KHÔNG GIAN HẸN HÒ" completely removed! */}
                    <div className="space-y-1">
                      {/* Line 1 */}
                      <p
                        className={`text-black transition-all ${
                          selectedOption === 'option-a'
                            ? 'font-jakarta font-light text-2xl sm:text-4xl lg:text-[44px] tracking-[0.04em]'
                            : selectedOption === 'option-b'
                            ? 'font-cormorant font-normal text-3xl sm:text-5xl lg:text-[54px] tracking-[0.02em]'
                            : 'font-jakarta font-medium text-xl sm:text-3xl lg:text-[34px] tracking-[0.18em] uppercase text-black/80'
                        }`}
                      >
                        Khác gu một chút.
                      </p>

                      {/* Line 2 */}
                      <h2
                        className={`text-black transition-all ${
                          selectedOption === 'option-a'
                            ? 'font-playfair italic font-medium text-4xl sm:text-6xl lg:text-[68px] tracking-tight leading-[1.08]'
                            : selectedOption === 'option-b'
                            ? 'font-cormorant italic font-semibold text-4xl sm:text-6xl lg:text-[76px] tracking-tight leading-[1.04]'
                            : 'font-playfair font-bold text-4xl sm:text-6xl lg:text-[74px] tracking-tight leading-[1.05]'
                        }`}
                      >
                        Đồng điệu một đời.
                      </h2>
                    </div>
                  </div>

                  <div className="lg:max-w-xs space-y-2">
                    <p className="text-xs sm:text-sm text-black/60 leading-relaxed font-sans">
                      Mỗi không gian được tuyển chọn khắt khe về ánh sáng, âm lượng, khoảng cách bàn và sự riêng tư cho cặp đôi tại TP.HCM.
                    </p>
                    <span className="text-[11px] font-mono text-black/40 block">
                      Asymmetric Magazine Spread • White Canvas
                    </span>
                  </div>
                </div>

                {/* 3 Asymmetric Magazine Cards with concise "Ảnh minh họa" badges */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                  {/* Left Column: Large Hero Vertical Card */}
                  <div className="lg:col-span-7 bg-[#fbfbfb] rounded-[6px] border border-black/10 overflow-hidden shadow-lg group">
                    <div className="relative aspect-[4/3] sm:aspect-[16/11] overflow-hidden">
                      <img
                        src="https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=1200&q=85"
                        alt="Ảnh minh họa Steakhouse"
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                      />
                      <div className="absolute top-4 left-4 bg-black/80 backdrop-blur-sm text-white text-[11px] font-mono tracking-wider px-3 py-1 rounded-[100px] border border-white/20">
                        Ảnh minh họa • Steakhouse & Fine Dining
                      </div>
                    </div>
                    <div className="p-6">
                      <div className="text-xs font-mono text-black/40 mb-1">01 / KHÔNG GIAN BÀN TIỆC</div>
                      <h3 className="font-playfair text-2xl font-normal text-black mb-2">
                        Bò Wagyu Nướng Sốt Nấm & Rượu Vang
                      </h3>
                      <p className="text-xs text-black/60 leading-relaxed">
                        Thịt bò nướng xém cạnh, sốt tiêu đen bóng bẩy và đĩa gốm mộc tối giản. Ánh sáng tự nhiên không dùng bộ lọc màu nhân tạo.
                      </p>
                    </div>
                  </div>

                  {/* Right Column: 2 Stacked Cards */}
                  <div className="lg:col-span-5 space-y-8">
                    {/* Card 2 */}
                    <div className="bg-[#fbfbfb] rounded-[6px] border border-black/10 overflow-hidden shadow-md group">
                      <div className="relative aspect-[16/9] overflow-hidden">
                        <img
                          src="https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=85"
                          alt="Ảnh minh họa Bàn tiệc ven sông"
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                        />
                        <div className="absolute top-3 left-3 bg-black/80 backdrop-blur-sm text-white text-[10px] font-mono tracking-wider px-2.5 py-0.5 rounded-[100px] border border-white/20">
                          Ảnh minh họa • Sân Vườn & Ven Sông
                        </div>
                      </div>
                      <div className="p-4">
                        <div className="text-[11px] font-mono text-black/40 mb-0.5">02 / ÁNH NẾN LÃNG MẠN</div>
                        <h4 className="font-playfair text-lg font-normal text-black">
                          Bàn Tiệc Nến Ấm & Không Gian Mở
                        </h4>
                      </div>
                    </div>

                    {/* Card 3 */}
                    <div className="bg-[#fbfbfb] rounded-[6px] border border-black/10 overflow-hidden shadow-md group">
                      <div className="relative aspect-[16/9] overflow-hidden">
                        <img
                          src="https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=800&q=85"
                          alt="Ảnh minh họa Cafe yên tĩnh"
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                        />
                        <div className="absolute top-3 left-3 bg-black/80 backdrop-blur-sm text-white text-[10px] font-mono tracking-wider px-2.5 py-0.5 rounded-[100px] border border-white/20">
                          Ảnh minh họa • Cafe Thư Thái
                        </div>
                      </div>
                      <div className="p-4">
                        <div className="text-[11px] font-mono text-black/40 mb-0.5">03 / KHÔNG GIAN RIÊNG TƯ</div>
                        <h4 className="font-playfair text-lg font-normal text-black">
                          Cà Phê Thủ Công & Kén Gỗ Đọc Sách
                        </h4>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Notice: Long footnote is completely removed! Only clean editorial footer remains */}
                <div className="flex items-center justify-between text-xs text-black/50 pt-4 border-t border-black/10">
                  <span className="font-mono text-[11px]">Tuyển tập ẩm thực & không gian hẹn hò TP.HCM</span>
                  <button className="bg-black text-white px-5 py-2.5 text-xs uppercase tracking-wider font-medium cursor-pointer hover:bg-neutral-800 transition-colors">
                    Xem Tất Cả 24 Không Gian →
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* VIEW 3: 3-WAY SIDE-BY-SIDE MATRIX */}
          {/* ======================================================== */}
          {previewMode === 'compare-all' && (
            <div className="space-y-8">
              <div className="text-center max-w-2xl mx-auto">
                <span className="text-xs font-mono uppercase text-ash tracking-widest block mb-2">
                  Trực Quan Hóa Ma Trận 3 Cột
                </span>
                <h3 className="text-2xl font-semibold text-paper">
                  So Sánh Trực Tiếp 3 Phương Án Typography
                </h3>
              </div>

              {/* HERO COMPARISON */}
              <div className="bg-charcoal/20 border border-white/10 rounded-[8px] p-6 space-y-6">
                <div className="flex items-center gap-2 border-b border-white/10 pb-3">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                  <h4 className="text-sm font-mono uppercase text-paper tracking-wider">
                    Hero Section: "MỘT ĐIỂM HẸN. VẠN KHOẢNH KHẮC." (Nền Tối)
                  </h4>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Col A */}
                  <div
                    onClick={() => setSelectedOption('option-a')}
                    className={`bg-obsidian/90 border rounded-[6px] p-5 cursor-pointer transition-all ${
                      selectedOption === 'option-a' ? 'border-emerald-400 ring-1 ring-emerald-400' : 'border-white/10 hover:border-white/30'
                    }`}
                  >
                    <div className="text-[10px] font-mono text-emerald-400 uppercase tracking-widest mb-3">
                      Phương Án A (Khuyên Dùng)
                    </div>
                    <div className="space-y-2 py-4 border-y border-white/5">
                      <p className="font-jakarta font-light text-lg sm:text-xl text-paper tracking-[0.14em]">
                        MỘT ĐIỂM HẸN.
                      </p>
                      <p className="font-playfair italic font-normal text-2xl sm:text-3xl text-paper tracking-tight leading-tight">
                        VẠN KHOẢNH KHẮC.
                      </p>
                    </div>
                    <div className="text-[11px] text-ash mt-3 space-y-1">
                      <div>Sans thanh mảnh + Serif Italic uyển chuyển</div>
                      <div className="text-emerald-400/90 font-mono">Plus Jakarta Sans + Playfair Italic</div>
                    </div>
                  </div>

                  {/* Col B */}
                  <div
                    onClick={() => setSelectedOption('option-b')}
                    className={`bg-obsidian/90 border rounded-[6px] p-5 cursor-pointer transition-all ${
                      selectedOption === 'option-b' ? 'border-blue-400 ring-1 ring-blue-400' : 'border-white/10 hover:border-white/30'
                    }`}
                  >
                    <div className="text-[10px] font-mono text-blue-400 uppercase tracking-widest mb-3">
                      Phương Án B (Full Luxury Serif)
                    </div>
                    <div className="space-y-2 py-4 border-y border-white/5">
                      <p className="font-cormorant font-normal text-lg sm:text-xl text-paper tracking-[0.08em]">
                        MỘT ĐIỂM HẸN.
                      </p>
                      <p className="font-cormorant italic font-medium text-2xl sm:text-3xl text-paper tracking-tight leading-tight">
                        VẠN KHOẢNH KHẮC.
                      </p>
                    </div>
                    <div className="text-[11px] text-ash mt-3 space-y-1">
                      <div>Cả hai dòng Serif cao cấp đậm chất Haute Cuisine</div>
                      <div className="text-blue-400/90 font-mono">Cormorant Garamond Regular + Italic</div>
                    </div>
                  </div>

                  {/* Col C */}
                  <div
                    onClick={() => setSelectedOption('option-c')}
                    className={`bg-obsidian/90 border rounded-[6px] p-5 cursor-pointer transition-all ${
                      selectedOption === 'option-c' ? 'border-purple-400 ring-1 ring-purple-400' : 'border-white/10 hover:border-white/30'
                    }`}
                  >
                    <div className="text-[10px] font-mono text-purple-400 uppercase tracking-widest mb-3">
                      Phương Án C (Minimal Contrast)
                    </div>
                    <div className="space-y-2 py-4 border-y border-white/5">
                      <p className="font-jakarta font-semibold text-xs sm:text-sm text-white/80 tracking-[0.24em]">
                        MỘT ĐIỂM HẸN.
                      </p>
                      <p className="font-playfair font-bold text-2xl sm:text-3xl text-paper tracking-tight leading-tight">
                        VẠN KHOẢNH KHẮC.
                      </p>
                    </div>
                    <div className="text-[11px] text-ash mt-3 space-y-1">
                      <div>Tương phản tỷ lệ lớn: Dòng 1 nhỏ, Dòng 2 khổng lồ</div>
                      <div className="text-purple-400/90 font-mono">Plus Jakarta Sans (Caps) + Playfair Bold</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* SECTION 2 COMPARISON (WHITE CANVAS) */}
              <div className="bg-[#ffffff] text-[#000000] border border-white/20 rounded-[8px] p-6 space-y-6">
                <div className="flex items-center gap-2 border-b border-black/10 pb-3">
                  <span className="w-2.5 h-2.5 rounded-full bg-black" />
                  <h4 className="text-sm font-mono uppercase text-black tracking-wider">
                    Section 2: "Khác gu một chút. Đồng điệu một đời." (White Canvas)
                  </h4>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Col A White */}
                  <div
                    onClick={() => setSelectedOption('option-a')}
                    className={`bg-[#f8f8f8] border rounded-[6px] p-5 cursor-pointer transition-all ${
                      selectedOption === 'option-a' ? 'border-black ring-1 ring-black' : 'border-black/10 hover:border-black/30'
                    }`}
                  >
                    <div className="text-[10px] font-mono text-black/60 uppercase tracking-widest mb-3">
                      Phương Án A (Khuyên Dùng)
                    </div>
                    <div className="space-y-1 py-4 border-y border-black/5">
                      <p className="font-jakarta font-light text-xl text-black tracking-[0.04em]">
                        Khác gu một chút.
                      </p>
                      <p className="font-playfair italic font-medium text-2xl sm:text-3xl text-black tracking-tight leading-tight">
                        Đồng điệu một đời.
                      </p>
                    </div>
                    <div className="text-[11px] text-black/60 mt-3">
                      Hiện đại, thanh thoát và lắng đọng
                    </div>
                  </div>

                  {/* Col B White */}
                  <div
                    onClick={() => setSelectedOption('option-b')}
                    className={`bg-[#f8f8f8] border rounded-[6px] p-5 cursor-pointer transition-all ${
                      selectedOption === 'option-b' ? 'border-black ring-1 ring-black' : 'border-black/10 hover:border-black/30'
                    }`}
                  >
                    <div className="text-[10px] font-mono text-black/60 uppercase tracking-widest mb-3">
                      Phương Án B (Editorial Haute)
                    </div>
                    <div className="space-y-1 py-4 border-y border-black/5">
                      <p className="font-cormorant font-normal text-2xl text-black tracking-[0.02em]">
                        Khác gu một chút.
                      </p>
                      <p className="font-cormorant italic font-semibold text-3xl sm:text-4xl text-black tracking-tight leading-tight">
                        Đồng điệu một đời.
                      </p>
                    </div>
                    <div className="text-[11px] text-black/60 mt-3">
                      Quý phái, cổ điển như tạp chí ẩm thực Kinfolk/Cereal
                    </div>
                  </div>

                  {/* Col C White */}
                  <div
                    onClick={() => setSelectedOption('option-c')}
                    className={`bg-[#f8f8f8] border rounded-[6px] p-5 cursor-pointer transition-all ${
                      selectedOption === 'option-c' ? 'border-black ring-1 ring-black' : 'border-black/10 hover:border-black/30'
                    }`}
                  >
                    <div className="text-[10px] font-mono text-black/60 uppercase tracking-widest mb-3">
                      Phương Án C (Minimal Contrast)
                    </div>
                    <div className="space-y-1 py-4 border-y border-black/5">
                      <p className="font-jakarta font-medium text-xs text-black/70 tracking-[0.20em] uppercase">
                        Khác gu một chút.
                      </p>
                      <p className="font-playfair font-bold text-2xl sm:text-3xl text-black tracking-tight leading-tight">
                        Đồng điệu một đời.
                      </p>
                    </div>
                    <div className="text-[11px] text-black/60 mt-3">
                      Tương phản nhịp điệu ấn tượng, cá tính mạnh
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* VIEW 4: RESEARCH DOSSIER (6 REAL LUXURY WEBSITES) */}
          {/* ======================================================== */}
          {previewMode === 'dossier' && (
            <div className="space-y-8">
              <div className="text-center max-w-3xl mx-auto">
                <span className="text-xs font-mono uppercase text-ash tracking-widest block mb-2">
                  Thực Tế & Chuyên Nghiệp
                </span>
                <h3 className="text-2xl sm:text-3xl font-semibold text-paper mb-3">
                  Nghiên Cứu Typography Từ 6 Website Cao Cấp Thế Giới
                </h3>
                <p className="text-xs sm:text-sm text-ash leading-relaxed">
                  Đối chiếu font chữ, tỉ lệ và giấy phép bản quyền của các thương hiệu Fine Dining, Luxury Hotel và Lifestyle hàng đầu thế giới được đề xuất ứng dụng cho Couple Assistant.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {LUXURY_WEBSITES.map((site) => (
                  <div
                    key={site.id}
                    className="bg-charcoal/20 border border-white/10 rounded-[8px] overflow-hidden p-6 space-y-4 hover:border-white/30 transition-all flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-4 mb-2">
                        <div>
                          <span className="text-[10px] font-mono uppercase text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full inline-block mb-1">
                            {site.category}
                          </span>
                          <h4 className="text-xl font-medium text-paper">{site.name}</h4>
                        </div>
                        <a
                          href={site.domain}
                          target="_blank"
                          rel="noreferrer"
                          className="text-ash hover:text-paper p-1.5 border border-white/10 rounded-[4px] hover:border-paper transition-colors"
                          title="Mở website gốc"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      </div>

                      <p className="text-xs text-ash leading-relaxed mb-4">
                        {site.styleDescription}
                      </p>

                      <div className="bg-obsidian/70 p-4 rounded-[6px] border border-white/5 space-y-2 text-xs">
                        <div>
                          <span className="text-ash font-mono text-[11px] block">Font thực tế nếu xác minh:</span>
                          <span className="text-paper font-semibold">{site.originalFonts}</span>
                        </div>
                        <div>
                          <span className="text-ash font-mono text-[11px] block">Font đề xuất tương đương (Google Fonts):</span>
                          <span className="text-emerald-400 font-semibold">{site.googleFontEquivalent}</span>
                        </div>
                        <div>
                          <span className="text-ash font-mono text-[11px] block">Thông số tham khảo:</span>
                          <span className="text-paper/90 text-[11px] leading-relaxed block">
                            {site.metrics.heroLine1} | {site.metrics.heroLine2}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-3 pt-3 border-t border-white/10">
                      <div>
                        <span className="text-[10px] font-mono text-ash uppercase block mb-0.5">Lý do phù hợp với Couple Assistant:</span>
                        <p className="text-xs text-paper/85 leading-relaxed">{site.rationale}</p>
                      </div>
                      <div className="flex items-center gap-2 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded">
                        <Check className="w-3 h-3" />
                        <span>{site.licenseAndVietnamese}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* VIEW 5: VIETNAMESE DIACRITIC STRESS-TEST */}
          {/* ======================================================== */}
          {previewMode === 'diacritics' && (
            <div className="bg-charcoal/20 border border-white/10 rounded-[8px] p-6 sm:p-10 space-y-8">
              <div className="max-w-2xl">
                <span className="text-xs font-mono uppercase text-emerald-400 tracking-wider flex items-center gap-1.5 mb-2">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Bảo Đảm Tuyệt Đối Không Lỗi Glyph Dấu Tiếng Việt</span>
                </span>
                <h3 className="text-2xl font-semibold text-paper mb-2">
                  Kiểm Thử Ký Tự Tiếng Việt Cả 3 Font Đang Sử Dụng
                </h3>
                <p className="text-xs text-ash leading-relaxed">
                  Kiểm chứng toàn bộ các nguyên âm tiếng Việt mang dấu thanh (hỏi, ngã, nặng, huyền, sắc) trên các kích thước hiển thị lớn và nhỏ để đảm bảo không bị chồng lấn hay vỡ giao diện.
                </p>
              </div>

              {/* Stress test blocks */}
              <div className="space-y-6">
                {/* 1. Plus Jakarta Sans */}
                <div className="bg-obsidian/70 p-6 rounded-[6px] border border-white/10 space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono text-ash">
                    <span className="text-paper font-semibold">1. Plus Jakarta Sans (Modern Grotesque)</span>
                    <span className="text-emerald-400">100% OK (Google Fonts)</span>
                  </div>
                  <p className="font-jakarta text-2xl sm:text-3xl text-paper tracking-wide">
                    MỘT ĐIỂM HẸN. VẠN KHOẢNH KHẮC.
                  </p>
                  <p className="font-jakarta text-base text-ash">
                    Khác gu một chút. Đồng điệu một đời. Tự động nối dài cảm xúc với Lịch trình 3 chặng.
                  </p>
                  <p className="font-jakarta text-xs text-ash/80 tracking-widest font-mono">
                    Á À Ả Ã Ạ Ă Ắ Ằ Ẳ Ẵ Ặ Â Ấ Ầ Ẩ Ẫ Ậ É È Ẻ Ẽ Ẹ Ê Ế Ề Ể Ễ Ệ Í Ì Ỉ Ĩ Ị Ó Ò Ỏ Õ Ọ Ô Ố Ồ Ổ Ỗ Ộ Ơ ỚỜỞỠỢ Ú Ù Ủ Ũ Ụ Ư Ứ Ừ Ử Ữ Ự Ý Ỳ Ỷ Ỹ Ỵ
                  </p>
                </div>

                {/* 2. Playfair Display Italic */}
                <div className="bg-obsidian/70 p-6 rounded-[6px] border border-white/10 space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono text-ash">
                    <span className="text-paper font-semibold">2. Playfair Display (Artistic Serif Italic)</span>
                    <span className="text-emerald-400">100% OK (Google Fonts)</span>
                  </div>
                  <p className="font-playfair italic text-3xl sm:text-4xl text-paper">
                    Vạn Khoảnh Khắc. Đồng Điệu Một Đời.
                  </p>
                  <p className="font-playfair italic text-lg text-ash">
                    Khám phá nhà hàng lãng mạn, ẩm thực tinh hoa và rượu vang bên ánh nến lung linh tại TP.HCM.
                  </p>
                  <p className="font-playfair italic text-xs text-ash/80 tracking-widest">
                    á à ả ã ạ ă ắ ằ ẳ ẵ ặ â ấn ầ ẩ ẫ ậ é è ẻ ẽ ẹ ê ế ề ể ễ ệ í ì ỉ ĩ ị ó ò ỏ õ ọ ô ố ồ ổ ỗ ộ ơ ớ ờ ở ỡ ợ ú ù ủ ũ ụ ư ứ ừ ử ữ ự ý ỳ ỷ ỹ ỵ
                  </p>
                </div>

                {/* 3. Cormorant Garamond */}
                <div className="bg-obsidian/70 p-6 rounded-[6px] border border-white/10 space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono text-ash">
                    <span className="text-paper font-semibold">3. Cormorant Garamond (Editorial Luxury Serif)</span>
                    <span className="text-emerald-400">100% OK (Google Fonts)</span>
                  </div>
                  <p className="font-cormorant text-3xl sm:text-4xl text-paper tracking-wide">
                    MỘT ĐIỂM HẸN. VẠN KHOẢNH KHẮC.
                  </p>
                  <p className="font-cormorant italic text-2xl text-ash">
                    Khác gu một chút. Đồng điệu một đời.
                  </p>
                  <p className="font-cormorant text-xs text-ash/80 tracking-widest">
                    á à ả ã ạ ă ắ ằ ẳ ẵ ặ â ấ ầ ẩ ẫ ậ é è ẻ ẽ ẹ ê ế ề ể ễ ệ í ì ỉ ĩ ị ó ò ỏ õ ọ ô ố ồ ổ ỗ ộ ơ ớ ờ ở ỡ ợ ú ù ủ ũ ụ ư ứ ừ ử ữ ự ý ỳ ỷ ỹ ỵ
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
