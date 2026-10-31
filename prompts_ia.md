# Registro de Apoyo con Herramientas de Inteligencia Artificial (IA)

**Proyecto:** BuildCorp - Sistema de Alquiler y Control de Herramientas (BuildCorp) 
**Estudiante:** Alexander Biaylli Lagos Allilef  
**Sección:** IEC_N4_C2  
**Herramienta Utilizada:** Gemini AI (Google)  

---

## PARTE 1: FASE DE DESARROLLO LOCAL Y LÓGICA BACKEND

### Bloque 1: Inicialización, Modelo de Datos y Arquitectura General del Proyecto BuildCorp

* **Prompt 1:**
  > *"Soy del proyecto 4 BuildCorp. Genérame el sistema en base a todo el proyecto anterior, obviamente modificando todo: serializadores, plantillas, administrador, URLs, URLs de la API, modelos, vistas y configuración, configurando la nueva base de datos y manteniendo las funciones de este pero adaptado al proyecto BuildCorp."*

* **Respuesta de la IA:**
  * Adaptación integral de la arquitectura Django 4.x y Django REST Framework (DRF) para la gestión de flota y arriendos en la industria de la construcción.
  * Diseño del modelo de datos relacional en Tercera Forma Normal (3NF): `CustomUser` (Control de Acceso Basado en Roles - RBAC), `Contratista`, `CategoriaHerramienta`, `Herramienta`, `Alquiler`, `Mantenimiento` y `CarroItem`.
  * Configuración de la capa de autenticación, control de acceso por roles (`ADMIN` y `CONTRATISTA`), puntos de entrada de la API RESTful y plantillas HTML adaptables diseñadas con Bootstrap 5.

---

### Bloque 2: Control de Acceso por Roles (RBAC), Permisos y Dashboard de Monitoreo

* **Prompt 2:**
  > *"Configura los permisos del sistema según el estado de sesión y rol:*
  >
  > *"Usuario no iniciado sesión (anónimo): Solo puede visualizar el catálogo. Si intenta solicitar una herramienta, debe ser redirigido a iniciar sesión.*
  >
  > *"Usuario Contratista: Puede ver el catálogo, su carrito de compras, realizar y firmar el contrato al solicitar herramientas y pagar. Puede ver sus solicitudes y contratos activos, devolver herramientas y cancelar contratos. No puede ver ni acceder al panel de control y monitoreo.*
  >
  > *"Usuario Administrador: Puede ver el panel de control y monitoreo con visualización del total de herramientas, disponibles, en uso y contratistas morosos/bloqueados en un gráfico integrado que se actualiza dinámicamente con cada cambio. Puede verificar morosidades y bloqueos, programar mantenimientos, ver catálogo y solicitar herramientas, ingresar al panel administrativo de Django para registrar herramientas en mantenimiento (preventivo o correctivo) y acceder a la documentación OpenAPI Docs."*

* **Respuesta de la IA:**
  * Implementación de decoradores `@login_required` y verificación de roles (`user.role == 'ADMIN'` vs `user.role == 'CONTRATISTA'`) en la capa de vistas.
  * Restricción de acceso al Dashboard mediante redirección automática si un Contratista intenta ingresar a las URLs del panel de monitoreo.
  * Desarrollo del Dashboard de Supervisión con indicadores clave de rendimiento (KPIs) e integración de un gráfico interactivo (Chart.js) que procesa en tiempo real los contadores de inventario (`DISPONIBLE`, `EN_USO`, `MANTENIMIENTO`) y estados de morosidad.
  * Habilitación de rutas protegidas para la documentación OpenAPI (Swagger / ReDoc) accesible por administradores.

---

### Bloque 3: Optimización del ORM y Resolución del Error `VariableDoesNotExist`

* **Prompt 3:**
  > *"Puedes verificar mi_carro.html y views.py" debido a la falla de renderizado de la categoría de la herramienta."*

* **Respuesta de la IA:**
  * Diagnóstico del origen de la excepción de variable no encontrada (`VariableDoesNotExist`), provocada por la evaluación diferida de claves foráneas en las plantillas de Django.
  * Optimización de consultas a la base de datos PostgreSQL aplicando `.select_related('categoria')` en las vistas `mi_carro_view` y `pago_web_view`, garantizando la precarga de datos de la categoría y eliminando el problema de consultas múltiples recurrentes (problema $N+1$).

---

### Bloque 4: Lógica Dinámica de Inventario, Conteo de Stock y Control de Estados

* **Prompt 4:**
  > *"Al hacer un contrato de una herramienta funciona, pero cuando hay más de la misma herramienta aparece como no disponible como si fuera una sola. Además, cuando dejamos una herramienta en mantenimiento, no aparece en mantenimiento y no se actualiza a no disponible en el catálogo."*
  >
  > *"Puedes verificar catalogo.html también."*
  >
  > *"Puedes mostrarme el bloque modificado en views.py"*

* **Respuesta de la IA:**
  * Rediseño de la vista `catalogo_herramientas_web` en `views.py` para calcular la disponibilidad real de inventario (`stock_disponible`) contando únicamente las unidades físicas en estado `'DISPONIBLE'`.
  * Actualización de la plantilla `catalogo.html` mediante etiquetas distintivas visuales e interactivas que diferencian entre:
    * **Disponible (Inventario: N):** Distintivo verde con botón de solicitud de arriendo habilitado.
    * **En Mantenimiento:** Distintivo amarillo con aviso de revisión y botón deshabilitado.
    * **Sin Stock / En Uso:** Distintivo rojo indicando equipo agotado.
  * Implementación de la asignación atómica de unidades por cantidad en la vista de procesamiento de solicitud (`procesar_checkout_html`).

---

### Bloque 5: Integración y Simulación de Pasarela de Pago Webpay / Transbank

* **Prompt 5:**
  > *"Agrega la simulación de pago con Webpay Transbank en el carrito antes de generar la firma digital del contrato de alquiler. Necesitamos que valide el pago, procese la orden y redirija a la confirmación del préstamo."*

* **Respuesta de la IA:**
  * Implementación de la vista de checkout y pasarela de pago simulando la SDK de Transbank Webpay Plus (`tbk_token`, redirección de retorno y respuesta de transacción aprobada).
  * Creación atómica de los registros en la tabla `Alquiler` al recibir el token de respuesta, generando la firma digital hash del contrato, actualizando el estado de la herramienta a `'EN_USO'` y vaciando el carrito activo (`CarroItem`).

---

### Bloque 6: Automatización de Negocio mediante Señales de Django (Sincronización Automática)

* **Prompt 6:**
  > *"coloqué en mantenimiento dos herramientas en el panel administrativo, pero solo marca 2 en mantención en el gráfico cuando puse 2 más."*
  >
  > *"La idea es no estar actualizando a cada rato con archivos JSON."*
  >
  > *"Puedes verificar models.py también."*
  >
  > *"Algo más. ¿No hace falta hacer migrate?"*

* **Respuesta de la IA:**
  * Implementación de la señal de Django (`@receiver(post_save, sender=Mantenimiento)`) al final del archivo `api/models.py`. Cada vez que se crea un registro de mantención en la tabla `Mantenimiento`, el estado del equipo cambia automáticamente a `MANTENIMIENTO`.
  * Aclaración conceptual indicando que las señales ejecutan lógica directa en Python sin modificar la estructura del esquema en la base de datos PostgreSQL, por lo que no es necesario ejecutar comandos de migración (`makemigrations` o `migrate`).

---

## PARTE 2: FASE DE DESPLIEGUE EN AWS EC2 Y PRODUCCIÓN

### Bloque 7: Configuraciones e Instalación en la Instancia AWS EC2 (Servidores, Base de Datos, Carga de Datos y Web Server)

* **Prompt 7:**
  > *"¿Puedes juntarme los comandos correspondientes para descargar el repositorio al servidor de Amazon AWS EC2, instalar todas las dependencias que corresponden, conectar con la base de datos PostgreSQL, activar el entorno virtual, configurar la carpeta `/var/www/buildcorp`, los permisos, la creación del superusuario, la carga y población de datos desde `backup_datos.json` y `backup_usuarios.json`, y por último la instalación y configuración de Gunicorn y Nginx?"*

* **Respuesta de la IA:**
  * Guía paso a paso para el aprovisionamiento completo en Ubuntu Server 22.04 LTS en AWS EC2:
    1. **Estructura y Permisos:** Creación del directorio `/var/www/buildcorp` y asignación de permisos de usuario (`sudo chown -R ubuntu:www-data /var/www/buildcorp`).
    2. **Clonación y Entorno Virtual:** Clonado del repositorio oficial en GitHub, creación del entorno virtual `.venv`, activación (`source .venv/bin/activate`) e instalación de dependencias vía `pip install -r requirements.txt`.
    3. **Base de Datos PostgreSQL:** Configuración e instalación de PostgreSQL, creación de la base de datos `buildcorp_db`, usuario y credenciales en `settings.py`.
    4. **Migraciones y Poblamiento:** Ejecución de `python manage.py migrate`, carga de fixtures iniciales `python manage.py loaddata backup_usuarios.json backup_datos.json` y creación interactiva del superusuario.
    5. **Servidor de Aplicaciones y Web Proxy:** Creación del archivo de servicio `gunicorn.service` administrado por `systemctl`, instalación y configuración de Nginx (`/etc/nginx/sites-available/buildcorp`) como proxy inverso redirigiendo la IP pública al socket de Gunicorn en el puerto 80.

---

### Bloque 8: Sincronización del Repositorio Git y Resolución de Conflictos en la Instancia EC2

* **Prompt 8:**
  > *"Entonces para activar el entorno virtual (env). En el servidor, ir primero al directorio `cd /var/www/buildcorp`, luego activar el entorno con `source .venv/bin/activate`, descartar o verificar cambios con `git checkout -- <archivo>`, descargar el código actualizado desde GitHub con `git pull origin main`, y por último reiniciar el servicio de aplicaciones con `sudo systemctl restart gunicorn`"*

* **Respuesta de la IA:**
  * Diagnóstico del bloqueo en la sincronización de Git causado por modificaciones locales temporales realizadas en el servidor en la nube.
  * Confirmación de la secuencia de comandos ejecutados en la consola remota SSH de la instancia Ubuntu EC2:
    1. Acceso al directorio raíz de la aplicación: `cd /var/www/buildcorp`
    2. Activación del entorno virtual de Python: `source .venv/bin/activate`
    3. Descarte de cambios locales no deseados en modelos y plantillas: `git checkout -- api/models.py`
    4. Sincronización e incorporación del código desde GitHub: `git pull origin main`
    5. Reinicio del servicio WSGI para aplicar los cambios en producción: `sudo systemctl restart gunicorn`
