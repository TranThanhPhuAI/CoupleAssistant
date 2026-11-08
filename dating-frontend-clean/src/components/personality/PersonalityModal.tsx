import React, { useState } from 'react';
import { X, HeartHandshake, ShieldCheck, Check, Sparkles } from 'lucide-react';
import { PERSONALITY_QUESTIONS } from '../../data/mockPersonality';

interface PersonalityModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: (vibe: string) => void;
}

export const PersonalityModal: React.FC<PersonalityModalProps> = ({
  isOpen,
  onClose,
  onComplete
}) => {
  const [currentQuestionIdx, setCurrentQuestionIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [isCompleted, setIsCompleted] = useState(false);

  if (!isOpen) return null;

  const question = PERSONALITY_QUESTIONS[currentQuestionIdx];

  const handleSelectOption = (score: number) => {
    const updated = { ...answers, [question.id]: score };
    setAnswers(updated);

    if (currentQuestionIdx < PERSONALITY_QUESTIONS.length - 1) {
      setCurrentQuestionIdx(currentQuestionIdx + 1);
    } else {
      setIsCompleted(true);
      onComplete('Lãng mạn & Nghệ thuật');
    }
  };

  const handleReset = () => {
    setAnswers({});
    setCurrentQuestionIdx(0);
    setIsCompleted(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md overflow-y-auto">
      <div className="relative w-full max-w-xl bg-obsidian border border-charcoal rounded-[8px] overflow-hidden my-8 shadow-2xl p-6 sm:p-8">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-ash hover:text-paper cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-2.5 text-xs uppercase tracking-widest text-ash mb-2">
          <HeartHandshake className="w-4 h-4 text-paper" />
          <span>Trắc Nghiệm Tính Cách Hẹn Hò (BFI-10 + Dating Vibe)</span>
        </div>

        {!isCompleted ? (
          <div>
            {/* Progress indicator */}
            <div className="flex items-center justify-between text-xs text-ash mb-4">
              <span>
                Câu hỏi {currentQuestionIdx + 1} / {PERSONALITY_QUESTIONS.length}
              </span>
              <span className="font-mono text-paper">
                {Math.round(((currentQuestionIdx + 1) / PERSONALITY_QUESTIONS.length) * 100)}%
              </span>
            </div>
            <div className="w-full bg-charcoal h-1 mb-8 rounded-full overflow-hidden">
              <div
                className="bg-paper h-full transition-all duration-300"
                style={{
                  width: `${((currentQuestionIdx + 1) / PERSONALITY_QUESTIONS.length) * 100}%`
                }}
              />
            </div>

            {/* Question Text */}
            <h3 className="font-display-clarkson text-2xl text-paper tracking-tight mb-8">
              {question.text}
            </h3>

            {/* Options List */}
            <div className="space-y-3 mb-8">
              {question.options.map((opt, i) => (
                <button
                  key={i}
                  onClick={() => handleSelectOption(opt.score)}
                  className="w-full text-left p-4 border border-charcoal hover:border-paper bg-charcoal/15 hover:bg-charcoal/30 transition-all text-xs sm:text-sm text-fog hover:text-paper cursor-pointer flex items-center justify-between group"
                >
                  <span>{opt.label}</span>
                  <span className="w-4 h-4 rounded-full border border-charcoal group-hover:border-paper flex items-center justify-center shrink-0 ml-4">
                    <span className="w-2 h-2 rounded-full bg-transparent group-hover:bg-paper" />
                  </span>
                </button>
              ))}
            </div>

            {/* Privacy Guarantee Note */}
            <div className="p-3 bg-charcoal/20 border border-charcoal/50 text-[11px] text-ash flex items-start gap-2">
              <ShieldCheck className="w-4 h-4 text-paper shrink-0 mt-0.5" />
              <span>
                Dữ liệu tính cách được bảo mật tuyệt đối, chỉ lưu khi bạn đồng ý và có thể xóa bất cứ lúc nào.
              </span>
            </div>
          </div>
        ) : (
          /* Completion Result */
          <div className="text-center py-6">
            <div className="w-12 h-12 bg-white/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <Sparkles className="w-6 h-6 text-paper" />
            </div>
            <p className="text-xs uppercase tracking-widest text-ash mb-2">Kết quả phân tích phong cách</p>
            <h3 className="font-display-clarkson text-3xl text-paper tracking-tight mb-4">
              CẶP ĐÔI LÃNG MẠN & NGHỆ THUẬT
            </h3>
            <p className="text-xs text-fog leading-relaxed max-w-md mx-auto mb-8">
              Hai bạn coi trọng chiều sâu cảm xúc, không gian yên tĩnh và những trải nghiệm ẩm thực tinh tế hơn là sự ồn ào náo nhiệt. AI sẽ ưu tiên các quán có date_score cao, view sông hoặc góc ngồi riêng tư.
            </p>

            <div className="flex items-center justify-center gap-4">
              <button onClick={handleReset} className="btn-ghost-white text-xs cursor-pointer">
                Làm Lại
              </button>
              <button onClick={onClose} className="btn-filled-white text-xs cursor-pointer">
                Áp Dụng Vào Gợi Ý
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
