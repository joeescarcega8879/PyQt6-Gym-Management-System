# Gym Management System

Sistema de gestión integral para gimnasios desarrollado con Python, PyQt6 y Supabase (PostgreSQL).

## Características Principales

- **Gestión de Miembros**: CRUD completo de clientes con datos personales y fotografías
- **Control de Asistencia**: Check-in/check-out con código de barras o QR
- **Membresías y Planes**: Gestión de diferentes tipos de planes con renovación automática
- **Pagos y Facturación**: Registro de pagos con múltiples métodos y estados de cuenta
- **Clases Grupales**: Programación de clases, horarios e inscripciones
- **Gestión de Instructores**: Control de instructores y asignación a clases
- **Inventario de Equipamiento**: Control de máquinas y mantenimiento
- **Reportes y Estadísticas**: Dashboard con gráficos y exportación a PDF/Excel
- **Sistema de Caja**: Apertura/cierre de caja con control de efectivo
- **Notificaciones Automáticas**: Alertas de vencimiento y recordatorios
- **Modo Offline**: Funcionamiento sin internet con sincronización posterior
- **Múltiples Roles**: Admin, Recepcionista, Instructor, Contador

## Arquitectura

El proyecto sigue el patrón **MVP (Model-View-Presenter)** para facilitar el mantenimiento y futura migración a web con Django.

```
gym-management-system/
├── src/
│   ├── models/           # Modelos de datos (dataclasses)
│   ├── presenters/       # Lógica de presentación (MVP)
│   ├── views/            # Interfaces PyQt6
│   ├── database/         # Conexión y repositorios Supabase
│   ├── services/         # Lógica de negocio reutilizable
│   ├── utils/            # Utilidades (validaciones, helpers)
│   ├── config/           # Configuración de la app
│   └── resources/        # Imágenes, iconos, estilos QSS
├── tests/                # Tests unitarios e integración
├── docs/                 # Documentación y esquema SQL
├── main.py               # Punto de entrada
└── requirements.txt      # Dependencias
```

## Requisitos Previos

- **Python 3.11+**
- **Cuenta de Supabase** (gratis en https://supabase.com)
- **Git** (opcional, para clonar el repositorio)

### Dependencias del Sistema (Linux)

```bash
sudo apt-get update
sudo apt-get install -y libzbar0 libxcb-xinerama0
```

## Instalación

### 1. Clonar o descargar el proyecto

```bash
cd gym-management-system
```

### 2. Crear entorno virtual

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# En Linux/Mac:
source venv/bin/activate

# En Windows:
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Supabase

#### 4.1. Crear proyecto en Supabase

1. Ve a https://supabase.com
2. Crea una cuenta o inicia sesión
3. Crea un nuevo proyecto:
   - Nombre: `gym-management` (o el que prefieras)
   - Contraseña de base de datos: (guárdala, la necesitarás)
   - Región: Elige la más cercana a ti

#### 4.2. Crear el esquema de base de datos

1. En Supabase, ve a **SQL Editor**
2. Abre el archivo `docs/database_schema.sql`
3. Copia todo el contenido y pégalo en el SQL Editor de Supabase
4. Ejecuta el script (botón "Run")

Esto creará:
- 15 tablas con todas las relaciones
- Índices para mejorar performance
- Triggers para actualización automática de timestamps
- Un usuario admin por defecto (ver credenciales abajo)

#### 4.3. Obtener credenciales de Supabase

1. En Supabase, ve a **Settings > API**
2. Copia:
   - **Project URL** (ejemplo: `https://abcdefghijk.supabase.co`)
   - **anon/public key** (ejemplo: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`)

#### 4.4. Configurar archivo .env

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar el archivo .env con tus credenciales
nano .env  # o usa tu editor favorito
```

Reemplaza los valores:

```env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_anon_key_aqui
```

## Uso

### Ejecutar la aplicación

```bash
python main.py
```

### Credenciales por defecto

Después de ejecutar el script SQL, habrá un usuario administrador creado:

- **Usuario**: `admin`
- **Contraseña**: `admin123`

**IMPORTANTE**: Cambia esta contraseña inmediatamente después del primer login.

## Desarrollo

### Estructura de un módulo (patrón MVP)

```python
# 1. Modelo (src/models/__init__.py)
@dataclass
class Member:
    id: str
    name: str
    # ...

# 2. Vista (src/views/member_view.py)
class MemberView(QWidget):
    # Interfaz gráfica con PyQt6
    member_added = pyqtSignal(dict)
    
# 3. Presenter (src/presenters/member_presenter.py)
class MemberPresenter:
    def __init__(self, view):
        self.view = view
        self.view.member_added.connect(self._handle_add)
```

### Agregar un nuevo módulo

1. Crear el modelo en `src/models/`
2. Crear la vista en `src/views/`
3. Crear el presenter en `src/presenters/`
4. Conectar en el menú principal

### Tests

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=src tests/

# Solo tests unitarios
pytest tests/unit/
```

### Formateo de código

```bash
# Formatear con black
black src/

# Verificar con flake8
flake8 src/

# Type checking con mypy
mypy src/
```

## Migración a Django (futuro)

El proyecto está diseñado para facilitar la migración a Django:

### Modelos
Los dataclasses se convierten fácilmente a Django Models:

```python
# Actual (dataclass)
@dataclass
class Member:
    name: str
    email: str

# Django (futuro)
class Member(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
```

### Servicios
La lógica en `src/services/` se puede reutilizar directamente o mover a managers de Django.

### Base de datos
Supabase usa PostgreSQL, compatible con Django. Solo necesitas actualizar `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'tu-proyecto.supabase.co',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'tu-contraseña',
        'PORT': '5432',
    }
}
```

## Resolución de Problemas

### Error: "SUPABASE_URL no está configurada"

- Verifica que el archivo `.env` existe (no `.env.example`)
- Asegúrate de haber configurado las variables correctamente

### Error: "Import dotenv could not be resolved"

```bash
pip install python-dotenv
```

### Error: "No se puede conectar a Supabase"

- Verifica que tu URL y API Key son correctos
- Asegúrate de tener conexión a internet
- Revisa los logs en `logs/gym_system.log`

### Error al leer códigos de barras (Linux)

```bash
sudo apt-get install libzbar0
```

## Roadmap

### Fase 1 - Core (Actual)
- [x] Sistema de autenticación
- [x] Configuración de base de datos
- [x] Estructura MVP
- [ ] CRUD de miembros
- [ ] Control de asistencia

### Fase 2 - Finanzas
- [ ] Sistema de pagos
- [ ] Control de caja
- [ ] Reportes financieros

### Fase 3 - Clases
- [ ] Gestión de instructores
- [ ] Programación de clases
- [ ] Inscripciones

### Fase 4 - Avanzado
- [ ] Lector de códigos QR/Barras
- [ ] Modo offline
- [ ] Backup automático
- [ ] Exportación PDF/Excel

### Fase 5 - Dashboard
- [ ] Estadísticas y gráficos
- [ ] Notificaciones automáticas
- [ ] Reportes customizables

## Contribuir

Este es un proyecto de práctica, pero las sugerencias son bienvenidas.

## Licencia

Este proyecto es de código abierto para fines educativos.

## Contacto

Para preguntas o sugerencias, abre un issue en el repositorio.

---

**Nota**: Este es un proyecto de práctica. No se recomienda usar en producción sin realizar pruebas exhaustivas y reforzar la seguridad.
