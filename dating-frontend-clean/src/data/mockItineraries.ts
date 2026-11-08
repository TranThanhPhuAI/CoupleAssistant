import { Itinerary } from '../types';
import { MOCK_RESTAURANTS } from './mockRestaurants';

export const MOCK_ITINERARIES: Itinerary[] = [
  {
    id: 'itin-romantic-river',
    title: 'Dạ Khúc Bên Sông & Jazz Bar Sài Gòn',
    tagline: 'Lộ trình lãng mạn cao cấp từ ẩm thực tre nghệ thuật đến cocktail hẻm cổ Pasteur',
    theme: 'Lãng mạn & Tinh tế',
    estimated_cost: 1650000,
    duration: '5 giờ (18:00 - 23:00)',
    fairness_rating: 96,
    description: 'Được AI tính toán tối ưu dựa trên vị trí trung tâm giữa Thảo Điền và Quận 1, cân bằng hoàn hảo giữa món ăn ngon (96%) và không gian hẹn hò lãng mạn (94%).',
    stops: [
      {
        order: 1,
        stage_name: 'Chặng 1: Bữa Tối Thăng Hoa Cảm Xúc',
        time_slot: '18:30 - 20:00',
        restaurant: MOCK_RESTAURANTS[7], // Tre Dining
        suggested_action: 'Thưởng thức Tasting menu ẩm thực Việt đương đại dưới ánh nến ấm áp.',
        cost_estimate: 1100000,
        transit_note: 'Xuất phát từ điểm hẹn đến Thảo Điền'
      },
      {
        order: 2,
        stage_name: 'Chặng 2: Gió Sông Hoàng Hôn & Tráng Miệng',
        time_slot: '20:15 - 21:15',
        restaurant: MOCK_RESTAURANTS[0], // The Deck
        suggested_action: 'Ngồi bàn sát mép nước, thưởng thức cocktail trái cây nhiệt đới và kem tráng miệng.',
        cost_estimate: 300000,
        transit_note: 'Di chuyển 5 phút bằng taxi (1.2 km)'
      },
      {
        order: 3,
        stage_name: 'Chặng 3: Lắng Đọng Trong Tiếng Nhạc Jazz',
        time_slot: '21:30 - 23:00',
        restaurant: MOCK_RESTAURANTS[4], // The Alley Bar
        suggested_action: 'Hai người thưởng thức Signature cocktail mang phong vị Sài Gòn xưa và trò chuyện sâu sắc.',
        cost_estimate: 250000,
        transit_note: 'Di chuyển qua cầu Sài Gòn về Quận 1 (15 phút, 6.5 km)'
      }
    ]
  },
  {
    id: 'itin-sky-night',
    title: 'Ánh Đèn Thành Phố & Tầng Mây Landmark',
    tagline: 'Trải nghiệm hẹn hò hiện đại, ngắm nhìn trọn vẹn vẻ tráng lệ của Sài Gòn từ trên cao',
    theme: 'Rooftop & Ánh đèn Thành phố',
    estimated_cost: 950000,
    duration: '4.5 giờ (18:30 - 23:00)',
    fairness_rating: 92,
    description: 'Sự kết hợp giữa bữa tối beefsteak New York cổ điển và ly đồ uống ngắm toàn cảnh Sài Gòn 360 độ từ tầng 75 Landmark 81.',
    stops: [
      {
        order: 1,
        stage_name: 'Chặng 1: Steakhouse & Rượu Vang',
        time_slot: '18:30 - 20:15',
        restaurant: MOCK_RESTAURANTS[1], // Moo Beefsteak
        suggested_action: 'Ăn tối thịt bò hảo hạng, nếm rượu vang đỏ trong không gian New York sang trọng.',
        cost_estimate: 600000,
        transit_note: 'Gặp nhau tại trung tâm Quận 1'
      },
      {
        order: 2,
        stage_name: 'Chặng 2: Ngắm Sài Gòn Từ Tầng 75',
        time_slot: '20:30 - 22:30',
        restaurant: MOCK_RESTAURANTS[3], // Blank Lounge
        suggested_action: 'Thưởng thức trà thảo mộc hoặc mocktail, chụp những bức hình kỷ niệm tuyệt đẹp.',
        cost_estimate: 350000,
        transit_note: 'Đi taxi dọc đường Nguyễn Hữu Cảnh sang Landmark 81 (10 phút, 3.8 km)'
      }
    ]
  },
  {
    id: 'itin-cozy-relax',
    title: 'Thư Thái & Hương Vị Thân Mật Bình Yên',
    tagline: 'Lẩu ấm cúng đậm đà kết hợp kén gỗ đọc sách kiểu Nhật tiết kiệm và ngọt ngào',
    theme: 'Ấm cúng & Sâu lắng',
    estimated_cost: 380000,
    duration: '4 giờ (18:00 - 22:00)',
    fairness_rating: 94,
    description: 'Dành riêng cho những cặp đôi hướng nội, yêu thích sự mộc mạc, gần gũi và không gian riêng tư tuyệt đối.',
    stops: [
      {
        order: 1,
        stage_name: 'Chặng 1: Nồi Lẩu Niêu Đất Ấm Nồng',
        time_slot: '18:00 - 19:45',
        restaurant: MOCK_RESTAURANTS[6], // Cù Đất
        suggested_action: 'Thưởng thức nồi lẩu bò niêu đất nóng hổi, thoải mái trò chuyện tự nhiên.',
        cost_estimate: 240000,
        transit_note: 'Gặp gỡ gần ranh giới Bình Thạnh'
      },
      {
        order: 2,
        stage_name: 'Chặng 2: Kén Giường Gỗ Riêng Tư & Trà Đào',
        time_slot: '20:00 - 22:00',
        restaurant: MOCK_RESTAURANTS[5], // Chidori Coffee in Bed
        suggested_action: 'Nghỉ ngơi trong kén giường gỗ thơm mùi tinh dầu, cùng đọc sách hoặc xem phim.',
        cost_estimate: 140000,
        transit_note: 'Đi xe máy 8 phút qua khu Phan Xích Long (2.5 km)'
      }
    ]
  }
];
