(function () {
    "use strict";

    var sidebar = document.getElementById("sidebar");
    var boton = document.getElementById("menuToggle");
    var overlay = document.getElementById("overlayMenu");

    /* ---------- menú móvil ---------- */

    function cerrarMenu() {
        if (sidebar) sidebar.classList.remove("active");
        if (boton) boton.setAttribute("aria-expanded", "false");
    }

    if (boton && sidebar) {
        boton.setAttribute("aria-expanded", "false");
        boton.addEventListener("click", function () {
            var abierto = sidebar.classList.toggle("active");
            boton.setAttribute("aria-expanded", abierto ? "true" : "false");
        });
    }
    if (overlay) overlay.addEventListener("click", cerrarMenu);
    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") cerrarMenu();
    });

    /* ---------- opción activa del menú ---------- */
    /* Gana el enlace cuya ruta coincide con la mayor parte de la URL actual. */

    if (sidebar) {
        var ruta = window.location.pathname.replace(/\/+$/, "") || "/";
        var mejor = null;
        var mejorLargo = -1;

        sidebar.querySelectorAll(".menu-item, .submenu-item").forEach(function (a) {
            if (a.classList.contains("salir")) return;
            var destino = (a.getAttribute("href") || "").split("?")[0].replace(/\/+$/, "") || "/";
            var coincide = destino === "/" ? ruta === "/" : (ruta === destino || ruta.indexOf(destino + "/") === 0);
            if (coincide && destino.length > mejorLargo) {
                mejor = a;
                mejorLargo = destino.length;
            }
        });

        if (mejor) {
            mejor.classList.add("active");
            mejor.setAttribute("aria-current", "page");
            var seccion = mejor.closest(".menu-section");
            if (seccion) seccion.classList.add("abierta");
        }

        /* al navegar en móvil, el menú se cierra solo */
        sidebar.addEventListener("click", function (e) {
            if (e.target.closest("a")) cerrarMenu();
        });
    }

    /* ---------- título de la barra superior ---------- */

    var titulo = document.getElementById("tituloPagina");
    if (titulo && document.title) {
        var texto = document.title.split(" - ")[0].trim();
        if (texto) titulo.textContent = texto;
    }
})();
