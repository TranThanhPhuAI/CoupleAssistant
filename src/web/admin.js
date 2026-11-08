// Màn "Phân quyền" (chỉ quản trị viên): vai trò, gói AI, đặt lại mật khẩu, xóa tài khoản.
// Dùng chung tiện ích của app.js ($, el, show, api, errBox, ME). Mọi nội dung chèn bằng textContent.
(() => {
  const box = () => $("#r-admin");
  const day = (ts) => (ts ? new Date(ts * 1000).toLocaleDateString("vi-VN") : "—");
  const flash = (row, text, bad = false) => {
    const m = $(".ad-msg", row); m.textContent = text; m.className = bad ? "ad-msg bad" : "ad-msg";
    clearTimeout(m._t); m._t = setTimeout(() => { m.textContent = ""; }, 4000);
  };

  async function patch(row, a, body) {
    try { await api(`/api/admin/accounts/${encodeURIComponent(a.user_id)}`, { method: "PATCH", body: JSON.stringify(body) }); flash(row, "Đã lưu"); return true; }
    catch (e) { flash(row, e.message, true); return false; }
  }

  function row(a, plans) {
    const r = el("div", { class: "ad-row", role: "row" });
    const roleSel = el("select", { "aria-label": `Vai trò của ${a.user_id}` },
      el("option", { value: "member" }, "Thành viên"), el("option", { value: "admin" }, "Quản trị viên"));
    roleSel.value = a.role;
    roleSel.onchange = async () => {
      const to = roleSel.value;
      if (a.is_me && to === "member" && !confirm("Bỏ quyền quản trị của chính bạn? Bạn sẽ không vào lại được trang này.")) { roleSel.value = a.role; return; }
      if (await patch(r, a, { role: to })) { a.role = to; if (a.is_me && to === "member") location.reload(); else render(); }
      else roleSel.value = a.role;
    };
    const planSel = el("select", { "aria-label": `Gói AI của ${a.user_id}`, disabled: !a.has_profile || a.role === "admin",
      title: !a.has_profile ? "Chưa có hồ sơ sở thích" : a.role === "admin" ? "Quản trị viên không giới hạn lượt" : null },
      Object.entries(plans).map(([k, n]) => el("option", { value: k }, `${k} · ${n} lượt/ngày`)));
    planSel.value = a.plan;
    planSel.onchange = async () => { if (await patch(r, a, { plan: planSel.value })) { a.plan = planSel.value; render(); } else planSel.value = a.plan; };

    const pw = el("input", { type: "password", minlength: "8", maxlength: "128", autocomplete: "new-password", placeholder: "Mật khẩu mới (≥ 8 ký tự)", "aria-label": `Mật khẩu mới cho ${a.user_id}` });
    const pwForm = el("form", { class: "ad-pw", hidden: true, onsubmit: async (e) => {
      e.preventDefault();
      if (!pw.reportValidity()) return;
      try { await api(`/api/admin/accounts/${encodeURIComponent(a.user_id)}/password`, { method: "POST", body: JSON.stringify({ password: pw.value }) });
            pw.value = ""; pwForm.hidden = true; flash(r, "Đã đặt mật khẩu mới, tài khoản được gỡ khóa"); }
      catch (err) { flash(r, err.message, true); }
    } }, pw, el("button", { type: "submit", class: "btn small primary" }, "Lưu"));

    const del = a.is_me ? null : el("button", { type: "button", class: "btn small danger", onclick: async () => {
      if (!confirm(`Xóa vĩnh viễn tài khoản "${a.user_id}", hồ sơ sở thích và hồ sơ Cộng đồng của người này?`)) return;
      try { await api(`/api/admin/accounts/${encodeURIComponent(a.user_id)}`, { method: "DELETE" }); window.loadAdmin(); }
      catch (e) { flash(r, e.message, true); }
    } }, "Xóa");

    const used = a.limit == null ? `${a.used_today} · không giới hạn` : `${a.used_today} / ${a.limit}`;
    show(r,
      el("div", { class: "ad-who", role: "cell" }, el("b", {}, a.user_id), a.is_me ? el("span", { class: "tag" }, "Bạn") : null,
        el("small", {}, a.display_name || (a.has_profile ? "" : "Chưa có hồ sơ sở thích"))),
      el("div", { role: "cell", "data-label": "Vai trò" }, roleSel),
      el("div", { role: "cell", "data-label": "Gói AI" }, planSel),
      el("div", { role: "cell", "data-label": "Lượt AI hôm nay", class: "num" }, used),
      el("div", { role: "cell", "data-label": "Ngày tạo", class: "num" }, day(a.created_at)),
      el("div", { role: "cell", class: "ad-acts" },
        el("button", { type: "button", class: "btn small ghost", onclick: () => { pwForm.hidden = !pwForm.hidden; if (!pwForm.hidden) pw.focus(); } }, "Đặt mật khẩu"), del),
      pwForm, el("p", { class: "ad-msg", role: "status" }));
    return r;
  }

  let data = null;
  function render() {
    const admins = data.accounts.filter((a) => a.role === "admin").length;
    show(box(),
      el("p", { class: "ad-sum" }, `${data.accounts.length} tài khoản · ${admins} quản trị viên`),
      el("div", { class: "ad-table", role: "table", "aria-label": "Danh sách tài khoản" },
        el("div", { class: "ad-row ad-head", role: "row" }, ["Tài khoản", "Vai trò", "Gói AI", "Lượt AI hôm nay", "Ngày tạo", ""].map((h) => el("div", { role: "columnheader" }, h))),
        data.accounts.map((a) => row(a, data.plans))),
      el("p", { class: "help", style: "margin-top:16px" },
        "Quản trị viên: xem Thống kê AI, sửa mọi hồ sơ, dùng AI không giới hạn lượt. Luôn phải còn ít nhất một quản trị viên."));
  }

  window.loadAdmin = async function loadAdmin() {
    show(box(), el("p", { class: "wait", style: "margin-top:32px" }, "Đang tải…"));
    findPlaces();
    try { data = await api("/api/admin/accounts"); render(); }
    catch (e) { show(box(), el("div", { style: "margin-top:32px" }, errBox(e, loadAdmin))); }
  };
  $("#ad-refresh").addEventListener("click", () => window.loadAdmin());

  // ===== Ảnh & menu quán: hiện trên thẻ gợi ý và chặng plan =====
  const pid = (p) => encodeURIComponent(p.id);

  // Thu nhỏ ảnh ngay trên máy (cạnh dài ≤ 1600px, JPEG) trước khi tải lên
  async function shrink(file) {
    const bmp = await createImageBitmap(file);
    const s = Math.min(1, 1600 / Math.max(bmp.width, bmp.height));
    const c = el("canvas", { width: Math.round(bmp.width * s), height: Math.round(bmp.height * s) });
    c.getContext("2d").drawImage(bmp, 0, 0, c.width, c.height);
    return c.toDataURL("image/jpeg", 0.85);
  }

  // Mỗi dòng một món: "Bạc xỉu - 45000", "Bạc xỉu 45k", hoặc chỉ tên món (chưa rõ giá)
  function parseMenu(text) {
    return text.split("\n").map((l) => l.trim()).filter(Boolean).map((l) => {
      const m = l.match(/^(.*?)[\s\-–:·]+(\d[\d.,]*)\s*(k|nghìn|ngàn|đ|d|vnd)?$/i);
      if (!m || !m[1].trim()) return { name: l.slice(0, 80), price: null };
      const n = Number(m[2].replace(/[.,]/g, ""));
      return { name: m[1].trim().slice(0, 80), price: /^(k|nghìn|ngàn)$/i.test(m[3] || "") ? n * 1000 : n };
    });
  }
  const menuText = (items) => items.map((i) => (i.price == null ? i.name : `${i.name} - ${i.price}`)).join("\n");

  async function findPlaces(q = $("#pm-q").value.trim()) {
    const list = $("#pm-list");
    show(list, el("p", { class: "wait" }, "Đang tìm…"));
    try {
      const rows = await api(`/api/admin/places?q=${encodeURIComponent(q)}`);
      show(list, rows.length ? el("div", { class: "pm-results" }, rows.map((p) =>
        el("button", { type: "button", class: "pm-item", onclick: () => editPlace(p) },
          el("b", {}, p.name), el("small", {}, [p.district, `${p.photos} ảnh`, `${p.menu} món`].filter(Boolean).join(" · ")))))
        : el("p", { class: "help" }, q ? "Không tìm thấy quán nào." : "Chưa quán nào có ảnh hoặc menu. Tìm một quán để thêm."));
    } catch (e) { show(list, errBox(e, () => findPlaces(q))); }
  }
  $("#pm-find").addEventListener("submit", (e) => { e.preventDefault(); findPlaces(); });

  async function editPlace(p, scroll = true, note = null) {
    const ed = $("#pm-editor");
    if (scroll) show(ed, el("p", { class: "wait" }, "Đang tải…"));
    let m;
    try { m = await api(`/api/places/${pid(p)}/media`); } catch (e) { show(ed, errBox(e, () => editPlace(p))); return; }
    const msg = el("p", { class: "ad-msg", role: "status" });
    const say = (t, bad = false) => { msg.textContent = t; msg.className = bad ? "ad-msg bad" : "ad-msg"; };
    const file = el("input", { type: "file", accept: "image/jpeg,image/png,image/webp", multiple: true, "aria-label": "Chọn ảnh quán" });
    file.onchange = async () => {
      let err = null, n = 0;
      for (const f of file.files) {
        say(`Đang tải ${f.name}…`);
        try { await api(`/api/admin/places/${pid(p)}/photos`, { method: "POST", body: JSON.stringify({ data: await shrink(f) }) }); n++; }
        catch (e) { err = `${f.name}: ${e.message}`; break; }
      }
      await editPlace(p, false, err ? [err, true] : [`Đã thêm ${n} ảnh`]); findPlaces();
    };
    const photos = el("div", { class: "pm-photos" }, m.photos.map((u) => el("figure", {},
      el("img", { src: u, alt: `Ảnh của ${p.name}`, loading: "lazy" }),
      el("button", { type: "button", class: "btn small danger", onclick: async () => {
        if (!confirm("Xóa ảnh này?")) return;
        try { await api(`/api/admin/places/${pid(p)}/photos/${u.split("/").pop()}`, { method: "DELETE" }); await editPlace(p, false, ["Đã xóa ảnh"]); findPlaces(); }
        catch (e) { say(e.message, true); }
      } }, "Xóa"))),
      m.photos.length < 8 ? el("label", { class: "pm-add" }, file, "+ Thêm ảnh") : null);
    const menu = el("textarea", { rows: "8", "aria-label": "Menu, mỗi dòng một món", placeholder: "Mỗi dòng một món, ví dụ:\nBạc xỉu - 45000\nTrà đào cam sả 55k\nBánh flan" });
    menu.value = menuText(m.menu);
    const save = el("form", { class: "pm-menu", onsubmit: async (e) => {
      e.preventDefault();
      const items = parseMenu(menu.value);
      if (items.length > 40) { say("Tối đa 40 món", true); return; }
      try { const r = await api(`/api/admin/places/${pid(p)}/menu`, { method: "PUT", body: JSON.stringify({ items }) });
            menu.value = menuText(r.menu); say(`Đã lưu ${r.menu.length} món`); findPlaces(); }
      catch (err) { say(err.message, true); }
    } }, el("p", { class: "eyebrow" }, "Menu"), menu, el("button", { type: "submit", class: "btn small primary" }, "Lưu menu"));
    show(ed, el("div", { class: "pm-edit" },
      el("h3", {}, p.name), el("p", { class: "help" }, [p.district, p.address].filter(Boolean).join(" · ")),
      el("p", { class: "eyebrow" }, `Ảnh (${m.photos.length}/8)`), photos,
      m.foody_photos.length || m.community_photos.length ? el("p", { class: "help" }, `Thẻ quán còn hiện ${
        [m.foody_photos.length && `${m.foody_photos.length} ảnh từ Foody`, m.community_photos.length && `${m.community_photos.length} ảnh người dùng ở Cộng đồng`].filter(Boolean).join(" và ")}.`) : null,
      save, msg,
      m.foody ? el("p", { class: "help" }, "Tham khảo: ", el("a", { href: m.foody, target: "_blank", rel: "noopener noreferrer" }, "trang quán trên Foody ↗"),
        ". Chỉ đăng ảnh bạn tự chụp hoặc được quán cho phép.") : null));
    if (note) say(...note);
    if (scroll) ed.scrollIntoView({ behavior: "smooth", block: "start" });
  }
})();
