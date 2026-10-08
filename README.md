# Cooperativa de Agua Tuscapujio

Sistema de gestion de socios, lecturas, cobranza y caja, construido con Django y PostgreSQL.

## Requisitos

- Python 3
- PostgreSQL
- Una base de datos con el esquema de la cooperativa

## Configuracion local en PowerShell

Desde la carpeta del proyecto, crea tu archivo local `.env` a partir de la plantilla y sustituye los valores de la base de datos por los de tu instalacion; no publiques contrasenas ni claves:

```powershell
Copy-Item .env.example .env
```

`python-dotenv` carga automaticamente ese archivo al iniciar Django, asi que se usan tus valores locales sin hacerlo parte del repositorio.

```powershell
$env:DB_NAME = "cooperativa_agua"
$env:DB_USER = "postgres"
$env:DB_PASSWORD = "<contrasena-local>"
$env:DB_HOST = "127.0.0.1"
$env:DB_PORT = "5432"
$env:DJANGO_SECRET_KEY = python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Instala las dependencias y ejecuta el servidor:

```powershell
python -m pip install -r requirements.txt
python manage.py check
python manage.py runserver
```

Para un entorno que no sea local, define tambien `DJANGO_DEBUG=false` y `DJANGO_ALLOWED_HOSTS` como una lista de nombres de host separados por comas. La aplicacion requiere `DJANGO_SECRET_KEY` cuando `DEBUG` esta desactivado.

## Datos y copias de seguridad

El respaldo PostgreSQL local no se incluye en este repositorio: puede contener datos personales y hashes de contrasenas. Usa una copia de seguridad apropiada en tu propio entorno y no la publiques en GitHub.
