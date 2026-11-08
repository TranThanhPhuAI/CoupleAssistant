import { Restaurant } from '../types';

export const MOCK_RESTAURANTS: Restaurant[] = [
  {
    id: 'res-the-deck',
    name: 'The Deck Saigon — Riverside Dining',
    category: 'Romantic Riverside & Fine Dining',
    district: 'Thảo Điền',
    address: '38 Nguyễn Ư Dĩ, Thảo Điền, TP. Thủ Đức, TP. HCM',
    price_min: 450000,
    price_max: 1200000,
    price_text: '450.000đ - 1.200.000đ',
    opening_hours: '08:00 - 23:00',
    latitude: 10.8037,
    longitude: 106.7328,
    image_url: 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=80',
    gallery: [
      'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1501386761578-eac5c94b800a?auto=format&fit=crop&w=1200&q=80'
    ],
    food_score: 0.88,
    date_score: 0.94,
    couple_score: 0.91,
    is_balanced: true,
    review_count: 486,
    explanation: 'Quán có view sông Sài Gòn hoàng hôn cực đẹp, bàn sát mép nước yên tĩnh và ánh nến lung linh. Món ăn hải sản và beefsteak được chế biến tinh tế, tỷ lệ review khen không gian lãng mạn đạt 96%.',
    tags: ['View sông', 'Hoàng hôn', 'Lãng mạn', 'Thảo Điền', 'Hải sản'],
    absa_scores: {
      food: 88,
      ambiance: 97,
      quiet: 92,
      romantic: 98,
      view: 99,
      privacy: 91,
      service: 90,
      price: 76
    },
    highlight_reviews: [
      {
        id: 'rev-deck-1',
        author: 'Hoàng My & Tuấn Anh',
        rating: 9.5,
        date: '2024-03-14',
        comment: 'Hẹn hò kỷ niệm 2 năm ở đây rất tuyệt vời. Hoàng hôn buông xuống trên sông đẹp như tranh vẽ, phục vụ lịch sự và món cá hồi nướng rất ngon.',
        sentimentAspects: ['view đẹp', 'lãng mạn', 'món ăn ngon']
      },
      {
        id: 'rev-deck-2',
        author: 'Thanh Nhã',
        rating: 9.0,
        date: '2024-02-28',
        comment: 'Bàn ngoài trời thoáng đãng, nhạc nhẹ vừa phải giúp hai người trò chuyện thoải mái mà không bị ồn ào.',
        sentimentAspects: ['yên tĩnh', 'không gian']
      }
    ]
  },
  {
    id: 'res-moo-beefsteak',
    name: 'Moo Beef Steak Prime — Ngô Đức Kế',
    category: 'Steakhouse & Wine Bar',
    district: 'Quận 1',
    address: '35 - 37 Ngô Đức Kế, P. Bến Nghé, Quận 1, TP. HCM',
    price_min: 350000,
    price_max: 950000,
    price_text: '350.000đ - 950.000đ',
    opening_hours: '10:30 - 14:00, 17:30 - 22:00',
    latitude: 10.7735,
    longitude: 106.7058,
    image_url: 'https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=1200&q=80',
    gallery: [
      'https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=1200&q=80'
    ],
    food_score: 0.92,
    date_score: 0.89,
    couple_score: 0.90,
    is_balanced: true,
    review_count: 624,
    explanation: 'Thiết kế ánh sáng vàng ấm phong cách New York cổ điển, bàn ăn có khoảng cách riêng tư tốt. Thịt bò Wagyu và sốt nấm tiêu được đánh giá cao, thích hợp cho buổi tối hẹn hò sang trọng.',
    tags: ['Steakhouse', 'Quận 1', 'Rượu vang', 'Ấm cúng', 'Riêng tư'],
    absa_scores: {
      food: 95,
      ambiance: 91,
      quiet: 87,
      romantic: 92,
      view: 78,
      privacy: 89,
      service: 94,
      price: 81
    },
    highlight_reviews: [
      {
        id: 'rev-moo-1',
        author: 'Đức Huy',
        rating: 9.2,
        date: '2024-04-05',
        comment: 'Thịt bò mềm tan, sốt phô mai đặc biệt ngon. Không gian tối mờ tạo cảm giác thân mật cho hai người.',
        sentimentAspects: ['món ăn ngon', 'riêng tư', 'phục vụ']
      }
    ]
  },
  {
    id: 'res-yazawa',
    name: 'Yazawa Niku Bar — Premium Wagyu Yakiniku',
    category: 'Japanese Yakiniku & Wine',
    district: 'Quận 3',
    address: '219 Điện Biên Phủ, P. Võ Thị Sáu, Quận 3, TP. HCM',
    price_min: 500000,
    price_max: 1500000,
    price_text: '500.000đ - 1.500.000đ',
    opening_hours: '17:00 - 23:30',
    latitude: 10.7812,
    longitude: 106.6914,
    image_url: 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1200&q=80',
    gallery: [
      'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1200&q=80'
    ],
    food_score: 0.95,
    date_score: 0.88,
    couple_score: 0.91,
    is_balanced: true,
    review_count: 312,
    explanation: 'Thịt bò Kuroge Wagyu nhập khẩu Nhật Bản với hệ thống hút khói âm bàn không bám mùi vào quần áo bạn gái. Từng phòng riêng kín đáo và dịch vụ nướng tận tình.',
    tags: ['Yakiniku', 'Wagyu', 'Quận 3', 'Phòng riêng', 'Đẳng cấp'],
    absa_scores: {
      food: 98,
      ambiance: 92,
      quiet: 89,
      romantic: 88,
      view: 72,
      privacy: 96,
      service: 95,
      price: 70
    },
    highlight_reviews: [
      {
        id: 'rev-yaz-1',
        author: 'Ngọc Trâm',
        rating: 9.8,
        date: '2024-03-20',
        comment: 'Chất lượng bò tuyệt hảo, phục vụ nướng từng miếng rất vừa vặn. Điểm cộng lớn là không hề bị ám mùi khói.',
        sentimentAspects: ['món ăn ngon', 'phục vụ', 'riêng tư']
      }
    ]
  },
  {
    id: 'res-blank-lounge',
    name: 'Blank Lounge — Landmark 81 Sky View',
    category: 'Rooftop Lounge & Cocktails',
    district: 'Bình Thạnh',
    address: 'Tầng 75 - 76, Tòa nhà Landmark 81, P. 22, Bình Thạnh, TP. HCM',
    price_min: 250000,
    price_max: 750000,
    price_text: '250.000đ - 750.000đ',
    opening_hours: '09:30 - 23:00',
    latitude: 10.7951,
    longitude: 106.7218,
    image_url: 'https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=1200&q=80',
    gallery: [
      'https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1574096079513-d8259312b785?auto=format&fit=crop&w=1200&q=80'
    ],
    food_score: 0.79,
    date_score: 0.96,
    couple_score: 0.87,
    is_balanced: true,
    review_count: 890,
    explanation: 'Tọa lạc tại tầng 75 của tòa nhà cao nhất Việt Nam, sở hữu tầm nhìn 360 độ toàn cảnh Sài Gòn lung linh về đêm. Điểm đến lý tưởng cho chặng tráng miệng và cocktail ngắm thành phố.',
    tags: ['Sky View', 'Landmark 81', 'Bình Thạnh', 'Cocktail', 'Check-in'],
    absa_scores: {
      food: 80,
      ambiance: 98,
      quiet: 84,
      romantic: 96,
      view: 100,
      privacy: 82,
      service: 88,
      price: 75
    },
    highlight_reviews: [
      {
        id: 'rev-blank-1',
        author: 'Khánh Linh & Minh Khoa',
        rating: 9.4,
        date: '2024-04-10',
        comment: 'Tầm nhìn từ trên cao choáng ngợp, ngồi uống ly cocktail lúc 20h ngắm trọn vẹn thành phố lên đèn thật sự lãng mạn.',
        sentimentAspects: ['view đẹp', 'lãng mạn', 'không gian']
      }
    ]
  },
  {
    id: 'res-the-alley-bar',
    name: 'The Alley Cocktail Bar & Speakeasy',
    category: 'Speakeasy Bar & Intimate Jazz',
    district: 'Quận 1',
    address: '63/1 Pasteur, P. Bến Nghé, Quận 1, TP. HCM',
    price_min: 180000,
    price_max: 450000,
    price_text: '180.000đ - 450.000đ',
    opening_hours: '18:00 - 01:30',
    latitude: 10.7748,
    longitude: 106.7021,
    image_url: 'https://images.unsplash.com/photo-1551024709-8f23befc6f87?auto=format&fit=crop&w=1200&q=80',
    gallery: [
      'https://images.unsplash.com/photo-1551024709-8f23befc6f87?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=1200&q=80'
    ],
    food_score: 0.84,
    date_score: 0.93,
    couple_score: 0.88,
    is_balanced: true,
    review_count: 245,
    explanation: 'Nằm ẩn mình trong con hẻm cổ Pasteur, quầy bar ánh sáng trầm mặc, nhạc Jazz êm dịu tạo bầu không khí tâm sự sâu sắc cho các cặp đôi sau bữa tối.',
    tags: ['Speakeasy', 'Quận 1', 'Cocktails', 'Nhạc Jazz', 'Trò chuyện'],
    absa_scores: {
      food: 84,
      ambiance: 96,
      quiet: 94,
      romantic: 95,
      view: 70,
      privacy: 96,
      service: 92,
      price: 85
    },
    highlight_reviews: [
      {
        id: 'rev-alley-1',
        author: 'Việt Phương',
        rating: 9.3,
        date: '2024-03-18',
        comment: 'Bartender pha chế theo tâm trạng rất tinh tế. Quán không ồn ào xô bồ, hai đứa ngồi thủ thỉ suốt 2 tiếng đồng hồ.',
        sentimentAspects: ['yên tĩnh', 'riêng tư', 'phục vụ']
      }
    ]
  },
  {
    id: 'res-chidori-bed',
    name: 'Chidori Coffee in Bed — Không Gian Trà & Đọc Sách',
    category: 'Cozy Japanese Cafe & Rest',
    district: 'Quận 3',
    address: '6 Hoa Huệ, P. 7, Phú Nhuận (giáp ranh Quận 3), TP. HCM',
    price_min: 80000,
    price_max: 220000,
    price_text: '80.000đ - 220.000đ',
    opening_hours: '08:00 - 22:30',
    latitude: 10.7963,
    longitude: 106.6874,
    image_url: 'https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=1200&q=80',
    gallery: [
      'https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=1200&q=80'
    ],
    food_score: 0.80,
    date_score: 0.91,
    couple_score: 0.85,
    is_balanced: true,
    review_count: 420,
    explanation: 'Thiết kế các kén giường gỗ riêng tư kiểu Nhật, có rèm che nhẹ nhàng, nệm êm ái thích hợp cho cặp đôi nghỉ ngơi, uống trà đào dầm và đọc sách cùng nhau.',
    tags: ['Cafe giường', 'Yên tĩnh', 'Quận 3', 'Phú Nhuận', 'Riêng tư'],
    absa_scores: {
      food: 80,
      ambiance: 94,
      quiet: 97,
      romantic: 88,
      view: 74,
      privacy: 98,
      service: 89,
      price: 90
    },
    highlight_reviews: [
      {
        id: 'rev-chi-1',
        author: 'Thảo My',
        rating: 9.0,
        date: '2024-04-02',
        comment: 'Kén giường rất sạch sẽ và thơm tho. Điểm dừng chân lý tưởng vào buổi chiều để hai đứa nằm xem phim hoặc đọc sách.',
        sentimentAspects: ['yên tĩnh', 'riêng tư']
      }
    ]
  },
  {
    id: 'res-cu-dat',
    name: 'Cù Đất Quán — Lẩu & Nướng Đồng Quê',
    category: 'Cozy Hotpot & Traditional Grilled',
    district: 'Bình Thạnh',
    address: '640/2 Nguyễn Oanh, giáp ranh Bình Thạnh, TP. HCM',
    price_min: 150000,
    price_max: 350000,
    price_text: '150.000đ - 350.000đ',
    opening_hours: '11:00 - 22:30',
    latitude: 10.8245,
    longitude: 106.6892,
    image_url: 'https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=1200&q=80',
    gallery: [
      'https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=1200&q=80'
    ],
    food_score: 0.90,
    date_score: 0.72,
    couple_score: 0.80,
    is_balanced: true,
    review_count: 530,
    explanation: 'Món lẩu bò niêu đất thơm ngậy, không gian sân vườn ấm cúng mộc mạc. Phù hợp cho những cặp đôi thích bữa ăn đậm đà, thoải mái không gò bó với chi phí rất tiết kiệm.',
    tags: ['Lẩu ấm cúng', 'Bình Thạnh', 'Giá tốt', 'Mộc mạc'],
    absa_scores: {
      food: 93,
      ambiance: 75,
      quiet: 68,
      romantic: 70,
      view: 65,
      privacy: 72,
      service: 86,
      price: 96
    },
    highlight_reviews: [
      {
        id: 'rev-cudat-1',
        author: 'Phạm Tuấn',
        rating: 8.8,
        date: '2024-01-15',
        comment: 'Lẩu bò niêu đất cực ngon, thịt mềm thơm phức. Hai đứa ăn no căng bụng mà chỉ hết hơn 300k.',
        sentimentAspects: ['món ăn ngon', 'giá cả']
      }
    ]
  },
  {
    id: 'res-tre-dining',
    name: 'Tre Dining — Contemporary Vietnamese Fine Dining',
    category: 'Contemporary Vietnamese & Art',
    district: 'Thảo Điền',
    address: '35 Xuân Thủy, Thảo Điền, TP. Thủ Đức, TP. HCM',
    price_min: 600000,
    price_max: 1800000,
    price_text: '600.000đ - 1.800.000đ',
    opening_hours: '18:00 - 23:00',
    latitude: 10.8041,
    longitude: 106.7345,
    image_url: 'https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?auto=format&fit=crop&w=1200&q=80',
    gallery: [
      'https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?auto=format&fit=crop&w=1200&q=80'
    ],
    food_score: 0.96,
    date_score: 0.95,
    couple_score: 0.95,
    is_balanced: true,
    review_count: 188,
    explanation: 'Đạt giải Michelin Selected. Không gian thiết kế từ tre nứa mộc mạc nhưng đạt chuẩn quốc tế xa hoa. Tasting menu đưa đôi bạn qua những câu chuyện văn hóa ẩm thực khó quên.',
    tags: ['Michelin Selected', 'Thảo Điền', 'Nghệ thuật', 'Kỷ niệm', 'Đẳng cấp'],
    absa_scores: {
      food: 99,
      ambiance: 98,
      quiet: 93,
      romantic: 97,
      view: 88,
      privacy: 94,
      service: 98,
      price: 68
    },
    highlight_reviews: [
      {
        id: 'rev-tre-1',
        author: 'Lan Anh & Dennis',
        rating: 9.8,
        date: '2024-03-29',
        comment: 'Trải nghiệm ẩm thực xuất sắc bậc nhất Sài Gòn. Từng món ăn là một tác phẩm nghệ thuật, ánh sáng tinh tế và phục vụ vô cùng chu đáo.',
        sentimentAspects: ['món ăn ngon', 'lãng mạn', 'phục vụ']
      }
    ]
  }
];
