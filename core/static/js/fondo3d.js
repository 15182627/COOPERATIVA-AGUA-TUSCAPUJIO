(function () {
    "use strict";

    var contenedor = document.querySelector(".login-burbujas");
    if (!contenedor) return;

    var burbujas = document.createDocumentFragment();
    for (var i = 0; i < 64; i++) {
        var burbuja = document.createElement("span");
        var tamano = 5 + Math.random() * 11;
        var duracion = 3.5 + Math.random() * 5;
        burbuja.className = "login-burbuja";
        burbuja.style.left = Math.random() * 100 + "%";
        burbuja.style.top = Math.random() * 100 + "%";
        burbuja.style.width = tamano + "px";
        burbuja.style.height = tamano + "px";
        burbuja.style.opacity = 0.6 + Math.random() * 0.4;
        burbuja.style.setProperty("--duracion", duracion + "s");
        burbuja.style.setProperty("--retraso", -Math.random() * duracion + "s");
        burbuja.style.setProperty("--deriva-x", Math.round((Math.random() - 0.5) * 30) + "px");
        burbuja.style.setProperty("--deriva-y", Math.round((Math.random() - 0.5) * 38) + "px");
        burbujas.appendChild(burbuja);
    }
    contenedor.appendChild(burbujas);
})();
