# Estructura del Proyecto

```
gym-management-system/
│
├── main.py                          # Punto de entrada de la aplicación
├── requirements.txt                 # Dependencias de Python
├── .env.example                     # Ejemplo de configuración
├── .env                            # Configuración (NO subir a git)
├── .gitignore                      # Archivos ignorados por git
├── README.md                       # Documentación principal
│
├── docs/                           # Documentación
│   ├── database_schema.sql        # Esquema completo de BD
│   ├── QUICKSTART.md              # Guía rápida
│   └── architecture.md            # (futuro) Documentación de arquitectura
│
├── src/                           # Código fuente
│   ├── __init__.py
│   │
│   ├── config/                    # Configuración
│   │   └── __init__.py           # Config centralizada, lee .env
│   │
│   ├── models/                    # Modelos de datos
│   │   └── __init__.py           # Dataclasses (User, Member, etc.)
│   │
│   ├── database/                  # Capa de acceso a datos
│   │   └── __init__.py           # DatabaseManager (Supabase)
│   │
│   ├── services/                  # Lógica de negocio
│   │   ├── __init__.py
│   │   └── auth_service.py       # Servicio de autenticación
│   │
│   ├── presenters/               # Presenters (MVP)
│   │   ├── __init__.py
│   │   └── login_presenter.py    # Presenter de login
│   │
│   ├── views/                    # Vistas (PyQt6)
│   │   ├── __init__.py
│   │   └── login_view.py         # Vista de login
│   │
│   ├── utils/                    # Utilidades
│   │   └── __init__.py
│   │
│   └── resources/                # Recursos (imágenes, estilos)
│       ├── icons/
│       ├── images/
│       └── styles/
│
├── tests/                        # Tests
│   ├── unit/                    # Tests unitarios
│   └── integration/             # Tests de integración
│
├── logs/                         # Logs (generado automáticamente)
│   └── gym_system.log
│
├── data/                         # Base de datos local (generado)
│   └── gym_local.db             # SQLite para modo offline
│
└── venv/                        # Entorno virtual (NO subir a git)
```

## Archivos Principales

### Configuración
- **main.py**: Inicia la aplicación, configura logging
- **.env**: Credenciales de Supabase (crear desde .env.example)
- **requirements.txt**: Todas las dependencias de Python

### Código Base
- **src/config/**: Configuración centralizada
- **src/models/**: Definición de modelos (preparados para Django)
- **src/database/**: Conexión y operaciones CRUD genéricas
- **src/services/**: Lógica de negocio reutilizable
- **src/presenters/**: Lógica de presentación (patrón MVP)
- **src/views/**: Interfaces gráficas con PyQt6

### Documentación
- **README.md**: Documentación completa
- **docs/database_schema.sql**: Esquema SQL completo para Supabase
- **docs/QUICKSTART.md**: Guía rápida de 5 minutos

## Estado Actual del Proyecto

### ✅ Completado (Fase 0: Setup y Base)

1. **Estructura del proyecto** - Organización modular y escalable
2. **Configuración** - Sistema de configuración con .env
3. **Base de datos**:
   - Esquema SQL completo (15 tablas)
   - DatabaseManager con CRUD genérico
   - Conexión a Supabase
4. **Modelos**:
   - 15 dataclasses definidos
   - Preparados para migración a Django
5. **Autenticación**:
   - AuthService con bcrypt
   - Login funcional
   - Gestión de sesiones
6. **UI Base**:
   - LoginView con PyQt6
   - LoginPresenter (patrón MVP)
   - Estilos CSS aplicados

### 📋 Siguiente Fase: Gestión de Miembros

1. **MemberService** - CRUD completo de miembros
2. **MainWindow** - Ventana principal con menú
3. **MemberListView** - Lista con búsqueda y filtros
4. **MemberFormView** - Formulario crear/editar
5. **MemberDetailView** - Vista de detalle

## Patrón MVP Implementado

```
┌─────────────┐
│   Model     │  (src/models/)
│  (Data)     │  Dataclasses
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌──────────────┐
│  Service    │◄────►│  Presenter   │  (src/presenters/)
│  (Business  │      │  (Logic)     │  Conecta View y Service
│   Logic)    │      └──────┬───────┘
└─────────────┘             │
  (src/services/)           │
                            ▼
                    ┌──────────────┐
                    │     View     │  (src/views/)
                    │   (UI/PyQt6) │  Solo interfaz gráfica
                    └──────────────┘
```

## Dependencias Clave

### Core
- **PyQt6** - Framework UI
- **Supabase** - Base de datos PostgreSQL
- **python-dotenv** - Variables de entorno
- **bcrypt** - Hash de contraseñas

### Reportes
- **reportlab** - PDFs
- **openpyxl** - Excel
- **matplotlib** - Gráficos

### Otros
- **qrcode** - Generación de QR
- **pyzbar** - Lectura de códigos
- **pytest** - Testing

## Convenciones de Código

### Nombres
- **Clases**: PascalCase (`MemberService`, `LoginView`)
- **Funciones**: snake_case (`get_member`, `create_user`)
- **Constantes**: UPPER_CASE (`MAX_MEMBERS`, `DEFAULT_ROLE`)
- **Privados**: _prefijo (`_handle_login`, `_validate_data`)

### Estructura de archivos
- Un archivo por clase principal
- `__init__.py` exporta las clases públicas
- Servicios terminan en `_service.py`
- Vistas terminan en `_view.py`
- Presenters terminan en `_presenter.py`

### Docstrings
```python
def create_member(self, data: dict) -> Member:
    """
    Crea un nuevo miembro en la base de datos.
    
    Args:
        data: Diccionario con los datos del miembro
        
    Returns:
        Member: Objeto Member creado
        
    Raises:
        ValueError: Si los datos son inválidos
    """
```

## Próximos Módulos a Desarrollar

1. **MainWindow** (Priority: HIGH)
2. **MemberModule** (Priority: HIGH)
3. **AttendanceModule** (Priority: HIGH)
4. **PaymentModule** (Priority: MEDIUM)
5. **ClassModule** (Priority: MEDIUM)
6. **ReportsModule** (Priority: MEDIUM)
7. **EquipmentModule** (Priority: LOW)
8. **NotificationsModule** (Priority: LOW)

---

Última actualización: 2026-03-03
