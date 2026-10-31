"""
VISTAS Y LÓGICA DE NEGOCIO (API/VIEWS.PY) - BUILDCORP AWS

Contenido principal:
1. Permisos RBAC (IsAdminOrReadOnly, IsOwnerContratistaOrAdmin).
2. Endpoints API RESTful con ModelViewSet (Django REST Framework).
3. Vistas del Portal Web (Dashboard, Catálogo, Mis Solicitudes, Alquileres).
4. Módulo de Autenticación, Carro Persistente y Pasarela Webpay Plus.
"""

from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import (
    CustomUser, Contratista, CategoriaHerramienta, 
    Herramienta, Alquiler, Mantenimiento, CarroItem
)
from .serializers import (
    CustomUserSerializer, ContratistaSerializer, 
    CategoriaHerramientaSerializer, HerramientaSerializer, 
    AlquilerSerializer, MantenimientoSerializer
)

# ==============================================================================
# 1. PERMISOS PERSONALIZADOS DE SEGURIDAD (RBAC)
# ==============================================================================

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permite lectura pública (GET, HEAD, OPTIONS) y restringe operaciones de escritura
    (POST, PUT, DELETE) exclusivamente a usuarios con rol ADMIN o superusuarios (is_staff).
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and (
            getattr(request.user, 'role', None) == 'ADMIN' or request.user.is_staff
        )


class IsOwnerContratistaOrAdmin(permissions.BasePermission):
    """
    Permite a los administradores ver todos los objetos, mientras que los contratistas
    solo pueden consultar u operar sobre sus propios registros de arriendo.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or getattr(request.user, 'role', None) == 'ADMIN':
            return True
        contratista_perfil = getattr(request.user, 'perfil_contratista', None)
        return contratista_perfil is not None and obj.contratista == contratista_perfil


# ==============================================================================
# 2. ENDPOINTS RESTFUL (DRF VIEWSETS - OPERACIONES CRUD COMPLETAS)
# ==============================================================================

class CategoriaHerramientaViewSet(viewsets.ModelViewSet):
    """
    API REST para la gestión CRUD de Categorías de Herramientas.
    """
    queryset = CategoriaHerramienta.objects.all()
    serializer_class = CategoriaHerramientaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre']


class HerramientaViewSet(viewsets.ModelViewSet):
    """
    API REST para la gestión de Flota y Equipos.
    Incluye filtrado por disponibilidad/categoría y acciones personalizadas para mantenimiento.
    """
    queryset = Herramienta.objects.select_related('categoria').all()
    serializer_class = HerramientaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'categoria']
    search_fields = ['codigo_activo', 'nombre', 'categoria__nombre']
    ordering_fields = ['nombre', 'horas_uso_acumuladas', 'codigo_activo']

    @action(detail=False, methods=['get'])
    def disponibles(self, request):
        """Endpoint personalizado: Devuelve únicamente las herramientas con estado DISPONIBLE."""
        disponibles = self.get_queryset().filter(estado='DISPONIBLE')
        serializer = self.get_serializer(disponibles, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrReadOnly])
    def enviar_a_mantenimiento(self, request, pk=None):
        """Endpoint personalizado: Modifica el estado del activo a MANTENIMIENTO y crea la bitácora."""
        with transaction.atomic():
            herramienta = Herramienta.objects.select_for_update().get(pk=pk)
            if herramienta.estado == 'EN_USO':
                return Response(
                    {"error": "No se puede enviar a mantenimiento una herramienta actualmente prestada."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            herramienta.estado = 'MANTENIMIENTO'
            herramienta.save()

            Mantenimiento.objects.create(
                herramienta=herramienta,
                tipo='PREVENTIVO',
                detalle=request.data.get('detalle', 'Mantenimiento preventivo programado'),
                proximo_mantenimiento=timezone.now().date() + timedelta(days=30)
            )

            return Response({
                "status": "Herramienta enviada a mantenimiento correctamente.",
                "herramienta": herramienta.codigo_activo
            })


class ContratistaViewSet(viewsets.ModelViewSet):
    """
    API REST para la administración de empresas Contratistas y gestión de desbloqueos por morosidad.
    """
    queryset = Contratista.objects.select_related('usuario').all()
    serializer_class = ContratistaSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['bloqueado_por_morosidad']
    search_fields = ['rut', 'razon_social', 'usuario__username']

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrReadOnly])
    def desbloquear(self, request, pk=None):
        """Endpoint exclusivo Admin: Restablece el acceso de un contratista bloqueado por morosidad."""
        contratista = self.get_object()
        contratista.bloqueado_por_morosidad = False
        contratista.save()
        return Response({"status": f"Contratista {contratista.razon_social} ha sido desbloqueado."})


class AlquilerViewSet(viewsets.ModelViewSet):
    """
    API REST para consultar y gestionar Contratos de Alquiler.
    Aplica filtrado por el rol del usuario (Contratista ve solo lo suyo, Admin ve todo).
    """
    queryset = Alquiler.objects.select_related('contratista', 'herramienta', 'herramienta__categoria').all()
    serializer_class = AlquilerSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerContratistaOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'contratista', 'herramienta']
    search_fields = ['responsable_obra', 'herramienta__nombre', 'contratista__razon_social']
    ordering_fields = ['fecha_prestamo', 'fecha_devolucion_estimada']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or getattr(user, 'role', None) == 'ADMIN':
            return self.queryset
        contratista = getattr(user, 'perfil_contratista', None)
        if contratista:
            return self.queryset.filter(contratista=contratista)
        return Alquiler.objects.none()


class MantenimientoViewSet(viewsets.ModelViewSet):
    """
    API REST para el registro técnico de mantenimientos.
    """
    queryset = Mantenimiento.objects.select_related('herramienta').all()
    serializer_class = MantenimientoSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['tipo', 'herramienta']
    search_fields = ['herramienta__nombre', 'detalle']


# ==============================================================================
# 3. VISTAS DEL PORTAL WEB (HTML BOOTSTRAP)
# ==============================================================================

def landing_page_web(request):
    """Vista pública de bienvenida."""
    return render(request, 'landing.html')


@login_required(login_url='login_web')
def dashboard_principal(request):
    """
    Panel de Monitoreo de Flota. EXCLUSIVO PARA ROL ADMIN / STAFF.
    Calcula métricas clave en vivo: disponibilidad, equipos en uso y morosidad.
    """
    if not (request.user.is_staff or getattr(request.user, 'role', '') == 'ADMIN'):
        messages.error(request, "Acceso restringido: El panel de monitoreo es exclusivo para Administradores.")
        return redirect('catalogo_web')

    total_herramientas = Herramienta.objects.count()
    en_uso = Herramienta.objects.filter(estado='EN_USO').count()
    disponibles = Herramienta.objects.filter(estado='DISPONIBLE').count()
    en_mantenimiento = Herramienta.objects.filter(estado='MANTENIMIENTO').count()
    contratistas_bloqueados = Contratista.objects.filter(bloqueado_por_morosidad=True).count()

    context = {
        'total_herramientas': total_herramientas,
        'en_uso': en_uso,
        'disponibles': disponibles,
        'en_mantenimiento': en_mantenimiento,
        'contratistas_bloqueados': contratistas_bloqueados,
    }
    return render(request, 'dashboard.html', context)


def catalogo_herramientas_web(request):
    """
    Catálogo interactivo de herramientas accesible para visitantes y usuarios autenticados.
    Permite filtrar por categoría y estado de disponibilidad.
    """
    categoria_id = request.GET.get('categoria')
    estado = request.GET.get('estado')

    herramientas = Herramienta.objects.select_related('categoria').all()

    if categoria_id:
        herramientas = herramientas.filter(categoria_id=categoria_id)
    if estado:
        herramientas = herramientas.filter(estado=estado)

    categorias = CategoriaHerramienta.objects.all()

    return render(request, 'catalogo.html', {
        'herramientas': herramientas,
        'categorias': categorias
    })


@login_required(login_url='login_web')
def lista_alquileres_web(request):
    """
    Panel Global de Alquileres & Control de Morosidad. EXCLUSIVO PARA ADMINISTRADORES.
    Verifica automáticamente contratos vencidos, los marca como ATRASADOS y bloquea al contratista.
    """
    user = request.user
    es_admin = user.is_staff or getattr(user, 'role', None) == 'ADMIN'

    if not es_admin:
        messages.warning(
            request, 
            "Acceso restringido: El panel global de alquileres y morosidad es exclusivo para Administradores."
        )
        return redirect('catalogo_web')

    ahora = timezone.now()
    # Identificar contratos con fecha de devolución superada
    alquileres_vencidos = Alquiler.objects.filter(estado='ACTIVO', fecha_devolucion_estimada__lt=ahora)

    # Actualizar estado de morosidad de forma atómica
    with transaction.atomic():
        for alquiler in alquileres_vencidos:
            alquiler.estado = 'ATRASADO'
            alquiler.save()
            alquiler.contratista.bloqueado_por_morosidad = True
            alquiler.contratista.save()

    alquileres = Alquiler.objects.select_related('contratista', 'herramienta').all().order_by('-fecha_prestamo')

    return render(request, 'alquileres.html', {
        'alquileres': alquileres,
        'es_admin': es_admin
    })


@login_required(login_url='login_web')
def mis_alquileres_web(request):
    """
    Vista personal del Contratista. Muestra únicamente sus propias solicitudes de arriendo.
    """
    contratista = getattr(request.user, 'perfil_contratista', None)
    if not contratista:
        alquileres = Alquiler.objects.none()
    else:
        alquileres = Alquiler.objects.filter(contratista=contratista).select_related('herramienta').order_by('-fecha_prestamo')

    return render(request, 'mis_alquileres.html', {'alquileres': alquileres})


@login_required(login_url='login_web')
def devolver_alquiler_web(request, alquiler_id):
    """
    Procesa la devolución de una herramienta prestada.
    Marca el contrato como DEVUELTO, libera el activo a DISPONIBLE, actualiza el horómetro
    y desbloquea al contratista si no mantiene otras moras pendientes.
    """
    alquiler = get_object_or_404(Alquiler, id=alquiler_id)
    es_admin = request.user.is_staff or getattr(request.user, 'role', None) == 'ADMIN'
    contratista = getattr(request.user, 'perfil_contratista', None)

    if not es_admin and (not contratista or alquiler.contratista != contratista):
        messages.error(request, "No tiene permisos para modificar este contrato.")
        return redirect('mis_alquileres_web')

    if request.method == 'POST':
        with transaction.atomic():
            ahora = timezone.now()
            alquiler.fecha_devolucion_real = ahora
            alquiler.estado = 'DEVUELTO'
            alquiler.save()

            # Liberación del activo y cálculo de horas de uso
            herramienta = alquiler.herramienta
            herramienta.estado = 'DISPONIBLE'
            horas_usadas = int((ahora - alquiler.fecha_prestamo).total_seconds() // 3600)
            herramienta.horas_uso_acumuladas += max(horas_usadas, 1)
            herramienta.save()

            # Evaluación de morosidad pendiente
            moras_pendientes = Alquiler.objects.filter(contratista=alquiler.contratista, estado='ATRASADO').exists()
            if not moras_pendientes:
                alquiler.contratista.bloqueado_por_morosidad = False
                alquiler.contratista.save()

        messages.success(request, f"Devolución registrada exitosamente para '{alquiler.herramienta.nombre}'.")
        return redirect('alquileres_web' if es_admin else 'mis_alquileres_web')

    return render(request, 'confirmar_devolucion_cancelacion.html', {
        'alquiler': alquiler, 
        'accion': 'devolver'
    })


@login_required(login_url='login_web')
def cancelar_alquiler_web(request, alquiler_id):
    """
    Permite cancelar una solicitud activa y liberar inmediatamente la herramienta a la flota.
    """
    alquiler = get_object_or_404(Alquiler, id=alquiler_id)
    es_admin = request.user.is_staff or getattr(request.user, 'role', None) == 'ADMIN'
    contratista = getattr(request.user, 'perfil_contratista', None)

    if not es_admin and (not contratista or alquiler.contratista != contratista):
        messages.error(request, "No tiene permisos para cancelar esta solicitud.")
        return redirect('mis_alquileres_web')

    if request.method == 'POST':
        with transaction.atomic():
            herramienta = alquiler.herramienta
            herramienta.estado = 'DISPONIBLE'
            herramienta.save()

            alquiler.delete()

        messages.info(request, f"Solicitud para '{herramienta.nombre}' cancelada correctamente.")
        return redirect('alquileres_web' if es_admin else 'mis_alquileres_web')

    return render(request, 'confirmar_devolucion_cancelacion.html', {
        'alquiler': alquiler, 
        'accion': 'cancelar'
    })


# ==============================================================================
# 4. AUTENTICACIÓN, CARRO PERSISTENTE Y PASARELA WEBPAY PLUS
# ==============================================================================

def login_web_view(request):
    """
    Inicio de sesión unificado. Carga el carro guardado en BD a la sesión y redirige según el rol.
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Cargar carro persistente guardado en la base de datos
            items_bd = list(CarroItem.objects.filter(usuario=user).values_list('herramienta_id', flat=True))
            request.session['carro_items'] = items_bd

            if user.is_staff or getattr(user, 'role', None) == 'ADMIN':
                messages.success(request, f"¡Sesión iniciada como Administrador ({user.username})!")
                return redirect('dashboard_admin')
            else:
                messages.success(request, f"¡Bienvenido, Contratista {user.username}!")
                return redirect('catalogo_web')
        else:
            messages.error(request, "Usuario o contraseña incorrectos. Verifique sus credenciales.")
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})


def logout_web_view(request):
    """Cierra la sesión conservando el carro persistente en la BD."""
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente. Tu carro se mantendrá guardado.")
    return redirect('home')


def registro_web_view(request):
    """Registro público para nuevos usuarios contratistas."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'CONTRATISTA'
            user.save()
            login(request, user)
            messages.success(request, "Cuenta de Contratista creada exitosamente.")
            return redirect('catalogo_web')
    else:
        form = UserCreationForm()
    return render(request, 'registro.html', {'form': form})


def agregar_al_carro_html(request, herramienta_id):
    """
    Registra una herramienta en el carro persistente (BD CarroItem) y en la sesión activa.
    """
    if not request.user.is_authenticated:
        messages.warning(
            request, 
            "Para solicitar herramientas y generar un contrato de obra debe iniciar sesión como Contratista."
        )
        return redirect('login_web')

    herramienta = get_object_or_404(Herramienta, id=herramienta_id)

    # Persistir en la tabla CarroItem de la base de datos
    CarroItem.objects.get_or_create(usuario=request.user, herramienta=herramienta)

    # Actualizar la sesión
    carro = request.session.get('carro_items', [])
    if herramienta_id not in carro:
        carro.append(herramienta_id)
        request.session['carro_items'] = carro
        messages.success(request, f"'{herramienta.nombre}' añadida a la solicitud de contrato.")

    return redirect('mi_carro')


@login_required(login_url='login_web')
def mi_carro_view(request):
    """Muestra los activos agregados sincronizando la base de datos con la sesión."""
    items_bd = list(CarroItem.objects.filter(usuario=request.user).values_list('herramienta_id', flat=True))
    carro_session = request.session.get('carro_items', [])
    carro_ids = list(set(items_bd + carro_session))
    request.session['carro_items'] = carro_ids

    items = Herramienta.objects.filter(id__in=carro_ids)
    return render(request, 'mi_carro.html', {'items': items})


@login_required(login_url='login_web')
def eliminar_item_carro_view(request, item_id):
    """Elimina un activo del carrito tanto en la BD como en la sesión."""
    CarroItem.objects.filter(usuario=request.user, herramienta_id=item_id).delete()

    carro = request.session.get('carro_items', [])
    if item_id in carro:
        carro.remove(item_id)
        request.session['carro_items'] = carro
        messages.info(request, "Herramienta eliminada de la solicitud.")

    return redirect('mi_carro')


@login_required(login_url='login_web')
def editar_item_carro_view(request, item_id):
    return redirect('mi_carro')


@login_required(login_url='login_web')
def pago_web_view(request):
    """
    Paso 2 del Checkout: Muestra el resumen del contrato, valida morosidad,
    calcula la tarifa dinámica (precio_diario * cantidad * dias) y deriva al Portal Webpay Plus si es POST.
    """
    contratista = getattr(request.user, 'perfil_contratista', None)
    if contratista and contratista.bloqueado_por_morosidad:
        messages.error(
            request, 
            "SOLICITUD RECHAZADA: Su empresa registra devoluciones atrasadas y morosidad activa."
        )
        return redirect('mi_carro')

    items_bd = list(CarroItem.objects.filter(usuario=request.user).values_list('herramienta_id', flat=True))
    carro_session = request.session.get('carro_items', [])
    carro_ids = list(set(items_bd + carro_session))
    request.session['carro_items'] = carro_ids

    items = Herramienta.objects.filter(id__in=carro_ids)

    if not items.exists():
        messages.error(request, "El carro de solicitudes está vacío.")
        return redirect('catalogo_web')

    herramienta_base = items.first()
    # Contar stock total en vivo disponible de ese mismo tipo de equipo
    stock_disponible = Herramienta.objects.filter(
        nombre=herramienta_base.nombre, 
        estado='DISPONIBLE'
    ).count()

    # Si el contratista confirma la firma (envío POST), calcular monto real y pasar a Webpay
    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad', 1))
        dias = int(request.POST.get('dias_estimados', 7))
        precio_diario = herramienta_base.precio_por_dia
        
        # Cálculo de la tarifa total del contrato
        monto_total = cantidad * dias * precio_diario

        context_webpay = {
            'cantidad': cantidad,
            'responsable_obra': request.POST.get('responsable_obra', request.user.username),
            'dias_estimados': dias,
            'firma_digital': request.POST.get('firma_digital', f'FIRMA-DIGITAL-{request.user.id}-2026'),
            'monto_total': monto_total,
            'precio_diario': precio_diario,
            'herramienta_nombre': herramienta_base.nombre
        }
        return render(request, 'webpay_portal.html', context_webpay)

    return render(request, 'pago.html', {
        'items': items,
        'stock_disponible': stock_disponible
    })


@login_required(login_url='login_web')
@transaction.atomic
def procesar_checkout_html(request):
    """
    Recepción y procesamiento de la transacción desde Webpay Plus.
    Asigna atómicamente las N unidades disponibles a estado EN_USO, genera los contratos y vacía el carro.
    """
    if request.method == 'POST':
        items_bd = list(CarroItem.objects.filter(usuario=request.user).values_list('herramienta_id', flat=True))
        carro_session = request.session.get('carro_items', [])
        carro = list(set(items_bd + carro_session))

        if not carro:
            messages.error(request, "El carro de solicitudes está vacío.")
            return redirect('mi_carro')

        contratista, _ = Contratista.objects.get_or_create(
            usuario=request.user,
            defaults={
                'rut': '76.123.456-7',
                'razon_social': f'Empresa {request.user.username}',
                'telefono': '+56912345678'
            }
        )

        if contratista.bloqueado_por_morosidad:
            messages.error(request, "Operación bloqueada por morosidad activa.")
            return redirect('mi_carro')

        responsable = request.POST.get('responsable_obra', request.user.username)
        firma = request.POST.get('firma_digital', 'FIRMA-DIGITAL-001')
        dias = int(request.POST.get('dias_estimados', 7))
        cantidad_solicitada = int(request.POST.get('cantidad', 1))

        herramienta_base = get_object_or_404(Herramienta, id=carro[0])

        # Selección segura con bloqueo de filas para prevenir colisiones de stock
        disponibles = Herramienta.objects.select_for_update().filter(
            nombre=herramienta_base.nombre,
            estado='DISPONIBLE'
        )

        if disponibles.count() < cantidad_solicitada:
            messages.error(
                request, 
                f"No hay suficiente stock. Solicitó {cantidad_solicitada} unidades, pero solo hay {disponibles.count()} disponibles."
            )
            return redirect('pago_web')

        unidades_asignadas = disponibles[:cantidad_solicitada]
        alquileres_creados = []

        # Crear contrato individual por cada activo físico entregado
        for herramienta in unidades_asignadas:
            herramienta.estado = 'EN_USO'
            herramienta.save()

            alquiler = Alquiler.objects.create(
                contratista=contratista,
                herramienta=herramienta,
                fecha_devolucion_estimada=timezone.now() + timedelta(days=dias),
                responsable_obra=responsable,
                firma_digital=firma,
                estado='ACTIVO'
            )
            alquileres_creados.append(alquiler)

        # Limpiar carro persistente y de sesión al concretar la transacción exitosamente
        CarroItem.objects.filter(usuario=request.user).delete()
        request.session['carro_items'] = []

        messages.success(request, f"¡Pago Webpay Exitoso! Se generaron {len(alquileres_creados)} contratos de arriendo.")
        return redirect('confirmacion_compra', alquiler_id=alquileres_creados[0].id)

    return redirect('mi_carro')


@login_required(login_url='login_web')
def confirmacion_compra_view(request, alquiler_id):
    """Paso 3 del Checkout: Muestra la confirmación final del contrato emitiendo el ticket de entrega."""
    alquiler = get_object_or_404(Alquiler, id=alquiler_id)
    return render(request, 'confirmacion.html', {'alquiler': alquiler})


def pagina_no_encontrada_view(request, exception=None):
    """Vista personalizada para la captura de rutas no encontradas (Error HTTP 404)."""
    return render(request, '404.html', status=404)


# ==============================================================================
# 5. CLASES REST API COMPLEMENTARIAS
# ==============================================================================

class CustomTokenObtainPairView(TokenObtainPairView):
    pass

class CarroHerramientasView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        return Response({"status": "Carro activo API REST"})

class CheckoutAlquilerView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        return Response({"status": "Checkout realizado"})

class MisAlquileresView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        return Response({"status": "Listado de alquileres contratista"})

class CambiarEstadoAlquilerView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    def patch(self, request, pk=None):
        return Response({"status": "Estado actualizado"})