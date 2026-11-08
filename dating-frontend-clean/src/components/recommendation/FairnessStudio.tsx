import React from 'react';
import { Sliders, User, Heart, MapPin, DollarSign, Scale } from 'lucide-react';
import { PersonProfile } from '../../types';

interface FairnessStudioProps {
  personA: PersonProfile;
  personB: PersonProfile;
  onChangePersonA: (updated: PersonProfile) => void;
  onChangePersonB: (updated: PersonProfile) => void;
}

export const FairnessStudio: React.FC<FairnessStudioProps> = ({
  personA,
  personB,
  onChangePersonA,
  onChangePersonB
}) => {
  const districts = ['Quận 1', 'Quận 3', 'Bình Thạnh', 'Thảo Điền', 'Phú Nhuận', 'Quận 2', 'Quận 7'];

  // Tính toán chỉ số công bằng mô phỏng
  const budgetGap = Math.abs(personA.budget_max - personB.budget_max);
  const fairnessRatio = Math.max(70, Math.min(99, Math.round(100 - (budgetGap / 20000))));

  return (
    <div className="bg-obsidian border border-charcoal p-6 lg:p-8 rounded-[8px] mb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 mb-6 border-b border-charcoal gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-white/10 flex items-center justify-center">
            <Scale className="w-5 h-5 text-paper" />
          </div>
          <div>
            <h3 className="font-display-clarkson text-xl text-paper tracking-tight">
              STUDIO CÂN BẰNG CẶP ĐÔI (TOPSIS FAIRNESS)
            </h3>
            <p className="text-xs text-ash">
              Tùy chỉnh vị trí và ngân sách riêng của từng người để AI tìm điểm hẹn hò tối ưu
            </p>
          </div>
        </div>

        {/* Dynamic Fairness Score */}
        <div className="flex items-center gap-2 bg-charcoal/50 border border-white/15 px-4 py-2 self-start sm:self-auto rounded-[100px]">
          <span className="text-xs text-ash uppercase tracking-wider">Chỉ số công bằng:</span>
          <span className="text-sm font-mono text-paper font-semibold">{fairnessRatio}%</span>
        </div>
      </div>

      {/* Two Partners Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Partner A */}
        <div className="border border-charcoal bg-charcoal/15 p-6 rounded-[8px]">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-charcoal">
            <div className="flex items-center gap-2">
              <User className="w-4 h-4 text-paper" />
              <input
                type="text"
                value={personA.name}
                onChange={(e) => onChangePersonA({ ...personA, name: e.target.value })}
                className="text-sm font-medium text-paper bg-transparent border-b border-white/20 focus:border-paper focus:outline-none px-1"
              />
            </div>
            <span className="text-[11px] font-mono text-ash uppercase">Bạn A</span>
          </div>

          <div className="space-y-4">
            {/* District Selection */}
            <div>
              <label className="text-xs text-ash flex items-center gap-1.5 mb-1.5">
                <MapPin className="w-3.5 h-3.5 text-paper" />
                <span>Vị trí xuất phát:</span>
              </label>
              <select
                value={personA.district}
                onChange={(e) => onChangePersonA({ ...personA, district: e.target.value })}
                className="w-full bg-obsidian border border-charcoal text-paper text-xs py-2 px-3 focus:outline-none focus:border-white/50"
              >
                {districts.map((d) => (
                  <option key={d} value={d} className="bg-obsidian text-paper">
                    {d}
                  </option>
                ))}
              </select>
            </div>

            {/* Budget Slider */}
            <div>
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-ash flex items-center gap-1">
                  <DollarSign className="w-3.5 h-3.5 text-paper" />
                  <span>Ngân sách tối đa:</span>
                </span>
                <span className="font-mono text-paper font-medium">
                  {personA.budget_max.toLocaleString('vi-VN')} đ
                </span>
              </div>
              <input
                type="range"
                min="100000"
                max="1500000"
                step="50000"
                value={personA.budget_max}
                onChange={(e) =>
                  onChangePersonA({ ...personA, budget_max: Number(e.target.value) })
                }
                className="w-full accent-white cursor-pointer"
              />
            </div>

            {/* Food vs Vibe Priority */}
            <div>
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-ash">Ưu tiên đồ ăn (Food):</span>
                <span className="font-mono text-paper">
                  {Math.round(personA.food_weight * 100)}%
                </span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.05"
                value={personA.food_weight}
                onChange={(e) =>
                  onChangePersonA({
                    ...personA,
                    food_weight: Number(e.target.value),
                    date_weight: 1 - Number(e.target.value)
                  })
                }
                className="w-full accent-white cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* Partner B */}
        <div className="border border-charcoal bg-charcoal/15 p-6 rounded-[8px]">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-charcoal">
            <div className="flex items-center gap-2">
              <User className="w-4 h-4 text-paper" />
              <input
                type="text"
                value={personB.name}
                onChange={(e) => onChangePersonB({ ...personB, name: e.target.value })}
                className="text-sm font-medium text-paper bg-transparent border-b border-white/20 focus:border-paper focus:outline-none px-1"
              />
            </div>
            <span className="text-[11px] font-mono text-ash uppercase">Bạn B</span>
          </div>

          <div className="space-y-4">
            {/* District Selection */}
            <div>
              <label className="text-xs text-ash flex items-center gap-1.5 mb-1.5">
                <MapPin className="w-3.5 h-3.5 text-paper" />
                <span>Vị trí xuất phát:</span>
              </label>
              <select
                value={personB.district}
                onChange={(e) => onChangePersonB({ ...personB, district: e.target.value })}
                className="w-full bg-obsidian border border-charcoal text-paper text-xs py-2 px-3 focus:outline-none focus:border-white/50"
              >
                {districts.map((d) => (
                  <option key={d} value={d} className="bg-obsidian text-paper">
                    {d}
                  </option>
                ))}
              </select>
            </div>

            {/* Budget Slider */}
            <div>
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-ash flex items-center gap-1">
                  <DollarSign className="w-3.5 h-3.5 text-paper" />
                  <span>Ngân sách tối đa:</span>
                </span>
                <span className="font-mono text-paper font-medium">
                  {personB.budget_max.toLocaleString('vi-VN')} đ
                </span>
              </div>
              <input
                type="range"
                min="100000"
                max="1500000"
                step="50000"
                value={personB.budget_max}
                onChange={(e) =>
                  onChangePersonB({ ...personB, budget_max: Number(e.target.value) })
                }
                className="w-full accent-white cursor-pointer"
              />
            </div>

            {/* Food vs Vibe Priority */}
            <div>
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-ash">Ưu tiên lãng mạn & không gian (Date):</span>
                <span className="font-mono text-paper">
                  {Math.round(personB.date_weight * 100)}%
                </span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.05"
                value={personB.date_weight}
                onChange={(e) =>
                  onChangePersonB({
                    ...personB,
                    date_weight: Number(e.target.value),
                    food_weight: 1 - Number(e.target.value)
                  })
                }
                className="w-full accent-white cursor-pointer"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
