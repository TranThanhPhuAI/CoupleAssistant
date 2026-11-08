// Ảnh, menu, link của quán trên thẻ gợi ý và chặng plan. Dữ liệu "media" do server gắn (src/place_media.py):
// ảnh + menu quản trị viên nhập, ảnh thật người dùng đăng ở Cộng đồng, link sang trang gốc Foody / ShopeeFood.
// Dùng el, fmtK của app.js (gọi lúc vẽ thẻ nên nạp trước hay sau app.js đều được).
const MENU_SHOW = 5;

function viewPhoto(src, alt) {
  let d = document.getElementById("photo-view");
  if (!d) {
    d = el("dialog", { id: "photo-view", class: "photo-view", "aria-label": "Xem ảnh",
      onclick: (e) => { if (e.target === d || e.target.closest(".pv-close")) d.close(); } },   // bấm ra ngoài ảnh để đóng
      el("img", { alt: "" }),
      el("button", { type: "button", class: "icon-btn pv-close", "aria-label": "Đóng ảnh" }, "✕"));
    document.body.append(d);
  }
  const img = d.querySelector("img");
  img.referrerPolicy = "no-referrer"; img.src = src; img.alt = alt;
  d.showModal();
}

function mediaPhotos(m, name) {
  // [ảnh nhỏ, ảnh lớn, ghi chú nguồn]; ảnh Foody nằm trên máy chủ ảnh của họ, đổi cỡ bằng hậu tố @resize_
  const own = (m?.photos || []).map((u) => [u, u, ""]);
  const foody = (m?.foody_photos || []).map((u) => [`${u}@resize_ss320x240`, `${u}@resize_w800`, " (nguồn Foody)"]);
  const community = (m?.community_photos || []).map((u) => [u, u, " (ảnh người dùng ở Cộng đồng)"]);
  const all = [...own, ...foody, ...community];
  if (!all.length) return null;
  const src = [foody.length ? "Foody" : null, community.length ? `${community.length} ảnh người dùng ở Cộng đồng` : null].filter(Boolean);
  return el("div", { class: "shots-wrap" },
    el("div", { class: "shots" }, all.map(([thumb, full, note], i) => {
      const alt = `Ảnh ${i + 1} của ${name}${note}`;
      return el("a", { href: full, target: "_blank", rel: "noopener noreferrer", "aria-label": `${alt}, mở cỡ lớn`,
        onclick: (e) => { if (typeof HTMLDialogElement === "function") { e.preventDefault(); viewPhoto(full, alt); } } },
        el("img", { src: thumb, alt: "", loading: "lazy", decoding: "async", referrerpolicy: "no-referrer",
          onerror: (e) => e.currentTarget.parentElement?.remove() }));   // ảnh gốc đã bị gỡ: bỏ ô trống
    })),
    src.length ? el("p", { class: "shots-src" }, `Ảnh: ${src.join(" · ")}`) : null);
}

function mediaInfo(m) {
  if (!m) return null;
  const menu = m.menu || [];
  const dish = (i) => el("li", {}, el("span", {}, i.name), el("b", {}, i.price == null ? "" : fmtK(i.price)));
  let box = null;
  if (menu.length) {
    const ul = el("ul", {}, menu.slice(0, MENU_SHOW).map(dish));
    const more = menu.length > MENU_SHOW ? el("button", { type: "button", class: "more", onclick: (e) => {
      ul.append(...menu.slice(MENU_SHOW).map(dish)); e.currentTarget.remove();
    } }, `Xem cả menu (${menu.length} món)`) : null;
    box = el("div", { class: "menu" }, el("p", { class: "eyebrow" }, "Menu"), ul, more);
  }
  const link = (href, text) => href && el("a", { class: "btn small ghost", href, target: "_blank", rel: "noopener noreferrer" }, text);
  const links = [link(m.foody, "Menu & review trên Foody ↗"), link(m.order, "Đặt món ShopeeFood ↗")].filter(Boolean);
  return [box, links.length ? el("div", { class: "links" }, links) : null];
}
