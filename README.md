# BuildCorp - Sistema de Alquiler y Control de Herramientas (BuildCorp)

Sistema backend completo desarrollado en **Django 4.x** y **Django REST Framework (DRF)** para la gestión de flota de herramientas, arriendos para contratistas y control de mantenimientos preventivos y correctivos en obras de construcción.

---
## Nota: El archivo .md de Prompts está en la raíz del proyecto como "prompts_ia"
## Servidor en Producción (AWS EC2)

- **IP Pública del Portal Web:** `http://44.220.131.111/`
- **Panel Administrativo (Django Admin):** `http://44.220.131.111/admin/`
- **Catálogo de Equipos:** `http://44.220.131.111/catalogo/`
- **Carro de Solicitud:** `http://44.220.131.111/carro/`
- **Documentación OpenAPI (Swagger):** `http://44.220.131.111/api/docs/`

---

## Arquitectura y Tecnologías

- **Backend Framework:** Django 4.2 / Django REST Framework (DRF)
- **Base de Datos:** PostgreSQL
- **Servidor de Aplicaciones:** Gunicorn (WSGI)
- **Servidor Web / Reverse Proxy:** Nginx
- **Infraestructura Cloud:** AWS EC2 (Ubuntu Server 22.04 LTS)
- **Seguridad:** Control de Acceso Basado en Roles (RBAC: `ADMIN` y `CONTRATISTA`)
- **SimpleJWT (djangorestframework-simplejwt):** Autenticación basada en Tokens JSON Web (JWT) para el consumo seguro e independiente de los endpoints de la API REST.
- **CoreApi / OpenAPI:** Esquematización y generación de la documentación interactiva de la API endpoints mediante Swagger UI y ReDoc.
- **Bootstrap 5:** Framework de diseño front-end para la creación de plantillas responsivas, modales de confirmación, tablas dinamizadas y tarjetas visuales de inventario.
---

## Características Principales

1. **Control de Acceso Basado en Roles (RBAC):**
   - **Usuario Anónimo:** Visualización del catálogo de herramientas de obra.
   - **Usuario Contratista:** Selección de equipos, carrito persistente, simulación de pasarela Webpay/Transbank, firma digital de contratos, devolución de activos y gestión de arriendos.
   - **Usuario Administrador:** Acceso completo al Dashboard de monitoreo con gráficos en tiempo real, gestión de morosidades, programación de mantenimientos y administración centralizada mediante Django Admin y OpenAPI Docs.

2. **Gestión de Flota e Inventario Dinámico:**
   - Cálculo en tiempo real de disponibilidad por modelo de herramienta (`DISPONIBLE`, `EN_USO`, `MANTENIMIENTO`).
   - Seguimiento de horómetros acumulados y tarifarios diarios en CLP.

3. **Automatización de Negocio (Django Signals):**
   - Transición automática del estado del activo a `MANTENIMIENTO` al registrar bitácoras técnicas mediante el evento `@receiver(post_save, sender=Mantenimiento)`.

4. **Pasarela de Pago y Firma Digital:**
   - Procesamiento atómico de arriendos con simulación de pasarela Transbank Webpay Plus y generación de firmas digitales hash por contrato.

---

## Instrucciones de Desarrollo Local

### 1. Clonar el repositorio
```bash
git clone https://github.com/AleBiaylli/IEC_N4_C2_backend-EV3.git
cd IEC_N4_C2_backend-EV3
```

### 2. Crear y activar el entorno virtual
```bash
python -m venv .venv

# En Windows (PowerShell):
.venv\Scripts\activate

# En Linux/macOS:
source .venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar e integrar la base de datos local
```bash
python manage.py migrate
python manage.py loaddata backup_usuarios.json backup_datos.json
```

### 5. Iniciar el servidor de desarrollo
```bash
python manage.py runserver
```

El proyecto estará accesible localmente en `http://127.0.0.1:8000/`.
Y la IP Pública de AWS EC2 funcional en `http://44.220.131.111/`.
En caso de cambio de cambio de la ip pública, settings, se definen en ALLOWED_HOSTS = ['44.220.131.111', '52.90.156.139', 'localhost', '127.0.0.1']

---

## Instrucciones de Despliegue en AWS EC2 (Producción)

### 1. Preparación de directorio y permisos en el servidor
```bash
sudo mkdir -p /var/www/buildcorp
sudo chown -R ubuntu:www-data /var/www/buildcorp
cd /var/www/buildcorp
```

### 2: Configurar PostgreSQL


```bash
sudo -u postgres psql

 - **Una vez que aparezca el prompt postgres=#, ejecuta las siguientes consultas SQL una por una o todas juntas**


SQL
CREATE DATABASE bd_buildcorp;
CREATE USER postgres WITH PASSWORD 'Biaylli20070';
ALTER ROLE postgres SET client_encoding TO 'utf8';
ALTER ROLE postgres SET default_transaction_isolation TO 'read committed';
ALTER ROLE postgres SET timezone TO 'America/Santiago';
GRANT ALL PRIVILEGES ON DATABASE bd_buildcorp TO postgres;
\q
```

### 3. Clonar repositorio e instalar entorno virtual
```bash
git clone https://github.com/AleBiaylli/IEC_N4_C2_backend-EV3.git .
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt #dependencias
```

### 4. Migraciones, carga de datos y estáticos
```bash
python manage.py migrate
python manage.py loaddata backup_usuarios.json backup_datos.json
python manage.py collectstatic --noinput
```

### 5. Configurar servicio Gunicorn (`/etc/systemd/system/gunicorn.service`)
```ini
[Unit]
Description=Gunicorn daemon for BuildCorp Django Application
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/var/www/buildcorp
ExecStart=/var/www/buildcorp/.venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/var/www/buildcorp/buildcorp.sock buildcorp.wsgi:application

[Install]
WantedBy=multi-user.target
```

Habilitar servicio:
```bash
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

### 6. Configurar Nginx (`/etc/nginx/sites-available/buildcorp`)
```nginx
server {
    listen 80;
    server_name 44.220.131.111;

    location /static/ {
        alias /var/www/buildcorp/staticfiles/;
    }

    location /media/ {
        alias /var/www/buildcorp/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/buildcorp/buildcorp.sock;
    }
}
```

Activar sitio y reiniciar Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/buildcorp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Flujo de Sincronización y Actualización en EC2

Para aplicar cambios nuevos del repositorio local en la instancia EC2:

```bash
cd /var/www/buildcorp
source .venv/bin/activate
git checkout -- .
git pull origin main
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

---

## Datos del Autor

- **Desarrollador:** Alexander Biaylli Lagos Allilef
- **Sección:** IEC_N4_C2
- **Proyecto:** BuildCorp (Evaluación 3 - Backend)
