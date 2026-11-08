// CHỈ DÙNG KHI PHÁT TRIỂN: dữ liệu xấu nhất cho thẻ quán (Gợi ý) và các chặng (Plan).
// Bật bằng ?data=worst | empty | one trên 127.0.0.1 / localhost (app.js mới nạp file này). Không bao giờ chạy trên tên miền thật.
// Giá trị lấy từ dữ liệu thật (853 quán) và giới hạn trong code: tên quán dài nhất 78 ký tự, địa chỉ 123, giờ mở nhiều khung,
// giá 1.000–5.500.000đ, 484 quán không có nhãn, 62 quán không có giá, user_id ≤ 40, display_name ≤ 60, lý do LLM không giới hạn.
(() => {
  const LONG_NAME = "Ăn Vặt Hày Ngộ - Cá Viên Chiên, Bánh Tráng Trộn & Chân Gà Sả Tắc - Khuông Việt";
  const LONG_ADDR = "G25 Tầng Trệt Aeon Mall Tân Phú, 30 Bờ Bao Tân Thắng, Phường Tân Sơn Nhì, TP. Hồ Chí Minh (cũ: Phường Sơn Kỳ, Quận Tân Phú)";
  const PARTNER_ID = "bartholomew_fitzgerald_northwind_2024";   // user_id hợp lệ, 37 ký tự, không có tên hiển thị
  const LONG_REASON = "Ăn Vặt Hày Ngộ (Huyện Bình Chánh, 1k - 5500k/người): vừa ngon vừa hợp hẹn hò. Điểm nổi bật theo review: món ăn ngon, không gian đẹp, lãng mạn, yên tĩnh, view đẹp, riêng tư, phục vụ tốt, giá hợp lý. Một review viết: “Quán <b>siêu</b> xinh &amp; chill, cá viên chiên giòn rụm, bánh tráng trộn đậm vị, chân gà sả tắc chua cay vừa miệng; nhân viên dễ thương, đi hai đứa ngồi tới khuya vẫn không bị hối, giữ xe free, có máy lạnh tầng 2, nhạc acoustic tối thứ 7…”. Hai bạn cùng thích ăn vặt và chụp ảnh nên đây là lựa chọn an toàn cho buổi tối đầu tuần.";
  const bd = (a, b, ka, kb) => ({ couple_score: 0.61, semantic_match: 0.42, price_fit: 0.1, food_score: 0.7, date_score: 0.55,
    [`topsis_${ka}`]: a.fit, [`distance_km_${ka}`]: a.km, [`interest_${ka}`]: 0.5, [`personality_${ka}`]: null,
    [`topsis_${kb}`]: b.fit, [`distance_km_${kb}`]: b.km, [`interest_${kb}`]: null, [`personality_${kb}`]: null });
  const item = (o) => ({ rank: 1, restaurant_id: "r_0000", district: "Quận 1", address: "1 Lê Lợi, Quận 1", opening_hours: "07:00-22:00",
    price_min: 50000, price_max: 90000, group_score: 0.7, tradeoff_label: "vừa ngon vừa hợp hẹn hò", tags: ["yên tĩnh"],
    explanation: "Hợp hẹn hò.", explanation_source: "llm", llm_rank: 1, ...o });
  const worstItems = [
    item({ rank: 1, restaurant_id: "r_a1", name: LONG_NAME, district: "Huyện Bình Chánh", address: LONG_ADDR,
      opening_hours: "00:01-01:30|06:00-09:30|15:30-23:59", price_min: 1000, price_max: 5500000, group_score: 0.0412,
      tags: ["không gian đẹp", "lãng mạn", "yên tĩnh", "view đẹp", "riêng tư", "món ngon", "phục vụ tốt"],
      tradeoff_label: "đúng yêu cầu, không gian hẹn hò chưa nổi bật", explanation: LONG_REASON,
      score_breakdown: bd({ fit: 0.0412, km: 0.04 }, { fit: 0.9988, km: 27.85 }, "nguyen_hoang_bao_ngoc", PARTNER_ID) }),
    item({ rank: 2, restaurant_id: "r_a2", name: "Hoa Mai", district: "Quận 3", opening_hours: null, price_min: null, price_max: null,
      tags: [], group_score: 1, explanation: "Hợp hẹn hò.",
      score_breakdown: bd({ fit: 1, km: null }, { fit: null, km: null }, "nguyen_hoang_bao_ngoc", "nguoi_di_cung") }),
    item({ rank: 3, restaurant_id: "r_a3", name: "Nhà Hàng Ngon - Khu Ẩm Thực Cao Cấp & Rooftop Bar \"Sky 360°\" <Lầu 26>", price_min: 5500000, price_max: 5500000,
      tags: ["ồn ào"], explanation: "Line one\nLine two: tối thứ 7 đông, nên đặt bàn trước 2 ngày.",
      score_breakdown: bd({ fit: 0.5, km: 1284.5 }, { fit: 0.5, km: 0 }, "nguyen_hoang_bao_ngoc", PARTNER_ID) }),
    item({ rank: 4, restaurant_id: "r_a4", name: "Highlands Coffee - Trà, Cà Phê & Bánh - Liberty Phạm Ngũ Lão",
      score_breakdown: bd({ fit: 0.66, km: 2.1 }, { fit: 0.64, km: 3.4 }, "nguyen_hoang_bao_ngoc", PARTNER_ID) }),
    item({ rank: 5, restaurant_id: "r_a5", name: "Highlands Coffee - Trà, Cà Phê & Bánh - Liberty Phạm Ngũ Lão",
      score_breakdown: bd({ fit: 0.65, km: 2.2 }, { fit: 0.63, km: 3.5 }, "nguyen_hoang_bao_ngoc", PARTNER_ID) }),
  ];
  const parsed = { districts: ["Quận 1", "Quận 3", "Quận Bình Thạnh", "Quận Phú Nhuận", "Huyện Bình Chánh"], budget_per_person: 5500000,
    semantic_query: "quán ăn vặt yên tĩnh có view đẹp để chụp ảnh và ngồi lâu trò chuyện tới khuya không bị hối", llm_ok: true };
  const notes = ["Không có quán nào khớp hết điều kiện -> đã nới ngân sách thêm 50%", "Không có quán nào khớp hết điều kiện -> đã mở rộng ra mọi quận",
    "Người đi cùng (bartholomew_fitzgerald_northwind_2024) chưa bật chia sẻ sở thích nên AI chỉ dùng sở thích của bạn"];
  const suggest = (items) => ({ status: "success", request_id: "b2b5c77e", quota: { used: 200, limit: 200 }, at_time: "23:59",
    parsed, items, notes, common_interests: ["Ăn vặt", "Chụp ảnh / sống ảo", "Yên tĩnh", "View đẹp", "Riêng tư", "Giá rẻ, bình dân"] });

  const stop = (o) => ({ order: 1, label: "Ăn tối", start: "19:00", end: "20:30", hop_km_from_prev: null, travel_min: 0, restaurant_id: "r_p",
    name: "Quán", district: "Quận 1", address: "1 Lê Lợi", opening_hours: "10:00-22:00", price: "100k - 200k", est_cost: 150000,
    group_score: 0.6, note: "Ghi chú.", ...o });
  const worstPlan = { status: "success", plan_id: "p1", title: "Hẹn hò ăn tối → cà phê / tráng miệng → đi dạo phố đi bộ", budget: 100000,
    quota: { used: 1, limit: 5 }, total_est_cost: 2751500,
    stops: [
      stop({ order: 1, start: "23:30", end: "01:00", name: LONG_NAME, district: "Huyện Bình Chánh", address: LONG_ADDR,
        opening_hours: "00:01-01:30|06:00-09:30|15:30-23:59", price: "1k - 5500k", est_cost: 2750500, note: LONG_REASON }),
      stop({ order: 2, label: "Cà phê / tráng miệng", start: "01:45", end: "02:45", hop_km_from_prev: 18.43, travel_min: 45,
        name: "Hoa Mai", opening_hours: null, price: "chưa có thông tin giá", est_cost: null, note: "Cà phê / tráng miệng tại Hoa Mai." }),
      stop({ order: 3, label: "Đi dạo phố đi bộ Nguyễn Huệ", start: "02:50", end: "03:00", hop_km_from_prev: 0, travel_min: 5,
        name: "Phố đi bộ", price: "1k", est_cost: 1000 }),
    ],
    issues: ["Hoa Mai có thể đóng cửa lúc 01:45 (không có giờ mở cửa)", "Hai chặng cách nhau 18,43 km (> 5 km)",
      "Tổng chi phí 2.751.500đ vượt ngân sách 100.000đ"],
    notes: ["Thiếu giá của 1 chặng nên tổng chưa đầy đủ"] };

  window.DEV_FIXTURES = {
    worst: { "/api/suggest": suggest(worstItems), "/api/plan": worstPlan },
    one: { "/api/suggest": suggest([worstItems[1]]), "/api/plan": { ...worstPlan, title: "Hẹn hò ăn tối", budget: null, issues: [], notes: [],
      stops: [stop({ name: "Hoa Mai", price: "chưa có thông tin giá", est_cost: null })] } },
    empty: { "/api/suggest": { status: "no_result", parsed, at_time: null, items: [], notes: [], common_interests: [] },
             "/api/plan": { status: "no_result", plan_id: null, stops: [], issues: ["Không tìm được quán cho mọi chặng"], notes: [] } },
  };

  // Công tắc: Demo data (API thật) / Worst case / One / Empty — ghi vào URL để tải lại vẫn giữ
  const cur = new URLSearchParams(location.search).get("data") || "demo";
  const bar = document.createElement("div");
  bar.style.cssText = "position:fixed;left:50%;bottom:12px;transform:translateX(-50%);z-index:99;display:flex;gap:2px;padding:3px;background:#e5e5e5;border-radius:999px;font:12px system-ui";
  for (const [k, label] of [["demo", "Demo data"], ["worst", "Worst case"], ["one", "One"], ["empty", "Empty"]]) {
    const b = document.createElement("button");
    b.textContent = label;
    b.style.cssText = `border:0;border-radius:999px;padding:6px 12px;cursor:pointer;background:${k === cur ? "#fff" : "transparent"}`;
    b.onclick = () => { const u = new URL(location.href); u.searchParams.set("data", k); location.href = u.toString(); };
    bar.append(b);
  }
  document.body.append(bar);
  window.DEV_AUTORUN = cur !== "demo";   // tự bấm Gợi ý và Lập plan để thấy ngay kết quả
})();
