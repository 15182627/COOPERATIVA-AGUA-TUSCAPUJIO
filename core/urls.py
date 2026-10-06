#urls.py
from django.urls import path

from .views import (
    prueba_socios,
    inicio,

    lista_socios,
    nuevo_socio,
    ver_socio,
    editar_socio,
    cambiar_estado_socio,

    lista_periodos,
    nuevo_periodo,
    cambiar_estado_periodo,

    generar_planilla,
    planilla_lecturas,
    registrar_lectura,
    editar_lectura,
    lista_consumos,
    lista_deudas,
    generar_deudas,
    lista_cobranza,
    detalle_cobranza,
    
    
    caja_principal,
    abrir_caja,
    caja_movimientos,
    registrar_egreso,
    cerrar_caja,
    historial_cajas,
    
    login_view,
    logout_view,
    acceso_denegado,
    
    lista_usuarios,
    
    lista_acciones,
    nueva_accion,
    editar_accion,
    cambiar_estado_accion,

    lista_asistencias,
    nueva_asistencia,
    editar_asistencia,
    eliminar_asistencia,

    lista_aportes,
    registrar_aporte,

    lista_otros_cobros,
    registrar_otro_cobro,

    informes,
    informe_cobranza,
    informe_consumos,
    informe_caja,
    exportar_cobranza_csv,

    configuracion,
    configuracion_general,
    configuracion_cobranza,
    lista_tarifas,
    nueva_tarifa,
    editar_tarifa,
    cambiar_estado_tarifa,
    lista_rangos_tarifa,
    nuevo_rango_tarifa,
    editar_rango_tarifa,
    cambiar_estado_rango_tarifa,

    utilidades,
    diagnostico_datos,
    sincronizar_estados_deudas,
    recalcular_saldos_cajas,

    nuevo_usuario,
    editar_usuario,
    cambiar_estado_usuario,
    
)


urlpatterns = [

    # =====================================================
    # INICIO
    # =====================================================

    path(
        "",
        inicio,
        name="inicio"
    ),


    # =====================================================
    # PRUEBA
    # =====================================================

    path(
        "prueba-socios/",
        prueba_socios,
        name="prueba_socios"
    ),
    
    
    # =====================================================
    # LOGIN
    # =====================================================
    
    path(
        "login/",
        login_view,
        name="login"
    ),
    path(
        "logout/",
         logout_view,
         name="logout"
    ),
    path(
        "acceso-denegado/",
        acceso_denegado,
        name="acceso_denegado"
    ),


    # =====================================================
    # SOCIOS
    # =====================================================

    path(
        "socios/",
        lista_socios,
        name="lista_socios"
    ),

    path(
        "socios/nuevo/",
        nuevo_socio,
        name="nuevo_socio"
    ),

    path(
        "socios/<int:id_socio>/",
        ver_socio,
        name="ver_socio"
    ),

    path(
        "socios/<int:id_socio>/editar/",
        editar_socio,
        name="editar_socio"
    ),

    path(
        "socios/<int:id_socio>/estado/",
        cambiar_estado_socio,
        name="cambiar_estado_socio"
    ),


    # =====================================================
    # PERIODOS
    # =====================================================

    path(
        "lecturas/periodos/",
        lista_periodos,
        name="lista_periodos"
    ),

    path(
        "lecturas/periodos/nuevo/",
        nuevo_periodo,
        name="nuevo_periodo"
    ),

    path(
        "lecturas/periodos/<int:id_periodo>/estado/",
        cambiar_estado_periodo,
        name="cambiar_estado_periodo"
    ),


    # =====================================================
    # PLANILLA
    # =====================================================

    path(
        "lecturas/periodos/<int:id_periodo>/generar/",
        generar_planilla,
        name="generar_planilla"
    ),

    path(
        "lecturas/periodos/<int:id_periodo>/",
        planilla_lecturas,
        name="planilla_lecturas"
    ),


    # =====================================================
    # LECTURAS
    # =====================================================

    path(
        "lecturas/<int:id_lectura>/registrar/",
        registrar_lectura,
        name="registrar_lectura"
    ),

    path(
        "lecturas/<int:id_lectura>/editar/",
        editar_lectura,
        name="editar_lectura"
    ),
    
    
    path(
        "cobranza/consumo/", 
        lista_consumos, 
        name="lista_consumos"
    ),
    path(
        "cobranza/deudas/",
        lista_deudas,
        name="lista_deudas"
    ),
    
    path(
        "cobranza/deudas/<int:id_periodo>/generar/",
        generar_deudas,
        name="generar_deudas"
    ),
    
    path(
        "cobranza/",
        lista_cobranza,
        name="lista_cobranza"
    ),

    path(
        "cobranza/deuda/<int:id_deuda>/",
        detalle_cobranza,
        name="detalle_cobranza"
    ),
    
    
        # =====================================================
    # CAJA
    # =====================================================

    path(
        "caja/",
        caja_principal,
        name="caja_principal"
    ),

    path(
        "caja/abrir/",
        abrir_caja,
        name="abrir_caja"
    ),

    path(
        "caja/movimientos/",
        caja_movimientos,
        name="caja_movimientos"
    ),

    path(
        "caja/egreso/",
        registrar_egreso,
        name="registrar_egreso"
    ),

    path(
        "caja/cerrar/",
        cerrar_caja,
        name="cerrar_caja"
    ),
    
    path(
        "caja/historial/",
        historial_cajas,
        name="historial_cajas"
    ),
    
    path(
        "usuarios/",
        lista_usuarios,
        name="lista_usuarios"
    ),
    
    
        # ========================================================
    # ACCIONES
    # ========================================================

    path(
        "acciones/",
        lista_acciones,
        name="lista_acciones"
    ),

    path(
        "acciones/nueva/",
        nueva_accion,
        name="nueva_accion"
    ),

    path(
        "acciones/<int:id_accion>/editar/",
        editar_accion,
        name="editar_accion"
    ),

    path(
        "acciones/<int:id_accion>/estado/",
        cambiar_estado_accion,
        name="cambiar_estado_accion"
    ),


    # ========================================================
    # ASISTENCIAS
    # ========================================================

    path(
        "asistencias/",
        lista_asistencias,
        name="lista_asistencias"
    ),

    path(
        "asistencias/nueva/",
        nueva_asistencia,
        name="nueva_asistencia"
    ),

    path(
        "asistencias/<int:id_asistencia>/editar/",
        editar_asistencia,
        name="editar_asistencia"
    ),

    path(
        "asistencias/<int:id_asistencia>/eliminar/",
        eliminar_asistencia,
        name="eliminar_asistencia"
    ),


    # ========================================================
    # APORTES
    # ========================================================

    path(
        "cobranza/aportes/",
        lista_aportes,
        name="lista_aportes"
    ),

    path(
        "cobranza/aportes/nuevo/",
        registrar_aporte,
        name="registrar_aporte"
    ),


    # ========================================================
    # OTROS COBROS
    # ========================================================

    path(
        "cobranza/otros/",
        lista_otros_cobros,
        name="lista_otros_cobros"
    ),

    path(
        "cobranza/otros/nuevo/",
        registrar_otro_cobro,
        name="registrar_otro_cobro"
    ),


    # ========================================================
    # INFORMES
    # ========================================================

    path(
        "informes/",
        informes,
        name="informes"
    ),

    path(
        "informes/cobranza/",
        informe_cobranza,
        name="informe_cobranza"
    ),

    path(
        "informes/consumos/",
        informe_consumos,
        name="informe_consumos"
    ),

    path(
        "informes/caja/",
        informe_caja,
        name="informe_caja"
    ),

    path(
        "informes/cobranza/csv/",
        exportar_cobranza_csv,
        name="exportar_cobranza_csv"
    ),


    # ========================================================
    # CONFIGURACIÓN
    # ========================================================

    path(
        "configuracion/",
        configuracion,
        name="configuracion"
    ),

    path(
        "configuracion/general/",
        configuracion_general,
        name="configuracion_general"
    ),

    path(
        "configuracion/cobranza/",
        configuracion_cobranza,
        name="configuracion_cobranza"
    ),

    path(
        "configuracion/tarifas/",
        lista_tarifas,
        name="lista_tarifas"
    ),

    path(
        "configuracion/tarifas/nueva/",
        nueva_tarifa,
        name="nueva_tarifa"
    ),

    path(
        "configuracion/tarifas/<int:id_tarifa>/editar/",
        editar_tarifa,
        name="editar_tarifa"
    ),

    path(
        "configuracion/tarifas/<int:id_tarifa>/estado/",
        cambiar_estado_tarifa,
        name="cambiar_estado_tarifa"
    ),

    path(
        "configuracion/tarifas/<int:id_tarifa>/rangos/",
        lista_rangos_tarifa,
        name="lista_rangos_tarifa"
    ),

    path(
        "configuracion/tarifas/<int:id_tarifa>/rangos/nuevo/",
        nuevo_rango_tarifa,
        name="nuevo_rango_tarifa"
    ),

    path(
        "configuracion/rangos/<int:id_rango>/editar/",
        editar_rango_tarifa,
        name="editar_rango_tarifa"
    ),

    path(
        "configuracion/rangos/<int:id_rango>/estado/",
        cambiar_estado_rango_tarifa,
        name="cambiar_estado_rango_tarifa"
    ),


    # ========================================================
    # UTILIDADES
    # ========================================================

    path(
        "utilidades/",
        utilidades,
        name="utilidades"
    ),

    path(
        "utilidades/diagnostico/",
        diagnostico_datos,
        name="diagnostico_datos"
    ),

    path(
        "utilidades/deudas/sincronizar/",
        sincronizar_estados_deudas,
        name="sincronizar_estados_deudas"
    ),

    path(
        "utilidades/cajas/recalcular/",
        recalcular_saldos_cajas,
        name="recalcular_saldos_cajas"
    ),


    # ========================================================
    # USUARIOS
    # ========================================================

    path(
        "usuarios/nuevo/",
        nuevo_usuario,
        name="nuevo_usuario"
    ),

    path(
        "usuarios/<int:id_usuario>/editar/",
        editar_usuario,
        name="editar_usuario"
    ),

    path(
        "usuarios/<int:id_usuario>/estado/",
        cambiar_estado_usuario,
        name="cambiar_estado_usuario"
    ), 
    
    
]
