"""
Este archivo mapea los endpoints REST de la aplicación 'api' utilizando:
1. DefaultRouter de DRF para generar automáticamente las URLs CRUD.
2. Endpoints de autenticación JWT (SimpleJWT).
3. Endpoints específicos para la gestión del flujo del contratista.

"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

# Importación de ViewSets y Vistas API desde views.py
from .views import (
    CategoriaHerramientaViewSet,
    HerramientaViewSet,
    ContratistaViewSet,
    AlquilerViewSet,
    MantenimientoViewSet,
    CustomTokenObtainPairView,
    CarroHerramientasView,
    CheckoutAlquilerView,
    MisAlquileresView,
    CambiarEstadoAlquilerView
)

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DEL ROUTER AUTOMÁTICO (DRF)
# -----------------------------------------------------------------------------
# Instanciamos el DefaultRouter que asigna automáticamente rutas para:
# - GET / (Listar)
# - POST / (Crear)
# - GET /{id}/ (Detalle)
# - PUT /{id}/ / PATCH /{id}/ (Actualizar)
# - DELETE /{id}/ (Eliminar)
router = DefaultRouter()

# Enrutamiento de Categorías de Herramientas
router.register(r'categorias', CategoriaHerramientaViewSet, basename='categoria')

# Enrutamiento de Herramientas / Activos (Incluye custom actions: 'disponibles', 'enviar_a_mantenimiento')
router.register(r'herramientas', HerramientaViewSet, basename='herramienta')

# Enrutamiento de Contratistas (Incluye custom action: 'desbloquear')
router.register(r'contratistas', ContratistaViewSet, basename='contratista')

# Enrutamiento de Alquileres / Préstamos (Incluye custom action: 'devolver_herramienta')
router.register(r'alquileres', AlquilerViewSet, basename='alquiler')

# Enrutamiento de Mantenimientos
router.register(r'mantenimientos', MantenimientoViewSet, basename='mantenimiento')

# -----------------------------------------------------------------------------
# 2. DEFINICIÓN DE PATRONES DE URLS
# -----------------------------------------------------------------------------
urlpatterns = [
    # Incorpora todas las rutas registradas en el DefaultRouter
    path('', include(router.urls)),

    # -------------------------------------------------------------------------
    # ENDPOINTS DE AUTENTICACIÓN JWT (JSON WEB TOKEN)
    # -------------------------------------------------------------------------
    # Obtener token de acceso y refresh pasando credenciales (username/password)
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # Renovar el token de acceso expirado mediante un refresh token válido
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # -------------------------------------------------------------------------
    # ENDPOINTS ADICIONALES PARA CONTRATISTAS
    # -------------------------------------------------------------------------
    # Consulta y gestión del carro de solicitudes activo vía API
    path('carro/', CarroHerramientasView.as_view(), name='api_carro'),
    
    # Procesar el checkout y la firma digital vía API
    path('checkout/', CheckoutAlquilerView.as_view(), name='api_checkout'),
    
    # Listado de alquileres específicos del contratista autenticado
    path('mis-alquileres/', MisAlquileresView.as_view(), name='api_mis_alquileres'),
    
    # Cambio de estado de un alquiler en específico
    path('alquileres/<int:pk>/estado/', CambiarEstadoAlquilerView.as_view(), name='api_cambiar_estado'),
]