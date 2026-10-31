import os
import django
from datetime import timedelta

# Ajusta el módulo de configuración a la carpeta principal del proyecto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'IEC_N4_C2_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from api.models import (
    Contratista, CategoriaHerramienta, 
    Herramienta, Alquiler, Mantenimiento
)

User = get_user_model()

print("==================================================")
print("   INICIANDO POBLAMIENTO MASIVO - BUILDCORP AWS   ")
print("==================================================")

# -----------------------------------------------------------------------------
# 1. CATEGORÍAS DE HERRAMIENTAS (USANDO DEFAULTS PARA EVITAR DUPLICADOS)
# -----------------------------------------------------------------------------
cat_pesada, _ = CategoriaHerramienta.objects.get_or_create(
    nombre="Maquinaria de Obra Gruesa", 
    defaults={'descripcion': "Betoneras, placas compactadoras, cortadoras de pavimento y rodillos"}
)
cat_corte, _ = CategoriaHerramienta.objects.get_or_create(
    nombre="Corte y Demolición", 
    defaults={'descripcion': "Rotomartillos, martillos demoledores (Cango) y sierras industriales"}
)
cat_electricas, _ = CategoriaHerramienta.objects.get_or_create(
    nombre="Herramientas Eléctricas Básicas", 
    defaults={'descripcion': "Taladros, esmeriles angulares, lijadoras y atornilladores"}
)
cat_generacion, _ = CategoriaHerramienta.objects.get_or_create(
    nombre="Generación y Limpieza", 
    defaults={'descripcion': "Generadores eléctricos, compresores de aire, hidrolavadoras y torres"}
)
cat_elevacion, _ = CategoriaHerramienta.objects.get_or_create(
    nombre="Elevación y Carga", 
    defaults={'descripcion': "Elevadores de pluma, tecles eléctricos y transpaletas"}
)

print("[✓] Categorías creadas/verificadas exitosamente.")

# -----------------------------------------------------------------------------
# 2. HERRAMIENTAS CON TARIFAS DIARIAS VARIADAS EN CLP
# -----------------------------------------------------------------------------
# Estructura: (Código, Nombre, Categoría, Estado, Horas_Uso, Precio_Por_Dia_CLP)
herramientas_datos = [
    # --- Herramientas Eléctricas Básicas ($3.500 a $8.500) ---
    ("HERR-010", "Taladro Percutor 1/2 Pulgada 750W", cat_electricas, "DISPONIBLE", 15, 3500),
    ("HERR-010-B", "Taladro Percutor 1/2 Pulgada 750W", cat_electricas, "DISPONIBLE", 4, 3500),
    ("HERR-011", "Lijadora de Banda Industrial", cat_electricas, "DISPONIBLE", 8, 4800),
    ("HERR-005", "Esmeril Angular 9 Pulgadas 2200W", cat_electricas, "EN_USO", 30, 6200),
    ("HERR-005-B", "Esmeril Angular 9 Pulgadas 2200W", cat_electricas, "DISPONIBLE", 8, 6200),
    ("HERR-012", "Atornillador Inalámbrico 20V Max", cat_electricas, "EN_USO", 40, 8500),
    ("HERR-012-B", "Atornillador Inalámbrico 20V Max", cat_electricas, "DISPONIBLE", 10, 8500),

    # --- Generación y Limpieza ($7.500 a $26.000) ---
    ("HERR-021", "Compresor de Aire 50 Litros 2 HP", cat_generacion, "DISPONIBLE", 15, 7500),
    ("HERR-015", "Hidrolavadora Industrial 200 Bar", cat_generacion, "MANTENIMIENTO", 310, 11500),
    ("HERR-015-B", "Hidrolavadora Industrial 200 Bar", cat_generacion, "DISPONIBLE", 90, 11500),
    ("HERR-013", "Generador Monofásico 5.5 KVA Gasolina", cat_generacion, "DISPONIBLE", 150, 14800),
    ("HERR-013-B", "Generador Monofásico 5.5 KVA Gasolina", cat_generacion, "DISPONIBLE", 60, 14800),
    ("HERR-014", "Generador Trifásico 10 KVA Diésel", cat_generacion, "EN_USO", 210, 26000),

    # --- Corte y Demolición ($9.500 a $27.500) ---
    ("HERR-001", "Rotomartillo SDS-PLUS 800W", cat_corte, "EN_USO", 18, 9500),
    ("HERR-001-B", "Rotomartillo SDS-PLUS 800W", cat_corte, "DISPONIBLE", 5, 9500),
    ("HERR-001-C", "Rotomartillo SDS-PLUS 800W", cat_corte, "DISPONIBLE", 12, 9500),
    ("HERR-004", "Sierra Sensitiva 14 Pulgadas", cat_corte, "MANTENIMIENTO", 120, 13200),
    ("HERR-004-B", "Sierra Sensitiva 14 Pulgadas", cat_corte, "DISPONIBLE", 15, 13200),
    ("HERR-003", "Martillo Demoledor Cango 1500W Hex", cat_corte, "DISPONIBLE", 65, 21500),
    ("HERR-003-B", "Martillo Demoledor Cango 1500W Hex", cat_corte, "DISPONIBLE", 20, 21500),
    ("HERR-002", "Cortadora de Pavimento 13 HP", cat_corte, "DISPONIBLE", 42, 27500),
    ("HERR-002-B", "Cortadora de Pavimento 13 HP", cat_corte, "DISPONIBLE", 10, 27500),

    # --- Elevación y Carga ($10.500 a $17.500) ---
    ("HERR-017", "Transpaleta Hidráulica 2.5 Toneladas", cat_elevacion, "DISPONIBLE", 75, 10500),
    ("HERR-016", "Tecle Eléctrico de Cadena 1 Tonelada", cat_elevacion, "DISPONIBLE", 50, 17500),

    # --- Maquinaria de Obra Gruesa ($16.000 a $48.000) ---
    ("HERR-008", "Vibrador de Inmersión para Hormigón", cat_pesada, "DISPONIBLE", 25, 16000),
    ("HERR-008-B", "Vibrador de Inmersión para Hormigón", cat_pesada, "DISPONIBLE", 6, 16000),
    ("HERR-009", "Concretera / Betonera 130L 1.5 HP", cat_pesada, "DISPONIBLE", 95, 19500),
    ("HERR-009-B", "Concretera / Betonera 130L 1.5 HP", cat_pesada, "DISPONIBLE", 40, 19500),
    ("HERR-006", "Placa Compactadora 5.5 HP", cat_pesada, "DISPONIBLE", 85, 24000),
    ("HERR-006-B", "Placa Compactadora 5.5 HP", cat_pesada, "DISPONIBLE", 14, 24000),
    ("HERR-018", "Alisadora de Hormigón / Helicóptero 9 HP", cat_pesada, "DISPONIBLE", 15, 36000),
    ("HERR-007", "Rodillo Compactador Manual 600kg", cat_pesada, "EN_USO", 110, 48000),
    ("HERR-007-B", "Rodillo Compactador Manual 600kg", cat_pesada, "DISPONIBLE", 35, 48000),
]

herramientas_objetos = {}
for cod, nom, cat, est, hrs, precio in herramientas_datos:
    obj, _ = Herramienta.objects.update_or_create(
        codigo_activo=cod,
        defaults={
            'nombre': nom,
            'categoria': cat,
            'estado': est,
            'horas_uso_acumuladas': hrs,
            'precio_por_dia': precio
        }
    )
    herramientas_objetos[cod] = obj

print(f"[✓] {len(herramientas_datos)} Herramientas registradas con precios variados en CLP.")

# -----------------------------------------------------------------------------
# 3. USUARIOS Y CONTRATISTAS
# -----------------------------------------------------------------------------
user_admin, created = User.objects.get_or_create(
    username="admin_obra", 
    email="jefe@buildcorp.cl", 
    defaults={'role': "ADMIN", 'is_staff': True, 'first_name': 'Alexander', 'last_name': 'Lagos'}
)
if created:
    user_admin.set_password("Inacap2026!")
    user_admin.save()
else:
    user_admin.role = "ADMIN"
    user_admin.save()

user_c1, created1 = User.objects.get_or_create(
    username="contratista1", 
    email="contacto@constructora-andina.cl", 
    defaults={'role': "CONTRATISTA", 'first_name': 'Pedro', 'last_name': 'Valenzuela'}
)
if created1:
    user_c1.set_password("Inacap2026!")
    user_c1.save()
cont_1, _ = Contratista.objects.get_or_create(
    usuario=user_c1,
    defaults={'rut': "76.123.456-7", 'razon_social': "Constructora Andina SpA", 'telefono': "+56912345678", 'bloqueado_por_morosidad': False}
)

user_c2, created2 = User.objects.get_or_create(
    username="contratista2", 
    email="obras@ingenieria-sur.cl", 
    defaults={'role': "CONTRATISTA", 'first_name': 'Carlos', 'last_name': 'Fuentes'}
)
if created2:
    user_c2.set_password("Inacap2026!")
    user_c2.save()
cont_2, _ = Contratista.objects.get_or_create(
    usuario=user_c2,
    defaults={'rut': "77.987.654-3", 'razon_social': "Ingeniería del Sur Ltda", 'telefono': "+56987654321", 'bloqueado_por_morosidad': True}
)

print("[✓] Usuarios y Contratistas cargados.")

# -----------------------------------------------------------------------------
# 4. REGISTRO DE ALQUILERES DE MUESTRA
# -----------------------------------------------------------------------------
ahora = timezone.now()

Alquiler.objects.get_or_create(
    herramienta=herramientas_objetos["HERR-001"],
    contratista=cont_1,
    defaults={
        'fecha_prestamo': ahora - timedelta(days=2),
        'fecha_devolucion_estimada': ahora + timedelta(days=5),
        'responsable_obra': "Juan Pérez - Jefe de Terreno",
        'firma_digital': "FIRMA-ANDINA-2026-01",
        'estado': 'ACTIVO'
    }
)

Alquiler.objects.get_or_create(
    herramienta=herramientas_objetos["HERR-014"],
    contratista=cont_2,
    defaults={
        'fecha_prestamo': ahora - timedelta(days=15),
        'fecha_devolucion_estimada': ahora - timedelta(days=3),
        'responsable_obra': "Gonzalo Tapia - Capataz",
        'firma_digital': "FIRMA-INGSUR-2026-X",
        'estado': 'ATRASADO'
    }
)

print("[✓] Contratos de Alquiler poblados.")
print("==================================================")
print("   ¡POBLAMIENTO DE DATOS DIVERSIFICADO EXITOSO!   ")
print("==================================================")