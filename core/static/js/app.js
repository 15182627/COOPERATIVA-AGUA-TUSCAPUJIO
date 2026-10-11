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

    /* ---------- modal de cobranza ---------- */
    var modalCobranza = document.getElementById("modalCobranza");
    if (modalCobranza) {
        var modalLista = document.getElementById("modalCobranzaLista");
        var modalTotal = document.getElementById("modalCobranzaTotal");
        var modalCerrar = document.getElementById("modalCobranzaCerrar");
        var modalCancelar = document.getElementById("modalCobranzaCancelar");

        function cerrarCobranza() {
            modalCobranza.classList.remove("activo");
            modalCobranza.setAttribute("aria-hidden", "true");
        }

        function abrirCobranza(button) {
            if (!button) return;

            var socioId = button.dataset.socioId || "";
            var filas = Array.from(document.querySelectorAll("[data-socio-id='" + socioId + "']"));
            var items = filas
                .filter(function (fila) {
                    return fila.dataset.estado !== "PAGADA" &&
                        fila.dataset.total &&
                        Number(fila.dataset.total) > 0;
                })
                .map(function (fila) {
                    return {
                        periodo: fila.dataset.mes || "",
                        total: Number(fila.dataset.total || 0),
                    };
                });

            if (!items.length) {
                items = [{ periodo: "-", total: Number(button.dataset.total || 0) }];
            }

            var totalGeneral = items.reduce(function (acc, item) {
                return acc + item.total;
            }, 0);

            var html = items.map(function (item) {
                return '<div class="modal-cobranza__item">' +
                    '<label><input type="checkbox" checked disabled></label>' +
                    '<span class="modal-cobranza__item-text">' + item.periodo + '</span>' +
                    '<strong>Bs ' + Number(item.total).toFixed(2) + '</strong>' +
                    '</div>';
            }).join("");

            modalLista.innerHTML = html;
            modalTotal.textContent = "Bs " + totalGeneral.toFixed(2);
            modalCobranza.setAttribute("aria-hidden", "false");
            modalCobranza.classList.add("activo");

        }

        document.addEventListener("click", function (event) {
            var botonPago = event.target.closest("[data-cobrar-modal]");
            if (botonPago) {
                abrirCobranza(botonPago);
            }
        });

        if (modalCerrar) {
            modalCerrar.addEventListener("click", cerrarCobranza);
        }

        if (modalCancelar) {
            modalCancelar.addEventListener("click", cerrarCobranza);
        }

        modalCobranza.addEventListener("click", function (event) {
            if (event.target === modalCobranza) {
                cerrarCobranza();
            }
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && modalCobranza.classList.contains("activo")) {
                cerrarCobranza();
            }
        });
    }
})();
