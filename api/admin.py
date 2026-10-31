"""
CONFIGURACIÓN Y PERSONALIZACIÓN DE DJANGO ADMIN (API/ADMIN.PY) - BUILDCORP
"""

from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Contratista, CategoriaHerramienta, 
    Herramienta, Alquiler, Mantenimiento, CarroItem
)

# Encabezados del sitio Admin
admin.site.site_header = "BuildCorp AWS - Administración del Sistema"
admin.site.site_title = "Portal Admin BuildCorp"
admin.site.index_title = "Gestión de Flota, Contratos y Morosidad"


# ==============================================================================
# 1. USUARIOS (CustomUser)
# ==============================================================================
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role_badge', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    fieldsets = UserAdmin.fieldsets + (
        ('Control de Roles RBAC', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Control de Roles RBAC', {'fields': ('role',)}),
    )

    @admin.display(description='Rol Asignado')
    def role_badge(self, obj):
        if obj.role == 'ADMIN' or obj.is_staff:
            return format_html(
                '<span style="background-color: #f59e0b; color: black; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
                'ADMIN'
            )
        return format_html(
            '<span style="background-color: #0284c7; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            'CONTRATISTA'
        )


# ==============================================================================
# 2. CONTRATISTAS
# ==============================================================================
@admin.register(Contratista)
class ContratistaAdmin(admin.ModelAdmin):
    list_display = ('razon_social', 'rut', 'telefono', 'usuario', 'estado_morosidad_badge')
    list_filter = ('bloqueado_por_morosidad',)
    search_fields = ('razon_social', 'rut', 'usuario__username', 'telefono')
    actions = ['desbloquear_contratistas', 'bloquear_contratistas']

    @admin.display(description='Estado de Morosidad')
    def estado_morosidad_badge(self, obj):
        if obj.bloqueado_por_morosidad:
            return format_html(
                '<span style="background-color: #dc2626; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
                'BLOQUEADO / MOROSO'
            )
        return format_html(
            '<span style="background-color: #16a34a; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            'AL DÍA / HABILITADO'
        )

    @admin.action(description="Desbloquear contratistas seleccionados")
    def desbloquear_contratistas(self, request, queryset):
        actualizados = queryset.update(bloqueado_por_morosidad=False)
        self.message_user(request, f"Se han desbloqueado {actualizados} contratistas exitosamente.")

    @admin.action(description="Bloquear contratistas por morosidad")
    def bloquear_contratistas(self, request, queryset):
        actualizados = queryset.update(bloqueado_por_morosidad=True)
        self.message_user(request, f"Se han bloqueado {actualizados} contratistas.")


# ==============================================================================
# 3. CATEGORÍAS DE HERRAMIENTAS
# ==============================================================================
@admin.register(CategoriaHerramienta)
class CategoriaHerramientaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'total_herramientas')
    search_fields = ('nombre', 'descripcion')

    @admin.display(description='Total de Equipos')
    def total_herramientas(self, obj):
        return obj.herramientas.count()


# ==============================================================================
# 4. HERRAMIENTAS / FLOTA DE OBRA
# ==============================================================================
@admin.register(Herramienta)
class HerramientaAdmin(admin.ModelAdmin):
    list_display = ('codigo_activo', 'nombre', 'categoria', 'precio_diario_clp', 'horas_uso_acumuladas', 'estado_badge')
    list_filter = ('estado', 'categoria')
    search_fields = ('codigo_activo', 'nombre', 'categoria__nombre')
    ordering = ('codigo_activo',)
    actions = ['marcar_disponibles', 'marcar_mantenimiento']

    @admin.display(description='Tarifa Diaria')
    def precio_diario_clp(self, obj):
        return f"${obj.precio_por_dia:,} CLP".replace(',', '.')

    @admin.display(description='Estado Operativo')
    def estado_badge(self, obj):
        if obj.estado == 'DISPONIBLE':
            return format_html(
                '<span style="background-color: #16a34a; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
                'DISPONIBLE'
            )
        elif obj.estado == 'EN_USO':
            return format_html(
                '<span style="background-color: #2563eb; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
                'EN USO'
            )
        return format_html(
            '<span style="background-color: #dc2626; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            'MANTENIMIENTO'
        )

    @admin.action(description="Marcar equipos seleccionados como DISPONIBLES")
    def marcar_disponibles(self, request, queryset):
        actualizados = queryset.update(estado='DISPONIBLE')
        self.message_user(request, f"{actualizados} equipos cambiados a estado DISPONIBLE.")

    @admin.action(description="Enviar equipos seleccionados a MANTENIMIENTO")
    def marcar_mantenimiento(self, request, queryset):
        actualizados = queryset.update(estado='MANTENIMIENTO')
        self.message_user(request, f"{actualizados} equipos enviados a MANTENIMIENTO.")


# ==============================================================================
# 5. ALQUILERES / CONTRATOS
# ==============================================================================
@admin.register(Alquiler)
class AlquilerAdmin(admin.ModelAdmin):
    list_display = ('id', 'contratista', 'herramienta', 'responsable_obra', 'fecha_prestamo', 'fecha_devolucion_estimada', 'estado_contrato_badge')
    list_filter = ('estado', 'fecha_prestamo', 'fecha_devolucion_estimada')
    search_fields = ('contratista__razon_social', 'herramienta__nombre', 'herramienta__codigo_activo', 'responsable_obra', 'firma_digital')
    date_hierarchy = 'fecha_prestamo'
    readonly_fields = ('fecha_prestamo',)

    @admin.display(description='Estado del Contrato')
    def estado_contrato_badge(self, obj):
        if obj.estado == 'ACTIVO':
            return format_html(
                '<span style="background-color: #2563eb; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
                'ACTIVO'
            )
        elif obj.estado == 'DEVUELTO':
            return format_html(
                '<span style="background-color: #16a34a; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
                'DEVUELTO'
            )
        return format_html(
            '<span style="background-color: #dc2626; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            'ATRASADO / MOROSO'
        )


# ==============================================================================
# 6. MANTENIMIENTOS
# ==============================================================================
@admin.register(Mantenimiento)
class MantenimientoAdmin(admin.ModelAdmin):
    list_display = ('id', 'herramienta', 'tipo_badge', 'fecha_ingreso', 'proximo_mantenimiento', 'detalle')
    list_filter = ('tipo', 'fecha_ingreso', 'proximo_mantenimiento')
    search_fields = ('herramienta__nombre', 'herramienta__codigo_activo', 'detalle')
    date_hierarchy = 'fecha_ingreso'

    @admin.display(description='Tipo Mantención')
    def tipo_badge(self, obj):
        if obj.tipo == 'PREVENTIVO':
            return format_html(
                '<span style="background-color: #0284c7; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
                'PREVENTIVO'
            )
        return format_html(
            '<span style="background-color: #ea580c; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            'CORRECTIVO'
        )


# ==============================================================================
# 7. CARRO DE SOLICITUDES
# ==============================================================================
@admin.register(CarroItem)
class CarroItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'herramienta', 'cantidad', 'fecha_agregado')
    list_filter = ('fecha_agregado',)
    search_fields = ('usuario__username', 'herramienta__nombre', 'herramienta__codigo_activo')