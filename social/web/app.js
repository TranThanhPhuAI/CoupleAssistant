// Lovespot Social — giao diện một trang. Mọi nội dung người dùng chèn bằng textContent (an toàn XSS).
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
function el(tag, attrs = {}, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") e.className = v; else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (v !== false && v != null) e.setAttribute(k, v === true ? "" : v);
  }
  for (const c of kids.flat()) if (c != null && c !== false) e.append(c instanceof Node ? c : document.createTextNode(String(c)));
  return e;
}
const show = (box, ...n) => box.replaceChildren(...n.flat().filter(Boolean));

// ===== API + token =====
// Chạy riêng (cổng 8100): API ở /api, tài khoản riêng. Chạy chung trong web Couple Assistant: API ở /social/api,
// dùng chung token đăng nhập của Couple Assistant (cùng trình duyệt, cùng tên miền).
const BASE = location.pathname.startsWith("/social") ? "/social" : "";
const EMBEDDED = window.self !== window.top;
let SHARED = false;
const tokenKey = () => (SHARED ? "couple_assistant_token" : "lovespot_token");
const tok = { get: () => { try { return localStorage.getItem(tokenKey()); } catch { return null; } },
              set: (t) => { try { t ? localStorage.setItem(tokenKey(), t) : localStorage.removeItem(tokenKey()); } catch {} } };
let ME = null, INTERESTS = [];

// ===== Nằm trong tab "Cộng đồng" của Couple Assistant (khung iframe cùng tên miền) =====
// Trang chính giữ thanh điều hướng + tab con; Lovespot báo chiều cao (để trang cuộn chung một thanh),
// màn đang mở và số thông báo; nhận lệnh chuyển màn khi người dùng bấm tab con ở trang chính.
const tellParent = (msg) => { if (EMBEDDED) window.parent.postMessage(msg, location.origin); };
if (EMBEDDED) {
  document.documentElement.classList.add("embedded");
  const report = () => tellParent({ type: "lovespot-height", h: Math.ceil(Math.max($("#app").hidden ? 0 : $("#app").scrollHeight, $("#auth").hidden ? 0 : $("#auth").scrollHeight)) });
  new ResizeObserver(report).observe(document.body);
  addEventListener("load", report);
  addEventListener("message", (e) => {
    if (e.origin !== location.origin) return;
    if (e.data?.type === "lovespot-go") location.hash = e.data.route;
    if (e.data?.type === "lovespot-theme") document.documentElement.dataset.theme = e.data.theme === "light" ? "light" : "dark";   // trang chính đổi sáng / tối
  });
}
async function api(path, opts = {}) {
  const headers = { "Content-Type": "application/json" };
  if (tok.get()) headers.Authorization = `Bearer ${tok.get()}`;
  const r = await fetch(BASE + path, { ...opts, headers, body: opts.body ? JSON.stringify(opts.body) : undefined });
  const d = await r.json().catch(() => ({}));
  if (r.status === 401 && !path.startsWith("/api/auth/")) { logout(); throw new Error("Cần đăng nhập lại"); }
  if (!r.ok) throw new Error(typeof d.detail === "string" ? d.detail : (d.detail?.[0]?.msg || `Lỗi ${r.status}`).replace(/^Value error, /, ""));
  return d;
}

// ===== Tiện ích hiển thị =====
const initial = (s) => { const t = (s || "?").trim(); const g = typeof Intl.Segmenter === "function"
  ? new Intl.Segmenter("vi", { granularity: "grapheme" }).segment(t)[Symbol.iterator]().next().value?.segment : Array.from(t)[0]; return (g || "?").toLocaleUpperCase("vi"); };
const avatar = (name, cls = "") => el("span", { class: `avatar ${cls}`, "aria-hidden": "true" }, initial(name));
const rtf = new Intl.RelativeTimeFormat("vi", { numeric: "auto" });
function ago(ts) {   // SQLite lưu giờ UTC "YYYY-MM-DD HH:MM:SS"
  const s = (Date.now() - new Date(ts.replace(" ", "T") + "Z")) / 1000;
  if (s < 60) return "vừa xong";
  for (const [u, n] of [["minute", 60], ["hour", 3600], ["day", 86400]]) if (s < n * (u === "day" ? 7 : u === "hour" ? 24 : 60)) return rtf.format(-Math.floor(s / n), u);
  return new Date(ts.replace(" ", "T") + "Z").toLocaleDateString("vi-VN");
}
const price = (p) => (p.price_min == null ? "chưa rõ giá" : `${Math.round(p.price_min / 1000)}k–${Math.round(p.price_max / 1000)}k`);
const stars = (n) => "★".repeat(n) + "☆".repeat(5 - n);
const errBox = (e) => el("p", { class: "err", role: "alert" }, e.message || String(e));
const empty = (...t) => el("p", { class: "empty" }, ...t);
const userLink = (u, cls = "name") => el("a", { href: `#/u/${u.username}`, class: cls }, u.display_name);
// Tài khoản mẫu (seed_demo.py) luôn có nhãn, để không ai nhầm là người thật
const demoTag = (u) => (u?.is_demo ? el("span", { class: "demo-tag", title: "Tài khoản mẫu để minh họa. Nội dung review lấy từ review thật của quán trên Foody." }, "Tài khoản mẫu") : null);

// ===== Đăng nhập / đăng ký =====
let registering = false;
$("#a-switch").addEventListener("click", () => {
  registering = !registering;
  $("#a-name-wrap").hidden = !registering; $("#a-name").required = registering;
  $("#auth-title").textContent = $("#a-submit").textContent = registering ? "Tạo tài khoản" : "Đăng nhập";
  $("#a-switch").textContent = registering ? "Đã có tài khoản? Đăng nhập" : "Chưa có tài khoản? Tạo tài khoản mới";
  $("#a-pass").autocomplete = registering ? "new-password" : "current-password";
});
$("#f-auth").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const f = ev.target, body = { username: f.username.value.trim().toLowerCase(), password: f.password.value };
  if (registering) body.display_name = f.display_name.value.trim();
  try { const r = await api(registering ? "/api/auth/register" : "/api/auth/login", { method: "POST", body }); tok.set(r.token); f.reset(); await start(); }
  catch (e) { show($("#a-msg"), errBox(e)); }
});
function logout() {
  ME = null; $("#app").hidden = true; $("#auth").hidden = false;
  if (!SHARED) { tok.set(null); return; }
  // Dùng chung đăng nhập: báo cho trang Couple Assistant bên ngoài đăng nhập lại, không tự xóa token của nó
  if (EMBEDDED) window.parent.postMessage({ type: "lovespot-need-login" }, location.origin);
  show($("#f-auth"), el("p", { class: "brand-line" }, "Lovespot"), el("h2", {}, "Cần đăng nhập"),
    el("p", { class: "muted" }, "Cộng đồng Lovespot dùng chung tài khoản Couple Assistant. Hãy đăng nhập ở trang chính."),
    el("a", { class: "btn primary", href: "/", target: "_top", style: "margin-top:20px;width:100%" }, "Về trang đăng nhập"));
}

async function start() {
  try { SHARED = (await api("/api/health")).shared_login; } catch {}
  if (!tok.get()) return logout();
  try { [ME, INTERESTS] = await Promise.all([api("/api/me"), api("/api/catalog/interests")]); } catch { return; }
  $("#auth").hidden = true; $("#app").hidden = false;
  $("#me-avatar").textContent = initial(ME.display_name);
  if (!location.hash) location.hash = "#/feed"; else route();
}

// ===== Điều hướng =====
const ROUTES = { feed: viewFeed, network: viewNetwork, places: viewPlaces, notifications: viewNotifications, me: viewMe, u: viewUser, p: viewPlace };
async function route() {
  if (!ME) return;
  const [name, arg] = location.hash.replace(/^#\/?/, "").split("/").map(decodeURIComponent);
  const fn = ROUTES[name] || viewFeed;
  $$(".tabs a").forEach((a) => { const on = a.dataset.route === (name || "feed"); a.classList.toggle("on", on); on ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current"); });
  $("#search-pop").hidden = true;
  const v = $("#view");
  show(v, el("p", { class: "muted" }, "Đang tải…"));
  tellParent({ type: "lovespot-route", name: name || "feed" });
  try { await fn(v, arg); } catch (e) { show(v, errBox(e)); }
  v.focus({ preventScroll: true }); EMBEDDED ? tellParent({ type: "lovespot-top" }) : scrollTo(0, 0); badges();
}
addEventListener("hashchange", route);
async function badges() {
  try {
    const [m, n] = await Promise.all([api("/api/me"), api("/api/notifications")]);
    ME = m;
    for (const [id, c] of [["#b-network", m.pending_requests], ["#b-notif", n.unread]]) { $(id).hidden = !c; $(id).textContent = c > 9 ? "9+" : c; }
    tellParent({ type: "lovespot-badges", network: m.pending_requests, notifications: n.unread });
  } catch {}
}

// ===== Tìm kiếm trên thanh trên =====
let searchTimer;
$("#q").addEventListener("input", (e) => { clearTimeout(searchTimer); searchTimer = setTimeout(() => runSearch(e.target.value.trim()), 250); });
$("#q").addEventListener("keydown", (e) => { if (e.key === "Escape") $("#search-pop").hidden = true; });
$("#f-search").addEventListener("submit", (e) => { e.preventDefault(); location.hash = `#/places/${encodeURIComponent($("#q").value.trim())}`; });
document.addEventListener("click", (e) => { if (!e.target.closest(".search")) $("#search-pop").hidden = true; });
async function runSearch(q) {
  const pop = $("#search-pop");
  if (!q) { pop.hidden = true; return; }
  const r = await api(`/api/search?q=${encodeURIComponent(q)}`).catch(() => null);
  if (!r) return;
  show(pop, r.people.length ? [el("h4", {}, "Người"), r.people.map((u) => el("a", { href: `#/u/${u.username}` }, u.display_name, el("small", {}, `@${u.username}${u.headline ? " · " + u.headline : ""}`)))] : null,
    r.places.length ? [el("h4", {}, "Quán"), r.places.map((p) => el("a", { href: `#/p/${p.id}` }, p.name, el("small", {}, `${p.district} · ${price(p)}`)))] : null,
    !r.people.length && !r.places.length ? el("h4", {}, "Không tìm thấy") : null);
  pop.hidden = false;
}

// ===== Thành phần dùng chung =====
function connectBtn(username, relation, onChange) {
  const label = { none: "Kết nối", sent: "Đã gửi lời mời", received: "Chấp nhận", connected: "Đã kết nối" }[relation];
  if (!label) return null;
  return el("button", { type: "button", class: relation === "none" || relation === "received" ? "btn primary sm" : "btn ghost sm", onclick: async (e) => {
    const b = e.currentTarget; b.disabled = true;
    try {
      if (relation === "connected" && !confirm(`Gỡ kết nối với @${username}?`)) { b.disabled = false; return; }
      const r = relation === "none" || relation === "received" ? await api(`/api/connections/${username}`, { method: "POST" })
        : await api(`/api/connections/${username}`, { method: "DELETE" });
      onChange ? onChange(r.relation) : b.replaceWith(connectBtn(username, r.relation));
    } catch (err) { alert(err.message); b.disabled = false; }
  } }, label);
}

function personRow(u, ...btns) {
  return el("div", { class: "person" }, avatar(u.display_name), el("div", { class: "who" }, userLink(u, ""), demoTag(u),
    el("small", {}, [u.headline, u.district].filter(Boolean).join(" · ") || `@${u.username}`), u.reason ? el("small", {}, u.reason) : null),
    el("div", { class: "btns" }, btns));
}

function postCard(p, onDelete) {
  const what = { review: "đã review", checkin: "đã check-in tại", status: null }[p.kind];
  const likeBtn = el("button", { type: "button", class: p.liked ? "act on" : "act", "aria-pressed": String(p.liked) }, "Thích");
  const cmtBtn = el("button", { type: "button", class: "act", "aria-expanded": "false" }, "Bình luận");
  const counts = el("span", {}, `${p.likes} lượt thích`);
  const ccount = el("span", {}, `${p.comments} bình luận`);
  const cbox = el("div", { class: "comments", hidden: true });
  likeBtn.onclick = async () => {
    try { const r = await api(`/api/posts/${p.id}/like`, { method: p.liked ? "DELETE" : "POST" });
      p.liked = r.liked; likeBtn.classList.toggle("on", r.liked); likeBtn.setAttribute("aria-pressed", String(r.liked)); counts.textContent = `${r.likes} lượt thích`; } catch (e) { alert(e.message); }
  };
  cmtBtn.onclick = async () => {
    const open = cbox.hidden; cbox.hidden = !open; cmtBtn.setAttribute("aria-expanded", String(open));
    if (!open) return;
    const list = el("div", { class: "stack" });
    const input = el("input", { type: "text", maxlength: "600", placeholder: "Viết bình luận…", "aria-label": "Viết bình luận", enterkeyhint: "send" });
    const form = el("form", { class: "comment-form", onsubmit: async (e) => {
      e.preventDefault(); if (!input.value.trim()) return;
      try { const c = await api(`/api/posts/${p.id}/comments`, { method: "POST", body: { body: input.value } }); list.append(comment(c)); input.value = ""; p.comments++; ccount.textContent = `${p.comments} bình luận`; }
      catch (err) { alert(err.message); }
    } }, input, el("button", { class: "btn sm", type: "submit" }, "Gửi"));
    show(cbox, list, form);
    try { (await api(`/api/posts/${p.id}/comments`)).forEach((c) => list.append(comment(c))); } catch (e) { list.append(errBox(e)); }
    input.focus();
  };
  const del = p.mine ? el("button", { type: "button", class: "icon-act", "aria-label": "Xóa bài viết", title: "Xóa bài viết", onclick: async () => {
    if (!confirm("Xóa bài viết này?")) return;
    try { await api(`/api/posts/${p.id}`, { method: "DELETE" }); card.remove(); onDelete?.(); } catch (e) { alert(e.message); }
  } }, "×") : null;
  const card = el("article", { class: "card post" },
    el("div", { class: "post-head" }, avatar(p.author.display_name),
      el("div", { class: "who" }, userLink(p.author), demoTag(p.author), el("small", {}, [p.author.headline, ago(p.created_at), p.visibility === "connections" ? "chỉ kết nối" : null].filter(Boolean).join(" · "))), del),
    p.place ? [what ? el("p", { class: "what" }, what) : null,
      el("a", { class: "place-chip", href: `#/p/${p.place.id}` }, el("b", {}, p.place.name), el("small", {}, `${p.place.district} · ${price(p.place)}`),
        p.rating ? el("span", { class: "rating", "aria-label": `${p.rating} trên 5 sao` }, stars(p.rating)) : null)] : null,
    p.body ? el("p", { class: "body" }, p.body) : null,
    gallery(p),
    el("div", { class: "meta-line" }, counts, ccount),
    el("div", { class: "acts" }, likeBtn, cmtBtn), cbox);
  return card;
}
// Ảnh trong bài: 1–4 ảnh xếp lưới. Ảnh của bài mẫu luôn có nhãn "Ảnh minh họa" (không phải ảnh chụp tại quán).
function gallery(p) {
  if (!p.images?.length) return null;
  return el("div", { class: `gallery g${Math.min(p.images.length, 4)}` }, p.images.map((im, i) => {
    const src = im.upload ? `${BASE}/api/uploads/${im.upload}` : im.url;
    const alt = im.demo ? "Ảnh minh họa món ăn hoặc không gian, không phải ảnh chụp tại quán"
      : `Ảnh ${i + 1} trong bài của ${p.author.display_name}${p.place ? ` về ${p.place.name}` : ""}`;
    return el("a", { class: "shot", href: src, target: "_blank", rel: "noopener" },
      el("img", { src, alt, loading: "lazy", decoding: "async" }),
      im.demo ? el("span", { class: "illus" }, `Ảnh minh họa · ${im.credit || "Unsplash"}`) : null);
  }));
}

// Thu nhỏ ảnh ngay trên máy (cạnh dài ≤ 1600px, JPEG) trước khi tải lên: nhanh hơn, tốn ít dung lượng
async function shrink(file) {
  const bmp = await createImageBitmap(file);
  const s = Math.min(1, 1600 / Math.max(bmp.width, bmp.height));
  const c = el("canvas", { width: Math.round(bmp.width * s), height: Math.round(bmp.height * s) });
  c.getContext("2d").drawImage(bmp, 0, 0, c.width, c.height);
  return c.toDataURL("image/jpeg", 0.85);
}

function comment(c) {
  return el("div", { class: "comment" }, avatar(c.author.display_name),
    el("div", { class: "bubble" }, userLink(c.author, ""), demoTag(c.author), el("p", {}, c.body)));
}

function postList(box, url, emptyMsg) {   // danh sách bài có nút "Xem thêm" (phân trang theo id)
  const list = el("div", { class: "stack" }), more = el("button", { type: "button", class: "btn ghost more", hidden: true }, "Xem thêm");
  async function load(before) {
    more.disabled = true;
    const r = await api(`${url}${url.includes("?") ? "&" : "?"}${before ? `before=${before}` : ""}`);
    if (!before && !r.items.length) list.append(empty(emptyMsg));
    r.items.forEach((p) => list.append(postCard(p)));
    more.hidden = !r.next; more.disabled = false; more.onclick = () => load(r.next).catch((e) => list.append(errBox(e)));
    return r.items.length;
  }
  show(box, list, more);
  return { load, prepend: (p) => { list.querySelector(".empty")?.remove(); list.prepend(postCard(p)); } };
}

function placePicker(onPick, preset) {   // gõ tên quán -> chọn từ danh sách quán thật
  const wrap = el("div", { class: "place-pick" });
  const input = el("input", { type: "search", placeholder: "Gắn quán (gõ tên quán)…", "aria-label": "Gắn quán", autocomplete: "off" });
  const pop = el("div", { class: "search-pop", hidden: true });
  let t;
  input.oninput = () => { clearTimeout(t); t = setTimeout(async () => {
    const q = input.value.trim(); if (!q) { pop.hidden = true; return; }
    const r = await api(`/api/places?q=${encodeURIComponent(q)}`).catch(() => []);
    show(pop, r.length ? r.slice(0, 8).map((p) => el("a", { href: "#", onclick: (e) => { e.preventDefault(); pick(p); } }, p.name, el("small", {}, `${p.district} · ${price(p)}`))) : el("h4", {}, "Không thấy quán"));
    pop.hidden = false;
  }, 250); };
  function pick(p) {
    onPick(p);
    show(wrap, el("span", { class: "picked" }, el("span", {}, p.name), el("button", { type: "button", "aria-label": "Bỏ quán", onclick: () => { onPick(null); show(wrap, input, pop); input.value = ""; input.focus(); } }, "×")));
  }
  show(wrap, input, pop);
  if (preset) pick(preset);
  return wrap;
}

function composer(onPosted, preset = null) {   // preset: quán gắn sẵn (trên trang quán) -> mặc định "Review quán"
  let place = preset, rating = 0, images = [], uploading = 0;
  const thumbs = el("div", { class: "thumbs" });
  const fileIn = el("input", { type: "file", accept: "image/*", multiple: true, class: "sr-only", id: `img-${Math.random().toString(36).slice(2)}`, "aria-label": "Chọn ảnh" });
  const addBtn = el("label", { class: "btn ghost sm add-img", for: fileIn.id }, "Thêm ảnh");
  function drawThumbs() {
    show(thumbs, images.map((name, i) => el("span", { class: "thumb" }, el("img", { src: `${BASE}/api/uploads/${name}`, alt: `Ảnh ${i + 1} sẽ đăng` }),
      el("button", { type: "button", "aria-label": `Bỏ ảnh ${i + 1}`, onclick: () => { images.splice(i, 1); drawThumbs(); } }, "×"))),
      uploading ? el("span", { class: "thumb loading" }, "Đang tải…") : null);
    addBtn.hidden = images.length + uploading >= 4;
  }
  fileIn.onchange = async () => {
    const files = [...fileIn.files].slice(0, 4 - images.length - uploading); fileIn.value = "";
    for (const f of files) {
      uploading++; drawThumbs();
      try { images.push((await api("/api/uploads", { method: "POST", body: { data: await shrink(f) } })).upload); }
      catch (e) { show(msg, errBox(new Error(`Không tải được ảnh "${f.name}": ${e.message}`))); }
      finally { uploading--; drawThumbs(); }
    }
  };
  const text = el("textarea", { rows: 3, maxlength: "2000", placeholder: "Hôm nay hai bạn đã đi đâu, ăn gì?", "aria-label": "Nội dung bài viết" });
  const kind = el("select", { "aria-label": "Loại bài" }, el("option", { value: "status" }, "Chia sẻ"), el("option", { value: "review" }, "Review quán"), el("option", { value: "checkin" }, "Check-in"));
  const vis = el("select", { "aria-label": "Ai được xem" }, el("option", { value: "public" }, "Mọi người"), el("option", { value: "connections" }, "Chỉ kết nối"));
  const starBox = el("div", { class: "stars", role: "group", "aria-label": "Chấm sao", hidden: true },
    [1, 2, 3, 4, 5].map((n) => el("button", { type: "button", "aria-label": `${n} sao`, onclick: () => { rating = n; $$("button", starBox).forEach((b, i) => { b.classList.toggle("on", i < n); b.setAttribute("aria-pressed", String(i < n)); }); } }, "★")));
  const picker = placePicker((p) => { place = p; }, preset);
  kind.onchange = () => { starBox.hidden = kind.value !== "review"; };
  if (preset) { kind.value = "review"; starBox.hidden = false; }
  const msg = el("div", { role: "alert" });
  const form = el("form", { class: "card composer", onsubmit: async (e) => {
    e.preventDefault(); show(msg);
    if (uploading) return show(msg, errBox(new Error("Đợi ảnh tải lên xong rồi đăng")));
    const body = { kind: kind.value, body: text.value, visibility: vis.value, place_id: place?.id || null, rating: kind.value === "review" ? rating || null : null, images };
    if (body.kind !== "status" && !place) return show(msg, errBox(new Error("Review và check-in cần gắn một quán")));
    if (body.kind === "review" && !rating) return show(msg, errBox(new Error("Chọn số sao cho quán")));
    try { onPosted(await api("/api/posts", { method: "POST", body })); text.value = ""; rating = 0; images = []; drawThumbs(); $$("button", starBox).forEach((b) => b.classList.remove("on"));
          if (!preset) { kind.value = "status"; starBox.hidden = true; } }
    catch (err) { show(msg, errBox(err)); }
  } }, text, thumbs, el("div", { class: "row" }, kind, picker, starBox, fileIn, addBtn, vis, el("button", { type: "submit", class: "btn primary" }, "Đăng")), msg);
  return form;
}

function meCard() {
  return el("div", { class: "card me-card" }, avatar(ME.display_name), el("a", { class: "name", href: `#/u/${ME.username}` }, ME.display_name),
    el("p", { class: "headline" }, ME.headline || "Thêm một dòng giới thiệu về gu của bạn"),
    el("div", { class: "nums" }, el("a", { href: "#/network" }, el("b", {}, ME.connections), el("small", {}, "Kết nối")),
      el("a", { href: "#/places" }, el("b", {}, ME.following_places), el("small", {}, "Quán theo dõi"))),
    ME.interests.length ? el("div", { class: "chips", style: "margin-top:16px;justify-content:center" }, ME.interests.slice(0, 6).map((i) => el("span", { class: "chip" }, INTERESTS.find((x) => x.id === i)?.label))) : null,
    el("a", { class: "link", href: "#/me", style: "display:inline-block;margin-top:12px" }, "Sửa hồ sơ"));
}

async function suggestCards() {
  const s = await api("/api/suggestions");
  return [el("div", { class: "card" }, el("h2", {}, "Người cùng gu"),
      s.people.length ? s.people.map((u) => personRow(u, connectBtn(u.username, "none"))) : el("p", { class: "muted" }, "Thêm sở thích và quận vào hồ sơ để thấy người cùng gu.")),
    el("div", { class: "card" }, el("h2", {}, "Quán đang được nhắc tới"),
      s.places.length ? s.places.map((p) => el("a", { class: "place-row", href: `#/p/${p.id}` }, el("b", {}, p.name), el("small", {}, `${p.district} · ${p.reason}`))) : el("p", { class: "muted" }, "Chưa có bài viết nào gắn quán."))];
}

// ===== Các màn hình =====
async function viewFeed(v) {
  const center = el("div", { class: "stack" }), box = el("div");
  let lister;
  const tabs = el("div", { class: "feed-tabs", role: "tablist" }, ["Bảng tin", "Khám phá"].map((t, i) => el("button", { type: "button", role: "tab", class: i ? "" : "on", "aria-selected": String(!i), onclick: (e) => {
    $$("button", tabs).forEach((b) => { b.classList.toggle("on", b === e.currentTarget); b.setAttribute("aria-selected", String(b === e.currentTarget)); });
    lister = postList(box, i ? "/api/explore" : "/api/feed", "Chưa có bài nào. Kết nối thêm người hoặc theo dõi quán, hoặc xem tab Khám phá."); lister.load().catch((er) => box.append(errBox(er)));
  } }, t)));
  show(center, composer((p) => lister.prepend(p)), tabs, box);
  show(v, el("div", { class: "cols" }, el("aside", { class: "left" }, el("div", { class: "stick" }, meCard())), center,
    el("aside", { class: "right" }, el("div", { class: "stick" }, await suggestCards()))));
  lister = postList(box, "/api/feed", "Chưa có bài nào. Kết nối thêm người hoặc theo dõi quán, hoặc xem tab Khám phá.");
  if (!(await lister.load())) tabs.children[1].click();   // người mới chưa có kết nối: mở thẳng tab Khám phá
}

async function viewNetwork(v) {
  const [c, s] = await Promise.all([api("/api/connections"), api("/api/suggestions")]);
  const again = () => viewNetwork(v);
  show(v, el("div", { class: "page-head" }, el("p", { class: "kicker" }, "Mạng lưới của bạn"), el("h1", { class: "title" }, "Kết nối")),
    el("div", { class: "cols two" }, el("div", { class: "stack" },
      el("div", { class: "card" }, el("h2", {}, `Lời mời đang chờ (${c.incoming.length})`),
        c.incoming.length ? c.incoming.map((u) => personRow({ ...u, reason: u.shared_interests.length ? `Cùng thích: ${u.shared_interests.join(", ")}` : null },
          connectBtn(u.username, "received", again), el("button", { type: "button", class: "btn ghost sm", onclick: async () => { await api(`/api/connections/${u.username}`, { method: "DELETE" }); again(); } }, "Bỏ qua")))
          : el("p", { class: "muted" }, "Không có lời mời nào.")),
      el("h2", { class: "kicker", style: "margin-top:12px" }, "Có thể bạn hợp gu"),
      s.people.length ? el("div", { class: "grid-people" }, s.people.map((u) => el("div", { class: "card" }, avatar(u.display_name), userLink(u, ""), demoTag(u), el("small", {}, u.headline || ""), el("small", {}, u.reason), connectBtn(u.username, "none"))))
        : empty("Chưa có gợi ý. Thêm sở thích và quận trong hồ sơ để tìm người cùng gu.")),
    el("div", { class: "stack" },
      el("div", { class: "card" }, el("h2", {}, `Đã kết nối (${c.connections.length})`), c.connections.length ? c.connections.map((u) => personRow(u, connectBtn(u.username, "connected", again))) : el("p", { class: "muted" }, "Chưa có kết nối.")),
      c.sent.length ? el("div", { class: "card" }, el("h2", {}, `Đã gửi lời mời (${c.sent.length})`), c.sent.map((u) => personRow(u, connectBtn(u.username, "sent", again)))) : null)));
}

async function viewPlaces(v, q = "") {
  const input = el("input", { type: "search", value: q, placeholder: "Tên quán, món, quận… (vd: lẩu Bình Thạnh)", "aria-label": "Tìm quán", enterkeyhint: "search" });
  const list = el("div");
  async function run() {
    const r = await api(`/api/places?q=${encodeURIComponent(input.value.trim())}`);
    show(list, r.length ? r.map((p) => el("a", { class: "place-row", href: `#/p/${p.id}` }, el("b", {}, p.name), el("small", {}, `${p.district} · ${p.address}`),
      el("span", { class: "num" }, price(p), el("br"), p.rating ? `${p.rating} điểm` : ""))) : empty("Không tìm thấy quán."));
  }
  let t; input.oninput = () => { clearTimeout(t); t = setTimeout(() => run().catch((e) => show(list, errBox(e))), 250); };
  show(v, el("div", { class: "page-head" }, el("p", { class: "kicker" }, "853 quán ăn và cà phê ở TP.HCM"), el("h1", { class: "title" }, "Quán")),
    el("div", { class: "card" }, input, list));
  await run();
}

async function viewPlace(v, id) {
  const p = await api(`/api/places/${encodeURIComponent(id)}`);
  const follow = el("button", { type: "button", class: p.following ? "btn ghost" : "btn primary", onclick: async () => {
    const r = await api(`/api/places/${p.id}/follow`, { method: p.following ? "DELETE" : "POST" }); p.following = r.following; viewPlace(v, id);
  } }, p.following ? "Đang theo dõi" : "Theo dõi quán");
  const posts = el("div", { class: "stack" }, p.posts.length ? p.posts.map((x) => postCard(x)) : empty("Chưa có bài viết về quán này. Hãy là người đầu tiên review."));
  show(v, el("div", { class: "card hero-card" }, el("span", { class: "avatar lg", "aria-hidden": "true" }, initial(p.name)),
      el("div", {}, el("p", { class: "kicker" }, p.type || "Quán"), el("h1", { class: "title" }, p.name), el("p", { class: "sub" }, p.address),
        el("div", { class: "facts" }, el("span", {}, p.district), el("span", {}, price(p) + " một người"), p.opening_hours ? el("span", {}, `Mở ${p.opening_hours.replaceAll("|", ", ")}`) : null,
          el("span", {}, `${p.followers} người theo dõi`), p.community_rating ? el("span", {}, `${stars(Math.round(p.community_rating))} ${p.community_rating} từ ${p.n_reviews} review trên Lovespot`) : null),
        p.n_friends_here ? el("p", { class: "sub" }, `${p.friends_here.join(", ")}${p.n_friends_here > 3 ? ` và ${p.n_friends_here - 3} người khác` : ""} trong kết nối của bạn đã nhắc tới quán này`) : null),
      el("div", { class: "btns" }, follow)),
    el("div", { class: "cols two", style: "margin-top:28px" }, el("div", { class: "stack" }, composer((x) => { posts.querySelector(".empty")?.remove(); posts.prepend(postCard(x)); }, p), posts),
      el("aside", { class: "right" }, el("div", { class: "stick" }, await suggestCards()))));
}

async function viewUser(v, username) {
  const u = await api(`/api/users/${encodeURIComponent(username)}`);
  const shared = new Set(u.shared_interests);
  show(v, el("div", { class: "card hero-card" }, avatar(u.display_name, "lg"),
      el("div", {}, el("p", { class: "kicker" }, `@${u.username} `, demoTag(u)), el("h1", { class: "title" }, u.display_name), u.headline ? el("p", { class: "sub" }, u.headline) : null,
        el("div", { class: "facts" }, u.district ? el("span", {}, u.district) : null, el("span", {}, `${u.connections} kết nối`), el("span", {}, `Tham gia ${u.joined}`),
          u.n_mutual ? el("span", {}, `${u.n_mutual} bạn chung: ${u.mutual.join(", ")}`) : null)),
      el("div", { class: "btns" }, u.relation === "self" ? el("a", { class: "btn ghost", href: "#/me" }, "Sửa hồ sơ") : connectBtn(u.username, u.relation, () => viewUser(v, username)))),
    el("div", { class: "cols two", style: "margin-top:28px" },
      el("div", { class: "stack" }, u.posts.length ? u.posts.map((p) => postCard(p)) : empty("Chưa có bài viết nào bạn được xem.")),
      el("aside", { class: "right" }, el("div", { class: "stick" },
        u.bio ? el("div", { class: "card" }, el("h2", {}, "Giới thiệu"), el("p", { style: "white-space:pre-line;overflow-wrap:anywhere" }, u.bio)) : null,
        el("div", { class: "card" }, el("h2", {}, "Gu ăn uống"), u.interests.length ? el("div", { class: "chips" }, u.interests.map((i) => el("span", { class: shared.has(i.label) ? "chip on" : "chip" }, i.label))) : el("p", { class: "muted" }, "Chưa chia sẻ."),
          shared.size ? el("p", { class: "help" }, `Chip trắng: ${shared.size} sở thích hai bạn cùng có`) : null)))));
}

async function viewNotifications(v) {
  const n = await api("/api/notifications");
  show(v, el("div", { class: "page-head" }, el("h1", { class: "title" }, "Thông báo")),
    el("div", { class: "card" }, n.items.length ? n.items.map((x) => el("div", { class: x.read ? "notif" : "notif unread" }, el("span", { class: "dot", "aria-hidden": "true" }), avatar(x.actor.display_name),
      el("p", {}, userLink(x.actor, ""), " ", x.text, el("small", {}, ago(x.created_at))),
      x.kind === "connect_request" ? el("a", { class: "btn sm ghost", href: "#/network" }, "Xem") : null)) : el("p", { class: "muted" }, "Chưa có thông báo.")));
  if (n.unread) api("/api/notifications/read", { method: "POST" }).then(badges).catch(() => {});
}

const DISTRICTS = ["Quận 1", "Quận 3", "Quận 4", "Quận 5", "Quận 6", "Quận 7", "Quận 8", "Quận 10", "Quận 11", "Quận 12", "Quận Bình Thạnh", "Quận Phú Nhuận",
  "Quận Gò Vấp", "Quận Tân Bình", "Quận Tân Phú", "Quận Bình Tân", "TP. Thủ Đức", "Huyện Bình Chánh", "Huyện Nhà Bè", "Huyện Hóc Môn", "Huyện Củ Chi"];
async function viewMe(v) {
  const groups = {}; INTERESTS.forEach((i) => (groups[i.group] ||= []).push(i));
  const f = el("form", { class: "card" },
    el("label", { for: "m-name" }, "Tên hiển thị"), el("input", { id: "m-name", name: "display_name", required: true, maxlength: "60", value: ME.display_name }),
    el("label", { for: "m-head" }, "Một dòng về gu của bạn"), el("input", { id: "m-head", name: "headline", maxlength: "120", value: ME.headline, placeholder: "vd: Mê cà phê yên tĩnh và lẩu ngày mưa" }),
    el("label", { for: "m-dist" }, "Quận hay lui tới"), el("select", { id: "m-dist", name: "district" }, el("option", { value: "" }, "Chưa chọn"), DISTRICTS.map((d) => el("option", { value: d, selected: d === ME.district }, d))),
    el("label", { for: "m-bio" }, "Giới thiệu"), el("textarea", { id: "m-bio", name: "bio", rows: 4, maxlength: "600" }, ME.bio),
    el("p", { class: "group-label" }, "Gu ăn uống"),
    Object.entries(groups).map(([g, items]) => [el("p", { class: "help" }, g), el("div", { class: "toggles" }, items.map((i) => el("label", {}, el("input", { type: "checkbox", name: "interest", value: i.id, checked: ME.interests.includes(i.id) }), i.label)))]),
    el("label", { class: "switch-row" }, el("span", {}, "Hiện gu ăn uống trên hồ sơ (tắt thì người khác không thấy, gợi ý cũng không dùng)"), el("input", { type: "checkbox", name: "show", checked: ME.show_interests })),
    el("div", { style: "display:flex;gap:12px;margin-top:22px;flex-wrap:wrap" }, el("button", { type: "submit", class: "btn primary" }, "Lưu hồ sơ"), el("a", { class: "btn ghost", href: `#/u/${ME.username}` }, "Xem hồ sơ")),
    el("div", { role: "status", id: "m-msg" }));
  f.onsubmit = async (e) => {
    e.preventDefault();
    try {
      ME = await api("/api/me", { method: "PATCH", body: { display_name: f.display_name.value, headline: f.headline.value, district: f.district.value, bio: f.bio.value,
        interests: $$("input[name=interest]:checked", f).map((c) => c.value), show_interests: f.show.checked } });
      $("#me-avatar").textContent = initial(ME.display_name); show($("#m-msg"), el("p", { class: "ok" }, "Đã lưu hồ sơ."));
    } catch (err) { show($("#m-msg"), errBox(err)); }
  };
  show(v, el("div", { class: "page-head" }, el("p", { class: "kicker" }, `@${ME.username}`), el("h1", { class: "title" }, "Hồ sơ của tôi")),
    el("div", { class: "cols two" }, f, el("aside", { class: "stack" },
      SHARED ? null : el("div", { class: "card" }, el("h2", {}, "Tài khoản"), el("button", { type: "button", class: "btn ghost", onclick: logout }, "Đăng xuất")),
      el("div", { class: "card" }, el("h2", {}, SHARED ? "Xóa hồ sơ cộng đồng" : "Xóa tài khoản"),
        el("p", { class: "muted", style: "margin-bottom:14px" }, SHARED
          ? "Xóa vĩnh viễn hồ sơ cộng đồng, bài viết, bình luận và kết nối. Tài khoản Couple Assistant vẫn giữ nguyên."
          : "Xóa vĩnh viễn hồ sơ, bài viết, bình luận và kết nối. Không khôi phục được."),
        el("button", { type: "button", class: "btn danger", onclick: async () => {
          if (!confirm(`Xóa vĩnh viễn hồ sơ cộng đồng @${ME.username}?`)) return;
          await api("/api/me", { method: "DELETE" });
          SHARED ? (location.hash = "#/feed", location.reload()) : logout();
        } }, SHARED ? "Xóa hồ sơ cộng đồng" : "Xóa tài khoản")))));
}

start();
