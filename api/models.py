"""
MODELOS DE DATOS (API/MODELS.PY) - BUILDCORP

Estructura de Base de Datos Relacional en Tercera Forma Normal (3NF):
1. CustomUser: Usuario extendido de Django con soporte de roles (ADMIN / CONTRATISTA).
2. Contratista: Perfil de empresa asociado a usuario con bandera de morosidad.
3. CategoriaHerramienta: Clasificación técnica de activos de obra.
4. Herramienta: Equipos individuales, código de activo, horómetro y tarifa diaria en CLP.
5. Alquiler: Contratos de arrendamiento activos, histórico, responsable y firma digital.
6. Mantenimiento: Registro de intervenciones técnicas preventivas y correctivas.
7. CarroItem: Carrito de solicitudes de alquiler persistente por usuario.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class CustomUser(AbstractUser):
    """
    Modelo de Usuario Extendido.
    Hereda de AbstractUser para agregar autenticación personalizada y control RBAC.
    """
    ROLE_CHOICES = (
        ('ADMIN', 'Administrador de Obra'),
        ('CONTRATISTA', 'Contratista / Empresa Obra'),
    )
    # Define el rol principal del usuario para restringir o permitir accesos a vistas y API REST
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='CONTRATISTA',
        help_text="Rol de acceso asignado en el sistema"
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Contratista(models.Model):
    """
    Perfil del Cliente / Empresa Contratista.
    Relación 1 a 1 con CustomUser. Almacena RUT, Razón Social y estado de bloqueo por morosidad.
    """
    usuario = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='perfil_contratista',
        help_text="Usuario Django asociado al perfil del contratista"
    )
    rut = models.CharField(max_length=12, unique=True, help_text="RUT Empresa (ej: 76.123.456-7)")
    razon_social = models.CharField(max_length=150, help_text="Razón Social o Nombre de la Empresa")
    telefono = models.CharField(max_length=20, help_text="Teléfono de contacto de la empresa")
    # Bandera activada automáticamente cuando el contratista presenta arriendos atrasados
    bloqueado_por_morosidad = models.BooleanField(
        default=False, 
        help_text="Indica si el contratista está bloqueado para nuevos contratos debido a retrasos"
    )

    class Meta:
        verbose_name = "Contratista"
        verbose_name_plural = "Contratistas"

    def __str__(self):
        return f"{self.razon_social} ({self.rut})"


class CategoriaHerramienta(models.Model):
    """
    Categorización técnica de la flota de activos (Ej: Herramientas Eléctricas, Demolición, etc.).
    """
    nombre = models.CharField(max_length=100, unique=True, help_text="Nombre de la categoría")
    descripcion = models.TextField(blank=True, null=True, help_text="Descripción o alcance de la categoría")

    class Meta:
        verbose_name = "Categoría de Herramienta"
        verbose_name_plural = "Categorías de Herramientas"

    def __str__(self):
        return self.nombre


class Herramienta(models.Model):
    """
    Registro individual de activos físicos de obra.
    Permite controlar el estado operativo, horómetro de uso acumulado y tarifa diaria de arriendo.
    """
    ESTADO_CHOICES = (
        ('DISPONIBLE', 'Disponible'),
        ('EN_USO', 'En Uso / Arrendado'),
        ('MANTENIMIENTO', 'En Mantenimiento'),
    )

    codigo_activo = models.CharField(max_length=50, unique=True, help_text="Código único de activo (ej: HERR-001)")
    nombre = models.CharField(max_length=150, help_text="Nombre o modelo comercial de la herramienta")
    categoria = models.ForeignKey(
        CategoriaHerramienta, 
        on_delete=models.PROTECT, 
        related_name='herramientas',
        help_text="Categoría técnica asociada"
    )
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='DISPONIBLE', help_text="Estado de disponibilidad actual")
    horas_uso_acumuladas = models.PositiveIntegerField(default=0, help_text="Horómetro de uso acumulado en horas")
    precio_por_dia = models.PositiveIntegerField(default=15000, help_text="Precio de arriendo diario en Pesos Chilenos (CLP)")

    class Meta:
        verbose_name = "Herramienta"
        verbose_name_plural = "Herramientas"

    def __str__(self):
        return f"[{self.codigo_activo}] {self.nombre} - ${self.precio_por_dia}/día"


class Alquiler(models.Model):
    """
    Registro de Contrato de Arriendo de Equipos.
    Asocia un Contratista con una Herramienta específica, registrando responsable de obra y firma digital.
    """
    ESTADO_ALQUILER = (
        ('ACTIVO', 'Activo'),
        ('DEVUELTO', 'Devuelto'),
        ('ATRASADO', 'Atrasado / Moroso'),
    )

    contratista = models.ForeignKey(Contratista, on_delete=models.CASCADE, related_name='alquileres', help_text="Empresa contratista titular del arriendo")
    herramienta = models.ForeignKey(Herramienta, on_delete=models.CASCADE, related_name='alquileres', help_text="Activo físico asignado al contrato")
    fecha_prestamo = models.DateTimeField(default=timezone.now, help_text="Fecha y hora de inicio de entrega del activo")
    fecha_devolucion_estimada = models.DateTimeField(help_text="Fecha máxima pactada para la devolución sin mora")
    fecha_devolucion_real = models.DateTimeField(blank=True, null=True, help_text="Fecha y hora real en que se registró la devolución")
    responsable_obra = models.CharField(max_length=150, help_text="Nombre del profesional receptor o jefe de terreno")
    firma_digital = models.CharField(max_length=255, help_text="Hash o token de validación de la firma digital")
    estado = models.CharField(max_length=20, choices=ESTADO_ALQUILER, default='ACTIVO', help_text="Estado del contrato")

    class Meta:
        verbose_name = "Alquiler / Préstamo"
        verbose_name_plural = "Alquileres / Préstamos"

    def __str__(self):
        return f"Contrato #{self.id} - {self.contratista.razon_social} ({self.herramienta.nombre})"


class Mantenimiento(models.Model):
    """
    Bitácora de Intervenciones Técnicas en Herramientas.
    Permite programar o documentar mantenimientos preventivos y correctivos.
    """
    TIPO_CHOICES = (
        ('PREVENTIVO', 'Preventivo'),
        ('CORRECTIVO', 'Correctivo'),
    )

    herramienta = models.ForeignKey(Herramienta, on_delete=models.CASCADE, related_name='mantenimientos', help_text="Activo intervenido")
    fecha_ingreso = models.DateTimeField(default=timezone.now, help_text="Fecha y hora de ingreso al taller")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='PREVENTIVO', help_text="Tipo de mantención realizada")
    detalle = models.TextField(help_text="Descripción técnica del trabajo realizado o repuestos cambiados")
    proximo_mantenimiento = models.DateField(blank=True, null=True, help_text="Fecha programada para la siguiente revisión")

    class Meta:
        verbose_name = "Mantenimiento"
        verbose_name_plural = "Mantenimientos"

    def __str__(self):
        return f"Mantenimiento {self.tipo} - {self.herramienta.codigo_activo}"


class CarroItem(models.Model):
    """
    Carro de Solicitudes Persistente en Base de Datos.
    Guarda los activos seleccionados por el contratista antes de concretar la firma y el pago en Webpay.
    """
    usuario = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='carro_items',
        help_text="Usuario propietario del carrito"
    )
    herramienta = models.ForeignKey(
        Herramienta, 
        on_delete=models.CASCADE,
        help_text="Herramienta agregada al carrito"
    )
    cantidad = models.PositiveIntegerField(default=1, help_text="Cantidad de unidades requeridas")
    fecha_agregado = models.DateTimeField(auto_now_add=True, help_text="Marca temporal de adición al carro")

    class Meta:
        verbose_name = "Item del Carro"
        verbose_name_plural = "Items del Carro"
        unique_together = ('usuario', 'herramienta')

    def __str__(self):
        return f"{self.usuario.username} - {self.herramienta.nombre} (x{self.cantidad})"