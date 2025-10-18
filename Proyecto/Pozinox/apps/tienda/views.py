from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Producto, CategoriaAcero, Cotizacion, DetalleCotizacion
from .forms import ProductoForm, CategoriaForm
import mercadopago
import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO


def home(request):
    """Vista principal de la página de inicio"""
    # Obtener productos destacados
    productos_destacados = Producto.objects.filter(activo=True)[:6]
    
    # Obtener categorías principales
    categorias = CategoriaAcero.objects.filter(activa=True)[:4]
    
    context = {
        'productos_destacados': productos_destacados,
        'categorias': categorias,
        'titulo': 'Pozinox - Tienda de Aceros',
    }
    return render(request, 'tienda/home.html', context)


def productos_publicos(request):
    """Vista pública de productos para todos los usuarios"""
    productos = Producto.objects.filter(activo=True)
    categorias = CategoriaAcero.objects.filter(activa=True)
    
    # Filtros
    categoria_id = request.GET.get('categoria')
    busqueda = request.GET.get('q')
    
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    
    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda) |
            Q(descripcion__icontains=busqueda) |
            Q(codigo_producto__icontains=busqueda)
        )
    
    # Paginación
    paginator = Paginator(productos, 12)
    page_number = request.GET.get('page')
    productos_paginados = paginator.get_page(page_number)
    
    context = {
        'productos': productos_paginados,
        'categorias': categorias,
        'categoria_actual': categoria_id,
        'busqueda': busqueda,
    }
    return render(request, 'tienda/productos.html', context)


def detalle_producto(request, producto_id):
    """Vista de detalle de un producto específico"""
    producto = get_object_or_404(Producto, id=producto_id, activo=True)
    
    # Productos relacionados (misma categoría)
    productos_relacionados = Producto.objects.filter(
        categoria=producto.categoria,
        activo=True
    ).exclude(id=producto.id)[:4]
    
    context = {
        'producto': producto,
        'productos_relacionados': productos_relacionados,
    }
    return render(request, 'tienda/detalle_producto.html', context)


# Decorador para verificar si es superusuario
def es_superusuario(user):
    return user.is_superuser


@login_required
@user_passes_test(es_superusuario)
def panel_admin(request):
    """Panel de administración para superusuarios"""
    context = {
        'total_productos': Producto.objects.count(),
        'productos_activos': Producto.objects.filter(activo=True).count(),
        'productos_stock_bajo': Producto.objects.filter(stock_actual__lte=F('stock_minimo')).count(),
        'total_categorias': CategoriaAcero.objects.count(),
    }
    return render(request, 'tienda/panel_admin.html', context)


@login_required
@user_passes_test(es_superusuario)
def lista_productos_admin(request):
    """Lista de productos para administración"""
    productos = Producto.objects.all().order_by('-fecha_creacion')
    
    # Filtros
    categoria_id = request.GET.get('categoria')
    estado = request.GET.get('estado')
    busqueda = request.GET.get('q')
    
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    
    if estado == 'activos':
        productos = productos.filter(activo=True)
    elif estado == 'inactivos':
        productos = productos.filter(activo=False)
    
    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda) |
            Q(descripcion__icontains=busqueda) |
            Q(codigo_producto__icontains=busqueda)
        )
    
    # Paginación
    paginator = Paginator(productos, 20)
    page_number = request.GET.get('page')
    productos_paginados = paginator.get_page(page_number)
    
    categorias = CategoriaAcero.objects.all()
    
    context = {
        'productos': productos_paginados,
        'categorias': categorias,
        'categoria_actual': categoria_id,
        'estado_actual': estado,
        'busqueda': busqueda,
    }
    return render(request, 'tienda/admin/lista_productos.html', context)


@login_required
@user_passes_test(es_superusuario)
def crear_producto(request):
    """Crear nuevo producto"""
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'Producto "{producto.nombre}" creado exitosamente.')
            return redirect('lista_productos_admin')
    else:
        form = ProductoForm()
    
    context = {'form': form, 'titulo': 'Crear Producto'}
    return render(request, 'tienda/admin/formulario_producto.html', context)


@login_required
@user_passes_test(es_superusuario)
def editar_producto(request, producto_id):
    """Editar producto existente"""
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'Producto "{producto.nombre}" actualizado exitosamente.')
            return redirect('lista_productos_admin')
    else:
        form = ProductoForm(instance=producto)
    
    context = {
        'form': form, 
        'producto': producto,
        'titulo': 'Editar Producto'
    }
    return render(request, 'tienda/admin/formulario_producto.html', context)


@login_required
@user_passes_test(es_superusuario)
def eliminar_producto(request, producto_id):
    """Eliminar producto"""
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        nombre_producto = producto.nombre
        producto.delete()
        messages.success(request, f'Producto "{nombre_producto}" eliminado exitosamente.')
        return redirect('lista_productos_admin')
    
    context = {'producto': producto}
    return render(request, 'tienda/admin/confirmar_eliminar.html', context)


@login_required
@user_passes_test(es_superusuario)
def lista_categorias_admin(request):
    """Lista de categorías para administración"""
    categorias = CategoriaAcero.objects.all().order_by('nombre')
    
    # Filtros
    estado = request.GET.get('estado')
    busqueda = request.GET.get('q')
    
    if estado == 'activas':
        categorias = categorias.filter(activa=True)
    elif estado == 'inactivas':
        categorias = categorias.filter(activa=False)
    
    if busqueda:
        categorias = categorias.filter(
            Q(nombre__icontains=busqueda) |
            Q(descripcion__icontains=busqueda)
        )
    
    # Paginación
    paginator = Paginator(categorias, 20)
    page_number = request.GET.get('page')
    categorias_paginadas = paginator.get_page(page_number)
    
    context = {
        'categorias': categorias_paginadas,
        'estado_actual': estado,
        'busqueda': busqueda,
    }
    return render(request, 'tienda/admin/lista_categorias.html', context)


@login_required
@user_passes_test(es_superusuario)
def crear_categoria(request):
    """Crear nueva categoría"""
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f'Categoría "{categoria.nombre}" creada exitosamente.')
            return redirect('lista_categorias_admin')
    else:
        form = CategoriaForm()
    
    context = {'form': form, 'titulo': 'Crear Categoría'}
    return render(request, 'tienda/admin/formulario_categoria.html', context)


@login_required
@user_passes_test(es_superusuario)
def editar_categoria(request, categoria_id):
    """Editar categoría existente"""
    categoria = get_object_or_404(CategoriaAcero, id=categoria_id)
    
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f'Categoría "{categoria.nombre}" actualizada exitosamente.')
            return redirect('lista_categorias_admin')
    else:
        form = CategoriaForm(instance=categoria)
    
    context = {
        'form': form, 
        'categoria': categoria,
        'titulo': 'Editar Categoría'
    }
    return render(request, 'tienda/admin/formulario_categoria.html', context)


@login_required
@user_passes_test(es_superusuario)
def eliminar_categoria(request, categoria_id):
    """Eliminar categoría"""
    categoria = get_object_or_404(CategoriaAcero, id=categoria_id)
    
    # Verificar si hay productos asociados
    productos_asociados = Producto.objects.filter(categoria=categoria).count()
    
    if request.method == 'POST':
        nombre_categoria = categoria.nombre
        categoria.delete()
        messages.success(request, f'Categoría "{nombre_categoria}" eliminada exitosamente.')
        return redirect('lista_categorias_admin')
    
    context = {
        'categoria': categoria,
        'productos_asociados': productos_asociados
    }
    return render(request, 'tienda/admin/confirmar_eliminar_categoria.html', context)


# ============================================
# SISTEMA DE COTIZACIONES
# ============================================

@login_required
def mis_cotizaciones(request):
    """Lista de cotizaciones del usuario actual"""
    cotizaciones = Cotizacion.objects.filter(usuario=request.user).order_by('-fecha_creacion')
    
    # Filtros
    estado = request.GET.get('estado')
    if estado:
        cotizaciones = cotizaciones.filter(estado=estado)
    
    # Paginación
    paginator = Paginator(cotizaciones, 10)
    page_number = request.GET.get('page')
    cotizaciones_paginadas = paginator.get_page(page_number)
    
    context = {
        'cotizaciones': cotizaciones_paginadas,
        'estado_actual': estado,
    }
    return render(request, 'tienda/cotizaciones/mis_cotizaciones.html', context)


@login_required
def crear_cotizacion(request):
    """Crear nueva cotización o obtener la cotización en borrador actual"""
    # Buscar si el usuario ya tiene una cotización en borrador
    cotizacion = Cotizacion.objects.filter(
        usuario=request.user, 
        estado='borrador'
    ).first()
    
    # Si no existe, crear una nueva
    if not cotizacion:
        cotizacion = Cotizacion.objects.create(usuario=request.user)
        messages.success(request, f'Nueva cotización {cotizacion.numero_cotizacion} creada.')
    
    return redirect('detalle_cotizacion', cotizacion_id=cotizacion.id)


@login_required
def detalle_cotizacion(request, cotizacion_id):
    """Ver detalle de una cotización"""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id, usuario=request.user)
    detalles = cotizacion.detalles.all().select_related('producto')
    
    # Productos disponibles para agregar (que aún no están en la cotización)
    productos_en_cotizacion = detalles.values_list('producto_id', flat=True)
    productos_disponibles = Producto.objects.filter(activo=True).exclude(
        id__in=productos_en_cotizacion
    )
    
    # Filtros de productos
    categoria_id = request.GET.get('categoria')
    busqueda = request.GET.get('q')
    
    if categoria_id:
        productos_disponibles = productos_disponibles.filter(categoria_id=categoria_id)
    
    if busqueda:
        productos_disponibles = productos_disponibles.filter(
            Q(nombre__icontains=busqueda) |
            Q(codigo_producto__icontains=busqueda)
        )
    
    categorias = CategoriaAcero.objects.filter(activa=True)
    
    context = {
        'cotizacion': cotizacion,
        'detalles': detalles,
        'productos_disponibles': productos_disponibles[:20],  # Limitar a 20 productos
        'categorias': categorias,
        'puede_editar': cotizacion.estado == 'borrador',
    }
    return render(request, 'tienda/cotizaciones/detalle_cotizacion.html', context)


@login_required
@require_POST
def agregar_producto_cotizacion(request, cotizacion_id):
    """Agregar un producto a la cotización"""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id, usuario=request.user)
    
    # Solo se puede agregar productos si la cotización está en borrador
    if cotizacion.estado != 'borrador':
        messages.error(request, 'No se pueden agregar productos a una cotización finalizada.')
        return redirect('detalle_cotizacion', cotizacion_id=cotizacion.id)
    
    producto_id = request.POST.get('producto_id')
    cantidad = int(request.POST.get('cantidad', 1))
    
    producto = get_object_or_404(Producto, id=producto_id, activo=True)
    
    # Verificar si el producto ya está en la cotización
    detalle, created = DetalleCotizacion.objects.get_or_create(
        cotizacion=cotizacion,
        producto=producto,
        defaults={
            'cantidad': cantidad,
            'precio_unitario': producto.precio_por_unidad
        }
    )
    
    if not created:
        # Si ya existe, actualizar la cantidad
        detalle.cantidad += cantidad
        detalle.save()
        messages.info(request, f'Se actualizó la cantidad de {producto.nombre} en la cotización.')
    else:
        messages.success(request, f'{producto.nombre} agregado a la cotización.')
    
    return redirect('detalle_cotizacion', cotizacion_id=cotizacion.id)


@login_required
@require_POST
def actualizar_cantidad_producto(request, detalle_id):
    """Actualizar cantidad de un producto en la cotización"""
    detalle = get_object_or_404(DetalleCotizacion, id=detalle_id)
    cotizacion = detalle.cotizacion
    
    # Verificar que el usuario sea el dueño de la cotización
    if cotizacion.usuario != request.user:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    # Solo se puede editar si está en borrador
    if cotizacion.estado != 'borrador':
        return JsonResponse({'error': 'No se puede editar una cotización finalizada'}, status=400)
    
    cantidad = int(request.POST.get('cantidad', 1))
    
    if cantidad <= 0:
        return JsonResponse({'error': 'La cantidad debe ser mayor a 0'}, status=400)
    
    detalle.cantidad = cantidad
    detalle.save()
    
    return JsonResponse({
        'success': True,
        'subtotal': float(detalle.subtotal),
        'total_cotizacion': float(cotizacion.total)
    })


@login_required
@require_POST
def eliminar_producto_cotizacion(request, detalle_id):
    """Eliminar un producto de la cotización"""
    detalle = get_object_or_404(DetalleCotizacion, id=detalle_id)
    cotizacion = detalle.cotizacion
    
    # Verificar que el usuario sea el dueño de la cotización
    if cotizacion.usuario != request.user:
        messages.error(request, 'No autorizado.')
        return redirect('mis_cotizaciones')
    
    # Solo se puede eliminar si está en borrador
    if cotizacion.estado != 'borrador':
        messages.error(request, 'No se pueden eliminar productos de una cotización finalizada.')
        return redirect('detalle_cotizacion', cotizacion_id=cotizacion.id)
    
    producto_nombre = detalle.producto.nombre
    detalle.delete()
    messages.success(request, f'{producto_nombre} eliminado de la cotización.')
    
    return redirect('detalle_cotizacion', cotizacion_id=cotizacion.id)


@login_required
def finalizar_cotizacion(request, cotizacion_id):
    """Finalizar cotización y mostrar opciones de pago"""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id, usuario=request.user)
    
    # Verificar que esté en borrador
    if cotizacion.estado != 'borrador':
        messages.error(request, 'Esta cotización ya fue finalizada.')
        return redirect('detalle_cotizacion', cotizacion_id=cotizacion.id)
    
    # Verificar que tenga al menos un producto
    if not cotizacion.detalles.exists():
        messages.error(request, 'Debe agregar al menos un producto a la cotización.')
        return redirect('detalle_cotizacion', cotizacion_id=cotizacion.id)
    
    # Actualizar estado
    cotizacion.estado = 'finalizada'
    cotizacion.fecha_finalizacion = timezone.now()
    cotizacion.save()
    
    messages.success(request, 'Cotización finalizada. Seleccione un método de pago.')
    return redirect('seleccionar_pago', cotizacion_id=cotizacion.id)


@login_required
def seleccionar_pago(request, cotizacion_id):
    """Página para seleccionar método de pago"""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id, usuario=request.user)
    
    # Verificar que esté finalizada
    if cotizacion.estado not in ['finalizada', 'pagada']:
        messages.error(request, 'La cotización debe estar finalizada para proceder al pago.')
        return redirect('detalle_cotizacion', cotizacion_id=cotizacion.id)
    
    detalles = cotizacion.detalles.all().select_related('producto')
    
    context = {
        'cotizacion': cotizacion,
        'detalles': detalles,
    }
    return render(request, 'tienda/cotizaciones/seleccionar_pago.html', context)


@login_required
def procesar_pago_mercadopago(request, cotizacion_id):
    """Crear preferencia de pago en MercadoPago y redirigir"""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id, usuario=request.user)
    
    # Verificar que esté finalizada
    if cotizacion.estado not in ['finalizada', 'pagada']:
        messages.error(request, 'La cotización debe estar finalizada para proceder al pago.')
        return redirect('detalle_cotizacion', cotizacion_id=cotizacion.id)
    
    # Obtener el Access Token de MercadoPago desde variables de entorno
    mp_access_token = os.getenv('MERCADOPAGO_ACCESS_TOKEN')
    
    if not mp_access_token:
        messages.error(request, 'MercadoPago no está configurado. Contacte al administrador.')
        return redirect('seleccionar_pago', cotizacion_id=cotizacion.id)
    
    try:
        # Inicializar SDK de MercadoPago
        sdk = mercadopago.SDK(mp_access_token)
        
        # Crear items de la preferencia
        items = []
        for detalle in cotizacion.detalles.all():
            items.append({
                "title": detalle.producto.nombre,
                "quantity": detalle.cantidad,
                "unit_price": float(detalle.precio_unitario),
                "currency_id": "CLP"  # Peso chileno
            })
        
        # Crear preferencia
        preference_data = {
            "items": items,
            "back_urls": {
                "success": request.build_absolute_uri(f'/cotizaciones/{cotizacion.id}/pago-exitoso/'),
                "failure": request.build_absolute_uri(f'/cotizaciones/{cotizacion.id}/pago-fallido/'),
                "pending": request.build_absolute_uri(f'/cotizaciones/{cotizacion.id}/pago-pendiente/'),
            },
            "auto_return": "approved",
            "external_reference": cotizacion.numero_cotizacion,
            "statement_descriptor": "Pozinox",
            "payer": {
                "name": request.user.first_name,
                "surname": request.user.last_name,
                "email": request.user.email,
            }
        }
        
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]
        
        # Guardar el ID de preferencia
        cotizacion.mercadopago_preference_id = preference["id"]
        cotizacion.metodo_pago = 'mercadopago'
        cotizacion.save()
        
        # Redirigir a MercadoPago
        return redirect(preference["init_point"])
        
    except Exception as e:
        messages.error(request, f'Error al procesar el pago: {str(e)}')
        return redirect('seleccionar_pago', cotizacion_id=cotizacion.id)


@login_required
def pago_exitoso(request, cotizacion_id):
    """Página de confirmación de pago exitoso"""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id, usuario=request.user)
    
    # Actualizar estado de la cotización
    cotizacion.estado = 'pagada'
    cotizacion.pago_completado = True
    
    # Obtener payment_id de MercadoPago si está disponible
    payment_id = request.GET.get('payment_id')
    if payment_id:
        cotizacion.mercadopago_payment_id = payment_id
    
    cotizacion.save()
    
    context = {
        'cotizacion': cotizacion,
    }
    return render(request, 'tienda/cotizaciones/pago_exitoso.html', context)


@login_required
def pago_fallido(request, cotizacion_id):
    """Página de pago fallido"""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id, usuario=request.user)
    
    context = {
        'cotizacion': cotizacion,
    }
    return render(request, 'tienda/cotizaciones/pago_fallido.html', context)


@login_required
def pago_pendiente(request, cotizacion_id):
    """Página de pago pendiente"""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id, usuario=request.user)
    
    context = {
        'cotizacion': cotizacion,
    }
    return render(request, 'tienda/cotizaciones/pago_pendiente.html', context)


@login_required
def descargar_cotizacion_pdf(request, cotizacion_id):
    """Generar y descargar PDF de la cotización"""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id, usuario=request.user)
    detalles = cotizacion.detalles.all().select_related('producto')
    
    # Crear el buffer
    buffer = BytesIO()
    
    # Crear el documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Contenedor para los elementos del PDF
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para el título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para encabezados
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    # Estilo normal
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=12,
    )
    
    # Título
    elements.append(Paragraph('POZINOX', title_style))
    elements.append(Paragraph('Tienda de Aceros', styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Información de la cotización
    elements.append(Paragraph(f'COTIZACIÓN N° {cotizacion.numero_cotizacion}', heading_style))
    
    # Datos del cliente y cotización
    info_data = [
        ['Cliente:', f'{request.user.get_full_name() or request.user.username}'],
        ['Email:', request.user.email],
        ['Fecha:', cotizacion.fecha_creacion.strftime('%d/%m/%Y %H:%M')],
        ['Estado:', cotizacion.get_estado_display()],
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1e3a8a')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 20))
    
    # Tabla de productos
    elements.append(Paragraph('DETALLE DE PRODUCTOS', heading_style))
    
    # Encabezados de tabla
    table_data = [['Producto', 'Código', 'Cantidad', 'Precio Unit.', 'Subtotal']]
    
    # Datos de productos
    for detalle in detalles:
        table_data.append([
            Paragraph(detalle.producto.nombre, normal_style),
            detalle.producto.codigo_producto,
            str(detalle.cantidad),
            f'${detalle.precio_unitario:,.0f}',
            f'${detalle.subtotal:,.0f}'
        ])
    
    # Crear tabla
    product_table = Table(table_data, colWidths=[2.5*inch, 1.2*inch, 0.8*inch, 1*inch, 1*inch])
    product_table.setStyle(TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Contenido
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
        ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    
    elements.append(product_table)
    elements.append(Spacer(1, 20))
    
    # Totales
    totales_data = [
        ['Subtotal:', f'${cotizacion.subtotal:,.0f}'],
        ['IVA (19%):', f'${cotizacion.iva:,.0f}'],
        ['', ''],
        ['TOTAL:', f'${cotizacion.total:,.0f}'],
    ]
    
    totales_table = Table(totales_data, colWidths=[5*inch, 1.5*inch])
    totales_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 1), 'Helvetica'),
        ('FONTNAME', (1, 0), (1, 1), 'Helvetica-Bold'),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 2), 11),
        ('FONTSIZE', (0, 3), (-1, 3), 14),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TEXTCOLOR', (0, 3), (-1, 3), colors.HexColor('#1e3a8a')),
        ('LINEABOVE', (0, 3), (-1, 3), 2, colors.HexColor('#1e3a8a')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    elements.append(totales_table)
    elements.append(Spacer(1, 30))
    
    # Observaciones si existen
    if cotizacion.observaciones:
        elements.append(Paragraph('OBSERVACIONES:', heading_style))
        elements.append(Paragraph(cotizacion.observaciones, normal_style))
        elements.append(Spacer(1, 20))
    
    # Pie de página
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER,
    )
    
    elements.append(Spacer(1, 30))
    elements.append(Paragraph('_______________________________________________', footer_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph('POZINOX - Tienda de Aceros', footer_style))
    elements.append(Paragraph('www.pozinox.cl | info@pozinox.cl | +56 2 1234 5678', footer_style))
    elements.append(Paragraph('Este documento es una cotización y no constituye una factura', footer_style))
    
    # Construir PDF
    doc.build(elements)
    
    # Obtener el valor del buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Crear la respuesta HTTP
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Cotizacion_{cotizacion.numero_cotizacion}.pdf"'
    response.write(pdf)
    
    return response
