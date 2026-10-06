/* Fondo decorativo del login: una gota de agua que respira, rodeada de
   gotitas en órbita. Es solo adorno: si three.js no carga o el navegador no
   soporta WebGL, se queda el degradado azul de fondo y el login funciona igual.
   Requiere three.js r128 (global THREE). */
(function () {
    "use strict";

    var contenedor = document.getElementById("fondo-3d-login");
    if (!contenedor || !window.THREE) return;

    var THREE = window.THREE;
    var renderer;

    try {
        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    } catch (e) {
        return;
    }

    var reducirMovimiento = window.matchMedia &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    var escena = new THREE.Scene();
    var camara = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
    camara.position.set(0, 0, 7);

    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    contenedor.appendChild(renderer.domElement);

    /* luces: una fría y una turquesa para que el agua tenga reflejos */
    escena.add(new THREE.AmbientLight(0x1b6fa3, 0.7));

    var luzPrincipal = new THREE.PointLight(0x3fd6cd, 3.2, 20);
    luzPrincipal.position.set(4, 4, 5);
    escena.add(luzPrincipal);

    var luzSecundaria = new THREE.PointLight(0x8be9e2, 2, 20);
    luzSecundaria.position.set(-4, -2, 4);
    escena.add(luzSecundaria);

    /* gota principal */
    var geometria = new THREE.IcosahedronGeometry(1.8, 6);
    var material = new THREE.MeshPhysicalMaterial({
        color: 0x1b8fb5,
        roughness: 0.08,
        metalness: 0.1,
        clearcoat: 1,
        clearcoatRoughness: 0.1,
        transparent: true,
        opacity: 0.78
    });
    var gota = new THREE.Mesh(geometria, material);
    escena.add(gota);

    var posiciones = geometria.attributes.position;
    var normales = geometria.attributes.normal;
    var originales = Float32Array.from(posiciones.array);

    /* gotitas en órbita */
    var cantidad = 60;
    var particulas = new THREE.InstancedMesh(
        new THREE.SphereGeometry(0.045, 8, 8),
        new THREE.MeshStandardMaterial({ color: 0x8be9e2, emissive: 0x1b6fa3, emissiveIntensity: 0.4, roughness: 0.3 }),
        cantidad
    );
    var datos = [];
    var auxiliar = new THREE.Object3D();
    for (var i = 0; i < cantidad; i++) {
        datos.push({
            radio: 2.6 + Math.random() * 2.2,
            angulo: Math.random() * Math.PI * 2,
            velocidad: 0.1 + Math.random() * 0.25,
            alturaY: (Math.random() - 0.5) * 5
        });
    }
    escena.add(particulas);

    var tiempo = 0;
    var activo = true;
    var cuadro = 0;

    function ajustar() {
        var ancho = contenedor.clientWidth || window.innerWidth;
        var alto = contenedor.clientHeight || window.innerHeight;
        camara.aspect = ancho / alto;
        /* en pantallas angostas la gota se aleja para no tapar el formulario */
        camara.position.z = ancho < 600 ? 9.5 : 7;
        camara.updateProjectionMatrix();
        renderer.setSize(ancho, alto);
    }

    function dibujar() {
        var n = posiciones.count;
        for (var k = 0; k < n; k++) {
            var ix = k * 3;
            var x0 = originales[ix], y0 = originales[ix + 1], z0 = originales[ix + 2];
            var onda = 1 + Math.sin(x0 * 2.2 + tiempo * 1.6) * 0.05 + Math.cos(y0 * 2.6 + tiempo * 1.3) * 0.05;
            posiciones.setXYZ(k, x0 * onda, y0 * onda, z0 * onda);

            /* en una esfera la normal es la posición normalizada: queda suave y es barato */
            var largo = Math.sqrt(x0 * x0 + y0 * y0 + z0 * z0) || 1;
            normales.setXYZ(k, x0 / largo, y0 / largo, z0 / largo);
        }
        posiciones.needsUpdate = true;
        normales.needsUpdate = true;

        gota.rotation.y += 0.0028;
        gota.rotation.x = Math.sin(tiempo * 0.3) * 0.15;

        for (var j = 0; j < cantidad; j++) {
            var p = datos[j];
            p.angulo += p.velocidad * 0.01;
            auxiliar.position.set(
                Math.cos(p.angulo) * p.radio,
                p.alturaY + Math.sin(tiempo + j) * 0.15,
                Math.sin(p.angulo) * p.radio
            );
            auxiliar.updateMatrix();
            particulas.setMatrixAt(j, auxiliar.matrix);
        }
        particulas.instanceMatrix.needsUpdate = true;

        renderer.render(escena, camara);
    }

    function animar() {
        if (!activo) return;
        tiempo += 0.006;
        dibujar();
        cuadro = requestAnimationFrame(animar);
    }

    ajustar();
    window.addEventListener("resize", ajustar);

    if (reducirMovimiento) {
        dibujar();               /* un solo cuadro, sin animación */
    } else {
        animar();
        /* no gastar batería con la pestaña en segundo plano */
        document.addEventListener("visibilitychange", function () {
            if (document.hidden) {
                activo = false;
                cancelAnimationFrame(cuadro);
            } else if (!activo) {
                activo = true;
                animar();
            }
        });
    }
})();
