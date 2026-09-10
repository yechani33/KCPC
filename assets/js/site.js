/* 신시내티 중앙장로교회 — navigation behaviour
   Small and dependency-free. Everything degrades to plain links without JS. */

(function () {
  "use strict";

  /* ---------- mobile drawer ---------- */

  var burger = document.querySelector(".burger");
  var drawer = document.getElementById("drawer");

  if (burger && drawer) {
    burger.addEventListener("click", function () {
      var open = drawer.getAttribute("data-open") === "true";
      drawer.setAttribute("data-open", String(!open));
      burger.setAttribute("aria-expanded", String(!open));
    });
  }

  /* ---------- desktop dropdowns ---------- */

  var items = Array.prototype.slice.call(
    document.querySelectorAll(".nav__item--has-panel")
  );

  var hover = window.matchMedia("(hover: hover)");
  var closeTimer = null;

  function setOpen(item, open) {
    item.classList.toggle("nav__item--open", open);
    var t = item.querySelector(".nav__link");
    if (t) t.setAttribute("aria-expanded", String(open));
  }

  function closeAll(except) {
    window.clearTimeout(closeTimer);
    items.forEach(function (item) {
      if (item !== except) setOpen(item, false);
    });
  }

  items.forEach(function (item) {
    var trigger = item.querySelector(".nav__link");
    if (!trigger) return;

    trigger.addEventListener("click", function (e) {
      e.preventDefault();
      var open = item.classList.contains("nav__item--open");
      closeAll(item);
      // With a mouse the panel is already open from hover, so a click should
      // leave it open rather than toggle it shut under the pointer. Keyboard
      // activation (detail === 0) still toggles.
      setOpen(item, hover.matches && e.detail !== 0 ? true : !open);
    });

    // Pointer users get hover, which feels faster than click-to-open.
    item.addEventListener("mouseenter", function () {
      if (!hover.matches) return;
      closeAll(item);
      setOpen(item, true);
    });

    item.addEventListener("mouseleave", function () {
      if (!hover.matches) return;
      // Brief grace period so a wobbly pointer doesn't dismiss the panel.
      window.clearTimeout(closeTimer);
      closeTimer = window.setTimeout(function () { setOpen(item, false); }, 180);
    });
  });

  document.addEventListener("click", function (e) {
    if (!e.target.closest(".nav__item--has-panel")) closeAll(null);
  });

  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    closeAll(null);
    if (drawer && drawer.getAttribute("data-open") === "true") {
      drawer.setAttribute("data-open", "false");
      burger.setAttribute("aria-expanded", "false");
      burger.focus();
    }
  });
})();
