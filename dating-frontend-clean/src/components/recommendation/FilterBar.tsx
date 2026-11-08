import React from 'react';

interface FilterBarProps {
  selectedCategory: string;
  onSelectCategory: (category: string) => void;
  selectedDistrict: string;
  onSelectDistrict: (district: string) => void;
  sortBy: 'couple_score' | 'food_score' | 'date_score' | 'price_asc';
  onSortChange: (sort: 'couple_score' | 'food_score' | 'date_score' | 'price_asc') => void;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  selectedCategory,
  onSelectCategory,
  selectedDistrict,
  onSelectDistrict,
  sortBy,
  onSortChange
}) => {
  const categories = [
    'Tất Cả',
    'Romantic Riverside & Fine Dining',
    'Steakhouse & Wine Bar',
    'Rooftop Lounge & Cocktails',
    'Speakeasy Bar & Intimate Jazz',
    'Cozy Hotpot & Traditional Grilled',
    'Cozy Japanese Cafe & Rest'
  ];

  const districts = ['Tất Cả Quận', 'Quận 1', 'Quận 3', 'Bình Thạnh', 'Thảo Điền'];

  return (
    <div className="flex flex-col gap-6 mb-8">
      {/* Category Pill Tabs - 100px radius */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => onSelectCategory(cat)}
            className={`pill-tab cursor-pointer ${
              selectedCategory === cat ? 'pill-tab-active' : 'pill-tab-inactive'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* District & Sort Dropdowns */}
      <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-charcoal text-xs">
        <div className="flex items-center gap-2">
          <span className="text-ash uppercase tracking-wider">Khu vực:</span>
          <div className="flex items-center gap-1.5 flex-wrap">
            {districts.map((d) => (
              <button
                key={d}
                onClick={() => onSelectDistrict(d)}
                className={`px-3 py-1 text-xs cursor-pointer transition-colors ${
                  selectedDistrict === d
                    ? 'bg-paper text-obsidian font-medium'
                    : 'bg-charcoal/40 text-ash hover:text-paper border border-charcoal'
                }`}
              >
                {d}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-ash uppercase tracking-wider">Xếp hạng theo:</span>
          <select
            value={sortBy}
            onChange={(e) => onSortChange(e.target.value as any)}
            className="bg-obsidian border border-charcoal text-paper text-xs py-1.5 px-3 focus:outline-none focus:border-white/50"
          >
            <option value="couple_score">Điểm Cân Bằng Cặp Đôi (Cao nhất)</option>
            <option value="food_score">Chất Lượng Món Ăn (Food Score)</option>
            <option value="date_score">Không Gian Lãng Mạn (Date Score)</option>
            <option value="price_asc">Giá Tiết Kiệm Nhất</option>
          </select>
        </div>
      </div>
    </div>
  );
};
