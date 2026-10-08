/* Escena 3D decorativa para el acceso: una gota cae y genera ondas en el agua. */
(function () {
    "use strict";

    var contenedor = document.getElementById("fondo-3d-login");
    if (!contenedor || !window.THREE) return;

    var THREE = window.THREE;
    var renderer;

    try {
        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    } catch (error) {
        return;
    }

    var reducirMovimiento = window.matchMedia &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var escena = new THREE.Scene();
    var camara = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
    var alturaAgua = -1.45;
    var duracionCaida = 1.25;
    var duracionCiclo = 5.2;
    var impactoX = 2.25;

    camara.position.set(0, 2.25, 9);
    camara.lookAt(0, -0.75, 0);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setClearColor(0x000000, 0);
    if (THREE.sRGBEncoding) renderer.outputEncoding = THREE.sRGBEncoding;
    contenedor.appendChild(renderer.domElement);

    escena.add(new THREE.AmbientLight(0x8be9e2, 0.72));

    var luzPrincipal = new THREE.PointLight(0x7be5ef, 3.4, 24);
    luzPrincipal.position.set(3, 5, 5);
    escena.add(luzPrincipal);

    var luzRelleno = new THREE.PointLight(0x1b6fa3, 3, 26);
    luzRelleno.position.set(-5, 1, 3);
    escena.add(luzRelleno);

    var geometriaAgua = new THREE.PlaneGeometry(24, 18, 96, 72);
    geometriaAgua.rotateX(-Math.PI / 2);
    var posicionesAgua = geometriaAgua.attributes.position;
    var posicionesOriginales = Float32Array.from(posicionesAgua.array);
    var materialAgua = new THREE.MeshPhysicalMaterial({
        color: 0x0a3855,
        roughness: 0.2,
        metalness: 0.24,
        clearcoat: 1,
        clearcoatRoughness: 0.16,
        transparent: true,
        opacity: 0.82,
        side: THREE.DoubleSide
    });
    var agua = new THREE.Mesh(geometriaAgua, materialAgua);
    agua.position.y = alturaAgua;
    escena.add(agua);

    var puntosGota = [
        new THREE.Vector2(0, -0.48),
        new THREE.Vector2(0.13, -0.4),
        new THREE.Vector2(0.24, -0.2),
        new THREE.Vector2(0.29, 0.02),
        new THREE.Vector2(0.24, 0.25),
        new THREE.Vector2(0.14, 0.48),
        new THREE.Vector2(0.06, 0.67),
        new THREE.Vector2(0, 0.82)
    ];
    var geometriaGota = new THREE.LatheGeometry(puntosGota, 40);
    var gota = new THREE.Mesh(
        geometriaGota,
        new THREE.MeshPhysicalMaterial({
            color: 0x7ddde9,
            roughness: 0.06,
            metalness: 0.08,
            clearcoat: 1,
            clearcoatRoughness: 0.04,
            transparent: true,
            opacity: 0.92
        })
    );
    escena.add(gota);

    var materialOndas = new THREE.MeshBasicMaterial({
        color: 0x8be9e2,
        transparent: true,
        opacity: 0.56,
        side: THREE.DoubleSide
    });
    var ondas = [];
    for (var i = 0; i < 3; i++) {
        var onda = new THREE.Mesh(new THREE.TorusGeometry(0.5, 0.012, 8, 72), materialOndas.clone());
        onda.rotation.x = -Math.PI / 2;
        onda.position.y = alturaAgua + 0.025 + i * 0.008;
        onda.visible = false;
        ondas.push(onda);
        escena.add(onda);
    }

    var inicio = null;
    var activo = true;
    var cuadro = 0;
    var geometriaLista = false;

    function ajustar() {
        var ancho = contenedor.clientWidth || window.innerWidth;
        var alto = contenedor.clientHeight || window.innerHeight;
        camara.aspect = ancho / alto;
        camara.position.z = ancho < 600 ? 10.5 : 9;
        camara.updateProjectionMatrix();
        impactoX = ancho < 600 ? 2.1 : 2.25;
        renderer.setSize(ancho, alto);
        if (reducirMovimiento) {
            dibujar(duracionCaida + 0.5);
        } else if (!geometriaLista) {
            dibujar(0);
            geometriaLista = true;
        }
    }

    function dibujar(tiempo) {
        var fase = tiempo % duracionCiclo;
        var edadOnda = fase - duracionCaida;
        var enCaida = fase < duracionCaida;

        if (enCaida) {
            var progreso = fase / duracionCaida;
            gota.visible = true;
            gota.position.set(impactoX, alturaAgua + 0.53 + (1 - progreso * progreso) * 2.75, 0);
            gota.scale.set(1 + progreso * 0.1, 1 - progreso * 0.16, 1 + progreso * 0.1);
            gota.rotation.z = Math.sin(tiempo * 1.5) * 0.035;
        } else {
            gota.visible = false;
        }

        for (var j = 0; j < posicionesAgua.count; j++) {
            var indice = j * 3;
            var x = posicionesOriginales[indice];
            var z = posicionesOriginales[indice + 1];
            var distancia = Math.sqrt((x - impactoX) * (x - impactoX) + z * z);
            var altura = Math.sin(x * 0.8 + tiempo * 0.75) * 0.018 +
                Math.cos(z * 0.9 - tiempo * 0.62) * 0.016;

            if (edadOnda >= 0 && edadOnda < 3.8) {
                var envolvente = Math.exp(-edadOnda * 0.72) * Math.exp(-distancia * 0.13);
                altura += Math.sin((distancia - edadOnda * 2.65) * 7.5) *
                    envolvente * 0.15;
            }

            posicionesAgua.setXYZ(j, x, altura, z);
        }
        posicionesAgua.needsUpdate = true;
        geometriaAgua.computeVertexNormals();

        for (var k = 0; k < ondas.length; k++) {
            var edadAnillo = edadOnda - k * 0.16;
            var anillo = ondas[k];
            anillo.visible = edadAnillo >= 0 && edadAnillo < 2.2;
            if (anillo.visible) {
                var crecimiento = edadAnillo / 2.2;
                anillo.position.x = impactoX;
                anillo.scale.setScalar(0.2 + crecimiento * 3.2);
                anillo.material.opacity = (1 - crecimiento) * 0.56;
            }
        }

        renderer.render(escena, camara);
    }

    function animar(marcaTiempo) {
        if (!activo) return;
        if (inicio === null) inicio = marcaTiempo;
        dibujar((marcaTiempo - inicio) / 1000);
        cuadro = requestAnimationFrame(animar);
    }

    ajustar();
    window.addEventListener("resize", ajustar);

    if (reducirMovimiento) {
        geometriaLista = true;
    } else {
        animar();
        document.addEventListener("visibilitychange", function () {
            if (document.hidden) {
                activo = false;
                cancelAnimationFrame(cuadro);
            } else if (!activo) {
                activo = true;
                inicio = null;
                animar();
            }
        });
    }
})();
