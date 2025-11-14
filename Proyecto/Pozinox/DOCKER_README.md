# Dockerización del Proyecto Pozinox

Este documento explica cómo ejecutar el proyecto Pozinox usando Docker y Docker Compose.

## 📋 Prerrequisitos

- Docker Desktop instalado
- Docker Compose instalado
- Git (opcional, para clonar el repositorio)

## 🚀 Inicio Rápido

### 1. Configurar Variables de Entorno

```bash
cp env.example .env
```

Edita el archivo `.env` con tus configuraciones:

```bash
# Configuración básica
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Base de datos (ya configurada para Docker)
DATABASE_URL=postgresql://pozinox_user:pozinox_password@db:5432/pozinox
```

### 2. Construir y Ejecutar

```bash
# Construir las imágenes
docker-compose build

# Ejecutar los servicios
docker-compose up -d
```

### 3. Acceder a la Aplicación

- **Aplicación**: http://localhost:8000
- **Con Nginx**: http://localhost (puerto 80)

## 🛠️ Comandos Útiles

### Gestión de Servicios

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f web

# Detener servicios
docker-compose down

# Detener y eliminar volúmenes
docker-compose down -v

# Reiniciar un servicio específico
docker-compose restart web
```

### Comandos Django

```bash
# Ejecutar migraciones
docker-compose exec web python manage.py migrate

# Crear superusuario
docker-compose exec web python manage.py createsuperuser

# Recopilar archivos estáticos
docker-compose exec web python manage.py collectstatic

# Acceder al shell de Django
docker-compose exec web python manage.py shell

# Ejecutar tests
docker-compose exec web python manage.py test
```

### Gestión de Base de Datos

```bash
# Acceder a PostgreSQL
docker-compose exec db psql -U pozinox_user -d pozinox

# Hacer backup de la base de datos
docker-compose exec db pg_dump -U pozinox_user pozinox > backup.sql

# Restaurar backup
docker-compose exec -T db psql -U pozinox_user -d pozinox < backup.sql
```

## 🏗️ Arquitectura de Servicios

### Servicios Incluidos

1. **web**: Aplicación Django
   - Puerto: 8000
   - Comando: `python manage.py runserver 0.0.0.0:8000`

2. **db**: Base de datos PostgreSQL
   - Puerto: 5432
   - Usuario: pozinox_user
   - Contraseña: pozinox_password
   - Base de datos: pozinox

3. **nginx**: Servidor web para archivos estáticos
   - Puerto: 80
   - Sirve archivos estáticos y media

### Volúmenes

- `postgres_data`: Datos de PostgreSQL
- `static_volume`: Archivos estáticos de Django
- `media_volume`: Archivos de media subidos por usuarios

## 🔧 Configuración Avanzada

### Variables de Entorno

El archivo `.env` soporta las siguientes variables:

```bash
# Django
SECRET_KEY=tu-clave-secreta
DEBUG=True/False
ALLOWED_HOSTS=host1,host2,host3

# Base de datos
DATABASE_URL=postgresql://user:pass@host:port/db

# Supabase (opcional)
SUPABASE_URL=tu-url-supabase
SUPABASE_KEY=tu-clave-supabase

# AWS S3 / Supabase Storage (opcional)
AWS_ACCESS_KEY_ID=tu-access-key
AWS_SECRET_ACCESS_KEY=tu-secret-key
AWS_STORAGE_BUCKET_NAME=tu-bucket
AWS_S3_ENDPOINT_URL=tu-endpoint
AWS_S3_REGION_NAME=us-east-1
AWS_S3_CUSTOM_DOMAIN=tu-dominio

# Email
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
```

### Personalización del Dockerfile

El `Dockerfile` está optimizado para:
- Python 3.11
- Instalación de dependencias del sistema
- Usuario no-root para seguridad
- Configuración de archivos estáticos

### Personalización de Nginx

El archivo `nginx.conf` incluye:
- Compresión gzip
- Cache para archivos estáticos
- Headers de seguridad
- Proxy para Django

## 🐛 Solución de Problemas

### Problemas Comunes

1. **Error de conexión a la base de datos**
   ```bash
   # Verificar que PostgreSQL esté ejecutándose
   docker-compose ps
   
   # Ver logs de la base de datos
   docker-compose logs db
   ```

2. **Archivos estáticos no se cargan**
   ```bash
   # Recopilar archivos estáticos
   docker-compose exec web python manage.py collectstatic
   
   # Verificar que Nginx esté ejecutándose
   docker-compose ps nginx
   ```

3. **Puerto ya en uso**
   ```bash
   # Cambiar puertos en docker-compose.yml
   # O detener servicios que usen el puerto
   ```

### Limpieza

```bash
# Eliminar contenedores, redes y volúmenes
docker-compose down -v

# Eliminar imágenes no utilizadas
docker system prune -a

# Eliminar volúmenes no utilizados
docker volume prune
```

## 📚 Recursos Adicionales

- [Documentación de Docker](https://docs.docker.com/)
- [Documentación de Docker Compose](https://docs.docker.com/compose/)
- [Documentación de Django](https://docs.djangoproject.com/)
- [Documentación de PostgreSQL](https://www.postgresql.org/docs/)

## 🤝 Contribución

Para contribuir al proyecto:

1. Fork el repositorio
2. Crea una rama para tu feature
3. Haz commit de tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo LICENSE para más detalles.
