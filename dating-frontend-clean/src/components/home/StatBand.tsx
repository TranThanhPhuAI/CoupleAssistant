import React from 'react';

export const StatBand: React.FC = () => {
  const stats = [
    {
      value: '853',
      unit: '+',
      label: 'Địa Điểm Hẹn Hò Tuyển Chọn',
      sublabel: 'Bao phủ khắp các quận trung tâm TP.HCM'
    },
    {
      value: '20.9',
      unit: 'K',
      label: 'Đánh Giá Thực Tế Từ Foody & ShopeeFood',
      sublabel: 'Loại bỏ review ảo và các quán bơm điểm 10'
    },
    {
      value: '98.6',
      unit: '%',
      label: 'Tỷ Lệ Cặp Đôi Hài Lòng Công Bằng',
      sublabel: 'Thuật toán TOPSIS cân bằng sở thích hai người'
    }
  ];

  return (
    <section className="bg-obsidian border-y border-charcoal py-20 lg:py-24">
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 text-center md:text-left divide-y md:divide-y-0 md:divide-x divide-charcoal">
          {stats.map((stat, idx) => (
            <div key={idx} className={`flex flex-col ${idx !== 0 ? 'pt-8 md:pt-0 md:pl-10' : ''}`}>
              <div className="flex items-baseline justify-center md:justify-start font-display-clarkson text-6xl sm:text-7xl lg:text-8xl text-paper tracking-tighter mb-2">
                <span>{stat.value}</span>
                <span className="text-3xl sm:text-4xl text-ash ml-1 font-light">{stat.unit}</span>
              </div>
              <p className="text-xs sm:text-sm font-medium uppercase tracking-wider text-paper mb-1">
                {stat.label}
              </p>
              <p className="text-xs text-ash leading-relaxed">
                {stat.sublabel}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
