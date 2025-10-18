from django.contrib import admin
from .models import Producto, CategoriaAcero, Cliente, Pedido, DetallePedido, Cotizacion, DetalleCotizacion


@admin.register(CategoriaAcero)
class CategoriaAceroAdmin(admin.ModelAdmin):
    """Administración de categorías de acero"""
    list_display = ['nombre', 'activa', 'created_at']
    list_filter = ['activa']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']
    
    def created_at(self, obj):
        return obj.id  # Placeholder para mostrar algo
    created_at.short_description = 'ID'


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """Administración de productos"""
    list_display = ['codigo_producto', 'nombre', 'categoria', 'tipo_acero', 'precio_por_unidad', 'stock_actual', 'activo', 'imagen_preview']
    list_filter = ['categoria', 'tipo_acero', 'activo']
    search_fields = ['nombre', 'codigo_producto', 'descripcion']
    ordering = ['categoria', 'nombre']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'codigo_producto', 'categoria', 'tipo_acero')
        }),
        ('Especificaciones Técnicas', {
            'fields': ('grosor', 'ancho', 'largo', 'peso_por_metro'),
            'classes': ('collapse',)
        }),
        ('Precios', {
            'fields': ('precio_por_unidad', 'precio_por_metro', 'precio_por_kg')
        }),
        ('Stock', {
            'fields': ('stock_actual', 'stock_minimo', 'unidad_medida')
        }),
        ('Imagen', {
            'fields': ('imagen',)
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )
    
    def imagen_preview(self, obj):
        """Mostrar preview de la imagen en el admin"""
        if obj.imagen:
            return f"✅ Tiene imagen: {obj.imagen.name}"
        return "❌ Sin imagen"
    imagen_preview.short_description = 'Imagen'


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    """Administración de clientes"""
    list_display = ['nombre', 'apellido', 'tipo_cliente', 'email', 'telefono', 'activo']
    list_filter = ['tipo_cliente', 'activo']
    search_fields = ['nombre', 'apellido', 'email', 'rut']
    ordering = ['apellido', 'nombre']


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    """Administración de pedidos"""
    list_display = ['numero_pedido', 'cliente', 'fecha_pedido', 'estado', 'total']
    list_filter = ['estado', 'metodo_pago', 'fecha_pedido']
    search_fields = ['numero_pedido', 'cliente__nombre', 'cliente__apellido']
    ordering = ['-fecha_pedido']


@admin.register(DetallePedido)
class DetallePedidoAdmin(admin.ModelAdmin):
    """Administración de detalles de pedidos"""
    list_display = ['pedido', 'producto', 'cantidad', 'precio_unitario', 'subtotal']
    list_filter = ['pedido__estado']
    search_fields = ['pedido__numero_pedido', 'producto__nombre']
    ordering = ['-pedido__fecha_pedido']


@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    """Administración de cotizaciones"""
    list_display = ['numero_cotizacion', 'usuario', 'estado', 'fecha_creacion', 'total', 'pago_completado']
    list_filter = ['estado', 'pago_completado', 'metodo_pago', 'fecha_creacion']
    search_fields = ['numero_cotizacion', 'usuario__username', 'usuario__email']
    ordering = ['-fecha_creacion']
    readonly_fields = ['numero_cotizacion', 'fecha_creacion', 'fecha_actualizacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('usuario', 'numero_cotizacion', 'estado')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion', 'fecha_finalizacion')
        }),
        ('Totales', {
            'fields': ('subtotal', 'iva', 'total')
        }),
        ('Pago', {
            'fields': ('metodo_pago', 'pago_completado', 'mercadopago_preference_id', 'mercadopago_payment_id')
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
    )


class DetalleCotizacionInline(admin.TabularInline):
    """Inline para detalles de cotización"""
    model = DetalleCotizacion
    extra = 0
    readonly_fields = ['subtotal']


@admin.register(DetalleCotizacion)
class DetalleCotizacionAdmin(admin.ModelAdmin):
    """Administración de detalles de cotizaciones"""
    list_display = ['cotizacion', 'producto', 'cantidad', 'precio_unitario', 'subtotal']
    list_filter = ['cotizacion__estado']
    search_fields = ['cotizacion__numero_cotizacion', 'producto__nombre']
    ordering = ['-cotizacion__fecha_creacion']
