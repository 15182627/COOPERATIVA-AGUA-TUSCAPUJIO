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

    /* ---------- mostrar QR según el método de pago ---------- */

    document.querySelectorAll("[data-qr-method]").forEach(function (select) {
        var panelQr = select.form
            ? select.form.querySelector("[data-qr-payment-details]")
            : null;

        if (!panelQr) return;

        function actualizarQr() {
            panelQr.hidden = select.value !== "QR";
        }

        select.addEventListener("change", actualizarQr);
        actualizarQr();
    });

    /* ---------- modal de cobranza ---------- */
    var modalCobranza = document.getElementById("modalCobranza");
    if (modalCobranza) {
        var modalLista = document.getElementById("modalCobranzaLista");
        var modalTotal = document.getElementById("modalCobranzaTotal");
        var modalMetodo = document.getElementById("modalMetodoPago");
        var modalConfirmar = document.getElementById("modalCobranzaConfirmar");
        var formularioCobranza = document.getElementById("formCobranzaMultiple");
        var modalCerrar = document.getElementById("modalCobranzaCerrar");
        var modalCancelar = document.getElementById("modalCobranzaCancelar");

        function cerrarCobranza() {
            modalCobranza.classList.remove("activo");
            modalCobranza.setAttribute("aria-hidden", "true");
        }

        function formatearPeriodo(periodo) {
            var partes = periodo.split("/");
            var mes = Number(partes[0]);
            var nombresMeses = [
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre",
                "Diciembre",
            ];

            if (partes.length === 2 && mes >= 1 && mes <= 12) {
                return nombresMeses[mes - 1] + " " + partes[1];
            }
            return periodo;
        }

        function abrirCobranza(button) {
            if (!button) return;

            var socioId = button.dataset.socioId || "";
            var deudaSeleccionada = button.dataset.deudaId || "";
            var filaSeleccionada = button.closest("tr");
            var cuerpoTabla = filaSeleccionada && filaSeleccionada.parentElement;
            var filas = cuerpoTabla
                ? Array.from(cuerpoTabla.querySelectorAll("tr[data-socio-id]"))
                : [];
            var items = filas
                .filter(function (fila) {
                    return fila.dataset.socioId === socioId;
                })
                .filter(function (fila) {
                    var saldo = Number(fila.dataset.total);
                    return fila.dataset.deudaId &&
                        Number.isFinite(saldo) &&
                        saldo > 0;
                })
                .map(function (fila) {
                    return {
                        id: fila.dataset.deudaId,
                        periodo: formatearPeriodo(fila.dataset.mes || ""),
                        total: Number(fila.dataset.total),
                    };
                });

            if (!items.length && deudaSeleccionada) {
                var saldoSeleccionado = Number(button.dataset.total);
                if (Number.isFinite(saldoSeleccionado) && saldoSeleccionado > 0) {
                    items.push({
                        id: deudaSeleccionada,
                        periodo: formatearPeriodo(button.dataset.mes || ""),
                        total: saldoSeleccionado,
                    });
                }
            }

            modalLista.replaceChildren();
            items.forEach(function (item) {
                var fila = document.createElement("div");
                fila.className = "modal-cobranza__item";

                var label = document.createElement("label");
                label.className = "modal-cobranza__item-label";

                var checkbox = document.createElement("input");
                checkbox.type = "checkbox";
                checkbox.name = "deudas";
                checkbox.value = item.id;
                checkbox.dataset.total = item.total;
                checkbox.checked = item.id === deudaSeleccionada;
                checkbox.addEventListener("change", actualizarTotalCobranza);
                label.appendChild(checkbox);

                var periodo = document.createElement("span");
                periodo.className = "modal-cobranza__item-text";
                periodo.textContent = item.periodo;
                label.appendChild(periodo);

                var importe = document.createElement("strong");
                importe.textContent = "Bs " + item.total.toFixed(2);

                fila.append(label, importe);
                modalLista.appendChild(fila);
            });

            if (!items.length) {
                var mensaje = document.createElement("p");
                mensaje.textContent = "No hay meses pendientes para cobrar.";
                modalLista.appendChild(mensaje);
            }

            actualizarTotalCobranza();
            if (modalMetodo) {
                modalMetodo.value = "EFECTIVO";
            }
            modalCobranza.setAttribute("aria-hidden", "false");
            modalCobranza.classList.add("activo");
        }

        function actualizarTotalCobranza() {
            var seleccionadas = modalLista.querySelectorAll(
                "input[name='deudas']:checked"
            );
            var total = 0;

            seleccionadas.forEach(function (checkbox) {
                total += Number(checkbox.dataset.total);
            });

            modalTotal.textContent = "Bs " + total.toFixed(2);
            modalConfirmar.disabled = seleccionadas.length === 0;
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

        if (formularioCobranza) {
            formularioCobranza.addEventListener("submit", function (event) {
                if (!modalLista.querySelector("input[name='deudas']:checked")) {
                    event.preventDefault();
                    actualizarTotalCobranza();
                }
            });
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
