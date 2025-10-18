from django.db import models
from django.contrib.auth.models import User
from apps.tienda.models import Producto


class Proveedor(models.Model):
    """Proveedores de productos de acero"""
    nombre = models.CharField(max_length=200)
    razon_social = models.CharField(max_length=200)
    rut = models.CharField(max_length=12, unique=True)
    
    # Contacto
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    telefono_alternativo = models.CharField(max_length=20, blank=True)
    
    # Dirección
    direccion = models.TextField()
    comuna = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    
    # Información comercial
    contacto_principal = models.CharField(max_length=100, blank=True)
    plazo_entrega_dias = models.PositiveIntegerField(default=7)
    condiciones_pago = models.TextField(blank=True)
    
    # Metadatos
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    notas = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class MovimientoInventario(models.Model):
    """Movimientos de inventario (entradas y salidas)"""
    TIPO_MOVIMIENTO = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
        ('transferencia', 'Transferencia'),
        ('devolucion', 'Devolución'),
    ]
    
    MOTIVO_ENTRADA = [
        ('compra', 'Compra'),
        ('devolucion_cliente', 'Devolución de Cliente'),
        ('ajuste_inventario', 'Ajuste de Inventario'),
        ('transferencia_entrada', 'Transferencia Entrada'),
        ('inventario_inicial', 'Inventario Inicial'),
    ]
    
    MOTIVO_SALIDA = [
        ('venta', 'Venta'),
        ('devolucion_proveedor', 'Devolución a Proveedor'),
        ('ajuste_inventario', 'Ajuste de Inventario'),
        ('transferencia_salida', 'Transferencia Salida'),
        ('perdida', 'Pérdida/Deterioro'),
        ('muestra', 'Muestra'),
    ]
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    tipo_movimiento = models.CharField(max_length=20, choices=TIPO_MOVIMIENTO)
    motivo_entrada = models.CharField(max_length=30, choices=MOTIVO_ENTRADA, blank=True)
    motivo_salida = models.CharField(max_length=30, choices=MOTIVO_SALIDA, blank=True)
    
    cantidad = models.PositiveIntegerField()
    cantidad_anterior = models.PositiveIntegerField()
    cantidad_nueva = models.PositiveIntegerField()
    
    # Referencias
    numero_documento = models.CharField(max_length=50, blank=True)  # Número de factura, pedido, etc.
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Usuario que registra el movimiento
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    
    # Observaciones
    observaciones = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Movimiento de Inventario'
        verbose_name_plural = 'Movimientos de Inventario'
        ordering = ['-fecha_movimiento']
    
    def __str__(self):
        return f"{self.producto} - {self.get_tipo_movimiento_display()} - {self.cantidad} unidades"


class Compra(models.Model):
    """Compras de productos a proveedores"""
    ESTADOS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('ordenada', 'Ordenada'),
        ('parcialmente_recibida', 'Parcialmente Recibida'),
        ('recibida', 'Recibida'),
        ('facturada', 'Facturada'),
        ('pagada', 'Pagada'),
        ('cancelada', 'Cancelada'),
    ]
    
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    numero_orden = models.CharField(max_length=20, unique=True)
    fecha_orden = models.DateTimeField(auto_now_add=True)
    fecha_esperada = models.DateField()
    fecha_recibida = models.DateField(null=True, blank=True)
    
    estado = models.CharField(max_length=25, choices=ESTADOS_CHOICES, default='pendiente')
    
    # Totales
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Usuario que crea la orden
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Observaciones
    observaciones = models.TextField(blank=True)
    notas_internas = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Compra'
        verbose_name_plural = 'Compras'
        ordering = ['-fecha_orden']
    
    def __str__(self):
        return f"Orden {self.numero_orden} - {self.proveedor}"
    
    def save(self, *args, **kwargs):
        if not self.numero_orden:
            # Generar número de orden automáticamente
            import datetime
            today = datetime.date.today()
            last_orden = Compra.objects.filter(fecha_orden__date=today).count()
            self.numero_orden = f"ORD{today.strftime('%Y%m%d')}{last_orden + 1:03d}"
        super().save(*args, **kwargs)


class DetalleCompra(models.Model):
    """Detalles de productos en una compra"""
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad_solicitada = models.PositiveIntegerField()
    cantidad_recibida = models.PositiveIntegerField(default=0)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = 'Detalle de Compra'
        verbose_name_plural = 'Detalles de Compra'
        unique_together = ['compra', 'producto']
    
    def __str__(self):
        return f"{self.compra.numero_orden} - {self.producto} x {self.cantidad_solicitada}"
    
    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad_solicitada * self.precio_unitario
        super().save(*args, **kwargs)


class AlertaInventario(models.Model):
    """Alertas automáticas de inventario"""
    TIPO_ALERTA = [
        ('stock_bajo', 'Stock Bajo'),
        ('stock_critico', 'Stock Crítico'),
        ('sin_stock', 'Sin Stock'),
        ('vencimiento', 'Vencimiento Próximo'),
        ('movimiento_anomalo', 'Movimiento Anómalo'),
    ]
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    tipo_alerta = models.CharField(max_length=20, choices=TIPO_ALERTA)
    mensaje = models.TextField()
    fecha_alerta = models.DateTimeField(auto_now_add=True)
    leida = models.BooleanField(default=False)
    usuario_asignado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Alerta de Inventario'
        verbose_name_plural = 'Alertas de Inventario'
        ordering = ['-fecha_alerta']
    
    def __str__(self):
        return f"Alerta {self.get_tipo_alerta_display()} - {self.producto}"
