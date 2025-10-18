from django.urls import path
from . import views

urlpatterns = [
    # URLs públicas
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_view, name='perfil'),
    
    
    # URLs AJAX para verificación
    path('ajax/enviar-codigo/', views.enviar_codigo_verificacion_ajax, name='enviar_codigo_ajax'),
    path('ajax/verificar-codigo/', views.verificar_codigo_ajax, name='verificar_codigo_ajax'),
    
    # URLs API para chatbot
    path('api/generate-token/', views.api_generate_token, name='api_generate_token'),
    path('api/validate-token/', views.api_validate_token, name='api_validate_token'),
    path('api/revoke-token/', views.api_revoke_token, name='api_revoke_token'),
    
    # URLs del Panel Admin (solo superusuarios)
    path('panel-admin/usuarios/', views.lista_usuarios_admin, name='lista_usuarios_admin'),
    path('panel-admin/usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('panel-admin/usuarios/editar/<int:usuario_id>/', views.editar_usuario, name='editar_usuario'),
    path('panel-admin/usuarios/eliminar/<int:usuario_id>/', views.eliminar_usuario, name='eliminar_usuario'),
]
