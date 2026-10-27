# Despliegue gratuito en PythonAnywhere

Este proyecto es Django + Inertia/Vue. En produccion Django sirve la API y el
HTML; los assets compilados de Vite se sirven como archivos estaticos.

## 1. Crear la cuenta y el web app

1. Crea una cuenta gratuita en https://www.pythonanywhere.com.
2. En la pestana **Web**, pulsa **Add a new web app**.
3. Elige **Manual configuration** (no "Django" automatico) y la version de
   Python **3.12** o **3.13**.
4. Anota tu usuario: la URL sera `https://<usuario>.pythonanywhere.com`.

## 2. Subir el codigo

En una consola **Bash** de PythonAnywhere:

```bash
cd ~
git clone https://github.com/AlfonsoFichas-bit/gradientes_conjugados.git
cd gradientes_conjugados
```

## 3. Entorno virtual e instalacion

```bash
mkvirtualenv --python=python3.12 gradientes
# o, si ya existe:
# workon gradientes
pip install -r requirements.txt
```

## 4. Construir el frontend

En PythonAnywhere no hay Bun por defecto, pero si `npm`. El script detecta la
herramienta disponible:

```bash
chmod +x build.sh
./build.sh
```

Esto ejecuta `npm install && npm run build` y luego `collectstatic`, dejando los
assets en `staticfiles/build/` (incluido `manifest.json`).

> Si la red gratuita bloquea `npm`, construye localmente con `bun run build`,
> ejecuta `python manage.py collectstatic --noinput` y sube `static/build` y
> `staticfiles` al repositorio con `git add -f`.

## 5. Configurar el archivo WSGI

En la pestana **Web**, abre el "WSGI configuration file" y pega el contenido de
`deploy/pythonanywhere_wsgi.py`, reemplazando `<usuario>` y la clave secreta.

Genera una clave segura en la consola:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

## 6. Mapear archivos estaticos

En la pestana **Web -> Static files**, anade:

| URL | Directory |
|---|---|
| `/static/` | `/home/<usuario>/gradientes_conjugados/staticfiles` |

Guarda.

## 7. Migraciones (opcional, sin modelos de datos)

```bash
cd ~/gradientes_conjugados
workon gradientes
python manage.py migrate --run-syncdb
```

## 8. Recargar

Pulsa **Reload** en la pestana Web. Visita
`https://<usuario>.pythonanywhere.com/` y `.../salud/`.

## Variables de entorno utiles

| Variable | Uso |
|---|---|
| `NOMBRE_ESTUDIANTE` | Nombre mostrado en el Modulo 1 |
| `DJANGO_SECRET_KEY` | Clave secreta en produccion |
| `DJANGO_DEBUG` | `0` desactiva el modo depuracion |
| `DJANGO_ALLOWED_HOSTS` | Dominio del despliegue |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Origen HTTPS del despliegue |

## Notas

- El tier gratuito duerme la app tras inactividad y tiene limites de CPU/disco.
- Si cambias el frontend, vuelve a ejecutar `./build.sh` y pulsa **Reload**.
- No se usa base de datos: las sesiones son cookies firmadas.
