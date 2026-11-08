import React, { useState, useMemo } from 'react';
import { useSmoothScroll } from './hooks/useSmoothScroll';
import { Navbar } from './components/common/Navbar';
import { Footer } from './components/common/Footer';
import { HeroSection } from './components/home/HeroSection';
import { CuratedDiningSection } from './components/home/CuratedDiningSection';
import { StatBand } from './components/home/StatBand';
import { AlgorithmExplainer } from './components/home/AlgorithmExplainer';
import { FeaturedGrid } from './components/home/FeaturedGrid';
import { FairnessStudio } from './components/recommendation/FairnessStudio';
import { FilterBar } from './components/recommendation/FilterBar';
import { RestaurantCard } from './components/recommendation/RestaurantCard';
import { DetailModal } from './components/restaurant-details/DetailModal';
import { ItineraryPlanner } from './components/itinerary/ItineraryPlanner';
import { RouteMapModal } from './components/itinerary/RouteMapModal';
import { PersonalityModal } from './components/personality/PersonalityModal';
import { HeroMotionDemo } from './components/demo/HeroMotionDemo';
import { MOCK_RESTAURANTS } from './data/mockRestaurants';
import { Restaurant, PersonProfile, Itinerary } from './types';
import { Search, Sparkles, SlidersHorizontal, ArrowRight } from 'lucide-react';

export function App() {
  // Kích hoạt smooth scroll điện ảnh Lenis
  useSmoothScroll();

  // Kiểm tra môi trường: Chỉ kích hoạt phòng thử nghiệm /demo trên localhost
  // Trên môi trường Production (Vercel), ẩn nút trên Navbar và vô hiệu hóa truy cập trực tiếp route /demo
  const isLocalEnvironment = useMemo(() => {
    if (typeof window === 'undefined') return false;
    return (
      import.meta.env.DEV ||
      window.location.hostname === 'localhost' ||
      window.location.hostname === '127.0.0.1' ||
      window.location.hostname.endsWith('.local')
    );
  }, []);

  // Route check độc lập cho phòng thử nghiệm /demo (Chỉ cho phép trên localhost)
  const [isDemoMode, setIsDemoMode] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    const isRequestingDemo =
      window.location.pathname.includes('/demo') ||
      window.location.search.includes('demo') ||
      window.location.hash.includes('demo');

    const isLocal =
      import.meta.env.DEV ||
      window.location.hostname === 'localhost' ||
      window.location.hostname === '127.0.0.1' ||
      window.location.hostname.endsWith('.local');

    if (isRequestingDemo && !isLocal) {
      // Trên Production: Vô hiệu hóa truy cập trực tiếp vào /demo và chuyển về trang chủ /
      window.history.replaceState({}, '', '/');
      return false;
    }

    return isRequestingDemo && isLocal;
  });

  // Navigation State
  const [currentView, setCurrentView] = useState<'home' | 'recommendation' | 'itinerary'>('home');

  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('Tất Cả');
  const [selectedDistrict, setSelectedDistrict] = useState('Tất Cả Quận');
  const [sortBy, setSortBy] = useState<'couple_score' | 'food_score' | 'date_score' | 'price_asc'>('couple_score');

  // Couple Profiles State (Bạn An & Bạn Bình)
  const [personA, setPersonA] = useState<PersonProfile>({
    name: 'Bạn An',
    district: 'Quận 1',
    budget_max: 450000,
    food_weight: 0.6,
    date_weight: 0.4,
    atmosphere_pref: 'Lãng mạn'
  });

  const [personB, setPersonB] = useState<PersonProfile>({
    name: 'Bạn Bình',
    district: 'Bình Thạnh',
    budget_max: 350000,
    food_weight: 0.4,
    date_weight: 0.6,
    atmosphere_pref: 'Yên tĩnh'
  });

  // Modal States
  const [selectedRestaurant, setSelectedRestaurant] = useState<Restaurant | null>(null);
  const [selectedItinerary, setSelectedItinerary] = useState<Itinerary | null>(null);
  const [isPersonalityOpen, setIsPersonalityOpen] = useState(false);

  // Search Submit Handler from Hero
  const handleHeroSearch = (query: string) => {
    setSearchQuery(query);
    setCurrentView('recommendation');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Filtered & Sorted Restaurants
  const filteredRestaurants = useMemo(() => {
    return MOCK_RESTAURANTS.filter((res) => {
      // Category Filter
      if (selectedCategory !== 'Tất Cả' && res.category !== selectedCategory) {
        return false;
      }
      // District Filter
      if (selectedDistrict !== 'Tất Cả Quận' && res.district !== selectedDistrict) {
        return false;
      }
      // Search Query Filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchName = res.name.toLowerCase().includes(q);
        const matchDistrict = res.district.toLowerCase().includes(q);
        const matchCategory = res.category.toLowerCase().includes(q);
        const matchTags = res.tags.some((t) => t.toLowerCase().includes(q));
        if (!matchName && !matchDistrict && !matchCategory && !matchTags) {
          return false;
        }
      }
      return true;
    }).sort((a, b) => {
      if (sortBy === 'couple_score') return b.couple_score - a.couple_score;
      if (sortBy === 'food_score') return b.food_score - a.food_score;
      if (sortBy === 'date_score') return b.date_score - a.date_score;
      if (sortBy === 'price_asc') return a.price_min - b.price_min;
      return 0;
    });
  }, [selectedCategory, selectedDistrict, searchQuery, sortBy]);

  // Nếu đang ở chế độ phòng thử nghiệm độc lập /demo
  if (isDemoMode) {
    return (
      <HeroMotionDemo
        onBackToMain={() => {
          setIsDemoMode(false);
          window.history.pushState({}, '', '/');
        }}
      />
    );
  }

  return (
    <div className="min-h-screen bg-obsidian text-paper flex flex-col font-sans">
      {/* Persistent Navigation Bar */}
      <Navbar
        currentView={currentView}
        onNavigate={(view) => {
          setCurrentView(view);
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }}
        onOpenPersonality={() => setIsPersonalityOpen(true)}
        onOpenDemo={
          isLocalEnvironment
            ? () => {
                setIsDemoMode(true);
                window.history.pushState({}, '', '/demo');
              }
            : undefined
        }
      />

      {/* Main Content Area */}
      <main className="flex-1">
        {currentView === 'home' && (
          <>
            <HeroSection
              onSearch={handleHeroSearch}
              onExplore={() => {
                setCurrentView('recommendation');
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              onOpenStudio={() => {
                setCurrentView('recommendation');
                window.scrollTo({ top: 400, behavior: 'smooth' });
              }}
              onSelectRestaurant={(res) => setSelectedRestaurant(res)}
            />
            {/* Section 2: White Canvas & Curated Dining (Phương Án 1 Đã Duyệt) */}
            <CuratedDiningSection
              onExplore={() => {
                setCurrentView('recommendation');
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              onSelectRestaurant={(res) => setSelectedRestaurant(res)}
            />
            <FeaturedGrid
              restaurants={MOCK_RESTAURANTS}
              onSelectRestaurant={(res) => setSelectedRestaurant(res)}
              onViewAll={() => {
                setCurrentView('recommendation');
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
            />

            {/* Quick Teaser to Itinerary Planner */}
            <section className="bg-obsidian py-24 border-b border-charcoal text-center">
              <div className="max-w-[800px] mx-auto px-6">
                <span className="text-xs uppercase tracking-widest text-ash block mb-3">
                  Buổi Tối Hẹn Hò Trọn Vẹn
                </span>
                <h2 className="font-jakarta font-normal text-2xl sm:text-4xl lg:text-[42px] text-paper tracking-[0.04em] uppercase leading-[1.32] max-w-3xl mx-auto mb-6">
                  TỰ ĐỘNG NỐI DÀI CẢM XÚC VỚI
                  <br />
                  LỊCH TRÌNH 3 CHẶNG
                </h2>
                <p className="text-sm text-ash leading-relaxed mb-8">
                  Không còn loay hoay sau bữa ăn tối "giờ đi đâu tiếp". AI tự động lên kế hoạch từ quán ăn ngon đến cafe ngắm cảnh và quán cocktail bar lắng đọng.
                </p>
                <button
                  onClick={() => {
                    setCurrentView('itinerary');
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }}
                  className="btn-filled-white text-xs px-8 py-3.5 cursor-pointer inline-flex items-center gap-2"
                >
                  <span>Khám Phá Lộ Trình Hẹn Hò</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </section>
          </>
        )}

        {currentView === 'recommendation' && (
          <section className="pt-32 pb-24 max-w-[1200px] mx-auto px-6">
            {/* Page Header */}
            <div className="text-center max-w-2xl mx-auto mb-12">
              <p className="text-xs uppercase tracking-widest text-ash mb-2">Hệ Thống Gợi Ý Thông Minh</p>
              <h1 className="font-display-clarkson text-4xl sm:text-6xl text-paper tracking-tighter mb-4">
                TÌM QUÁN ĂN HỢP Ý CẢ HAI
              </h1>
              <p className="text-sm text-ash leading-relaxed">
                Khám phá top quán đạt chuẩn cả về độ ngon miệng và không gian lãng mạn, được xếp hạng công bằng theo công thức TOPSIS.
              </p>
            </div>

            {/* Live Search Input */}
            <div className="max-w-2xl mx-auto mb-10">
              <div className="flex items-center bg-charcoal/20 border border-charcoal hover:border-white/50 focus-within:border-paper transition-all p-2">
                <Search className="w-4 h-4 text-ash ml-2 mr-2" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Lọc theo tên, quận hoặc không khí (VD: Steakhouse, Thảo Điền, Lãng mạn)..."
                  className="w-full bg-transparent text-paper placeholder-ash/70 text-xs sm:text-sm py-1.5 focus:outline-none"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="text-xs text-ash hover:text-paper px-2 cursor-pointer"
                  >
                    Xóa
                  </button>
                )}
              </div>
            </div>

            {/* Couple Fairness Studio */}
            <FairnessStudio
              personA={personA}
              personB={personB}
              onChangePersonA={setPersonA}
              onChangePersonB={setPersonB}
            />

            {/* Filter Bar with 100px Pill Tabs */}
            <FilterBar
              selectedCategory={selectedCategory}
              onSelectCategory={setSelectedCategory}
              selectedDistrict={selectedDistrict}
              onSelectDistrict={setSelectedDistrict}
              sortBy={sortBy}
              onSortChange={setSortBy}
            />

            {/* Restaurant Cards Grid */}
            {filteredRestaurants.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredRestaurants.map((restaurant) => (
                  <RestaurantCard
                    key={restaurant.id}
                    restaurant={restaurant}
                    onSelect={(res) => setSelectedRestaurant(res)}
                    onAddToItinerary={(res) => {
                      setSelectedRestaurant(res);
                    }}
                  />
                ))}
              </div>
            ) : (
              <div className="text-center py-20 border border-charcoal bg-charcoal/10 rounded-[8px]">
                <p className="text-ash text-sm mb-4">
                  Không tìm thấy quán phù hợp với bộ lọc hiện tại.
                </p>
                <button
                  onClick={() => {
                    setSelectedCategory('Tất Cả');
                    setSelectedDistrict('Tất Cả Quận');
                    setSearchQuery('');
                  }}
                  className="btn-ghost-white text-xs cursor-pointer"
                >
                  Đặt Lại Bộ Lọc
                </button>
              </div>
            )}
          </section>
        )}

        {currentView === 'itinerary' && (
          <ItineraryPlanner
            onOpenRouteMap={(itin) => setSelectedItinerary(itin)}
            onSelectRestaurant={(res) => setSelectedRestaurant(res)}
          />
        )}
      </main>

      {/* Modals */}
      <DetailModal
        restaurant={selectedRestaurant}
        onClose={() => setSelectedRestaurant(null)}
        onAddToItinerary={(res) => {
          // Can navigate or notify
        }}
      />

      <RouteMapModal
        itinerary={selectedItinerary}
        onClose={() => setSelectedItinerary(null)}
      />

      <PersonalityModal
        isOpen={isPersonalityOpen}
        onClose={() => setIsPersonalityOpen(false)}
        onComplete={(vibe) => {
          // Adjust state or filter
        }}
      />

      {/* Footer */}
      <Footer />
    </div>
  );
}

export default App;
