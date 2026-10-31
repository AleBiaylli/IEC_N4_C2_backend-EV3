from api.models import CustomUser, Contratista

# Lista de contratistas ficticios para poblar la base de datos
contratistas_demo = [
    {
        "username": "Cristiano.OzvaldoSur",
        "email": "contacto@constructorasur.cl",
        "password": "Constructorasur26",
        "rut": "76.111.222-3",
        "razon_social": "Constructora del Sur SpA",
        "telefono": "+56911112222"
    },
    {
        "username": "JonasSanche.ingvial",
        "email": "proyectos@ingvial.cl",
        "password": "Vialaracuania64",
        "rut": "77.333.444-5",
        "razon_social": "Ingeniería Vial Araucanía Ltda.",
        "telefono": "+56933334444"
    },
    {
        "username": "Pedro.Sanchestemu",
        "email": "contacto@obrastemuco.cl",
        "password": "obramontajetemu",
        "rut": "78.555.666-7",
        "razon_social": "Obras y Montajes Temuco EIRL",
        "telefono": "+56955556666"
    },
    {
        "username": "Alexander.Gorbeayork",
        "email": "gerencia@constructoragorbea.cl",
        "password": "Gorbeayork07",
        "rut": "79.777.888-9",
        "razon_social": "Constructora Gorbea S.A.",
        "telefono": "+56977778888"
    }
]

# Proceso de creación en bucle
creados = 0
for data in contratistas_demo:
    if not CustomUser.objects.filter(username=data["username"]).exists():
        # 1. Crear el usuario CustomUser con rol CONTRATISTA
        user = CustomUser.objects.create_user(
            username=data["username"],
            email=data["email"],
            password=data["password"],
            role='CONTRATISTA'
        )
        
        # 2. Crear el perfil de Contratista asociado
        Contratista.objects.create(
            usuario=user,
            rut=data["rut"],
            razon_social=data["razon_social"],
            telefono=data["telefono"],
            bloqueado_por_morosidad=False
        )
        creados += 1
        print(f"✅ Contratista '{data['razon_social']}' ({data['username']}) creado con éxito.")
    else:
        print(f"⚠️ El usuario '{data['username']}' ya existía en la base de datos.")

print(f"\n🚀 Proceso finalizado. Se crearon {creados} nuevos contratistas.")
exit()