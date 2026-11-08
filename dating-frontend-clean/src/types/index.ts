export interface ABSAScores {
  food: number;        // Món ăn (0-100)
  ambiance: number;    // Không gian (0-100)
  quiet: number;       // Yên tĩnh (0-100)
  romantic: number;    // Lãng mạn (0-100)
  view: number;        // View đẹp (0-100)
  privacy: number;     // Riêng tư (0-100)
  service: number;     // Phục vụ (0-100)
  price: number;       // Giá cả hợp lý (0-100)
}

export interface ReviewItem {
  id: string;
  author: string;
  rating: number; // Thang 10 (Bayesian)
  date: string;
  comment: string;
  sentimentAspects: string[];
}

export interface Restaurant {
  id: string;
  name: string;
  category: string;
  district: string;
  address: string;
  price_min: number;
  price_max: number;
  price_text: string;
  opening_hours: string;
  latitude: number;
  longitude: number;
  image_url: string;
  gallery: string[];
  food_score: number;       // 0 - 1.0 (chuẩn guide dating app)
  date_score: number;       // 0 - 1.0
  couple_score: number;     // food^0.5 * date^0.5
  is_balanced: boolean;     // food >= 0.55 && date >= 0.50
  review_count: number;
  explanation: string;      // Lời giải thích khách quan dựa trên review thật
  tags: string[];
  absa_scores: ABSAScores;
  highlight_reviews: ReviewItem[];
}

export interface PersonProfile {
  name: string;
  district: string;
  budget_max: number;
  food_weight: number;      // 0 - 1
  date_weight: number;      // 0 - 1
  atmosphere_pref: string;
}

export interface ItineraryStop {
  order: number;
  stage_name: string;
  time_slot: string;
  restaurant: Restaurant;
  suggested_action: string;
  cost_estimate: number;
  transit_note?: string;
}

export interface Itinerary {
  id: string;
  title: string;
  tagline: string;
  theme: 'Lãng mạn & Tinh tế' | 'Ấm cúng & Sâu lắng' | 'Rooftop & Ánh đèn Thành phố' | 'Trẻ trung & Chill';
  estimated_cost: number;
  duration: string;
  stops: ItineraryStop[];
  fairness_rating: number; // 0 - 100%
  description: string;
}

export interface PersonalityQuestion {
  id: number;
  text: string;
  options: {
    label: string;
    score: number;
    trait: string;
  }[];
}
