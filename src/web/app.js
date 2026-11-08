// Giao diện Couple Assistant — gọi API /api/*. Mọi nội dung từ dữ liệu/LLM được chèn bằng textContent (an toàn XSS).
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

function el(tag, attrs = {}, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") e.className = v;
    else if (k === "style") e.style.cssText = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (v !== false && v != null) e.setAttribute(k, v);
  }
  for (const c of kids.flat()) if (c != null && c !== false) e.append(c instanceof Node ? c : document.createTextNode(String(c)));
  return e;
}
const show = (box, ...nodes) => box.replaceChildren(...nodes.flat().filter(Boolean));

// ===== Token đăng nhập (lưu trong trình duyệt này) =====
const TOKEN_KEY = "couple_assistant_token";
const getToken = () => { try { return localStorage.getItem(TOKEN_KEY); } catch { return null; } };
const setToken = (t) => { try { t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY); } catch {} };
let AUTH = false, ME = null, HEALTH = null, INTERESTS = [], PROFILES = [], MY_PROFILE = null;

// Chỉ khi phát triển (127.0.0.1/localhost + ?data=worst|one|empty|demo): nạp dữ liệu xấu nhất từ /static/dev/fixtures.js
const DEV_DATA = ["127.0.0.1", "localhost"].includes(location.hostname) && new URLSearchParams(location.search).get("data");
const loadDevFixtures = () => new Promise((ok) => { const s = document.createElement("script"); s.src = "/static/dev/fixtures.js"; s.onload = s.onerror = ok; document.head.append(s); });

async function api(path, opts = {}) {
  const fx = DEV_DATA && window.DEV_FIXTURES?.[DEV_DATA]?.[path];
  if (fx) return structuredClone(fx);
  const headers = { "Content-Type": "application/json" };
  const tok = getToken();
  if (tok) headers.Authorization = `Bearer ${tok}`;
  const r = await fetch(path, { ...opts, headers });
  const data = await r.json().catch(() => ({}));
  if (r.status === 401 && AUTH && !path.startsWith("/api/auth/login")) { logout(data.detail); throw new Error(data.detail || "Cần đăng nhập lại"); }
  if (!r.ok) throw new Error(typeof data.detail === "string" ? data.detail : (data.detail?.[0]?.msg || `Lỗi ${r.status}`));
  return data;
}

// ===== Định dạng =====
// 50k, 1,5tr: giá từ 1 triệu trở lên đọc bằng "tr" (dữ liệu có quán 5.500.000đ)
const fmtK = (v) => (v == null ? "—" : v >= 1e6 ? `${(v / 1e6).toLocaleString("vi-VN", { maximumFractionDigits: 1 })}tr` : `${Math.round(v / 1000)}k`);
const price = (lo, hi) => (lo == null ? "chưa rõ giá" : `${lo === hi ? fmtK(lo) : `${fmtK(lo)}–${fmtK(hi)}`} một người`);
// "00:01-01:30|06:00-09:30" -> "00:01–01:30, 06:00–09:30"
const fmtHours = (oh) => oh.split("|").map((s) => s.trim().replace("-", "–")).join(", ");
const vnd = (v) => `${Math.round(v).toLocaleString("vi-VN")}đ`;
// limit = null: quản trị viên, không giới hạn lượt
const quotaText = (q) => (q.limit == null ? `${q.used} (quản trị, không giới hạn)` : `${q.used} / ${q.limit}`);
const pct = (v) => (v == null ? "—" : `${Math.round(v * 100)}%`);
const km = (v) => (v < 0.05 ? "ngay gần" : `${v.toLocaleString("vi-VN", { maximumFractionDigits: v >= 100 ? 0 : 1 })} km`);
const toMin = (t) => +t.slice(0, 2) * 60 + +t.slice(3, 5);
// chữ cái đầu theo cụm ký tự (emoji, chữ có dấu không bị cắt đôi)
const initial = (s) => { const t = (s || "").trim(); if (!t) return "?";
  const g = typeof Intl.Segmenter === "function" ? new Intl.Segmenter("vi", { granularity: "grapheme" }).segment(t)[Symbol.iterator]().next().value.segment : Array.from(t)[0];
  return g.toLocaleUpperCase("vi"); };
const PARTNER = "nguoi_di_cung";

const errorBox = (e, retry) => el("div", { class: "error-box", role: "alert" }, e.message || String(e),
  retry ? el("button", { type: "button", onclick: retry }, "Thử lại") : null);

// ===== Màn hình (thanh bên) =====
const TITLES = { suggest: "Gợi ý quán", plan: "Lập plan", community: "Cộng đồng", profile: "Hồ sơ của tôi", stats: "Thống kê AI", admin: "Phân quyền" };
// push: thêm vào lịch sử để nút Back của trình duyệt quay về màn trước; focus: đưa focus tới tiêu đề màn mới
function go(view, push = true, focus = push) {
  const hiddenTab = { stats: "#tab-stats", community: "#tab-community", admin: "#tab-admin" }[view];
  if (!TITLES[view] || (hiddenTab && $(hiddenTab).hidden)) view = "suggest";
  if (view === "admin") window.loadAdmin?.();   // static/admin.js
  if (view === "community") openCommunity();
  $$(".nav").forEach((b) => { const on = b.dataset.view === view; b.classList.toggle("active", on); on ? b.setAttribute("aria-current", "page") : b.removeAttribute("aria-current"); });
  $$(".view").forEach((v) => v.classList.toggle("active", v.id === view));
  $("#top-title").textContent = TITLES[view];
  document.title = `${TITLES[view]} · Couple Assistant`;
  if (push && location.hash !== `#${view}`) history.pushState(null, "", `#${view}`);
  toggleMenu(false, false);
  if (focus) { const h = $(`#${view} h1`); h.setAttribute("tabindex", "-1"); h.focus({ preventScroll: true }); window.scrollTo(0, 0); }
  playHeroVideo(view); onScroll();
  if (view === "stats") loadStats();
}
$$(".nav").forEach((b) => b.addEventListener("click", () => go(b.dataset.view)));
$$("[data-go]").forEach((b) => b.addEventListener("click", () => go(b.dataset.go)));

// Tab Cộng đồng: mạng xã hội Lovespot (/social/) trong khung cùng tên miền, tải ở lần đầu mở tab.
// Trang chính giữ tiêu đề + tab con; khung cao theo nội dung Lovespot báo lên -> cả trang cuộn chung một thanh.
function openCommunity() {
  const f = $("#community-frame");
  if (!f.dataset.loaded) { f.src = "/social/#/feed"; f.dataset.loaded = "1"; }
}
$$(".subtabs button").forEach((b) => b.addEventListener("click", () => {
  $("#community-frame").contentWindow?.postMessage({ type: "lovespot-go", route: `#/${b.dataset.sub}` }, location.origin);
}));
addEventListener("message", (e) => {
  if (e.origin !== location.origin || !e.data?.type) return;
  const d = e.data, f = $("#community-frame");
  if (d.type === "lovespot-height") f.style.height = `${Math.max(400, d.h)}px`;
  else if (d.type === "lovespot-route") $$(".subtabs button").forEach((b) => {
    const on = b.dataset.sub === d.name; b.classList.toggle("on", on); on ? b.setAttribute("aria-current", "page") : b.removeAttribute("aria-current");
  });
  else if (d.type === "lovespot-badges") for (const k of ["network", "notifications"]) { const s = $(`#sb-${k}`); s.hidden = !d[k]; s.textContent = d[k] > 9 ? "9+" : d[k]; }
  else if (d.type === "lovespot-top") { const top = f.getBoundingClientRect().top + scrollY - $("#topnav").offsetHeight; if (scrollY > top) scrollTo(0, top); }
  else if (d.type === "lovespot-need-login") logout("Phiên đăng nhập đã hết hạn, hãy đăng nhập lại.");   // phiên hết hạn -> đăng nhập lại ở trang chính
});

// Video đầu trang: chỉ phát ở màn đang mở; người chọn giảm chuyển động thì để yên khung hình
const REDUCED = matchMedia("(prefers-reduced-motion: reduce)").matches;
function playHeroVideo(view) {
  $$(".view .hero-video").forEach((v) => { if (v.closest(".view").id === view && !REDUCED) v.play().catch(() => {}); else v.pause(); });
}
// Thanh điều hướng trong suốt trên video, chuyển nền đen khi cuộn (hoặc khi màn không có video); video phóng nhẹ khi cuộn
let ticking = false;
function onScroll() {
  if (ticking) return; ticking = true;
  requestAnimationFrame(() => {
    ticking = false;
    const hero = $(".view.active .hero");
    $("#topnav").classList.toggle("solid", !hero || scrollY > 40);
    if (hero && !REDUCED) hero.querySelector(".hero-video").style.setProperty("--zoom", 1 + Math.min(1, scrollY / hero.offsetHeight) * 0.12);
  });
}
addEventListener("scroll", onScroll, { passive: true });
function toggleMenu(open, restore = true) {
  const side = $("#side"), was = side.classList.contains("open");
  side.classList.toggle("open", open); $("#menu").setAttribute("aria-expanded", String(open));
  document.body.style.overflow = open ? "hidden" : "";
  if (open) $(".nav.active").focus(); else if (was && restore) $("#menu").focus();
}
$("#menu").addEventListener("click", () => toggleMenu(true));
$("#menu-close").addEventListener("click", () => toggleMenu(false));
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && $("#side").classList.contains("open")) toggleMenu(false); });

// ===== Khởi động: trạng thái server -> đăng nhập (nếu cần) -> ứng dụng =====
async function init() {
  if (DEV_DATA) await loadDevFixtures();
  try {
    HEALTH = await api("/api/health");
    AUTH = HEALTH.auth_required;
    const ai = { ollama: "AI máy nhà sẵn sàng", anthropic: "AI Claude (dự phòng) sẵn sàng" }[HEALTH.llm_provider]
      || "AI chưa chạy: vẫn gợi ý theo điểm";
    const s = $("#status");
    s.textContent = ai; s.className = `status ${HEALTH.llm_provider ? "ok" : "warn"}`;
    $("#auth-status").textContent = `${HEALTH.restaurants.toLocaleString("vi-VN")} quán ở TP.HCM · ${ai}`;
    $("#scope").textContent = `TP.HCM · ${HEALTH.restaurants.toLocaleString("vi-VN")} quán`;
    $("#p-plan").replaceChildren(...Object.entries(HEALTH.ai_plans).map(([k, n]) => el("option", { value: k }, `${k}: ${n} lượt/ngày`)));
    $("#l-register").hidden = !HEALTH.allow_register;
    $("#tab-community").hidden = !HEALTH.social;
  } catch {
    $("#auth").hidden = false;
    show($("#r-login"), errorBox(new Error("Không kết nối được máy chủ. Kiểm tra server đã chạy chưa."), () => location.reload()));
    return;
  }
  INTERESTS = await api("/api/interests");
  if (AUTH && !getToken()) return showLogin();
  try { await enterApp(); } catch { /* 401 đã chuyển về màn hình đăng nhập */ }
}

function showLogin(msg) {
  $("#app").hidden = true; $("#auth").hidden = false;
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) $("#auth video").pause();
  show($("#r-login"), msg ? errorBox(new Error(msg)) : null);
  $("#l-user").focus();
}
function logout(msg) {
  setToken(null); ME = null; MY_PROFILE = null;
  const f = $("#community-frame"); f.src = "about:blank"; f.dataset.loaded = "";   // người đăng nhập sau không thấy phiên Cộng đồng của người trước
  showLogin(msg);
}
$("#logout").addEventListener("click", () => logout());

// Tên đăng nhập không có dấu: gõ "phú" tự thành "phu" (giữ nguyên chữ hoa/thường vì "phu" và "PHu" là hai tài khoản khác nhau)
const noAccent = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D").trim();
async function authSubmit(path) {
  const form = $("#f-login");
  form.user_id.value = noAccent(form.user_id.value);
  if (!form.reportValidity()) return;
  try {
    const r = await api(path, { method: "POST", body: JSON.stringify({ user_id: form.user_id.value.trim(), password: form.password.value }) });
    setToken(r.token); form.reset();
    await enterApp();
  } catch (e) { show($("#r-login"), errorBox(e)); }
}
$("#f-login").addEventListener("submit", (ev) => { ev.preventDefault(); authSubmit("/api/auth/login"); });
$("#l-register").addEventListener("click", () => authSubmit("/api/auth/register"));

async function enterApp() {
  ME = AUTH ? await api("/api/auth/me") : null;
  $("#auth").hidden = true; $("#app").hidden = false;
  const isAdmin = !AUTH || ME.role === "admin";
  $("#me-row").hidden = $("#logout").hidden = !ME;
  $$(".asker").forEach((f) => (f.hidden = AUTH));   // người hỏi = người đang đăng nhập
  $("#tab-stats").hidden = !isAdmin;
  $("#tab-admin").hidden = !(AUTH && ME.role === "admin");   // phân quyền chỉ có nghĩa khi bật đăng nhập
  $("#p-pick-wrap").hidden = AUTH && !isAdmin;
  $("#p-plan").disabled = !isAdmin;
  $("#p-delete-account-row").hidden = !AUTH;
  MY_PROFILE = ME?.has_profile ? await api(`/api/profiles/${encodeURIComponent(ME.user_id)}`).catch(() => null) : null;
  renderInterestToggles();
  await refreshProfiles();
  if (AUTH && !isAdmin) await loadOwnProfile();
  renderMe(); renderIdle();
  go(location.hash.slice(1) || "suggest", false);
  if (window.DEV_AUTORUN) for (const f of ["#f-suggest", "#f-plan"]) { $(`${f} textarea`).value ||= "dữ liệu xấu nhất"; $(f).requestSubmit(); }
}

const myName = () => MY_PROFILE?.display_name || ME?.user_id || "bạn";
function renderMe() {
  const hour = new Date().getHours();
  const part = hour < 11 ? "Sáng nay" : hour < 14 ? "Trưa nay" : hour < 17 ? "Chiều nay" : "Tối nay";
  $("#greeting").textContent = `${ME ? `${part} đi đâu, ${myName()}?` : `${part} hai bạn đi đâu?`} Quán ăn, cà phê hợp gu cả hai giữa lòng Sài Gòn.`;
  const d = new Date().toLocaleDateString("vi-VN", { weekday: "long", day: "numeric", month: "long" });
  $("#today").textContent = `${d.charAt(0).toUpperCase() + d.slice(1)} · ${HEALTH.restaurants.toLocaleString("vi-VN")} quán ăn và cà phê ở TP.HCM`;
  if (ME) {
    $("#me-avatar").textContent = initial(myName());
    $("#me-name").textContent = myName();
    $("#me-role").textContent = ME.role === "admin" ? `${ME.user_id} · quản trị` : ME.user_id;
  }
}

async function loadOwnProfile() {
  const form = $("#f-profile");
  form.reset(); form.user_id.value = ME.user_id; form.user_id.readOnly = true;
  if (!MY_PROFILE) { $("#p-sub").textContent = "Bạn chưa có hồ sơ. Chọn vài sở thích, bật đồng ý rồi bấm Lưu hồ sơ."; renderInterestToggles(); return; }
  fillProfile(MY_PROFILE);
}
function fillProfile(p) {
  const form = $("#f-profile");
  form.user_id.value = p.user_id; form.user_id.readOnly = true;
  form.display_name.value = p.display_name || ""; form.plan.value = p.plan;
  form.share.checked = p.share_interests_with_partner; form.consent.checked = true;
  renderInterestToggles(p.interests);
}

async function refreshProfiles(selectId) {
  PROFILES = await api("/api/profiles");
  const opts = (none, skipSelf) => [el("option", { value: "" }, none),
    ...PROFILES.filter((p) => !(skipSelf && ME && p.user_id === ME.user_id))
               .map((p) => el("option", { value: p.user_id }, p.display_name && p.display_name !== p.user_id ? `${p.display_name} (${p.user_id})` : p.user_id))];
  $$("select.who[name=user_a]").forEach((s) => { const v = s.value; s.replaceChildren(...opts("Khách (dùng thử)")); s.value = v; });
  $$("select.who[name=user_b]").forEach((s) => { const v = s.value; s.replaceChildren(...opts("Chưa chọn (không có hồ sơ)", true)); s.value = v; });
  const pick = $("#p-pick");
  pick.replaceChildren(el("option", { value: "" }, "Tạo hồ sơ mới"), ...opts("").slice(1));
  pick.value = selectId || "";
}

$$(".examples .chip").forEach((c) => c.addEventListener("click", () => { const q = $("#s-query"); q.value = c.textContent; q.focus(); }));

function formBody(form, extra = {}) {
  const f = new FormData(form);
  const body = { query: f.get("query").trim(), use_llm: form.use_llm.checked, ...extra };
  for (const k of ["user_a", "user_b"]) if (f.get(k) && !(AUTH && k === "user_a")) body[k] = f.get(k);
  if (f.get("budget")) body.budget = Number(f.get("budget"));
  return body;
}

// ===== Gợi ý quán =====
function renderIdle() {
  $("#r-count").hidden = true;
  show($("#r-suggest"), el("div", { class: "empty" }, el("b", {}, "Chưa có gợi ý nào. "),
    "Gõ mong muốn ở trên (khu vực, món, không khí, giờ, ngân sách) rồi bấm Gợi ý quán. Có AI thì mất khoảng 30 giây.",
    el("p", { class: "side-note" }, "Cách chấm: mỗi quán được chấm riêng cho từng người rồi gộp lại, một nửa là điểm trung bình, một nửa là điểm của người kém hài lòng hơn, nên không ai phải chịu thiệt nhiều.")));
  const mine = MY_PROFILE?.interests?.map((id) => INTERESTS.find((i) => i.id === id)?.label).filter(Boolean) || [];
  show($("#r-side"),
    el("div", { class: "side-block" }, el("h2", {}, "Sở thích của bạn"),
      mine.length ? el("div", { class: "chips" }, mine.map((m) => el("span", { class: "tag" }, m)))
                  : el("p", { class: "side-note" }, ME ? "Chưa có. Hồ sơ giúp AI chọn quán sát hơn." : "Chọn người hỏi để dùng hồ sơ."),
      ME ? el("button", { type: "button", class: "btn small", style: "margin-top:12px", onclick: () => go("profile") }, mine.length ? "Sửa hồ sơ" : "Tạo hồ sơ") : null),
    el("div", { class: "side-block" }, el("h2", {}, "Nói rõ để gợi ý sát hơn"),
      el("dl", { class: "kv" }, [["Nơi, ngân sách", "Quận 3, 200k/người"], ["Không khí, món", "yên tĩnh, lẩu"]]
        .map(([k, v]) => el("div", {}, el("dt", {}, k), el("dd", {}, v))))));
}

function skeleton(msg) {
  const row = () => el("div", { class: "skeleton", "aria-hidden": "true" }, el("i", { class: "s" }),
    el("div", {}, el("i", { class: "h" }), el("i", { class: "s" }), el("i", { class: "l" }), el("i", { class: "l" })),
    el("div", {}, el("i", {}), el("i", {}), el("i", {})));
  return [el("p", { class: "wait" }, msg), el("div", { class: "places" }, row(), row(), row())];
}

function emptyBox(res, fallback) {
  if (res.status !== "no_profile") return el("div", { class: "empty" }, res.message || fallback);
  return el("div", { class: "empty" }, el("b", {}, res.message), el("br"),
    el("button", { type: "button", class: "btn primary", onclick: () => go("profile") }, "Tạo hồ sơ ngay"));
}

$("#f-suggest").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const form = ev.target, box = $("#r-suggest"), btn = $("button[type=submit]", form);
  const body = formBody(form, form.at_time.value ? { at_time: form.at_time.value } : {});
  btn.disabled = true; $("#r-count").hidden = true;
  show(box, skeleton(body.use_llm ? "AI đang lọc 853 quán và chọn cho hai bạn, khoảng 30 giây…" : "Đang chấm điểm các quán…"));
  try {
    const res = await api("/api/suggest", { method: "POST", body: JSON.stringify(body) });
    renderSide(res);
    if (res.status !== "success") { show(box, emptyBox(res, "Không có quán phù hợp. Thử bỏ bớt khu vực, tăng ngân sách hoặc đổi giờ.")); return; }
    $("#r-count").textContent = `${res.items.length} quán`; $("#r-count").hidden = false;
    show(box, el("div", { class: "places" }, res.items.map((it) => placeCard(it, res, ME ? ME.user_id : body.user_a))));
  } catch (e) { show(box, errorBox(e, () => form.requestSubmit())); } finally { btn.disabled = false; }
});

// Tên hai người lấy từ khóa topsis_<tên> trong score_breakdown (người hỏi trước, người đi cùng sau)
function people(it) {
  return Object.keys(it.score_breakdown || {}).filter((k) => k.startsWith("topsis_")).map((k, i) => {
    const id = k.slice(7);
    const prof = PROFILES.find((p) => p.user_id === id);
    const name = id === PARTNER ? "Người đi cùng" : ME && id === ME.user_id ? myName() : prof?.display_name || id;
    return { id, name, cls: i === 0 ? "p-a" : "p-b", fit: it.score_breakdown[k], km: it.score_breakdown[`distance_km_${id}`] };
  });
}

function markIcon() {
  const ns = "http://www.w3.org/2000/svg", svg = document.createElementNS(ns, "svg"), use = document.createElementNS(ns, "use");
  use.setAttribute("href", "#mark"); svg.append(use); svg.setAttribute("width", "16"); svg.setAttribute("height", "16");
  return svg;
}

// Lý do dài (LLM không giới hạn độ dài): kẹp 5 dòng + nút Xem thêm; giữ xuống dòng của văn bản
const REASON_CLAMP = 320;
function reason(text, cls = "why") {
  const p = el("p", { class: text && text.length > REASON_CLAMP ? `${cls} clamp` : cls }, text);
  if (!p.classList.contains("clamp")) return p;
  const btn = el("button", { type: "button", class: "more", "aria-expanded": "false", onclick: () => {
    const open = p.classList.toggle("clamp") === false;
    btn.textContent = open ? "Thu gọn" : "Xem thêm"; btn.setAttribute("aria-expanded", String(open));
  } }, "Xem thêm");
  return el("div", {}, p, btn);
}

function lane(name, cls, v, sub, total) {
  const width = Math.max(0, Math.min(100, Math.round((v ?? 0) * 100)));
  return el("div", { class: total ? "lane total" : "lane" },
    total ? el("span", { class: "avatar both", "aria-hidden": "true" }, markIcon()) : el("span", { class: `avatar ${cls}` }, initial(name)),
    el("div", {}, el("div", { class: "who" }, el("span", { class: "nm", title: name }, name), sub ? el("span", { class: "km" }, ` · ${sub}`) : null),
      el("div", { class: "bar" }, el("i", { style: `width:${width}%` }))),
    el("span", { class: "val" }, v == null ? "—" : String(width)));
}

function placeCard(it, res, user) {
  const ps = people(it);
  // Nút bật / tắt: bấm để chọn quán, bấm lần nữa để bỏ chọn (trả hồ sơ về như trước khi chọn)
  const choose = res.request_id && user ? el("button", { type: "button", class: "btn small choose", "aria-pressed": "false", onclick: async (e) => {
    const b = e.currentTarget, chosen = b.getAttribute("aria-pressed") !== "true";
    b.disabled = true;
    try {
      await api("/api/choose", { method: "POST", body: JSON.stringify({ request_id: res.request_id, place_id: it.restaurant_id, user_id: user, chosen }) });
      b.setAttribute("aria-pressed", String(chosen)); b.classList.toggle("done", chosen);
      b.textContent = chosen ? "Đã chọn · bỏ chọn" : "Chọn quán này";
    } catch (err) { b.textContent = chosen ? "Chưa chọn được, bấm lại" : "Chưa bỏ chọn được, bấm lại"; }
    finally { b.disabled = false; }
  } }, "Chọn quán này") : null;
  return el("article", { class: "place" },
    el("span", { class: "rank" }, String(it.rank)),
    el("div", {},
      el("h3", {}, it.name),
      el("p", { class: "meta" }, [it.district, price(it.price_min, it.price_max), it.opening_hours && `mở ${fmtHours(it.opening_hours)}`].filter(Boolean).join(" · ")),
      el("p", { class: "meta" }, it.address),
      mediaPhotos(it.media, it.name),
      reason(it.explanation),
      it.tags?.length ? el("div", { class: "tags" }, it.tags.map((t) => el("span", { class: t === "ồn ào" ? "tag neg" : "tag" }, t))) : null,
      mediaInfo(it.media)),
    el("div", { class: "side-col" },
      el("div", { class: "balance", role: "group", "aria-label": "Mức hợp với từng người, thang 0–100" },
        ps.map((p) => lane(p.name, p.cls, p.fit, p.km != null ? km(p.km) : null)),
        lane("Cả hai", null, it.group_score, null, true)),
      el("p", { class: "verdict" }, it.tradeoff_label),
      choose));
}

function renderSide(res) {
  const p = res.parsed || {};
  const rows = [["Khu vực", p.districts?.length ? p.districts.join(", ") : "mọi quận"],
    ["Ngân sách", p.budget_per_person ? price(p.budget_per_person, p.budget_per_person) : "không giới hạn"],
    ["Giờ hẹn", res.at_time || "—"], ["Tìm theo", p.semantic_query || "—"]];
  if (res.common_interests) rows.push(["Sở thích chung", res.common_interests.length ? res.common_interests.join(", ") : "chưa có"]);
  if (res.quota) rows.push(["Lượt AI hôm nay", quotaText(res.quota)]);
  show($("#r-side"),
    el("div", { class: "side-block" }, el("h2", {}, "Hệ thống hiểu là"),
      el("dl", { class: "kv" }, rows.map(([k, v]) => el("div", {}, el("dt", {}, k), el("dd", {}, v))))),
    (res.notes || []).length ? el("div", { class: "side-block" }, el("h2", {}, "Lưu ý"), res.notes.map((n) => el("p", { class: "side-note" }, n))) : null,
    res.status === "quota_exceeded" ? el("p", { class: "notice" }, res.message) : null);
}

// ===== Lập plan: cả buổi tối trên một trục giờ =====
$("#f-plan").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const form = ev.target, box = $("#r-plan"), btn = $("button[type=submit]", form);
  const body = formBody(form, { ...(form.start.value ? { start: form.start.value } : {}), walk: form.walk.checked });
  btn.disabled = true;
  show(box, el("div", { class: "panel plan-card" }, skeleton("Đang xếp các chặng và kiểm tra giờ mở cửa, quãng đường, ngân sách…")));
  try {
    const p = await api("/api/plan", { method: "POST", body: JSON.stringify(body) });
    if (p.status !== "success") { show(box, el("div", { class: "panel plan-card" }, emptyBox(p, (p.issues || []).join("; ") || "Không lập được plan."))); return; }
    show(box, planCard(p));
  } catch (e) { show(box, el("div", { class: "panel plan-card" }, errorBox(e, () => form.requestSubmit()))); } finally { btn.disabled = false; }
});

function evening(stops) {
  const t0 = toMin(stops[0].start);
  const at = (t) => { let m = toMin(t) - t0; return m < 0 ? m + 1440 : m; };
  const total = at(stops.at(-1).end) || 1;
  const segs = [], marks = [];
  stops.forEach((s, i) => {
    if (i > 0 && at(s.start) > at(stops[i - 1].end)) segs.push(el("div", { class: "seg move", style: `width:${(at(s.start) - at(stops[i - 1].end)) / total * 100}%`, title: `Di chuyển ${s.travel_min} phút` }));
    const w = (at(s.end) - at(s.start)) / total * 100;
    segs.push(el("div", { class: "seg stop", style: `width:${w}%`, title: `${s.label} ${s.start}–${s.end}` }, w >= 16 ? s.label : ""));  // chặng quá ngắn: chỉ hiện khi rê chuột
    marks.push([at(s.start) / total * 100, s.start]);
  });
  marks.push([100, stops.at(-1).end]);
  // bỏ nhãn giờ nằm quá sát nhãn kế tiếp (luôn giữ giờ đầu và giờ cuối) để không chồng chữ
  const ticks = marks.filter(([pos], i) => i === 0 || i === marks.length - 1 || (pos - marks[i - 1][0] >= 18 && marks.at(-1)[0] - pos >= 18))
    .map(([pos, t]) => el("span", { style: `left:${pos}%` }, t));
  return el("div", { class: "evening", role: "img", "aria-label": `Từ ${stops[0].start} đến ${stops.at(-1).end}: ${stops.map((s) => `${s.label} ${s.start}–${s.end}`).join(", ")}` },
    el("div", { class: "track" }, segs), el("div", { class: "ticks" }, ticks));
}

function planCard(p) {
  const costs = p.stops.map((s) => (s.est_cost == null ? null : Math.round(s.est_cost)));   // để nguyên đồng: tổng khớp với cảnh báo của server
  const known = costs.filter((c) => c != null);
  const total = known.reduce((a, b) => a + b, 0);
  const stops = p.stops.map((s, i) => [
    i > 0 ? el("p", { class: "hop" }, `Đi khoảng ${s.travel_min} phút${s.hop_km_from_prev != null ? `, ${km(s.hop_km_from_prev)}` : " (ước tính)"}`) : null,
    el("article", { class: "stop" },
      el("div", { class: "when" }, `${s.start}–${s.end}`, el("span", {}, s.label)),
      el("div", {}, el("h3", {}, s.name),
        el("p", { class: "meta" }, [s.district, s.opening_hours ? `mở ${fmtHours(s.opening_hours)}` : s.kind === "walk" ? "không gian mở" : null].filter(Boolean).join(" · ")),
        el("p", { class: "meta" }, s.address), mediaPhotos(s.media, s.name), reason(s.note), mediaInfo(s.media)),
      s.kind === "walk"   // chặng đi dạo: chỗ công cộng, không tốn tiền
        ? el("div", { class: "cost" }, "Miễn phí", el("span", {}, "đi dạo, không phải quán"))
        : el("div", { class: "cost" }, costs[i] == null ? "—" : vnd(costs[i]),
            el("span", {}, costs[i] == null ? "chưa rõ giá" : `giá ${s.price.replace(" - ", "–")} một người`)))]);
  const over = p.budget && total > p.budget;
  const money = known.length ? el("div", { class: "money" },
    el("div", {}, el("p", { class: "help" }, "Ước tính một người"), el("p", { class: "big" }, vnd(total)),
      known.length < costs.length ? el("p", { class: "help" }, `Chưa tính ${costs.length - known.length} chặng thiếu giá`) : null),
    el("p", { class: "of" }, p.budget ? (over ? `vượt ${vnd(total - p.budget)} so với ngân sách ${vnd(p.budget)}` : `còn ${vnd(p.budget - total)} trong ngân sách ${vnd(p.budget)}`) : "Chưa đặt ngân sách"),
    p.budget ? el("div", { class: over ? "budget-track over" : "budget-track" }, el("i", { style: `width:${Math.min(100, total / p.budget * 100)}%` })) : null) : null;
  const checks = p.issues?.length ? p.issues.map((i) => el("span", { class: "pill bad" }, i))
    : ["Đúng giờ mở cửa", p.stops.length > 1 ? "Các chặng gần nhau" : null, p.budget && known.length ? "Trong ngân sách" : null]
        .filter(Boolean).map((t) => el("span", { class: "pill ok" }, t));
  return el("div", { class: "panel plan-card" },
    el("div", { class: "plan-head" }, el("h2", {}, p.title), el("span", { class: "help" }, p.quota ? `Lượt AI hôm nay ${quotaText(p.quota)}` : "")),
    evening(p.stops),
    el("div", { class: "stops" }, stops.flat()),
    money,
    el("div", { class: "checks-line" }, checks),
    (p.notes || []).map((n) => el("p", { class: "side-note" }, n)));
}

// ===== Hồ sơ =====
function renderInterestToggles(selected = []) {
  const groups = {};
  INTERESTS.forEach((i) => (groups[i.group] ||= []).push(i));
  show($("#p-interests"), Object.entries(groups).map(([g, items]) => el("fieldset", { class: "interest-group", style: "border:0;margin:0;padding:0" },
    el("h3", {}, g),
    el("div", { class: "toggles" }, items.map((i) => el("label", {},
      el("input", { type: "checkbox", name: "interest", value: i.id, checked: selected.includes(i.id) || false }), i.label))))));
  countPicked();
}
function countPicked() {
  const n = $$("input[name=interest]:checked").length;
  $("#p-picked").textContent = n ? `Đã chọn ${n} sở thích` : "Chưa chọn sở thích nào";
}
$("#p-interests").addEventListener("change", countPicked);
$("#p-consent").addEventListener("change", (e) => { if (e.target.checked) { $("#p-consent-err").hidden = true; e.target.removeAttribute("aria-invalid"); } });

$("#p-pick").addEventListener("change", async (ev) => {
  const form = $("#f-profile"), id = ev.target.value;
  form.reset(); show($("#r-profile"));
  if (!id) { form.user_id.readOnly = false; renderInterestToggles(); return; }
  try { fillProfile(await api(`/api/profiles/${encodeURIComponent(id)}`)); } catch (e) { show($("#r-profile"), errorBox(e)); }
});

$("#f-profile").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const form = ev.target, id = form.user_id.value.trim();
  const err = $("#p-consent-err");
  err.hidden = form.consent.checked;
  form.consent.setAttribute("aria-invalid", String(!form.consent.checked));
  if (!form.consent.checked) { form.consent.focus(); return; }   // lỗi hiện ngay cạnh công tắc, không gọi API
  const body = { consent: form.consent.checked, display_name: form.display_name.value.trim() || null, plan: form.plan.value,
                 interests: $$("input[name=interest]:checked", form).map((c) => c.value),
                 share_interests_with_partner: form.share.checked };
  try {
    const p = await api(`/api/profiles/${encodeURIComponent(id)}`, { method: "PUT", body: JSON.stringify(body) });
    if (ME && p.user_id === ME.user_id) { ME.has_profile = true; MY_PROFILE = p; renderMe(); renderIdle(); $("#p-sub").textContent = "Sở thích giúp AI chọn quán hợp cả hai."; }
    await refreshProfiles(p.user_id);
    form.user_id.readOnly = true;
    show($("#r-profile"), el("p", { class: "ok-box" }, `Đã lưu hồ sơ ${p.display_name} với ${p.interests.length} sở thích.`));
  } catch (e) { show($("#r-profile"), errorBox(e)); }
});

$("#p-delete").addEventListener("click", async () => {
  const id = $("#f-profile").user_id.value.trim();
  if (!id || !confirm(`Xóa vĩnh viễn hồ sơ "${id}"?`)) return;
  try {
    await api(`/api/profiles/${encodeURIComponent(id)}`, { method: "DELETE" });
    if (ME && id === ME.user_id) { ME.has_profile = false; MY_PROFILE = null; renderMe(); renderIdle(); }
    $("#f-profile").reset(); renderInterestToggles();
    await refreshProfiles();
    if (AUTH && ME.role !== "admin") await loadOwnProfile(); else $("#f-profile").user_id.readOnly = false;
    show($("#r-profile"), el("p", { class: "ok-box" }, `Đã xóa hồ sơ ${id}.`));
  } catch (e) { show($("#r-profile"), errorBox(e)); }
});

$("#p-delete-account").addEventListener("click", async () => {
  if (!confirm(`Xóa vĩnh viễn tài khoản "${ME.user_id}" cùng hồ sơ sở thích? Không khôi phục được.`)) return;
  try { await api("/api/auth/me", { method: "DELETE" }); logout("Đã xóa tài khoản và dữ liệu của bạn."); }
  catch (e) { show($("#r-profile"), errorBox(e)); }
});

// ===== Thống kê AI =====
const STATUS = { success: ["Có gợi ý", "var(--paper)"], no_result: ["Không có quán hợp", "#8f8f8f"],
  quota_exceeded: ["Hết lượt trong ngày", "#5c5c5c"], no_profile: ["Chưa có hồ sơ", "#3d3d3d"], error: ["Lỗi hệ thống", "var(--negative)"] };
$("#s-refresh").addEventListener("click", loadStats);
async function loadStats() {
  const box = $("#r-stats");
  show(box, el("p", { class: "wait", style: "margin-top:32px" }, "Đang tải…"));
  try {
    const m = await api("/api/metrics");
    $("#st-sub").textContent = `Cập nhật lúc ${new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })} · mọi yêu cầu có hồ sơ từ khi bắt đầu ghi nhật ký.`;
    if (!m.n_requests) { show(box, el("div", { class: "empty", style: "margin-top:32px" }, "Chưa có yêu cầu AI nào. Số liệu xuất hiện sau lần hỏi gợi ý đầu tiên.")); return; }
    const sec = (v) => (v == null ? "—" : `${(v / 1000).toLocaleString("vi-VN", { maximumFractionDigits: 1 })} giây`);
    const kpi = (label, value, note, lead) => el("div", { class: lead ? "kpi lead" : "kpi" }, el("dt", {}, label), el("dd", {}, value), note ? el("small", {}, note) : null);
    const statuses = Object.entries(m.by_status).sort((a, b) => b[1] - a[1]);
    const n = statuses.reduce((a, [, v]) => a + v, 0);
    const kv = (rows) => el("dl", { class: "kv" }, rows.map(([k, v]) => el("div", {}, el("dt", {}, k), el("dd", {}, v))));
    show(box,
      el("dl", { class: "kpis" },
        kpi("Tỷ lệ chọn quán AI gợi ý", pct(m.choose_rate), "trên các lần gợi ý thành công", true),
        kpi("Yêu cầu", m.n_requests.toLocaleString("vi-VN"), "gợi ý và lập plan"),
        kpi("Dùng được AI", pct(m.llm_used_rate), "còn lại xếp theo điểm"),
        kpi("Độ trễ trung bình", sec(m.latency_ms_avg), `95% dưới ${sec(m.latency_ms_p95)}`)),
      el("div", { class: "grid even" },
        el("div", { class: "panel span-6" }, el("div", { class: "panel-head" }, el("h2", {}, "AI có chọn đúng quán thật không"), el("span", { class: "end" }, "code kiểm tra mọi lựa chọn")),
          kv([["Mã quán bịa bị chặn", (m.invalid_id_blocked ?? 0).toLocaleString("vi-VN")],
              ["Lý do bịa bị thay", (m.bad_reason_replaced ?? 0).toLocaleString("vi-VN")],
              ["Phải bù bằng thứ tự điểm", pct(m.fallback_rate)],
              ["Trùng với top của công thức", pct(m.llm_vs_formula_overlap)]])),
        el("div", { class: "panel span-6" }, el("div", { class: "panel-head" }, el("h2", {}, "Kết quả các yêu cầu"), el("span", { class: "count" }, n.toLocaleString("vi-VN"))),
          el("div", { class: "stack", role: "img", "aria-label": statuses.map(([k, v]) => `${(STATUS[k] || [k])[0]} ${v}`).join(", ") },
            statuses.map(([k, v]) => el("i", { style: `width:${v / n * 100}%;background:${(STATUS[k] || [k, "#8c8c88"])[1]}` }))),
          el("div", { class: "legend" }, statuses.map(([k, v]) => el("div", {},
            el("i", { style: `background:${(STATUS[k] || [k, "#8c8c88"])[1]}` }), el("span", {}, (STATUS[k] || [k])[0]),
            el("span", { class: "n" }, v.toLocaleString("vi-VN")), el("span", { class: "p" }, `${Math.round(v / n * 100)}%`)))),
          kv([["Token trung bình mỗi lần AI chọn", m.tokens_avg == null ? "—" : m.tokens_avg.toLocaleString("vi-VN")]]))));
  } catch (e) { show(box, el("div", { style: "margin-top:32px" }, errorBox(e, loadStats))); }
}

window.addEventListener("popstate", () => { if (!$("#app").hidden) go(location.hash.slice(1) || "suggest", false, true); });
init();
