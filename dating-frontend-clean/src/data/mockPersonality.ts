import { PersonalityQuestion } from '../types';

export const PERSONALITY_QUESTIONS: PersonalityQuestion[] = [
  {
    id: 1,
    text: 'Vào tối cuối tuần, bạn thích một không gian như thế nào?',
    options: [
      { label: 'Yên tĩnh, bàn riêng biệt, nhạc nhẹ du dương', score: 95, trait: 'Quiet & Intimate' },
      { label: 'Rooftop thoáng đãng, ngắm nhìn phố xá lung linh', score: 90, trait: 'View & Romance' },
      { label: 'Náo nhiệt, sôi động, quầy bar mở để giao lưu', score: 85, trait: 'Vibrant & Social' }
    ]
  },
  {
    id: 2,
    text: 'Mức độ ưu tiên của bạn đối với ẩm thực và không gian?',
    options: [
      { label: 'Đồ ăn phải ngon xuất sắc là trên hết (Food First)', score: 90, trait: 'Foodie' },
      { label: 'Cân bằng cả hai — đồ ăn ngon vừa miệng và quán phải đẹp', score: 95, trait: 'Balanced Couple' },
      { label: 'Không gian lãng mạn và sự riêng tư là ưu tiên số 1 (Vibe First)', score: 92, trait: 'Atmosphere Seeker' }
    ]
  },
  {
    id: 3,
    text: 'Khi bạn và người ấy có sở thích ăn uống trái ngược nhau?',
    options: [
      { label: 'Cùng tìm một nơi dung hòa sở thích của cả hai người', score: 98, trait: 'Agreeableness' },
      { label: 'Thay phiên nhau: lần này theo ý bạn, lần sau theo ý mình', score: 90, trait: 'Compromising' },
      { label: 'Ưu tiên cảm xúc và sự hài lòng của người mình yêu', score: 94, trait: 'Altruistic' }
    ]
  },
  {
    id: 4,
    text: 'Gu âm nhạc lý tưởng trong bữa hẹn hò của bạn?',
    options: [
      { label: 'Nhạc Acoustic mộc mạc hoặc Jazz cổ điển', score: 95, trait: 'Artistic & Thoughtful' },
      { label: 'Lo-fi chill, nhạc không lời êm dịu dễ trò chuyện', score: 92, trait: 'Cozy & Calm' },
      { label: 'Deep house, pop hiện đại tràn đầy năng lượng', score: 86, trait: 'Modern & Energetic' }
    ]
  }
];
