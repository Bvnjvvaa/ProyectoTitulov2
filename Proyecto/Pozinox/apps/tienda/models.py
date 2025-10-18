from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage
from decimal import Decimal


class CategoriaAcero(models.Model):
    """Categorías de productos de acero (perfiles, planchas, tubos, etc.)"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Categoría de Acero'
        verbose_name_plural = 'Categorías de Acero'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """Productos de acero de la tienda Pozinox"""
    TIPOS_ACERO = [
        ('inoxidable', 'Acero Inoxidable'),
        ('carbono', 'Acero al Carbono'),
        ('galvanizado', 'Acero Galvanizado'),
        ('estructural', 'Acero Estructural'),
    ]
    
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    codigo_producto = models.CharField(max_length=50, unique=True)
    categoria = models.ForeignKey(CategoriaAcero, on_delete=models.CASCADE)
    tipo_acero = models.CharField(max_length=20, choices=TIPOS_ACERO)
    
    # Especificaciones técnicas
    grosor = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="En mm")
    ancho = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="En mm")
    largo = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="En mm")
    peso_por_metro = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="En kg/m")
    
    # Precios
    precio_por_unidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_por_metro = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    precio_por_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Stock y disponibilidad
    stock_actual = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=5)
    unidad_medida = models.CharField(max_length=20, default='unidad')
    
    # Metadatos
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True, storage=S3Boto3Storage())
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['categoria', 'nombre']
    
    def __str__(self):
        return f"{self.codigo_producto} - {self.nombre}"
    
    @property
    def stock_bajo(self):
        return self.stock_actual <= self.stock_minimo


class Cliente(models.Model):
    """Clientes de la tienda Pozinox"""
    TIPO_CLIENTE = [
        ('particular', 'Particular'),
        ('empresa', 'Empresa'),
        ('constructor', 'Constructor'),
        ('distribuidor', 'Distribuidor'),
    ]
    
    tipo_cliente = models.CharField(max_length=20, choices=TIPO_CLIENTE, default='particular')
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    razon_social = models.CharField(max_length=200, blank=True, help_text="Solo para empresas")
    rut = models.CharField(max_length=12, unique=True)
    
    # Contacto
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20)
    telefono_alternativo = models.CharField(max_length=20, blank=True)
    
    # Dirección
    direccion = models.TextField()
    comuna = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    codigo_postal = models.CharField(max_length=10, blank=True)
    
    # Metadatos
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['apellido', 'nombre']
    
    def __str__(self):
        if self.tipo_cliente == 'empresa':
            return self.razon_social or f"{self.nombre} {self.apellido}"
        return f"{self.nombre} {self.apellido}"


class Pedido(models.Model):
    """Pedidos de la tienda Pozinox"""
    ESTADOS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
        ('preparando', 'Preparando'),
        ('listo', 'Listo para Retiro'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    
    METODOS_PAGO = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('tarjeta', 'Tarjeta'),
        ('cheque', 'Cheque'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    numero_pedido = models.CharField(max_length=20, unique=True)
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    fecha_entrega = models.DateField(null=True, blank=True)
    
    estado = models.CharField(max_length=20, choices=ESTADOS_CHOICES, default='pendiente')
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='efectivo')
    
    # Totales
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Observaciones
    observaciones = models.TextField(blank=True)
    notas_internas = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-fecha_pedido']
    
    def __str__(self):
        return f"Pedido {self.numero_pedido} - {self.cliente}"
    
    def save(self, *args, **kwargs):
        if not self.numero_pedido:
            # Generar número de pedido automáticamente
            import datetime
            today = datetime.date.today()
            last_pedido = Pedido.objects.filter(fecha_pedido__date=today).count()
            self.numero_pedido = f"POZ{today.strftime('%Y%m%d')}{last_pedido + 1:03d}"
        super().save(*args, **kwargs)


class DetallePedido(models.Model):
    """Detalles de cada producto en un pedido"""
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Porcentaje de descuento")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = 'Detalle de Pedido'
        verbose_name_plural = 'Detalles de Pedido'
        unique_together = ['pedido', 'producto']
    
    def __str__(self):
        return f"{self.pedido.numero_pedido} - {self.producto} x {self.cantidad}"
    
    def save(self, *args, **kwargs):
        # Calcular subtotal
        precio_con_descuento = self.precio_unitario * (1 - self.descuento / 100)
        self.subtotal = precio_con_descuento * self.cantidad
        super().save(*args, **kwargs)


class Cotizacion(models.Model):
    """Cotizaciones creadas por usuarios registrados"""
    ESTADOS_COTIZACION = [
        ('borrador', 'Borrador'),
        ('finalizada', 'Finalizada'),
        ('pagada', 'Pagada'),
        ('cancelada', 'Cancelada'),
    ]
    
    METODOS_PAGO = [
        ('mercadopago', 'MercadoPago'),
        ('transferencia', 'Transferencia'),
        ('efectivo', 'Efectivo'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cotizaciones')
    numero_cotizacion = models.CharField(max_length=20, unique=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_COTIZACION, default='borrador')
    
    # Fechas
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_finalizacion = models.DateTimeField(null=True, blank=True)
    
    # Totales
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Pago
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, null=True, blank=True)
    pago_completado = models.BooleanField(default=False)
    
    # MercadoPago
    mercadopago_preference_id = models.CharField(max_length=100, blank=True, null=True)
    mercadopago_payment_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Observaciones
    observaciones = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Cotización'
        verbose_name_plural = 'Cotizaciones'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Cotización {self.numero_cotizacion} - {self.usuario.username}"
    
    def save(self, *args, **kwargs):
        if not self.numero_cotizacion:
            # Generar número de cotización automáticamente
            import datetime
            today = datetime.date.today()
            last_cotizacion = Cotizacion.objects.filter(fecha_creacion__date=today).count()
            self.numero_cotizacion = f"COT{today.strftime('%Y%m%d')}{last_cotizacion + 1:04d}"
        super().save(*args, **kwargs)
    
    def calcular_totales(self):
        """Calcula los totales de la cotización basándose en los detalles"""
        detalles = self.detalles.all()
        self.subtotal = sum(detalle.subtotal for detalle in detalles) if detalles else Decimal('0')
        self.iva = self.subtotal * Decimal('0.19')  # IVA del 19%
        self.total = self.subtotal + self.iva
        self.save()


class DetalleCotizacion(models.Model):
    """Detalles de cada producto en una cotización"""
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = 'Detalle de Cotización'
        verbose_name_plural = 'Detalles de Cotización'
        unique_together = ['cotizacion', 'producto']
    
    def __str__(self):
        return f"{self.cotizacion.numero_cotizacion} - {self.producto} x {self.cantidad}"
    
    def save(self, *args, **kwargs):
        # Calcular subtotal
        self.subtotal = self.precio_unitario * self.cantidad
        super().save(*args, **kwargs)
        # Actualizar totales de la cotización
        self.cotizacion.calcular_totales()