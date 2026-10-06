#views.py
import csv
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Sum
from django.db import transaction
from django.utils import timezone

from datetime import date
from decimal import Decimal

from .models import (
    Socios,
    Medidores,
    Periodos,
    Lecturas,
    Consumos,
    RangosTarifa,
    Deudas,
    DetalleDeudas,
    Cajas,
    Pagos,
    MovimientosCaja,
    Usuarios,
    Roles,
    Acciones,
    Asistencias,
    ConfiguracionGeneral,
    ConfiguracionCobranza,
    Tarifas,
    
)
ROL_ADMIN = 1
ROL_CAJERO = 2
ROL_LECTOR = 3
def usuario_sesion(request):
    """
    Devuelve el usuario de nuestra tabla Usuarios
    que está guardado en la sesión.
    """
    id_usuario = request.session.get("id_usuario")

    if not id_usuario:
        return None

    try:
        return Usuarios.objects.get(id_usuario=id_usuario)
    except Usuarios.DoesNotExist:
        request.session.flush()
        return None


def requiere_login(view_func):
    """
    Protege una vista obligando a iniciar sesión.
    """
    def wrapper(request, *args, **kwargs):

        usuario = usuario_sesion(request)

        if not usuario:
            return redirect("login")

        request.usuario_actual = usuario

        return view_func(request, *args, **kwargs)

    return wrapper


def requiere_rol(roles_permitidos):

    def decorador(view_func):

        def wrapper(request, *args, **kwargs):

            usuario = usuario_sesion(request)

            if not usuario:
                return redirect("login")

            if usuario.id_rol_id not in roles_permitidos:

                return redirect("acceso_denegado")

            request.usuario_actual = usuario

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorador

def login_view(request):

    if usuario_sesion(request):
        return redirect("inicio")

    error = None

    if request.method == "POST":

        nombre_usuario = request.POST.get("nombre_usuario", "").strip()
        password = request.POST.get("password", "")

        if not nombre_usuario or not password:

            error = "Debe ingresar usuario y contraseña."

        else:

            usuario = (
                Usuarios.objects
                .filter(
                    nombre_usuario=nombre_usuario,
                    password=password,
                    estado="ACTIVO"
                )
                .first()
            )

            if usuario:

                request.session["id_usuario"] = usuario.id_usuario

                return redirect("inicio")

            error = "Usuario o contraseña incorrectos."

    return render(
        request,
        "core/usuarios/login.html",
        {
            "error": error,
        }
    )


def logout_view(request):

    request.session.flush()

    return redirect("login")

def acceso_denegado(request):

    usuario = usuario_sesion(request)

    return render(
        request,
        "core/usuarios/acceso_denegado.html",
        {
            "usuario": usuario,
        },
        status=403
    )

# =========================================================
# PRUEBA DE CONEXIÓN
# =========================================================

def prueba_socios(request):

    socios = Socios.objects.all()

    datos = []

    for socio in socios:
        datos.append({
            "id": socio.id_socio,
            "numero": socio.numero_socio,
            "nombre": f"{socio.nombres} {socio.apellidos}",
        })

    return JsonResponse({
        "mensaje": "Conexión Django + PostgreSQL funcionando",
        "cantidad_socios": len(datos),
        "socios": datos,
    })


# =========================================================
# INICIO
# =========================================================
@requiere_login
def inicio(request):

    usuario = request.usuario_actual
    rol = usuario.id_rol_id
    
    periodo_actual = (
    Periodos.objects
    .filter(estado="EN_LECTURA")
    .order_by("-id_periodo")
    .first()
    )

    # =========================
    # DATOS GENERALES
    # =========================

    total_socios = Socios.objects.filter(
        estado="ACTIVO"
    ).count()

    total_lecturas = Lecturas.objects.filter(
        id_periodo__estado="EN_LECTURA",
        lectura_actual__isnull=True
    ).count()

    total_deudas = Deudas.objects.filter(
        estado="PENDIENTE"
    ).count()

    monto_pendiente = (
        Deudas.objects
        .filter(estado="PENDIENTE")
        .aggregate(total=Sum("total"))["total"]
        or Decimal("0.00")
    )

    # =========================
    # CAJA ABIERTA
    # =========================

    caja = (
        Cajas.objects
        .filter(estado="ABIERTA")
        .order_by("-id_caja")
        .first()
    )

    saldo_caja = Decimal("0.00")

    if caja:

        ingresos = (
            MovimientosCaja.objects
            .filter(
                id_caja=caja,
                tipo="INGRESO"
            )
            .aggregate(total=Sum("importe"))["total"]
            or Decimal("0.00")
        )

        egresos = (
            MovimientosCaja.objects
            .filter(
                id_caja=caja,
                tipo="EGRESO"
            )
            .aggregate(total=Sum("importe"))["total"]
            or Decimal("0.00")
        )

        saldo_caja = (
            caja.saldo_inicial
            + ingresos
            - egresos
        )

    # =========================
    # CONTEXTO
    # =========================

    contexto = {
        "usuario": usuario,
        "rol": rol,
        "periodo_actual": periodo_actual,
        "total_socios": total_socios,
        "total_lecturas": total_lecturas,
        "total_deudas": total_deudas,
        "monto_pendiente": monto_pendiente,

        "caja": caja,
        "saldo_caja": saldo_caja,
    }

    return render(
        request,
        "core/inicio.html",
        contexto
    )


# =========================================================
# SOCIOS
# =========================================================
@requiere_login
@requiere_rol([ROL_ADMIN, ROL_CAJERO])
def lista_socios(request):

    buscar = request.GET.get(
        "buscar",
        ""
    ).strip()

    socios = Socios.objects.all().order_by(
        "id_socio"
    )

    if buscar:

        socios = socios.filter(
            Q(numero_socio__icontains=buscar) |
            Q(ci__icontains=buscar) |
            Q(nombres__icontains=buscar) |
            Q(apellidos__icontains=buscar)
        )

    return render(
        request,
        "core/socios.html",
        {
            "socios": socios,
            "buscar": buscar,
        }
    )

@requiere_login
@requiere_rol([ROL_ADMIN, ROL_CAJERO])
def nuevo_socio(request):

    if request.method == "POST":

        numero_socio = request.POST.get(
            "numero_socio",
            ""
        ).strip()

        ci = request.POST.get(
            "ci",
            ""
        ).strip()

        nombres = request.POST.get(
            "nombres",
            ""
        ).strip()

        apellidos = request.POST.get(
            "apellidos",
            ""
        ).strip()

        direccion = request.POST.get(
            "direccion",
            ""
        ).strip()

        telefono = request.POST.get(
            "telefono",
            ""
        ).strip()

        correo = request.POST.get(
            "correo",
            ""
        ).strip()

        fecha_afiliacion = request.POST.get(
            "fecha_afiliacion"
        ) or None

        estado = request.POST.get(
            "estado",
            "ACTIVO"
        )

        observacion = request.POST.get(
            "observacion",
            ""
        ).strip()

        Socios.objects.create(
            numero_socio=numero_socio,
            ci=ci or None,
            nombres=nombres,
            apellidos=apellidos,
            direccion=direccion or None,
            telefono=telefono or None,
            correo=correo or None,
            fecha_afiliacion=fecha_afiliacion,
            estado=estado,
            observacion=observacion or None,
        )

        return redirect("lista_socios")

    return render(
        request,
        "core/nuevo_socio.html"
    )

@requiere_login
@requiere_rol([ROL_ADMIN, ROL_CAJERO])
def ver_socio(request, id_socio):

    socio = get_object_or_404(
        Socios,
        id_socio=id_socio
    )

    return render(
        request,
        "core/ver_socio.html",
        {
            "socio": socio,
        }
    )
@requiere_login
@requiere_rol([ROL_ADMIN, ROL_CAJERO])
def editar_socio(request, id_socio):

    socio = get_object_or_404(
        Socios,
        id_socio=id_socio
    )

    if request.method == "POST":

        socio.numero_socio = request.POST.get(
            "numero_socio",
            ""
        ).strip()

        socio.ci = request.POST.get(
            "ci",
            ""
        ).strip() or None

        socio.nombres = request.POST.get(
            "nombres",
            ""
        ).strip()

        socio.apellidos = request.POST.get(
            "apellidos",
            ""
        ).strip()

        socio.direccion = request.POST.get(
            "direccion",
            ""
        ).strip() or None

        socio.telefono = request.POST.get(
            "telefono",
            ""
        ).strip() or None

        socio.correo = request.POST.get(
            "correo",
            ""
        ).strip() or None

        socio.fecha_afiliacion = request.POST.get(
            "fecha_afiliacion"
        ) or None

        socio.estado = request.POST.get(
            "estado",
            "ACTIVO"
        )

        socio.observacion = request.POST.get(
            "observacion",
            ""
        ).strip() or None

        socio.save()

        return redirect("lista_socios")

    return render(
        request,
        "core/editar_socio.html",
        {
            "socio": socio,
        }
    )

@requiere_login
@requiere_rol([ROL_ADMIN])
def cambiar_estado_socio(request, id_socio):

    socio = get_object_or_404(
        Socios,
        id_socio=id_socio
    )

    if request.method == "POST":

        if socio.estado == "ACTIVO":
            socio.estado = "INACTIVO"
        else:
            socio.estado = "ACTIVO"

        socio.save()

    return redirect("lista_socios")


# =========================================================
# PERIODOS
# =========================================================
@requiere_login
@requiere_rol([ROL_ADMIN, ROL_LECTOR])
def lista_periodos(request):

    periodos = Periodos.objects.all().order_by(
        "-gestion",
        "-mes"
    )

    return render(
        request,
        "core/periodos.html",
        {
            "periodos": periodos,
        }
    )

@requiere_login
@requiere_rol([ROL_ADMIN])
def nuevo_periodo(request):

    if request.method == "POST":

        mes = request.POST.get("mes")
        gestion = request.POST.get("gestion")
        fecha_inicio = request.POST.get("fecha_inicio")
        fecha_fin = request.POST.get("fecha_fin")

        fecha_limite_pago = request.POST.get(
            "fecha_limite_pago"
        ) or None

        # Estado válido según la base de datos.
        estado = request.POST.get(
            "estado",
            "NO_HABILITADO"
        )

        observacion = request.POST.get(
            "observacion",
            ""
        ).strip()

        existe = Periodos.objects.filter(
            mes=mes,
            gestion=gestion
        ).exists()

        if existe:

            return render(
                request,
                "core/nuevo_periodo.html",
                {
                    "error": (
                        "Ya existe un periodo "
                        "para ese mes y gestión."
                    )
                }
            )

        Periodos.objects.create(
            mes=mes,
            gestion=gestion,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            fecha_limite_pago=fecha_limite_pago,
            estado=estado,
            observacion=observacion or None,
        )

        return redirect("lista_periodos")

    return render(
        request,
        "core/nuevo_periodo.html"
    )
@requiere_login
@requiere_rol([ROL_ADMIN])
def cambiar_estado_periodo(request, id_periodo):

    periodo = get_object_or_404(
        Periodos,
        id_periodo=id_periodo
    )

    if request.method == "POST":

        if periodo.estado == "NO_HABILITADO":

            periodo.estado = "HABILITADO"

        elif periodo.estado == "HABILITADO":

            periodo.estado = "EN_LECTURA"

        elif periodo.estado == "EN_LECTURA":

            periodo.estado = "LECTURA_CERRADA"

        elif periodo.estado == "LECTURA_CERRADA":

            periodo.estado = "EN_COBRANZA"

        elif periodo.estado == "EN_COBRANZA":

            periodo.estado = "CERRADO"

        elif periodo.estado == "CERRADO":

            periodo.estado = "HABILITADO"

        periodo.save()

    return redirect("lista_periodos")


# =========================================================
# GENERAR PLANILLA
# =========================================================
@requiere_login
@requiere_rol([ROL_ADMIN, ROL_LECTOR])
def generar_planilla(request, id_periodo):

    periodo = get_object_or_404(
        Periodos,
        id_periodo=id_periodo
    )

    if periodo.estado not in [
        "HABILITADO",
        "EN_LECTURA"
    ]:

        return render(
            request,
            "core/generar_planilla.html",
            {
                "periodo": periodo,
                "error": (
                    "El periodo no está habilitado "
                    "para generar la planilla."
                )
            }
        )

    if request.method == "POST":

        medidores = Medidores.objects.filter(
            estado="ACTIVO"
        ).order_by(
            "id_medidor"
        )

        creadas = 0

        for medidor in medidores:

            existe = Lecturas.objects.filter(
                id_medidor=medidor,
                id_periodo=periodo
            ).exists()

            if existe:
                continue

            ultima_lectura = (
                Lecturas.objects
                .filter(
                    id_medidor=medidor,
                    lectura_actual__isnull=False
                )
                .order_by(
                    "-id_periodo__gestion",
                    "-id_periodo__mes"
                )
                .first()
            )

            if ultima_lectura:

                lectura_anterior = (
                    ultima_lectura.lectura_actual
                )

            else:

                lectura_anterior = (
                    medidor.lectura_inicial
                )

            Lecturas.objects.create(
                id_medidor=medidor,
                id_periodo=periodo,
                lectura_anterior=lectura_anterior,
                lectura_actual=None,
                fecha_lectura=None,
                id_usuario=None,
                estado="PENDIENTE",
                observacion=None,
            )

            creadas += 1

        return redirect(
            "planilla_lecturas",
            id_periodo=periodo.id_periodo
        )

    return render(
        request,
        "core/generar_planilla.html",
        {
            "periodo": periodo,
        }
    )


# =========================================================
# PLANILLA DE LECTURAS
# =========================================================
@requiere_login
@requiere_rol([ROL_ADMIN, ROL_LECTOR])
def planilla_lecturas(request, id_periodo):

    periodo = get_object_or_404(
        Periodos,
        id_periodo=id_periodo
    )

    lecturas = (
        Lecturas.objects
        .filter(id_periodo=periodo)
        .select_related(
            "id_medidor",
            "id_medidor__id_socio"
        )
        .order_by(
            "id_medidor__id_socio__numero_socio"
        )
    )

    periodo_anterior = (
        Periodos.objects
        .filter(
            Q(gestion__lt=periodo.gestion) |
            Q(
                gestion=periodo.gestion,
                mes__lt=periodo.mes
            )
        )
        .order_by(
            "-gestion",
            "-mes"
        )
        .first()
    )

    periodo_siguiente = (
        Periodos.objects
        .filter(
            Q(gestion__gt=periodo.gestion) |
            Q(
                gestion=periodo.gestion,
                mes__gt=periodo.mes
            )
        )
        .order_by(
            "gestion",
            "mes"
        )
        .first()
    )

    return render(
        request,
        "core/planilla_lecturas.html",
        {
            "periodo": periodo,
            "lecturas": lecturas,
            "periodo_anterior": periodo_anterior,
            "periodo_siguiente": periodo_siguiente,
        }
    )


# =========================================================
# REGISTRAR LECTURA
# =========================================================
@requiere_login
@requiere_rol([ROL_ADMIN, ROL_LECTOR])
def registrar_lectura(request, id_lectura):

    lectura = get_object_or_404(
        Lecturas,
        id_lectura=id_lectura
    )

    if request.method == "POST":

        if lectura.id_periodo.estado != "EN_LECTURA":

            return render(
                request,
                "core/lectura.html",
                {
                    "lectura": lectura,
                    "error": (
                        "El periodo está cerrado y "
                        "no permite registrar lecturas."
                    )
                }
            )

        valor = request.POST.get(
            "lectura_actual",
            ""
        ).strip()

        observacion = request.POST.get(
            "observacion",
            ""
        ).strip()

        try:

            lectura_actual = Decimal(valor)

        except Exception:

            return render(
                request,
                "core/lectura.html",
                {
                    "lectura": lectura,
                    "error": (
                        "La lectura actual debe "
                        "ser un número válido."
                    )
                }
            )

        if lectura_actual < lectura.lectura_anterior:

            return render(
                request,
                "core/lectura.html",
                {
                    "lectura": lectura,
                    "error": (
                        "La lectura actual no puede "
                        "ser menor que la lectura anterior."
                    )
                }
            )

        lectura.lectura_actual = lectura_actual
        lectura.fecha_lectura = timezone.now()
        lectura.estado = "REGISTRADA"
        lectura.observacion = observacion or None

        lectura.save()

        metros_cubicos = (
            lectura_actual -
            lectura.lectura_anterior
        )

        socio = lectura.id_medidor.id_socio

        rango = None

        if socio.id_tarifa:

            rango = (
                RangosTarifa.objects
                .filter(
                    id_tarifa=socio.id_tarifa,
                    consumo_desde__lte=metros_cubicos,
                    consumo_hasta__gte=metros_cubicos,
                    estado="ACTIVO",
                )
                .first()
            )

        if rango:

            importe = rango.precio_base

            if metros_cubicos > rango.consumo_desde:

                excedente = (
                    metros_cubicos -
                    rango.consumo_desde
                )

                importe += (
                    excedente *
                    rango.precio_excedente
                )

            consumo, creado = (
                Consumos.objects.get_or_create(
                    id_lectura=lectura,
                    defaults={
                        "id_rango": rango,
                        "metros_cubicos": metros_cubicos,
                        "importe": importe,
                        "fecha_calculo": timezone.now(),
                    }
                )
            )

            if not creado:

                consumo.id_rango = rango
                consumo.metros_cubicos = metros_cubicos
                consumo.importe = importe
                consumo.fecha_calculo = timezone.now()

                consumo.save()

        return redirect(
            "planilla_lecturas",
            id_periodo=lectura.id_periodo.id_periodo
        )

    return render(
        request,
        "core/lectura.html",
        {
            "lectura": lectura,
        }
    )


# =========================================================
# EDITAR LECTURA
# =========================================================
@requiere_login
@requiere_rol([ROL_ADMIN, ROL_LECTOR])
def editar_lectura(request, id_lectura):

    lectura = get_object_or_404(
        Lecturas,
        id_lectura=id_lectura
    )

    if request.method == "POST":

        valor = request.POST.get(
            "lectura_actual",
            ""
        ).strip()

        observacion = request.POST.get(
            "observacion",
            ""
        ).strip()

        try:

            lectura_actual = Decimal(valor)

        except Exception:

            return render(
                request,
                "core/editar_lectura.html",
                {
                    "lectura": lectura,
                    "error": (
                        "La lectura actual debe "
                        "ser un número válido."
                    )
                }
            )

        if lectura_actual < lectura.lectura_anterior:

            return render(
                request,
                "core/editar_lectura.html",
                {
                    "lectura": lectura,
                    "error": (
                        "La lectura actual no puede "
                        "ser menor que la lectura anterior."
                    )
                }
            )

        lectura.lectura_actual = lectura_actual
        lectura.fecha_lectura = timezone.now()
        lectura.estado = "REGISTRADA"
        lectura.observacion = observacion or None

        lectura.save()

        try:

            consumo = Consumos.objects.get(
                id_lectura=lectura
            )

            metros_cubicos = (
                lectura_actual -
                lectura.lectura_anterior
            )

            consumo.metros_cubicos = metros_cubicos
            consumo.fecha_calculo = timezone.now()

            if consumo.id_rango:

                rango = consumo.id_rango

                importe = rango.precio_base

                if metros_cubicos > rango.consumo_desde:

                    excedente = (
                        metros_cubicos -
                        rango.consumo_desde
                    )

                    importe += (
                        excedente *
                        rango.precio_excedente
                    )

                consumo.importe = importe

            consumo.save()

        except Consumos.DoesNotExist:

            pass

        return redirect(
            "planilla_lecturas",
            id_periodo=lectura.id_periodo.id_periodo
        )

    return render(
        request,
        "core/editar_lectura.html",
        {
            "lectura": lectura,
        }
    )


# =========================================================
# CONSUMOS
# =========================================================
@requiere_login
@requiere_rol([ROL_ADMIN, ROL_LECTOR])
def lista_consumos(request):

    periodo_id = request.GET.get(
        "periodo"
    )

    consumos = (
        Consumos.objects.select_related(
            "id_lectura",
            "id_lectura__id_medidor",
            "id_lectura__id_medidor__id_socio",
            "id_lectura__id_periodo",
            "id_rango",
        )
        .order_by(
            "-id_lectura__id_periodo__gestion",
            "-id_lectura__id_periodo__mes",
            "id_lectura__id_medidor__id_socio__numero_socio",
        )
    )

    if periodo_id:

        consumos = consumos.filter(
            id_lectura__id_periodo_id=periodo_id
        )

    periodos = Periodos.objects.all().order_by(
        "-gestion",
        "-mes"
    )

    return render(
        request,
        "core/consumos.html",
        {
            "consumos": consumos,
            "periodos": periodos,
            "periodo_seleccionado": periodo_id,
        }
    )


# =========================================================
# DEUDAS
# =========================================================
@requiere_login
@requiere_rol([ROL_ADMIN, ROL_LECTOR])
def lista_deudas(request):

    periodo_id = request.GET.get(
        "periodo"
    )

    deudas = (
        Deudas.objects
        .select_related(
            "id_socio",
            "id_periodo",
        )
        .prefetch_related(
            "detalledeudas_set"
        )
        .order_by(
            "-id_periodo__gestion",
            "-id_periodo__mes",
            "id_socio__numero_socio",
        )
    )

    if periodo_id:

        deudas = deudas.filter(
            id_periodo_id=periodo_id
        )

    periodos = Periodos.objects.all().order_by(
        "-gestion",
        "-mes"
    )

    return render(
        request,
        "core/deudas.html",
        {
            "deudas": deudas,
            "periodos": periodos,
            "periodo_seleccionado": periodo_id,
        }
    )

@requiere_login
@requiere_rol([ROL_ADMIN])
def generar_deudas(request, id_periodo):

    periodo = get_object_or_404(
        Periodos,
        id_periodo=id_periodo
    )

    if request.method == "POST":

        consumos = (
            Consumos.objects.select_related(
                "id_lectura",
                "id_lectura__id_medidor",
                "id_lectura__id_medidor__id_socio",
            )
            .filter(
                id_lectura__id_periodo=periodo
            )
        )

        creadas = 0

        for consumo in consumos:

            socio = (
                consumo.id_lectura
                .id_medidor
                .id_socio
            )

            deuda_existente = (
                Deudas.objects
                .filter(
                    id_socio=socio,
                    id_periodo=periodo
                )
                .first()
            )

            if deuda_existente:
                continue

            subtotal = consumo.importe
            recargo = Decimal("0.00")

            deuda = Deudas.objects.create(
                id_socio=socio,
                id_periodo=periodo,
                fecha_generacion=date.today(),
                fecha_vencimiento=periodo.fecha_limite_pago,
                subtotal=subtotal,
                recargo=recargo,
                total=subtotal,
                estado="PENDIENTE",
            )

            DetalleDeudas.objects.create(
                id_deuda=deuda,
                concepto="CONSUMO",
                descripcion=(
                    f"Consumo de "
                    f"{consumo.metros_cubicos} m3"
                ),
                importe=subtotal,
            )

            creadas += 1

        return redirect(
            "lista_deudas"
        )

    return render(
        request,
        "core/generar_deudas.html",
        {
            "periodo": periodo,
        }
    )


# =========================================================
# COBRANZA - LISTA
# =========================================================

@requiere_login
@requiere_rol([ROL_ADMIN, ROL_CAJERO])
def lista_cobranza(request):

    buscar = request.GET.get(
        "buscar",
        ""
    ).strip()

    estado = request.GET.get(
        "estado",
        ""
    ).strip()

    deudas = (
        Deudas.objects
        .select_related(
            "id_socio",
            "id_periodo"
        )
        .order_by(
            "-id_periodo__gestion",
            "-id_periodo__mes",
            "id_socio__numero_socio"
        )
    )

    if buscar:

        deudas = deudas.filter(
            Q(id_socio__numero_socio__icontains=buscar) |
            Q(id_socio__ci__icontains=buscar) |
            Q(id_socio__nombres__icontains=buscar) |
            Q(id_socio__apellidos__icontains=buscar)
        )

    if estado:

        deudas = deudas.filter(
            estado=estado
        )

    return render(
        request,
        "core/cobranza/lista.html",
        {
            "deudas": deudas,
            "buscar": buscar,
            "usuario": request.usuario_actual,
            "estado_seleccionado": estado,
        }
    )


# =========================================================
# COBRANZA - DETALLE Y PAGO
# =========================================================
@requiere_login
@requiere_rol([ROL_ADMIN, ROL_CAJERO])
def detalle_cobranza(request, id_deuda):

    deuda = get_object_or_404(
        Deudas.objects.select_related(
            "id_socio",
            "id_periodo"
        ),
        id_deuda=id_deuda
    )

    detalles = (
        DetalleDeudas.objects
        .filter(
            id_deuda=deuda
        )
        .order_by(
            "id_detalle"
        )
    )

    # -----------------------------------------------------
    # CAJA ABIERTA
    # -----------------------------------------------------

    caja = (
        Cajas.objects
        .filter(estado="ABIERTA")
        .order_by("-id_caja")
        .first()
    )

    # -----------------------------------------------------
    # PAGOS EXISTENTES
    # -----------------------------------------------------

    pagos = (
        Pagos.objects
        .filter(
            id_deuda=deuda
        )
        .select_related(
            "id_usuario",
            "id_caja"
        )
        .order_by(
            "-fecha_pago",
            "-id_pago"
        )
    )

    total_pagado = (
        pagos.aggregate(
            total=Sum("importe")
        )["total"]
        or Decimal("0.00")
    )

    saldo_pendiente = (
        deuda.total -
        total_pagado
    )

    if saldo_pendiente < 0:

        saldo_pendiente = Decimal("0.00")

    # -----------------------------------------------------
    # USUARIOS
    # -----------------------------------------------------

    usuarios = (
        Usuarios.objects
        .filter(
            estado="ACTIVO"
        )
        .order_by(
            "nombre_completo"
        )
    )

    # =====================================================
    # PROCESAR PAGO
    # =====================================================

    if request.method == "POST":

        # -------------------------------------------------
        # VERIFICAR ESTADO
        # -------------------------------------------------

        if saldo_pendiente <= 0:

            deuda.estado = "PAGADA"
            deuda.save()

            return render(
                request,
                "core/cobranza/detalle.html",
                {
                    "deuda": deuda,
                    "detalles": detalles,
                    "caja": caja,
                    "usuarios": usuarios,
                    "pagos": pagos,
                    "total_pagado": total_pagado,
                    "saldo_pendiente": Decimal("0.00"),
                    "error": (
                        "Esta deuda ya se encuentra "
                        "completamente pagada."
                    ),
                }
            )

        # -------------------------------------------------
        # CAJA
        # -------------------------------------------------

        if not caja:

            return render(
                request,
                "core/cobranza/detalle.html",
                {
                    "deuda": deuda,
                    "detalles": detalles,
                    "caja": None,
                    "usuarios": usuarios,
                    "pagos": pagos,
                    "total_pagado": total_pagado,
                    "saldo_pendiente": saldo_pendiente,
                    "error": (
                        "No existe una caja abierta. "
                        "Debe abrir una caja antes "
                        "de registrar el cobro."
                    ),
                }
            )

        # -------------------------------------------------
        # DATOS DEL FORMULARIO
        # -------------------------------------------------

        importe_texto = request.POST.get(
            "importe",
            ""
        ).strip()

        metodo_pago = request.POST.get(
            "metodo_pago",
            ""
        ).strip()

        observacion = request.POST.get(
            "observacion",
            ""
        ).strip()

        id_usuario = request.POST.get(
            "id_usuario",
            ""
        ).strip()

        # -------------------------------------------------
        # IMPORTE
        # -------------------------------------------------

        try:

            importe = Decimal(
                importe_texto
            )

        except Exception:

            return render(
                request,
                "core/cobranza/detalle.html",
                {
                    "deuda": deuda,
                    "detalles": detalles,
                    "caja": caja,
                    "usuarios": usuarios,
                    "pagos": pagos,
                    "total_pagado": total_pagado,
                    "saldo_pendiente": saldo_pendiente,
                    "error": (
                        "El importe debe ser "
                        "un número válido."
                    ),
                }
            )

        if importe <= 0:

            return render(
                request,
                "core/cobranza/detalle.html",
                {
                    "deuda": deuda,
                    "detalles": detalles,
                    "caja": caja,
                    "usuarios": usuarios,
                    "pagos": pagos,
                    "total_pagado": total_pagado,
                    "saldo_pendiente": saldo_pendiente,
                    "error": (
                        "El importe debe ser "
                        "mayor que cero."
                    ),
                }
            )

        # -------------------------------------------------
        # NO SOBREPAGAR
        # -------------------------------------------------

        if importe > saldo_pendiente:

            return render(
                request,
                "core/cobranza/detalle.html",
                {
                    "deuda": deuda,
                    "detalles": detalles,
                    "caja": caja,
                    "usuarios": usuarios,
                    "pagos": pagos,
                    "total_pagado": total_pagado,
                    "saldo_pendiente": saldo_pendiente,
                    "error": (
                        "El importe no puede ser "
                        "mayor al saldo pendiente."
                    ),
                }
            )

        # -------------------------------------------------
        # MÉTODO DE PAGO
        # -------------------------------------------------

        metodos_validos = [
            "EFECTIVO",
            "TRANSFERENCIA",
            "QR",
            "OTRO",
        ]

        if metodo_pago not in metodos_validos:

            return render(
                request,
                "core/cobranza/detalle.html",
                {
                    "deuda": deuda,
                    "detalles": detalles,
                    "caja": caja,
                    "usuarios": usuarios,
                    "pagos": pagos,
                    "total_pagado": total_pagado,
                    "saldo_pendiente": saldo_pendiente,
                    "error": (
                        "El método de pago "
                        "seleccionado no es válido."
                    ),
                }
            )

        # -------------------------------------------------
        # USUARIO
        # -------------------------------------------------

        if not id_usuario:

            return render(
                request,
                "core/cobranza/detalle.html",
                {
                    "deuda": deuda,
                    "detalles": detalles,
                    "caja": caja,
                    "usuarios": usuarios,
                    "pagos": pagos,
                    "total_pagado": total_pagado,
                    "saldo_pendiente": saldo_pendiente,
                    "error": (
                        "Debe seleccionar el usuario "
                        "que registra el pago."
                    ),
                }
            )

        usuario = get_object_or_404(
            Usuarios,
            id_usuario=id_usuario
        )

        # =================================================
        # TRANSACCIÓN
        # =================================================

        with transaction.atomic():

            # ---------------------------------------------
            # CREAR PAGO
            # ---------------------------------------------

            pago = Pagos.objects.create(
                id_deuda=deuda,
                id_usuario=usuario,
                id_caja=caja,
                fecha_pago=timezone.now(),
                importe=importe,
                metodo_pago=metodo_pago,
                observacion=observacion or None,
            )

            # ---------------------------------------------
            # MOVIMIENTO DE CAJA
            # ---------------------------------------------

            MovimientosCaja.objects.create(
                id_caja=caja,
                id_pago=pago,
                id_usuario=usuario,
                fecha_movimiento=timezone.now(),
                tipo="INGRESO",
                concepto=(
                    f"Pago deuda #{deuda.id_deuda} - "
                    f"{deuda.id_socio.numero_socio}"
                ),
                importe=importe,
                observacion=observacion or None,
            )

            # ---------------------------------------------
            # NUEVO TOTAL PAGADO
            # ---------------------------------------------

            nuevo_total_pagado = (
                total_pagado +
                importe
            )

            # ---------------------------------------------
            # ACTUALIZAR DEUDA
            # ---------------------------------------------

            if nuevo_total_pagado >= deuda.total:

                deuda.estado = "PAGADA"

            else:

                deuda.estado = "PENDIENTE"

            deuda.save()

        return redirect(
            "detalle_cobranza",
            id_deuda=deuda.id_deuda
        )

    # =====================================================
    # MOSTRAR DETALLE
    # =====================================================

    return render(
        request,
        "core/cobranza/detalle.html",
        {
            "deuda": deuda,
            "detalles": detalles,
            "caja": caja,
            "usuarios": usuarios,
            "pagos": pagos,
            "total_pagado": total_pagado,
            "saldo_pendiente": saldo_pendiente,
        }
    )


# =========================================================
# CAJA PRINCIPAL
# =========================================================
@requiere_login
@requiere_rol([ROL_ADMIN, ROL_CAJERO])
def caja_principal(request):

    caja = (
        Cajas.objects
        .filter(
            estado="ABIERTA"
        )
        .order_by(
            "-id_caja"
        )
        .first()
    )

    if not caja:

        return render(
            request,
            "core/caja/principal.html",
            {
                "caja": None,
                "mensaje": (
                    "No existe una caja abierta actualmente."
                ),
            }
        )

    movimientos = (
        MovimientosCaja.objects
        .filter(
            id_caja=caja
        )
        .select_related(
            "id_usuario",
            "id_pago",
        )
        .order_by(
            "-fecha_movimiento",
            "-id_movimiento"
        )
    )

    ingresos = (
        MovimientosCaja.objects
        .filter(
            id_caja=caja,
            tipo="INGRESO"
        )
        .aggregate(
            total=Sum("importe")
        )["total"]
        or Decimal("0.00")
    )

    egresos = (
        MovimientosCaja.objects
        .filter(
            id_caja=caja,
            tipo="EGRESO"
        )
        .aggregate(
            total=Sum("importe")
        )["total"]
        or Decimal("0.00")
    )

    saldo_actual = (
        caja.saldo_inicial +
        ingresos -
        egresos
    )

    return render(
        request,
        "core/caja/principal.html",
        {
            "caja": caja,
            "movimientos": movimientos,
            "ingresos": ingresos,
            "egresos": egresos,
            "saldo_actual": saldo_actual,
        }
    )


# =========================================================
# ABRIR CAJA
# =========================================================
@requiere_login
@requiere_rol([ROL_ADMIN, ROL_CAJERO])
def abrir_caja(request):

    caja_abierta = (
        Cajas.objects
        .filter(
            estado="ABIERTA"
        )
        .first()
    )

    if caja_abierta:

        return redirect(
            "caja_principal"
        )

    usuarios = (
        Usuarios.objects
        .filter(
            estado="ACTIVO"
        )
        .order_by(
            "nombre_completo"
        )
    )

    if request.method == "POST":

        saldo_inicial_texto = request.POST.get(
            "saldo_inicial",
            ""
        ).strip()

        id_usuario = request.POST.get(
            "id_usuario",
            ""
        ).strip()

        try:

            saldo_inicial = Decimal(
                saldo_inicial_texto
            )

        except Exception:

            return render(
                request,
                "core/caja/abrir.html",
                {
                    "usuarios": usuarios,
                    "error": (
                        "El saldo inicial debe "
                        "ser un número válido."
                    )
                }
            )

        if saldo_inicial < 0:

            return render(
                request,
                "core/caja/abrir.html",
                {
                    "usuarios": usuarios,
                    "error": (
                        "El saldo inicial no "
                        "puede ser negativo."
                    )
                }
            )

        if not id_usuario:

            return render(
                request,
                "core/caja/abrir.html",
                {
                    "usuarios": usuarios,
                    "error": (
                        "Debe seleccionar el usuario "
                        "que abre la caja."
                    )
                }
            )

        usuario = get_object_or_404(
            Usuarios,
            id_usuario=id_usuario
        )

        Cajas.objects.create(
            fecha_apertura=date.today(),
            fecha_cierre=None,
            saldo_inicial=saldo_inicial,
            saldo_final=None,
            estado="ABIERTA",
            id_usuario_apertura=usuario,
            id_usuario_cierre=None,
        )

        return redirect(
            "caja_principal"
        )

    return render(
        request,
        "core/caja/abrir.html",
        {
            "usuarios": usuarios,
        }
    )


# =========================================================
# MOVIMIENTOS DE CAJA
# =========================================================
@requiere_login
@requiere_rol([ROL_ADMIN, ROL_CAJERO])
def caja_movimientos(request):

    caja = (
        Cajas.objects
        .filter(
            estado="ABIERTA"
        )
        .order_by(
            "-id_caja"
        )
        .first()
    )

    if not caja:

        return render(
            request,
            "core/caja/movimientos.html",
            {
                "caja": None,
                "movimientos": [],
                "mensaje": (
                    "No existe una caja abierta actualmente."
                ),
            }
        )

    movimientos = (
        MovimientosCaja.objects
        .filter(
            id_caja=caja
        )
        .select_related(
            "id_usuario",
            "id_pago",
        )
        .order_by(
            "-fecha_movimiento",
            "-id_movimiento"
        )
    )

    return render(
        request,
        "core/caja/movimientos.html",
        {
            "caja": caja,
            "movimientos": movimientos,
        }
    )


# =========================================================
# EGRESO DE CAJA
# =========================================================
@requiere_login
@requiere_rol([ROL_ADMIN, ROL_CAJERO])
def registrar_egreso(request):

    caja = (
        Cajas.objects
        .filter(
            estado="ABIERTA"
        )
        .order_by(
            "-id_caja"
        )
        .first()
    )

    if not caja:

        return redirect(
            "caja_principal"
        )

    usuarios = (
        Usuarios.objects
        .filter(
            estado="ACTIVO"
        )
        .order_by(
            "nombre_completo"
        )
    )

    if request.method == "POST":

        importe_texto = request.POST.get(
            "importe",
            ""
        ).strip()

        concepto = request.POST.get(
            "concepto",
            ""
        ).strip()

        observacion = request.POST.get(
            "observacion",
            ""
        ).strip()

        id_usuario = request.POST.get(
            "id_usuario",
            ""
        ).strip()

        try:

            importe = Decimal(
                importe_texto
            )

        except Exception:

            return render(
                request,
                "core/caja/egreso.html",
                {
                    "caja": caja,
                    "usuarios": usuarios,
                    "error": (
                        "El importe debe ser "
                        "un número válido."
                    ),
                }
            )

        if importe <= 0:

            return render(
                request,
                "core/caja/egreso.html",
                {
                    "caja": caja,
                    "usuarios": usuarios,
                    "error": (
                        "El importe debe ser "
                        "mayor que cero."
                    ),
                }
            )

        if not concepto:

            return render(
                request,
                "core/caja/egreso.html",
                {
                    "caja": caja,
                    "usuarios": usuarios,
                    "error": (
                        "Debe ingresar un concepto."
                    ),
                }
            )

        if not id_usuario:

            return render(
                request,
                "core/caja/egreso.html",
                {
                    "caja": caja,
                    "usuarios": usuarios,
                    "error": (
                        "Debe seleccionar el usuario."
                    ),
                }
            )

        usuario = get_object_or_404(
            Usuarios,
            id_usuario=id_usuario
        )

        MovimientosCaja.objects.create(
            id_caja=caja,
            id_pago=None,
            id_usuario=usuario,
            fecha_movimiento=timezone.now(),
            tipo="EGRESO",
            concepto=concepto,
            importe=importe,
            observacion=observacion or None,
        )

        return redirect(
            "caja_principal"
        )

    return render(
        request,
        "core/caja/egreso.html",
        {
            "caja": caja,
            "usuarios": usuarios,
        }
    )


# =========================================================
# CERRAR CAJA
# =========================================================
@requiere_login
@requiere_rol([ROL_ADMIN, ROL_CAJERO])
def cerrar_caja(request):

    caja = (
        Cajas.objects
        .filter(
            estado="ABIERTA"
        )
        .order_by(
            "-id_caja"
        )
        .first()
    )

    if not caja:

        return redirect(
            "caja_principal"
        )

    usuarios = (
        Usuarios.objects
        .filter(
            estado="ACTIVO"
        )
        .order_by(
            "nombre_completo"
        )
    )

    ingresos = (
        MovimientosCaja.objects
        .filter(
            id_caja=caja,
            tipo="INGRESO"
        )
        .aggregate(
            total=Sum("importe")
        )["total"]
        or Decimal("0.00")
    )

    egresos = (
        MovimientosCaja.objects
        .filter(
            id_caja=caja,
            tipo="EGRESO"
        )
        .aggregate(
            total=Sum("importe")
        )["total"]
        or Decimal("0.00")
    )

    saldo_actual = (
        caja.saldo_inicial +
        ingresos -
        egresos
    )

    if request.method == "POST":

        id_usuario = request.POST.get(
            "id_usuario",
            ""
        ).strip()

        if not id_usuario:

            return render(
                request,
                "core/caja/cerrar.html",
                {
                    "caja": caja,
                    "usuarios": usuarios,
                    "ingresos": ingresos,
                    "egresos": egresos,
                    "saldo_actual": saldo_actual,
                    "error": (
                        "Debe seleccionar el usuario "
                        "que cierra la caja."
                    ),
                }
            )

        usuario = get_object_or_404(
            Usuarios,
            id_usuario=id_usuario
        )

        caja.fecha_cierre = date.today()
        caja.saldo_final = saldo_actual
        caja.estado = "CERRADA"
        caja.id_usuario_cierre = usuario

        caja.save()

        return redirect(
            "caja_principal"
        )

    return render(
        request,
        "core/caja/cerrar.html",
        {
            "caja": caja,
            "usuarios": usuarios,
            "ingresos": ingresos,
            "egresos": egresos,
            "saldo_actual": saldo_actual,
        }
    )
    
@requiere_login
@requiere_rol([ROL_ADMIN, ROL_CAJERO])
def historial_cajas(request):
    cajas = (
        Cajas.objects
        .all()
        .order_by("-id_caja")
    )

    return render(
        request,
        "core/caja/historial.html",
        {
            "cajas": cajas,
        }
    )
    
    
@requiere_rol([ROL_ADMIN])
def lista_usuarios(request):

    usuarios = (
        Usuarios.objects
        .all()
        .order_by("nombre_completo")
    )

    return render(
        request,
        "core/usuarios/lista.html",
        {
            "usuarios": usuarios,
        }
    )
    
    
# ============================================================
# BLOQUE 1 - ACCIONES
# ============================================================

@requiere_rol([ROL_ADMIN])
def lista_acciones(request):
    texto = request.GET.get("q", "").strip()

    acciones = Acciones.objects.select_related(
        "id_socio"
    ).order_by("-fecha_registro", "-id_accion")

    if texto:
        acciones = acciones.filter(
            Q(codigo_accion__icontains=texto) |
            Q(id_socio__numero_socio__icontains=texto) |
            Q(id_socio__nombres__icontains=texto) |
            Q(id_socio__apellidos__icontains=texto)
        )

    return render(request, "core/acciones/lista.html", {
        "acciones": acciones,
        "q": texto,
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN])
def nueva_accion(request):
    socios = Socios.objects.filter(
        estado="ACTIVO"
    ).order_by(
        "apellidos",
        "nombres"
    )

    if request.method == "POST":
        id_socio = request.POST.get("id_socio")
        codigo = request.POST.get("codigo_accion", "").strip()
        fecha_registro = request.POST.get("fecha_registro") or date.today()
        estado = request.POST.get("estado", "ACTIVO")
        observacion = request.POST.get("observacion", "").strip()

        if not id_socio:
            return render(request, "core/acciones/form.html", {
                "socios": socios,
                "error": "Debe seleccionar un socio.",
                "usuario": request.usuario_actual,
            })

        socio = get_object_or_404(
            Socios,
            id_socio=id_socio
        )

        if codigo and Acciones.objects.filter(
            codigo_accion=codigo
        ).exists():
            return render(request, "core/acciones/form.html", {
                "socios": socios,
                "error": "El código de acción ya existe.",
                "usuario": request.usuario_actual,
            })

        Acciones.objects.create(
            id_socio=socio,
            codigo_accion=codigo or None,
            fecha_registro=fecha_registro,
            estado=estado,
            observacion=observacion or None,
        )

        return redirect("lista_acciones")

    return render(request, "core/acciones/form.html", {
        "socios": socios,
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN])
def editar_accion(request, id_accion):
    accion = get_object_or_404(
        Acciones,
        id_accion=id_accion
    )

    socios = Socios.objects.all().order_by(
        "apellidos",
        "nombres"
    )

    if request.method == "POST":
        id_socio = request.POST.get("id_socio")
        codigo = request.POST.get("codigo_accion", "").strip()
        fecha_registro = request.POST.get("fecha_registro") or date.today()
        estado = request.POST.get("estado", "ACTIVO")
        observacion = request.POST.get("observacion", "").strip()

        if Acciones.objects.filter(
            codigo_accion=codigo
        ).exclude(
            id_accion=id_accion
        ).exists():
            return render(request, "core/acciones/form.html", {
                "accion": accion,
                "socios": socios,
                "error": "El código de acción ya existe.",
                "usuario": request.usuario_actual,
            })

        accion.id_socio = get_object_or_404(
            Socios,
            id_socio=id_socio
        )
        accion.codigo_accion = codigo or None
        accion.fecha_registro = fecha_registro
        accion.estado = estado
        accion.observacion = observacion or None
        accion.save()

        return redirect("lista_acciones")

    return render(request, "core/acciones/form.html", {
        "accion": accion,
        "socios": socios,
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN])
def cambiar_estado_accion(request, id_accion):
    if request.method != "POST":
        return redirect("lista_acciones")

    accion = get_object_or_404(
        Acciones,
        id_accion=id_accion
    )

    if accion.estado == "ACTIVO":
        accion.estado = "INACTIVO"
    else:
        accion.estado = "ACTIVO"

    accion.save()

    return redirect("lista_acciones")



# ============================================================
# BLOQUE 2 - ASISTENCIAS
# ============================================================

@requiere_rol([ROL_ADMIN, ROL_LECTOR])
def lista_asistencias(request):

    asistencias = Asistencias.objects.select_related(
        "id_socio"
    ).order_by("-fecha", "-id_asistencia")

    socio_id = request.GET.get("socio", "")
    fecha = request.GET.get("fecha", "")
    tipo = request.GET.get("tipo", "").strip()

    if socio_id:
        asistencias = asistencias.filter(id_socio_id=socio_id)

    if fecha:
        asistencias = asistencias.filter(fecha=fecha)

    if tipo:
        asistencias = asistencias.filter(tipo__icontains=tipo)

    socios = Socios.objects.filter(
        estado="ACTIVO"
    ).order_by(
        "apellidos",
        "nombres"
    )

    return render(request, "core/asistencias/lista.html", {
        "asistencias": asistencias,
        "socios": socios,
        "usuario": request.usuario_actual,
        "socio_filtro": socio_id,
        "fecha_filtro": fecha,
        "tipo_filtro": tipo,
    })


@requiere_rol([ROL_ADMIN, ROL_LECTOR])
def nueva_asistencia(request):

    socios = Socios.objects.filter(
        estado="ACTIVO"
    ).order_by(
        "apellidos",
        "nombres"
    )

    if request.method == "POST":

        id_socio = request.POST.get("id_socio")
        fecha_asistencia = request.POST.get("fecha") or date.today()
        tipo = request.POST.get("tipo", "").strip()
        observacion = request.POST.get("observacion", "").strip()

        socio = get_object_or_404(
            Socios,
            id_socio=id_socio
        )

        Asistencias.objects.create(
            id_socio=socio,
            fecha=fecha_asistencia,
            tipo=tipo or None,
            observacion=observacion or None,
        )

        return redirect("lista_asistencias")

    return render(request, "core/asistencias/form.html", {
        "socios": socios,
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN, ROL_LECTOR])
def editar_asistencia(request, id_asistencia):

    asistencia = get_object_or_404(
        Asistencias,
        id_asistencia=id_asistencia
    )

    socios = Socios.objects.all().order_by(
        "apellidos",
        "nombres"
    )

    if request.method == "POST":

        asistencia.id_socio = get_object_or_404(
            Socios,
            id_socio=request.POST.get("id_socio")
        )

        asistencia.fecha = request.POST.get("fecha")
        asistencia.tipo = request.POST.get("tipo", "").strip() or None
        asistencia.observacion = request.POST.get(
            "observacion", ""
        ).strip() or None

        asistencia.save()

        return redirect("lista_asistencias")

    return render(request, "core/asistencias/form.html", {
        "asistencia": asistencia,
        "socios": socios,
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN, ROL_LECTOR])
def eliminar_asistencia(request, id_asistencia):

    if request.method == "POST":

        asistencia = get_object_or_404(
            Asistencias,
            id_asistencia=id_asistencia
        )

        asistencia.delete()

    return redirect("lista_asistencias")

# ============================================================
# BLOQUE 3 - COBRANZA DE APORTES
# ============================================================

def _agregar_detalle_deuda(
    socio,
    periodo,
    concepto,
    descripcion,
    importe
):

    deuda = Deudas.objects.filter(
        id_socio=socio,
        id_periodo=periodo
    ).first()

    if deuda and deuda.estado == "PAGADA":
        raise ValueError(
            "La deuda ya está pagada. No se puede agregar un nuevo cobro."
        )

    if deuda is None:

        deuda = Deudas.objects.create(
            id_socio=socio,
            id_periodo=periodo,
            subtotal=importe,
            recargo=Decimal("0.00"),
            total=importe,
            estado="PENDIENTE",
        )

    else:

        deuda.subtotal = (
            deuda.subtotal or Decimal("0.00")
        ) + importe

        deuda.total = (
            deuda.total or Decimal("0.00")
        ) + importe

        deuda.estado = "PENDIENTE"

        deuda.save()

    DetalleDeudas.objects.create(
        id_deuda=deuda,
        concepto=concepto,
        descripcion=descripcion,
        importe=importe,
    )

    return deuda


@requiere_rol([ROL_ADMIN, ROL_CAJERO])
def lista_aportes(request):

    detalles = DetalleDeudas.objects.filter(
        concepto="APORTE"
    ).select_related(
        "id_deuda__id_socio",
        "id_deuda__id_periodo"
    ).order_by("-id_detalle")

    return render(request, "core/cobranza/aportes.html", {
        "detalles": detalles,
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN, ROL_CAJERO])
def registrar_aporte(request):

    socios = Socios.objects.filter(
        estado="ACTIVO"
    ).order_by(
        "apellidos",
        "nombres"
    )

    periodos = Periodos.objects.order_by(
        "-gestion",
        "-mes"
    )

    error = None

    if request.method == "POST":

        try:

            socio = get_object_or_404(
                Socios,
                id_socio=request.POST.get("id_socio")
            )

            periodo = get_object_or_404(
                Periodos,
                id_periodo=request.POST.get("id_periodo")
            )

            importe = Decimal(
                request.POST.get("importe", "0")
            )

            descripcion = request.POST.get(
                "descripcion",
                "Aporte de socio"
            ).strip()

            if importe <= 0:
                raise ValueError(
                    "El importe debe ser mayor a cero."
                )

            with transaction.atomic():

                deuda = _agregar_detalle_deuda(
                    socio,
                    periodo,
                    "APORTE",
                    descripcion,
                    importe
                )

            return redirect(
                "detalle_cobranza",
                id_deuda=deuda.id_deuda
            )

        except (ValueError, TypeError, ArithmeticError) as e:

            error = str(e)

    return render(request, "core/cobranza/aporte_form.html", {
        "socios": socios,
        "periodos": periodos,
        "error": error,
        "usuario": request.usuario_actual,
    })
    
# ============================================================
# BLOQUE 4 - OTROS COBROS
# ============================================================

@requiere_rol([ROL_ADMIN, ROL_CAJERO])
def lista_otros_cobros(request):

    detalles = DetalleDeudas.objects.filter(
        concepto="OTRO"
    ).select_related(
        "id_deuda__id_socio",
        "id_deuda__id_periodo"
    ).order_by("-id_detalle")

    return render(request, "core/cobranza/otros.html", {
        "detalles": detalles,
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN, ROL_CAJERO])
def registrar_otro_cobro(request):

    socios = Socios.objects.filter(
        estado="ACTIVO"
    ).order_by(
        "apellidos",
        "nombres"
    )

    periodos = Periodos.objects.order_by(
        "-gestion",
        "-mes"
    )

    error = None

    if request.method == "POST":

        try:

            socio = get_object_or_404(
                Socios,
                id_socio=request.POST.get("id_socio")
            )

            periodo = get_object_or_404(
                Periodos,
                id_periodo=request.POST.get("id_periodo")
            )

            importe = Decimal(
                request.POST.get("importe", "0")
            )

            descripcion = request.POST.get(
                "descripcion",
                ""
            ).strip()

            if importe <= 0:
                raise ValueError(
                    "El importe debe ser mayor a cero."
                )

            if not descripcion:
                raise ValueError(
                    "Debe indicar la descripción del cobro."
                )

            with transaction.atomic():

                deuda = _agregar_detalle_deuda(
                    socio,
                    periodo,
                    "OTRO",
                    descripcion,
                    importe
                )

            return redirect(
                "detalle_cobranza",
                id_deuda=deuda.id_deuda
            )

        except (ValueError, TypeError, ArithmeticError) as e:

            error = str(e)

    return render(request, "core/cobranza/otro_form.html", {
        "socios": socios,
        "periodos": periodos,
        "error": error,
        "usuario": request.usuario_actual,
    })
    
# ============================================================
# BLOQUE 6 - INFORMES
# ============================================================

@requiere_rol([ROL_ADMIN, ROL_CAJERO, ROL_LECTOR])
def informes(request):

    total_socios = Socios.objects.filter(
        estado="ACTIVO"
    ).count()

    total_consumos = Consumos.objects.count()

    total_deudas = Deudas.objects.count()

    total_cajas = Cajas.objects.count()

    return render(request, "core/informes/index.html", {
        "total_socios": total_socios,
        "total_consumos": total_consumos,
        "total_deudas": total_deudas,
        "total_cajas": total_cajas,
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN, ROL_CAJERO])
def informe_cobranza(request):

    periodo_id = request.GET.get("periodo")

    periodos = Periodos.objects.order_by(
        "-gestion",
        "-mes"
    )

    deudas = Deudas.objects.select_related(
        "id_socio",
        "id_periodo"
    ).annotate(
        total_pagado=Sum("pagos__importe")
    ).order_by(
        "-id_periodo__gestion",
        "-id_periodo__mes",
        "id_socio__numero_socio"
    )

    if periodo_id:
        deudas = deudas.filter(
            id_periodo_id=periodo_id
        )

    total_deuda = Decimal("0.00")
    total_pagado = Decimal("0.00")

    for deuda in deudas:

        deuda.total_pagado = (
            deuda.total_pagado or Decimal("0.00")
        )

        deuda.saldo = max(
            deuda.total - deuda.total_pagado,
            Decimal("0.00")
        )

        total_deuda += deuda.total
        total_pagado += deuda.total_pagado

    return render(request, "core/informes/cobranza.html", {
        "deudas": deudas,
        "periodos": periodos,
        "periodo_id": periodo_id,
        "total_deuda": total_deuda,
        "total_pagado": total_pagado,
        "total_saldo": total_deuda - total_pagado,
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN, ROL_LECTOR])
def informe_consumos(request):

    periodo_id = request.GET.get("periodo")

    periodos = Periodos.objects.order_by(
        "-gestion",
        "-mes"
    )

    consumos = Consumos.objects.select_related(
            "id_lectura",
            "id_lectura__id_medidor",
            "id_lectura__id_medidor__id_socio",
            "id_lectura__id_periodo",
            "id_rango"
        ).order_by(
            "-id_lectura__id_periodo__gestion",
            "-id_lectura__id_periodo__mes",
            "id_lectura__id_medidor__id_socio__numero_socio"
    )

    if periodo_id:
        consumos = consumos.filter(
            id_lectura__id_periodo_id=periodo_id
        )

    total_consumo = Decimal("0.00")
    total_importe = Decimal("0.00")

    for consumo in consumos:

        total_consumo += (
            consumo.metros_cubicos or Decimal("0.00")
        )

        total_importe += (
            consumo.importe or Decimal("0.00")
        )

    return render(request, "core/informes/consumos.html", {
        "consumos": consumos,
        "periodos": periodos,
        "periodo_id": periodo_id,
        "total_consumo": total_consumo,
        "total_importe": total_importe,
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN, ROL_CAJERO])
def informe_caja(request):

    cajas = Cajas.objects.order_by("-fecha_apertura")

    for caja in cajas:

        movimientos = MovimientosCaja.objects.filter(
            id_caja=caja
        )

        ingresos = movimientos.filter(
            tipo="INGRESO"
        ).aggregate(
            total=Sum("importe")
        )["total"] or Decimal("0.00")

        egresos = movimientos.filter(
            tipo="EGRESO"
        ).aggregate(
            total=Sum("importe")
        )["total"] or Decimal("0.00")

        caja.total_ingresos = ingresos
        caja.total_egresos = egresos
        caja.saldo_calculado = (
            caja.saldo_inicial +
            ingresos -
            egresos
        )

    return render(request, "core/informes/caja.html", {
        "cajas": cajas,
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN, ROL_CAJERO])
def exportar_cobranza_csv(request):

    response = HttpResponse(
        content_type="text/csv; charset=utf-8"
    )

    response["Content-Disposition"] = (
        'attachment; filename="reporte_cobranza.csv"'
    )

    writer = csv.writer(response)

    writer.writerow([
        "Socio",
        "Periodo",
        "Total deuda",
        "Pagado",
        "Saldo",
        "Estado",
    ])

    deudas = Deudas.objects.select_related(
        "id_socio",
        "id_periodo"
    ).annotate(
        total_pagado=Sum("pagos__importe")
    )

    for deuda in deudas:

        pagado = (
            deuda.total_pagado or Decimal("0.00")
        )

        saldo = max(
            deuda.total - pagado,
            Decimal("0.00")
        )

        writer.writerow([
            deuda.id_socio.numero_socio,
            f"{deuda.id_periodo.mes}/{deuda.id_periodo.gestion}",
            deuda.total,
            pagado,
            saldo,
            deuda.estado,
        ])

    return response

# ============================================================
# BLOQUE 7 - CONFIGURACIÓN
# ============================================================

@requiere_rol([ROL_ADMIN])
def configuracion(request):

    general = ConfiguracionGeneral.objects.order_by(
        "id_configuracion"
    ).first()

    cobranza = ConfiguracionCobranza.objects.order_by(
        "id_configuracion"
    ).first()

    total_tarifas = Tarifas.objects.count()

    return render(request, "core/configuracion/index.html", {
        "general": general,
        "cobranza": cobranza,
        "total_tarifas": total_tarifas,
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN])
def configuracion_general(request):

    configuracion = ConfiguracionGeneral.objects.order_by(
        "id_configuracion"
    ).first()

    if request.method == "POST":

        if configuracion is None:

            configuracion = ConfiguracionGeneral()

        configuracion.nombre_cooperativa = request.POST.get(
            "nombre_cooperativa",
            ""
        ).strip()

        configuracion.direccion = request.POST.get(
            "direccion",
            ""
        ).strip() or None

        configuracion.telefono = request.POST.get(
            "telefono",
            ""
        ).strip() or None

        configuracion.correo = request.POST.get(
            "correo",
            ""
        ).strip() or None

        configuracion.nit = request.POST.get(
            "nit",
            ""
        ).strip() or None

        configuracion.logo = request.POST.get(
            "logo",
            ""
        ).strip() or None

        configuracion.fecha_actualizacion = timezone.now()

        configuracion.save()

        return redirect("configuracion")

    return render(request, "core/configuracion/general.html", {
        "configuracion": configuracion,
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN])
def configuracion_cobranza(request):

    configuracion = ConfiguracionCobranza.objects.order_by(
        "id_configuracion"
    ).first()

    if request.method == "POST":

        if configuracion is None:

            configuracion = ConfiguracionCobranza()

        configuracion.dia_limite_pago = int(
            request.POST.get("dia_limite_pago", "10")
        )

        configuracion.recargo_mora = Decimal(
            request.POST.get("recargo_mora", "0")
        )

        configuracion.moneda = request.POST.get(
            "moneda",
            "BOB"
        ).strip()

        configuracion.fecha_actualizacion = timezone.now()

        configuracion.save()

        return redirect("configuracion")

    return render(request, "core/configuracion/cobranza.html", {
        "configuracion": configuracion,
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN])
def lista_tarifas(request):

    tarifas = Tarifas.objects.order_by(
        "codigo",
        "nombre"
    )

    return render(request, "core/configuracion/tarifas.html", {
        "tarifas": tarifas,
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN])
def nueva_tarifa(request):

    if request.method == "POST":

        codigo = request.POST.get("codigo", "").strip()
        nombre = request.POST.get("nombre", "").strip()
        descripcion = request.POST.get(
            "descripcion",
            ""
        ).strip()

        consumo_maximo = request.POST.get(
            "consumo_maximo"
        )

        estado = request.POST.get(
            "estado",
            "ACTIVO"
        )

        if not codigo or not nombre:
            return render(request, "core/configuracion/tarifa_form.html", {
                "error": "Código y nombre son obligatorios.",
                "usuario": request.usuario_actual,
            })

        if Tarifas.objects.filter(
            codigo=codigo
        ).exists():

            return render(request, "core/configuracion/tarifa_form.html", {
                "error": "El código de tarifa ya existe.",
                "usuario": request.usuario_actual,
            })

        tarifa = Tarifas(
            codigo=codigo,
            nombre=nombre,
            descripcion=descripcion or None,
            consumo_maximo=(
                Decimal(consumo_maximo)
                if consumo_maximo
                else None
            ),
            estado=estado,
        )

        tarifa.save()

        return redirect("lista_tarifas")

    return render(request, "core/configuracion/tarifa_form.html", {
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN])
def editar_tarifa(request, id_tarifa):

    tarifa = get_object_or_404(
        Tarifas,
        id_tarifa=id_tarifa
    )

    if request.method == "POST":

        tarifa.codigo = request.POST.get(
            "codigo",
            ""
        ).strip()

        tarifa.nombre = request.POST.get(
            "nombre",
            ""
        ).strip()

        tarifa.descripcion = request.POST.get(
            "descripcion",
            ""
        ).strip() or None

        consumo_maximo = request.POST.get(
            "consumo_maximo"
        )

        tarifa.consumo_maximo = (
            Decimal(consumo_maximo)
            if consumo_maximo
            else None
        )

        tarifa.estado = request.POST.get(
            "estado",
            "ACTIVO"
        )

        tarifa.save()

        return redirect("lista_tarifas")

    return render(request, "core/configuracion/tarifa_form.html", {
        "tarifa": tarifa,
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN])
def cambiar_estado_tarifa(request, id_tarifa):

    if request.method == "POST":

        tarifa = get_object_or_404(
            Tarifas,
            id_tarifa=id_tarifa
        )

        tarifa.estado = (
            "INACTIVO"
            if tarifa.estado == "ACTIVO"
            else "ACTIVO"
        )

        tarifa.save()

    return redirect("lista_tarifas")


@requiere_rol([ROL_ADMIN])
def lista_rangos_tarifa(request, id_tarifa):

    tarifa = get_object_or_404(
        Tarifas,
        id_tarifa=id_tarifa
    )

    rangos = RangosTarifa.objects.filter(
        id_tarifa=tarifa
    ).order_by(
        "consumo_desde"
    )

    return render(request, "core/configuracion/rangos.html", {
        "tarifa": tarifa,
        "rangos": rangos,
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN])
def nuevo_rango_tarifa(request, id_tarifa):

    tarifa = get_object_or_404(
        Tarifas,
        id_tarifa=id_tarifa
    )

    if request.method == "POST":

        desde = Decimal(
            request.POST.get("consumo_desde", "0")
        )

        hasta = Decimal(
            request.POST.get("consumo_hasta", "0")
        )

        precio_base = Decimal(
            request.POST.get("precio_base", "0")
        )

        precio_excedente = Decimal(
            request.POST.get("precio_excedente", "0")
        )

        if hasta < desde:

            return render(
                request,
                "core/configuracion/rango_form.html",
                {
                    "tarifa": tarifa,
                    "error": "El consumo hasta no puede ser menor que desde.",
                    "usuario": request.usuario_actual,
                }
            )

        RangosTarifa.objects.create(
            id_tarifa=tarifa,
            consumo_desde=desde,
            consumo_hasta=hasta,
            precio_base=precio_base,
            precio_excedente=precio_excedente,
            estado=request.POST.get(
                "estado",
                "ACTIVO"
            ),
        )

        return redirect(
            "lista_rangos_tarifa",
            id_tarifa=tarifa.id_tarifa
        )

    return render(request, "core/configuracion/rango_form.html", {
        "tarifa": tarifa,
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN])
def editar_rango_tarifa(request, id_rango):

    rango = get_object_or_404(
        RangosTarifa,
        id_rango=id_rango
    )

    if request.method == "POST":

        rango.consumo_desde = Decimal(
            request.POST.get("consumo_desde", "0")
        )

        rango.consumo_hasta = Decimal(
            request.POST.get("consumo_hasta", "0")
        )

        rango.precio_base = Decimal(
            request.POST.get("precio_base", "0")
        )

        rango.precio_excedente = Decimal(
            request.POST.get("precio_excedente", "0")
        )

        rango.estado = request.POST.get(
            "estado",
            "ACTIVO"
        )

        rango.save()

        return redirect(
            "lista_rangos_tarifa",
            id_tarifa=rango.id_tarifa.id_tarifa
        )

    return render(request, "core/configuracion/rango_form.html", {
        "rango": rango,
        "tarifa": rango.id_tarifa,
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN])
def cambiar_estado_rango_tarifa(request, id_rango):

    if request.method == "POST":

        rango = get_object_or_404(
            RangosTarifa,
            id_rango=id_rango
        )

        rango.estado = (
            "INACTIVO"
            if rango.estado == "ACTIVO"
            else "ACTIVO"
        )

        rango.save()

    return redirect(
        "lista_rangos_tarifa",
        id_tarifa=rango.id_tarifa.id_tarifa
    )
    
    
# ============================================================
# BLOQUE 8 - UTILIDADES
# ============================================================

@requiere_rol([ROL_ADMIN])
def utilidades(request):

    return render(request, "core/utilidades/index.html", {
        "total_socios": Socios.objects.count(),
        "total_medidores": Medidores.objects.count(),
        "total_lecturas": Lecturas.objects.count(),
        "total_consumos": Consumos.objects.count(),
        "total_deudas": Deudas.objects.count(),
        "total_pagos": Pagos.objects.count(),
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN])
def diagnostico_datos(request):

    socios_sin_medidor = Socios.objects.filter(
        estado="ACTIVO"
    ).exclude(
        id_socio__in=Medidores.objects.values("id_socio")
    )

    deudas_sin_detalle = Deudas.objects.exclude(
        id_deuda__in=DetalleDeudas.objects.values("id_deuda")
    )

    consumos_sin_rango = Consumos.objects.filter(
        id_rango__isnull=True
    )

    pagos_sin_caja = Pagos.objects.filter(
        id_caja__isnull=True
    )

    return render(request, "core/utilidades/diagnostico.html", {
        "socios_sin_medidor": socios_sin_medidor,
        "deudas_sin_detalle": deudas_sin_detalle,
        "consumos_sin_rango": consumos_sin_rango,
        "pagos_sin_caja": pagos_sin_caja,
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN])
def sincronizar_estados_deudas(request):

    if request.method == "POST":

        deudas = Deudas.objects.all()

        for deuda in deudas:

            total_pagado = Pagos.objects.filter(
                id_deuda=deuda
            ).aggregate(
                total=Sum("importe")
            )["total"] or Decimal("0.00")

            if total_pagado >= deuda.total:
                deuda.estado = "PAGADA"
            else:
                deuda.estado = "PENDIENTE"

            deuda.save()

    return redirect("diagnostico_datos")


@requiere_rol([ROL_ADMIN])
def recalcular_saldos_cajas(request):

    if request.method == "POST":

        cajas = Cajas.objects.all()

        for caja in cajas:

            movimientos = MovimientosCaja.objects.filter(
                id_caja=caja
            )

            ingresos = movimientos.filter(
                tipo="INGRESO"
            ).aggregate(
                total=Sum("importe")
            )["total"] or Decimal("0.00")

            egresos = movimientos.filter(
                tipo="EGRESO"
            ).aggregate(
                total=Sum("importe")
            )["total"] or Decimal("0.00")

            caja.saldo_final = (
                caja.saldo_inicial +
                ingresos -
                egresos
            )

            caja.save()

    return redirect("utilidades")


# ============================================================
# BLOQUE 9 - USUARIOS
# ============================================================

@requiere_rol([ROL_ADMIN])
def nuevo_usuario(request):

    roles = Roles.objects.filter(
        estado="ACTIVO"
    ).order_by("nombre")

    if request.method == "POST":

        nombre_usuario = request.POST.get(
            "nombre_usuario",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        nombre_completo = request.POST.get(
            "nombre_completo",
            ""
        ).strip()

        correo = request.POST.get(
            "correo",
            ""
        ).strip() or None

        id_rol = request.POST.get("id_rol")

        if not nombre_usuario or not password:
            return render(request, "core/usuarios/form.html", {
                "roles": roles,
                "error": "Usuario y contraseña son obligatorios.",
                "usuario": request.usuario_actual,
            })

        if Usuarios.objects.filter(
            nombre_usuario=nombre_usuario
        ).exists():

            return render(request, "core/usuarios/form.html", {
                "roles": roles,
                "error": "El nombre de usuario ya existe.",
                "usuario": request.usuario_actual,
            })

        Usuarios.objects.create(
            nombre_usuario=nombre_usuario,
            password=password,
            nombre_completo=nombre_completo,
            correo=correo,
            id_rol_id=id_rol,
            estado="ACTIVO",
            fecha_creacion=timezone.now(),
        )

        return redirect("lista_usuarios")

    return render(request, "core/usuarios/form.html", {
        "roles": roles,
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN])
def editar_usuario(request, id_usuario):

    usuario_editar = get_object_or_404(
        Usuarios,
        id_usuario=id_usuario
    )

    roles = Roles.objects.filter(
        estado="ACTIVO"
    ).order_by("nombre")

    if request.method == "POST":

        usuario_editar.nombre_usuario = request.POST.get(
            "nombre_usuario",
            ""
        ).strip()

        usuario_editar.nombre_completo = request.POST.get(
            "nombre_completo",
            ""
        ).strip()

        usuario_editar.correo = request.POST.get(
            "correo",
            ""
        ).strip() or None

        usuario_editar.id_rol_id = request.POST.get(
            "id_rol"
        )

        nueva_password = request.POST.get(
            "password",
            ""
        )

        if nueva_password:
            usuario_editar.password = nueva_password

        usuario_editar.estado = request.POST.get(
            "estado",
            usuario_editar.estado
        )

        usuario_editar.save()

        return redirect("lista_usuarios")

    return render(request, "core/usuarios/form.html", {
        "usuario_editar": usuario_editar,
        "roles": roles,
        "usuario": request.usuario_actual,
    })


@requiere_rol([ROL_ADMIN])
def cambiar_estado_usuario(request, id_usuario):

    if request.method != "POST":
        return redirect("lista_usuarios")

    usuario_editar = get_object_or_404(
        Usuarios,
        id_usuario=id_usuario
    )

    # Evita que el administrador se desactive a sí mismo.
    if usuario_editar.id_usuario == request.usuario_actual.id_usuario:
        return redirect("lista_usuarios")

    if usuario_editar.estado == "ACTIVO":
        usuario_editar.estado = "INACTIVO"
    else:
        usuario_editar.estado = "ACTIVO"

    usuario_editar.save()

    return redirect("lista_usuarios")