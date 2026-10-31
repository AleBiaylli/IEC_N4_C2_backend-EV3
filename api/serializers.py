"""
Módulo encargado de transformar las instancias de los modelos en JSON y 
viceversa.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field

from .models import (
    CustomUser, Contratista, CategoriaHerramienta, 
    Herramienta, Alquiler, Mantenimiento
)

User = get_user_model()


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role', 'first_name', 'last_name']
        extra_kwargs = {'password': {'write_only': True}}


class ContratistaSerializer(serializers.ModelSerializer):
    usuario_datos = CustomUserSerializer(source='usuario', read_only=True)
    total_alquileres_activos = serializers.SerializerMethodField()

    class Meta:
        model = Contratista
        fields = ['id', 'usuario', 'usuario_datos', 'rut', 'razon_social', 'telefono', 'bloqueado_por_morosidad', 'total_alquileres_activos']

    @extend_schema_field(serializers.IntegerField())
    def get_total_alquileres_activos(self, obj):
        return obj.alquileres.filter(estado='ACTIVO').count()


class CategoriaHerramientaSerializer(serializers.ModelSerializer):
    total_herramientas = serializers.SerializerMethodField()

    class Meta:
        model = CategoriaHerramienta
        fields = ['id', 'nombre', 'descripcion', 'total_herramientas']

    @extend_schema_field(serializers.IntegerField())
    def get_total_herramientas(self, obj):
        return obj.herramientas.count()


class HerramientaSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Herramienta
        fields = ['id', 'codigo_activo', 'nombre', 'categoria', 'categoria_nombre', 'estado', 'estado_display', 'horas_uso_acumuladas']


class AlquilerSerializer(serializers.ModelSerializer):
    herramienta_detalle = HerramientaSerializer(source='herramienta', read_only=True)
    contratista_detalle = ContratistaSerializer(source='contratista', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Alquiler
        fields = [
            'id', 'contratista', 'contratista_detalle', 'herramienta', 
            'herramienta_detalle', 'fecha_prestamo', 'fecha_devolucion_estimada', 
            'fecha_devolucion_real', 'responsable_obra', 'firma_digital', 'estado', 'estado_display'
        ]

    def validate(self, data):
        # Validación de coherencia en fechas
        if data.get('fecha_devolucion_estimada') and data['fecha_devolucion_estimada'] <= timezone.now():
            raise serializers.ValidationError({"fecha_devolucion_estimada": "La fecha estimada de devolución debe ser futura."})
        return data


class MantenimientoSerializer(serializers.ModelSerializer):
    herramienta_codigo = serializers.ReadOnlyField(source='herramienta.codigo_activo')
    herramienta_nombre = serializers.ReadOnlyField(source='herramienta.nombre')

    class Meta:
        model = Mantenimiento
        # Se reemplaza 'fecha_mantenimiento' por el campo real 'fecha_ingreso'
        fields = ['id', 'herramienta', 'herramienta_codigo', 'herramienta_nombre', 'fecha_ingreso', 'tipo', 'detalle', 'proximo_mantenimiento']