from django import forms
from .models import Producto, CategoriaAcero


class CategoriaForm(forms.ModelForm):
    """Formulario para crear y editar categorías"""
    
    class Meta:
        model = CategoriaAcero
        fields = ['nombre', 'descripcion', 'activa']
        
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la categoría'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción de la categoría'
            }),
            'activa': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar labels
        self.fields['nombre'].label = 'Nombre de la Categoría'
        self.fields['descripcion'].label = 'Descripción'
        self.fields['activa'].label = 'Categoría Activa'
        
        # Hacer campos requeridos
        self.fields['nombre'].required = True
    
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            # Verificar si el nombre ya existe (excepto para la instancia actual)
            queryset = CategoriaAcero.objects.filter(nombre__iexact=nombre)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise forms.ValidationError('Ya existe una categoría con este nombre.')
        return nombre


class ProductoForm(forms.ModelForm):
    """Formulario para crear y editar productos"""
    
    class Meta:
        model = Producto
        fields = [
            'nombre', 'descripcion', 'codigo_producto', 'categoria', 'tipo_acero',
            'grosor', 'ancho', 'largo', 'peso_por_metro',
            'precio_por_unidad', 'precio_por_metro', 'precio_por_kg',
            'stock_actual', 'stock_minimo', 'unidad_medida',
            'imagen', 'activo'
        ]
        
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción detallada del producto'
            }),
            'codigo_producto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código único del producto'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tipo_acero': forms.Select(attrs={
                'class': 'form-select'
            }),
            'grosor': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Grosor en mm'
            }),
            'ancho': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Ancho en mm'
            }),
            'largo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Largo en mm'
            }),
            'peso_por_metro': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Peso por metro en kg'
            }),
            'precio_por_unidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Precio por unidad'
            }),
            'precio_por_metro': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Precio por metro'
            }),
            'precio_por_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Precio por kilogramo'
            }),
            'stock_actual': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Stock actual'
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Stock mínimo'
            }),
            'unidad_medida': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'unidad, metro, kg, etc.'
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar labels
        self.fields['nombre'].label = 'Nombre del Producto'
        self.fields['descripcion'].label = 'Descripción'
        self.fields['codigo_producto'].label = 'Código de Producto'
        self.fields['categoria'].label = 'Categoría'
        self.fields['tipo_acero'].label = 'Tipo de Acero'
        self.fields['grosor'].label = 'Grosor (mm)'
        self.fields['ancho'].label = 'Ancho (mm)'
        self.fields['largo'].label = 'Largo (mm)'
        self.fields['peso_por_metro'].label = 'Peso por Metro (kg/m)'
        self.fields['precio_por_unidad'].label = 'Precio por Unidad ($)'
        self.fields['precio_por_metro'].label = 'Precio por Metro ($)'
        self.fields['precio_por_kg'].label = 'Precio por Kilogramo ($)'
        self.fields['stock_actual'].label = 'Stock Actual'
        self.fields['stock_minimo'].label = 'Stock Mínimo'
        self.fields['unidad_medida'].label = 'Unidad de Medida'
        self.fields['imagen'].label = 'Imagen del Producto'
        self.fields['activo'].label = 'Producto Activo'
        
        # Hacer campos requeridos
        self.fields['nombre'].required = True
        self.fields['codigo_producto'].required = True
        self.fields['categoria'].required = True
        self.fields['tipo_acero'].required = True
        self.fields['precio_por_unidad'].required = True
        self.fields['stock_actual'].required = True
        self.fields['stock_minimo'].required = True
        self.fields['unidad_medida'].required = True
        
        # Queries para el dropdown de categorías
        self.fields['categoria'].queryset = CategoriaAcero.objects.filter(activa=True)
    
    def clean_codigo_producto(self):
        codigo = self.cleaned_data.get('codigo_producto')
        if codigo:
            # Verificar si el código ya existe (excepto para la instancia actual)
            queryset = Producto.objects.filter(codigo_producto=codigo)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise forms.ValidationError('Este código de producto ya existe.')
        return codigo
    
    def clean_stock_minimo(self):
        stock_minimo = self.cleaned_data.get('stock_minimo')
        if stock_minimo is not None and stock_minimo < 0:
            raise forms.ValidationError('El stock mínimo no puede ser negativo.')
        return stock_minimo
    
    def clean_precio_por_unidad(self):
        precio = self.cleaned_data.get('precio_por_unidad')
        if precio is not None and precio <= 0:
            raise forms.ValidationError('El precio debe ser mayor a 0.')
        return precio
