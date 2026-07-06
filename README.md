# Gym Management System

Sistema de gestión integral para gimnasios desarrollado con Python, PyQt6 y PostgreSQL local.

## Características Principales

11 módulos completos, cada uno con permisos por rol y tests unitarios:

- **Dashboard**: KPIs (miembros activos, ingresos del mes, check-ins de hoy, membresías por vencer) + tablas de detalle
- **Members**: CRUD completo de miembros con datos personales y código único
- **Attendance**: Check-in/check-out por búsqueda de nombre o código, con historial por fecha
- **Payments**: Registro de cobros con múltiples métodos (efectivo/tarjeta/transferencia) y estados
- **Memberships**: Planes de membresía + asignación, suspensión, cancelación y reactivación
- **Classes**: Clases grupales, horarios semanales e inscripciones con control de capacidad
- **Instructors**: CRUD de instructores con especialidades
- **Equipment**: Inventario de equipamiento + historial de mantenimiento
- **Reports**: Reportes financieros, de membresías, asistencia y operativos, con exportación a PDF
- **Settings**: 5 temas de color con cambio en vivo y persistencia
- **Múltiples Roles**: Admin, Recepcionista, Instructor, Contador — permisos distintos por módulo

## Arquitectura

El proyecto sigue el patrón **MVP (Model-View-Presenter)**.

```
gym-management-system/
├── src/
│   ├── models/       # Dataclasses (Member, User, Payment, etc.) y enums
│   ├── presenters/   # Lógica de presentación — coordinación view ↔ service
│   ├── views/        # Interfaces PyQt6 + archivos .ui de Qt Designer
│   ├── database/     # DatabaseManager singleton — SQL puro via psycopg2
│   ├── services/     # Lógica de negocio (MemberService, AuthService, ReportsService, etc.)
│   ├── domain/       # Permisos por rol (PermissionService, Permissions)
│   ├── utils/        # Helpers: StatusBar, SetFormat, ErrorMessages, PdfExporter
│   └── config/       # Lectura de .env (Settings)
├── tests/            # Tests unitarios (581 tests, 100% passing)
├── scripts/          # build_resources.py, generate_themes.py, scripts de seed data
├── docs/             # database_schema.sql (único archivo versionado de esta carpeta)
├── main_application.py  # Punto de entrada
└── requirements.txt  # Dependencias
```

## Requisitos Previos

- **Python 3.11+**
- **PostgreSQL 14+** instalado y corriendo localmente

## Instalación

### 1. Clonar o descargar el proyecto

```bash
cd PyQt6-Gym-Management-System
```

### 2. Crear entorno virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar en Linux/Mac:
source venv/bin/activate

# Activar en Windows:
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar la base de datos

#### 4.1. Crear la base de datos en PostgreSQL

```sql
CREATE DATABASE "gym-system";
```

(pgAdmin funciona igual de bien: clic derecho en "Databases" → Create → Database)

#### 4.2. Crear el esquema

Ejecuta el archivo de esquema en psql o en el Query Tool de pgAdmin **conectado a la base recién creada**:

```bash
psql -U postgres -d gym-system -f docs/database_schema.sql
```

Esto crea las tablas, índices, triggers y un usuario `admin` por defecto.

#### 4.3. Configurar el archivo .env

Copia el archivo de ejemplo y edítalo con tus credenciales:

```bash
cp .env.example .env
```

Como mínimo necesitas ajustar `DB_NAME` (si usaste un nombre distinto a `gym-system` — recuerda que PostgreSQL distingue mayúsculas si el nombre lleva comillas) y `DB_PASSWORD`.

### 5. Generar recursos de iconos

```bash
python scripts/build_resources.py
```

Esto genera `src/assets/resources_rc.py` con los iconos embebidos en base64.

## Uso

### Ejecutar la aplicación

```bash
python main_application.py
```

### Credenciales por defecto

- **Usuario**: `admin`
- **Contraseña**: `admin123`

**IMPORTANTE**: Cambia esta contraseña inmediatamente después del primer login.

## Desarrollo

### Estructura de un módulo (patrón MVP)

```python
# 1. Modelo (src/models/models.py)
@dataclass
class Member:
    id: Optional[str]
    first_name: str
    last_name: str
    # ...

# 2. Vista (src/views/member_view.py)
class MemberView(QWidget):
    save_requested = pyqtSignal()
    search_requested = pyqtSignal()

# 3. Service (src/services/member_service.py)
class MemberService:
    def create_member(self, member: Member) -> ServiceResult[Member]: ...

# 4. Presenter (src/presenters/member_presenter.py)
class MemberPresenter:
    def __init__(self, view, main_app, status_handler, current_user):
        self.view = view
        self.view.create_requested.connect(self._handle_create)
```

### Agregar un nuevo módulo

1. Agregar dataclass en `src/models/models.py`
2. Crear service en `src/services/`
3. Crear view en `src/views/` (con archivo `.ui` en `src/views/ui/`)
4. Crear presenter en `src/presenters/`
5. Conectar al sidebar en `src/views/main_view.py` + `src/presenters/main_presenter.py` + `main_application.py`
6. Agregar tests en `tests/`

### Tests

```bash
# Ejecutar todos los tests
python -m pytest tests/ -v

# Con cobertura
python -m pytest tests/ --cov=src
```

Estrategia de mocking: `db_manager` se parchea con `unittest.mock.patch('src.services.<modulo>.db_manager')`. No se usa una BD real en los tests — son 100% unitarios.

## Resolución de Problemas

### Error: "Could not connect to PostgreSQL"

- Verifica que PostgreSQL esté corriendo: `pg_isready` o revisar el servicio
- Confirma que las credenciales en `.env` son correctas
- Verifica que la base de datos existe con el nombre exacto configurado en `DB_NAME` (ojo con mayúsculas/minúsculas)

### Error: "No module named 'psycopg2'"

```bash
pip install psycopg2-binary
```

### Error: "resources_rc not found" o iconos no aparecen

```bash
python scripts/build_resources.py
```

### Error al exportar PDFs desde Reports

```bash
pip install reportlab
```

### Error al importar en Windows

Asegúrate de tener el entorno virtual activado y haber instalado las dependencias con `pip install -r requirements.txt`.

## Roadmap

Los 11 módulos planeados están completos. Sin pendientes identificados actualmente.

## Licencia

Este proyecto está bajo la licencia MIT — ver el archivo [LICENSE](LICENSE) para más detalles.
