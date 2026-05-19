# Gym Management System

Sistema de gestión integral para gimnasios desarrollado con Python, PyQt6 y PostgreSQL local.

## Características Principales

- **Gestión de Miembros**: CRUD completo con datos personales
- **Control de Asistencia**: Check-in/check-out por búsqueda de nombre o código
- **Membresías y Planes**: Gestión de planes con asignación, suspensión y cancelación
- **Pagos**: Registro de cobros con múltiples métodos y estados
- **Múltiples Roles**: Admin, Recepcionista, Contador

## Arquitectura

El proyecto sigue el patrón **MVP (Model-View-Presenter)**.

```
gym-management-system/
├── src/
│   ├── models/       # Dataclasses (Member, User, Payment, etc.) y enums
│   ├── presenters/   # Lógica de presentación — coordinación view ↔ service
│   ├── views/        # Interfaces PyQt6 + archivos .ui de Qt Designer
│   ├── database/     # DatabaseManager singleton — SQL puro via psycopg2
│   ├── services/     # Lógica de negocio (MemberService, AuthService, etc.)
│   ├── domain/       # Permisos por rol (PermissionService, Permissions)
│   ├── utils/        # Helpers: StatusBar, SetFormat, ErrorMessages
│   └── config/       # Lectura de .env (Settings)
├── tests/            # Tests unitarios (316 tests, 100% passing)
├── scripts/          # build_resources.py — genera resources_rc.py con iconos base64
├── docs/             # Esquema SQL
├── main.py           # Punto de entrada
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

#### 4.2. Crear el esquema

Ejecuta el archivo de esquema en psql o pgAdmin:

```bash
psql -U postgres -d gym-system -f docs/database_schema.sql
```

Esto creará las tablas, índices, triggers y un usuario `admin` por defecto.

#### 4.3. Configurar el archivo .env

Copia el archivo de ejemplo y edítalo:

```bash
cp .env.example .env
```

Contenido de `.env`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gym-system
DB_USER=postgres
DB_PASSWORD=tu_password_aqui
```

### 5. Generar recursos de iconos

```bash
python scripts/build_resources.py
```

Esto genera `src/assets/resources_rc.py` con los iconos embebidos en base64.

## Uso

### Ejecutar la aplicación

```bash
python main.py
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
    def __init__(self, view, current_user):
        self.view = view
        self.view.save_requested.connect(self._handle_save)
```

### Agregar un nuevo módulo

1. Agregar dataclass en `src/models/models.py`
2. Crear service en `src/services/`
3. Crear view en `src/views/` (con archivo `.ui` en `src/views/ui/`)
4. Crear presenter en `src/presenters/`
5. Conectar al sidebar en `main_window.py`
6. Agregar tests en `tests/`

### Tests

```bash
# Ejecutar todos los tests
python -m pytest tests/ -v

# Con cobertura
python -m pytest tests/ --cov=src
```

Estrategia de mocking: `db_manager` se parchea con `unittest.mock.patch('src.services.<modulo>.db_manager')`. No se usa una BD real en los tests.

## Resolución de Problemas

### Error: "Could not connect to PostgreSQL"

- Verifica que PostgreSQL esté corriendo: `pg_isready` o revisar el servicio
- Confirma que las credenciales en `.env` son correctas
- Verifica que la base de datos `gym-system` existe

### Error: "No module named 'psycopg2'"

```bash
pip install psycopg2-binary
```

### Error: "resources_rc not found" o iconos no aparecen

```bash
python scripts/build_resources.py
```

### Error al importar en Windows

Asegúrate de tener el entorno virtual activado y haber instalado las dependencias con `pip install -r requirements.txt`.

## Roadmap

### Completado
- [x] Sistema de autenticacion (bcrypt + QThread)
- [x] CRUD de miembros
- [x] Control de asistencia (check-in/check-out)
- [x] Pagos y facturacion
- [x] Membresías y planes

### Pendiente
- [ ] Dashboard con estadísticas
- [ ] Gestión de instructores
- [ ] Programación de clases
- [ ] Inventario de equipamiento
- [ ] Reportes y exportación

## Licencia

Proyecto de práctica educativa. No recomendado para producción sin pruebas exhaustivas de seguridad.
