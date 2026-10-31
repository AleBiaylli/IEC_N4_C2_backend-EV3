"""
URL configuration for IEC_N4_C2_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""
ENRUTAMIENTO Y RUTAS PRINCIPALES (IEC_N4_C2_BACKEND/URLS.PY) - BUILDCORP AWS


Estructura de Enrutamiento:
1. Configuración de Marca y Sobreescritura Explícita de Plantillas de Django Admin.
2. Endpoints API RESTful v1 e integración de Documentación Swagger/Redoc.
3. Portal Web Bootstrap (Dashboard, Catálogo y Gestión de Alquileres).
4. Módulo de Autenticación de Usuarios (Login, Logout y Registro).
5. Carro de Solicitudes Persistente y Pasarela de Pago Webpay Plus.
6. Manejo Global de Errores (Catch-all 404).
"""

from django.contrib import admin
from django.urls import path, include, re_path
from drf_spectacular.views import (
    SpectacularAPIView, 
    SpectacularSwaggerView, 
    SpectacularRedocView
)

from api.views import (
    landing_page_web,
    dashboard_principal,
    catalogo_herramientas_web,
    lista_alquileres_web,
    mis_alquileres_web,
    devolver_alquiler_web,
    cancelar_alquiler_web,
    login_web_view,
    logout_web_view,
    registro_web_view,
    mi_carro_view,
    agregar_al_carro_html,
    eliminar_item_carro_view,
    editar_item_carro_view,
    pago_web_view,
    procesar_checkout_html,
    confirmacion_compra_view,
    pagina_no_encontrada_view,
)

# ==============================================================================
# 1. PERSONALIZACIÓN Y ENCABEZADOS DE DJANGO ADMIN
# ==============================================================================
admin.site.site_header = "BuildCorp AWS - Administración del Sistema"
admin.site.site_title = "Portal Admin BuildCorp"
admin.site.index_title = "Gestión de Flota, Contratos y Morosidad"

# Asignación de la vista personalizada para errores HTTP 404
handler404 = pagina_no_encontrada_view


# ==============================================================================
# 2. PATRONES DE URL (PATTERNS)
# ==============================================================================
urlpatterns = [
    # -------------------------------------------------------------------------
    # 2.1. PANEL DE ADMINISTRACIÓN (DJANGO ADMIN)
    # -------------------------------------------------------------------------
    path('admin/', admin.site.urls),

    # -------------------------------------------------------------------------
    # 2.2. API RESTFUL v1 & DOCUMENTACIÓN AUTOMÁTICA OPENAPI 3.0 (SWAGGER/REDOC)
    # -------------------------------------------------------------------------
    # Endpoints dinámicos de los ViewSets (Categorías, Herramientas, Contratistas, Alquileres, Mantenimientos)
    path('api/v1/', include('api.urls')),
    
    # Esquema JSON OpenAPI 3.0
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # Interfaz interactiva Swagger UI
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Interfaz alternativa Redoc
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # -------------------------------------------------------------------------
    # 2.3. PORTAL WEB PRINCIPAL (BOOTSTRAP FRONTEND)
    # -------------------------------------------------------------------------
    path('', landing_page_web, name='home'),
    path('dashboard/', dashboard_principal, name='dashboard_admin'),
    path('catalogo/', catalogo_herramientas_web, name='catalogo_web'),
    path('alquileres-web/', lista_alquileres_web, name='alquileres_web'),

    # -------------------------------------------------------------------------
    # 2.4. MÓDULO DE SOLICITUDES DEL CONTRATISTA
    # -------------------------------------------------------------------------
    path('mis-alquileres/', mis_alquileres_web, name='mis_alquileres_web'),
    path('alquileres/devolver/<int:alquiler_id>/', devolver_alquiler_web, name='devolver_alquiler_web'),
    path('alquileres/cancelar/<int:alquiler_id>/', cancelar_alquiler_web, name='cancelar_alquiler_web'),

    # -------------------------------------------------------------------------
    # 2.5. AUTENTICACIÓN Y CONTROL DE ACCESO
    # -------------------------------------------------------------------------
    path('login/', login_web_view, name='login_web'),
    path('logout/', logout_web_view, name='logout_web'),
    path('registro/', registro_web_view, name='registro_web'),

    # -------------------------------------------------------------------------
    # 2.6. CARRO PERSISTENTE & PASARELA DE PAGO WEBPAY PLUS
    # -------------------------------------------------------------------------
    path('carro/', mi_carro_view, name='mi_carro'),
    path('carro/agregar/<int:herramienta_id>/', agregar_al_carro_html, name='agregar_al_carro_html'),
    path('carro/eliminar/<int:item_id>/', eliminar_item_carro_view, name='eliminar_item_carro'),
    path('carro/editar/<int:item_id>/', editar_item_carro_view, name='editar_item_carro'),
    path('checkout/', pago_web_view, name='pago_web'),
    path('checkout/procesar/', procesar_checkout_html, name='procesar_checkout'),
    path('confirmacion/<int:alquiler_id>/', confirmacion_compra_view, name='confirmacion_compra'),

    # -------------------------------------------------------------------------
    # 2.7. REGLA COMODÍN PARA ERRORES HTTP 404
    # -------------------------------------------------------------------------
    re_path(r'^.*/$', pagina_no_encontrada_view, name='catch_all_404'),
]