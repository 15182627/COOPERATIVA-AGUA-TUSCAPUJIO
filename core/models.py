# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
#models.py
from django.db import models


class Roles(models.Model):
    id_rol = models.AutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=200, blank=True, null=True)
    estado = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'roles'


class Usuarios(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    id_rol = models.ForeignKey(Roles, models.DO_NOTHING, db_column='id_rol')
    nombre_usuario = models.CharField(unique=True, max_length=50)
    password = models.CharField(max_length=255)
    nombre_completo = models.CharField(max_length=150)
    correo = models.CharField(max_length=150, blank=True, null=True)
    estado = models.CharField(max_length=20)
    fecha_creacion = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'usuarios'


class ConfiguracionGeneral(models.Model):
    id_configuracion = models.AutoField(primary_key=True)
    nombre_cooperativa = models.CharField(max_length=150)
    direccion = models.CharField(max_length=250, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    correo = models.CharField(max_length=150, blank=True, null=True)
    nit = models.CharField(max_length=30, blank=True, null=True)
    logo = models.CharField(max_length=255, blank=True, null=True)
    fecha_actualizacion = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'configuracion_general'


class ConfiguracionCobranza(models.Model):
    id_configuracion = models.AutoField(primary_key=True)
    dia_limite_pago = models.IntegerField()
    recargo_mora = models.DecimalField(max_digits=10, decimal_places=2)
    moneda = models.CharField(max_length=10)
    fecha_actualizacion = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'configuracion_cobranza'


class Socios(models.Model):
    id_socio = models.AutoField(primary_key=True)
    numero_socio = models.CharField(unique=True, max_length=30)
    ci = models.CharField(unique=True, max_length=30, blank=True, null=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    direccion = models.CharField(max_length=250, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    correo = models.CharField(max_length=150, blank=True, null=True)
    fecha_afiliacion = models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=20)
    observacion = models.CharField(max_length=300, blank=True, null=True)
    id_tarifa = models.ForeignKey('Tarifas', models.DO_NOTHING, db_column='id_tarifa', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'socios'


class Medidores(models.Model):
    id_medidor = models.AutoField(primary_key=True)
    id_socio = models.ForeignKey(Socios, models.DO_NOTHING, db_column='id_socio')
    numero_medidor = models.CharField(unique=True, max_length=50)
    fecha_instalacion = models.DateField(blank=True, null=True)
    lectura_inicial = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20)
    observacion = models.CharField(max_length=300, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'medidores'


class Acciones(models.Model):
    id_accion = models.AutoField(primary_key=True)
    id_socio = models.ForeignKey(Socios, models.DO_NOTHING, db_column='id_socio')
    codigo_accion = models.CharField(max_length=50, blank=True, null=True)
    fecha_registro = models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=20)
    observacion = models.CharField(max_length=300, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'acciones'


class Periodos(models.Model):
    id_periodo = models.AutoField(primary_key=True)
    mes = models.IntegerField()
    gestion = models.IntegerField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    fecha_limite_pago = models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=30)
    observacion = models.CharField(max_length=300, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'periodos'
        unique_together = (('mes', 'gestion'),)


class Lecturas(models.Model):
    id_lectura = models.AutoField(primary_key=True)
    id_medidor = models.ForeignKey(Medidores, models.DO_NOTHING, db_column='id_medidor')
    id_periodo = models.ForeignKey(Periodos, models.DO_NOTHING, db_column='id_periodo')
    lectura_anterior = models.DecimalField(max_digits=12, decimal_places=2)
    lectura_actual = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    fecha_lectura = models.DateTimeField(blank=True, null=True)
    id_usuario = models.ForeignKey(Usuarios, models.DO_NOTHING, db_column='id_usuario', blank=True, null=True)
    estado = models.CharField(max_length=20)
    observacion = models.CharField(max_length=300, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'lecturas'
        unique_together = (('id_medidor', 'id_periodo'),)


class Tarifas(models.Model):
    id_tarifa = models.AutoField(primary_key=True)
    codigo = models.CharField(unique=True, max_length=30)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=250, blank=True, null=True)
    consumo_maximo = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    estado = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'tarifas'


class RangosTarifa(models.Model):
    id_rango = models.AutoField(primary_key=True)
    id_tarifa = models.ForeignKey(Tarifas, models.DO_NOTHING, db_column='id_tarifa')
    consumo_desde = models.DecimalField(max_digits=12, decimal_places=2)
    consumo_hasta = models.DecimalField(max_digits=12, decimal_places=2)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    precio_excedente = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'rangos_tarifa'


class Consumos(models.Model):
    id_consumo = models.AutoField(primary_key=True)
    id_lectura = models.OneToOneField(Lecturas, models.DO_NOTHING, db_column='id_lectura')
    id_rango = models.ForeignKey(RangosTarifa, models.DO_NOTHING, db_column='id_rango', blank=True, null=True)
    metros_cubicos = models.DecimalField(max_digits=12, decimal_places=2)
    importe = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_calculo = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'consumos'


class Deudas(models.Model):
    id_deuda = models.AutoField(primary_key=True)
    id_socio = models.ForeignKey(Socios, models.DO_NOTHING, db_column='id_socio')
    id_periodo = models.ForeignKey(Periodos, models.DO_NOTHING, db_column='id_periodo')
    fecha_generacion = models.DateField()
    fecha_vencimiento = models.DateField(blank=True, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    recargo = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'deudas'
        unique_together = (('id_socio', 'id_periodo'),)


class DetalleDeudas(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    id_deuda = models.ForeignKey(Deudas, models.CASCADE, db_column='id_deuda')
    concepto = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=250, blank=True, null=True)
    importe = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'detalle_deudas'


class Cajas(models.Model):
    id_caja = models.AutoField(primary_key=True)
    fecha_apertura = models.DateField()
    fecha_cierre = models.DateField(blank=True, null=True)
    saldo_inicial = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_final = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    estado = models.CharField(max_length=20)
    id_usuario_apertura = models.ForeignKey(Usuarios, models.DO_NOTHING, db_column='id_usuario_apertura')
    id_usuario_cierre = models.ForeignKey(Usuarios, models.DO_NOTHING, db_column='id_usuario_cierre', related_name='cajas_id_usuario_cierre_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cajas'


class Pagos(models.Model):
    id_pago = models.AutoField(primary_key=True)
    id_deuda = models.ForeignKey(Deudas, models.DO_NOTHING, db_column='id_deuda')
    id_usuario = models.ForeignKey(Usuarios, models.DO_NOTHING, db_column='id_usuario')
    id_caja = models.ForeignKey(Cajas, models.DO_NOTHING, db_column='id_caja', blank=True, null=True)
    fecha_pago = models.DateTimeField()
    importe = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=30)
    observacion = models.CharField(max_length=300, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pagos'


class MovimientosCaja(models.Model):
    id_movimiento = models.AutoField(primary_key=True)
    id_caja = models.ForeignKey(Cajas, models.DO_NOTHING, db_column='id_caja')
    id_pago = models.ForeignKey(Pagos, models.DO_NOTHING, db_column='id_pago', blank=True, null=True)
    id_usuario = models.ForeignKey(Usuarios, models.DO_NOTHING, db_column='id_usuario')
    fecha_movimiento = models.DateTimeField()
    tipo = models.CharField(max_length=20)
    concepto = models.CharField(max_length=100)
    importe = models.DecimalField(max_digits=10, decimal_places=2)
    observacion = models.CharField(max_length=300, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'movimientos_caja'


class Asistencias(models.Model):
    id_asistencia = models.AutoField(primary_key=True)
    id_socio = models.ForeignKey(Socios, models.DO_NOTHING, db_column='id_socio')
    fecha = models.DateField()
    tipo = models.CharField(max_length=50, blank=True, null=True)
    observacion = models.CharField(max_length=300, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'asistencias'
