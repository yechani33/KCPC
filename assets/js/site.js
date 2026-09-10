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

  function closeAll(except) {
    items.forEach(function (item) {
      if (item === except) return;
      item.classList.remove("nav__item--open");
      var t = item.querySelector(".nav__link");
      if (t) t.setAttribute("aria-expanded", "false");
    });
  }

  items.forEach(function (item) {
    var trigger = item.querySelector(".nav__link");
    if (!trigger) return;

    trigger.addEventListener("click", function (e) {
      e.preventDefault();
      var open = item.classList.contains("nav__item--open");
      closeAll(item);
      item.classList.toggle("nav__item--open", !open);
      trigger.setAttribute("aria-expanded", String(!open));
    });

    // Pointer users get hover, which feels faster than click-to-open.
    item.addEventListener("mouseenter", function () {
      if (window.matchMedia("(hover: hover)").matches) {
        closeAll(item);
        item.classList.add("nav__item--open");
        trigger.setAttribute("aria-expanded", "true");
      }
    });

    item.addEventListener("mouseleave", function () {
      if (window.matchMedia("(hover: hover)").matches) {
        item.classList.remove("nav__item--open");
        trigger.setAttribute("aria-expanded", "false");
      }
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
