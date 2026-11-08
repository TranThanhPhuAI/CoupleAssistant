// Giao diện Tối / Sáng (công tắc "Tối | Sáng" ở thanh điều hướng, thanh trên điện thoại và màn đăng nhập).
// Giá trị ban đầu đã đặt bởi đoạn script trong <head> (không nháy khi tải trang).
// Bấm: đổi + lưu lựa chọn; chưa chọn bao giờ thì đi theo cài đặt sáng / tối của máy. Tab Cộng đồng đổi theo.
(() => {
  const KEY = "ca_theme";
  const root = document.documentElement;
  const saved = () => { try { return localStorage.getItem(KEY); } catch { return null; } };

  function apply(theme, save) {
    root.dataset.theme = theme;
    document.querySelector('meta[name="theme-color"]').content = theme === "light" ? "#ffffff" : "#000000";
    document.querySelectorAll("[data-theme-set]").forEach((b) => {
      const on = b.dataset.themeSet === theme;
      b.setAttribute("aria-checked", String(on)); b.classList.toggle("on", on); b.tabIndex = on ? 0 : -1;
    });
    if (save) { try { localStorage.setItem(KEY, theme); } catch {} }
    document.getElementById("community-frame")?.contentWindow?.postMessage({ type: "lovespot-theme", theme }, location.origin);
  }

  document.querySelectorAll("[data-theme-set]").forEach((b) => {
    b.addEventListener("click", () => apply(b.dataset.themeSet, true));
    b.addEventListener("keydown", (e) => {   // phím mũi tên chuyển giữa Tối / Sáng (nhóm radio)
      if (!["ArrowLeft", "ArrowRight"].includes(e.key)) return;
      e.preventDefault();
      const next = b.dataset.themeSet === "dark" ? "light" : "dark";
      apply(next, true);
      b.parentElement.querySelector(`[data-theme-set="${next}"]`).focus();
    });
  });
  matchMedia("(prefers-color-scheme: light)").addEventListener("change", (e) => { if (!saved()) apply(e.matches ? "light" : "dark", false); });
  document.getElementById("community-frame")?.addEventListener("load", () => apply(root.dataset.theme, false));
  apply(root.dataset.theme || "dark", false);
})();
