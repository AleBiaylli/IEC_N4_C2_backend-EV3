from django.contrib.auth import get_user_model

User = get_user_model()

# Configuración del usuario Admin de Flota
USERNAME = 'admin_flota'
EMAIL = 'admin@buses.cl'
PASSWORD = 'Admin123_'
NOMBRE = 'Administrador'
APELLIDO = 'Flota'

# 1. Buscar si ya existe el usuario o crearlo
user, created = User.objects.get_or_create(
    username=USERNAME,
    defaults={
        'email': EMAIL,
        'first_name': NOMBRE,
        'last_name': APELLIDO,
        'is_staff': True,       # Permite acceso al panel /admin/
        'is_superuser': True    # Permite permisos totales
    }
)

if created:
    user.set_password(PASSWORD)
    print(f"--> Usuario '{USERNAME}' CREADO desde cero.")
else:
    print(f"--> Usuario '{USERNAME}' ya existía. Actualizando rol...")

# 2. Asignar el rol obligatorio ADMIN_FLOTA
if hasattr(user, 'role'):
    user.role = 'ADMIN_FLOTA'

user.save()

print("-" * 50)
print(f"   Usuario: {user.username}")
print(f"   Password: {PASSWORD}")
print(f"   Rol asignado: {getattr(user, 'role', 'N/A')}")
print("-" * 50)
print("¡Configuración de ADMIN_FLOTA completada con éxito!")