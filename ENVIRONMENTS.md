# 🛠️ Configuración de Entornos - Econline API

Esta guía explica cómo configurar y usar los diferentes entornos (desarrollo, staging, producción) en el proyecto Econline API.

## 📁 Estructura de Configuración

```
config/
├── settings/
│   ├── __init__.py          # Carga automática de configuración
│   ├── base.py              # Configuraciones compartidas
│   ├── development.py       # Configuraciones de desarrollo
│   ├── staging.py           # Configuraciones de staging
│   └── production.py        # Configuraciones de producción
└── ...

# Archivos de variables de entorno
.env                         # Desarrollo (local)
.env.staging                 # Staging
.env.production             # Producción

# Ejemplos de configuración
.env.example                # Ejemplo para desarrollo
.env.staging.example        # Ejemplo para staging
.env.production.example     # Ejemplo para producción
```

## 🔧 Configuración Rápida

### 1. Configurar entorno de desarrollo
```bash
# Usar el script automático
./scripts/set-environment.sh development

# O manualmente
export DJANGO_ENVIRONMENT=development
cp .env.example .env
# Editar .env con tus configuraciones locales
```

### 2. Configurar entorno de staging
```bash
# Usar el script automático
./scripts/set-environment.sh staging

# O manualmente
export DJANGO_ENVIRONMENT=staging
cp .env.staging.example .env.staging
# Editar .env.staging con configuraciones de staging
```

### 3. Configurar entorno de producción
```bash
# Usar el script automático
./scripts/set-environment.sh production

# O manualmente
export DJANGO_ENVIRONMENT=production
cp .env.production.example .env.production
# Editar .env.production con configuraciones de producción
```

## 🚀 Comandos de Makefile

### Configuración de entornos
```bash
make set-dev      # Configurar desarrollo
make set-staging  # Configurar staging
make set-prod     # Configurar producción
```

### Construcción por entorno
```bash
# Desarrollo (por defecto)
make build
make up

# Staging
ENVIRONMENT=staging make build
ENVIRONMENT=staging make up

# Producción
ENVIRONMENT=production make build
ENVIRONMENT=production make up
```

### Despliegue automático
```bash
make staging-deploy   # Despliega en staging
make prod-deploy      # Despliega en producción
```

## 🔍 Variables de Entorno Importantes

### Desarrollo (.env)
```bash
DEBUG=True
SECRET_KEY=clave-local-de-desarrollo
POSTGRES_HOST=localhost
REDIS_HOST=localhost
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### Staging (.env.staging)
```bash
DEBUG=False
SECRET_KEY=clave-segura-staging
POSTGRES_HOST=staging-db.tudominio.com
REDIS_HOST=staging-redis.tudominio.com
CORS_ALLOWED_ORIGINS=https://staging.tudominio.com
```

### Producción (.env.production)
```bash
DEBUG=False
SECRET_KEY=clave-super-segura-produccion
POSTGRES_HOST=produccion-db.tudominio.com
REDIS_HOST=produccion-redis.tudominio.com
CORS_ALLOWED_ORIGINS=https://tudominio.com
```

## 📋 Diferencias por Entorno

| Característica | Desarrollo | Staging | Producción |
|----------------|------------|---------|-------------|
| **DEBUG** | `True` | `False` | `False` |
| **Seguridad SSL** | Deshabilitada | Habilitada | Habilitada |
| **Email Backend** | Console | SMTP/Test | SMTP Real |
| **Stripe Keys** | Test | Test | Live |
| **Rate Limiting** | Relajado | Medio | Estricto |
| **JWT Timeout** | 60 min | 30 min | 15 min |
| **Logging** | Console | File + Console | File + Sentry |
| **CORS** | Localhost | Staging URLs | Production URLs |

## 🛡️ Configuraciones de Seguridad

### Desarrollo
- SSL deshabilitado para localhost
- CORS permisivo para desarrollo local
- Logs en consola
- Rate limiting relajado

### Staging
- SSL habilitado
- CORS configurado para URLs de staging
- Logs en archivos y consola
- Configuraciones similares a producción

### Producción
- SSL obligatorio
- CORS estricto
- HSTS habilitado
- Rate limiting estricto
- Logs estructurados
- Monitoreo con Sentry

## 🔄 Cambio entre Entornos

### Método 1: Variable de entorno
```bash
export DJANGO_ENVIRONMENT=production
python manage.py runserver
```

### Método 2: Script automático
```bash
./scripts/set-environment.sh production
```

### Método 3: Makefile
```bash
make set-prod
```

## 🐳 Docker por Entorno

### Desarrollo
```bash
docker-compose up --build
```

### Staging
```bash
docker-compose -f docker-compose.staging.yml up --build
```

### Producción
```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

## 🔧 Comandos Útiles

### Verificar configuración actual
```bash
python manage.py check
python manage.py diffsettings
```

### Ejecutar migraciones por entorno
```bash
DJANGO_ENVIRONMENT=development python manage.py migrate
DJANGO_ENVIRONMENT=staging python manage.py migrate
DJANGO_ENVIRONMENT=production python manage.py migrate
```

### Recolectar archivos estáticos
```bash
DJANGO_ENVIRONMENT=production python manage.py collectstatic --noinput
```

### Crear superusuario
```bash
DJANGO_ENVIRONMENT=production python manage.py createsuperuser
```

## ⚠️ Consideraciones Importantes

### Para Desarrollo
1. Nunca usar claves de producción en desarrollo
2. Mantener `.env` en `.gitignore`
3. Usar servicios locales (PostgreSQL, Redis local)

### Para Staging
1. Usar claves de test para servicios externos
2. Configurar subdominios de staging
3. Mantener datos de prueba, no reales

### Para Producción
1. **NUNCA** commitear `.env.production`
2. Usar servicios gestionados (RDS, ElastiCache, etc.)
3. Configurar backups automáticos
4. Usar HTTPS obligatorio
5. Configurar monitoreo y alertas

## 🚨 Troubleshooting

### Error: "No module named 'config.settings.development'"
```bash
# Verificar que existe el archivo
ls config/settings/development.py

# Verificar variable de entorno
echo $DJANGO_ENVIRONMENT
```

### Error: "ALLOWED_HOSTS"
- Asegurar que `ALLOWED_HOSTS` esté configurado en el archivo `.env` apropiado

### Error: Database connection
- Verificar que las credenciales de BD sean correctas en el archivo `.env`
- Verificar que el servicio de BD esté ejecutándose

### Error: Redis connection
- Verificar configuración de Redis en el archivo `.env`
- Verificar que Redis esté ejecutándose

## 📚 Recursos Adicionales

- [Django Settings Best Practices](https://docs.djangoproject.com/en/stable/topics/settings/)
- [12-Factor App](https://12factor.net/)
- [Django Environment Variables](https://django-environ.readthedocs.io/)

## 🤝 Contribuir

Al contribuir al proyecto:
1. Usar entorno de desarrollo para cambios
2. Probar en staging antes de producción
3. Nunca commitear archivos `.env` reales
4. Documentar nuevas variables de entorno
