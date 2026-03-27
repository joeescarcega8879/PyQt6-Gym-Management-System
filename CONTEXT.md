# Contexto del Proyecto — PyQt6 Gym Management System

> Archivo de seguimiento interno. NO agregar a git.

---

## Descripción General

Aplicación de escritorio para gestión de gimnasios construida con PyQt6 y Supabase (PostgreSQL en la nube).

- **Patrón de arquitectura:** MVP (Model-View-Presenter)
- **Base de datos:** Supabase (cliente `supabase-py`)
- **UI:** PyQt6 con archivos `.ui` de Qt Designer
- **Autenticación:** bcrypt + usuarios almacenados en Supabase

---

## Estructura Principal

```
src/
├── assets/         # Stylesheet global (dark theme, styles.css)
├── config/         # Lectura de .env (Settings)
├── database/       # Singleton DatabaseManager — CRUD genérico sobre Supabase
├── domain/         # Permisos por rol (PermissionService, Permissions)
├── models/         # Dataclasses (Member, User, etc.) y enums
├── presenters/     # Lógica de negocio UI (MemberPresenter, LoginPresenter)
├── services/       # Lógica de negocio pura (MemberService, AuthService)
├── utils/          # Helpers: StatusBar, SetFormat, ErrorMessages
└── views/          # QWidget/QMainWindow + archivos .ui
```

---

## Módulos Implementados

| Módulo     | Estado          | Notas                                                        |
|------------|-----------------|--------------------------------------------------------------|
| Login      | Completo        | bcrypt, roles, sesión. Login en QThread (no bloquea UI)      |
| Members    | Completo        | CRUD funcional, tests, código limpio                         |
| Attendance | En progreso     | Service + tests completos. View (.ui) lista. Falta presenter + view.py + wiring en main |
| Otros      | No iniciados    | Sidebar conectado solo a Members y (pendiente) Attendance    |

---

## Módulo Members — Archivos Clave

| Archivo                              | Responsabilidad                            |
|--------------------------------------|--------------------------------------------|
| `src/models/models.py`               | Dataclass `Member`                         |
| `src/services/member_service.py`     | CRUD + búsqueda + validación               |
| `src/presenters/member_presenter.py` | Señales, permisos, coordinación view↔service |
| `src/views/member_view.py`           | UI pura, señales, populate_table          |
| `src/views/ui/member_view.ui`        | Layout Qt Designer                         |
| `src/database/manager.py`            | select / insert / update / delete / search |

---

## Módulo Attendance — Estado Actual

### Lo que ya existe ✅
| Archivo                                   | Estado   | Notas                                                      |
|-------------------------------------------|----------|------------------------------------------------------------|
| `src/models/models.py` — `Attendance`     | Completo | Dataclass con member_id, check_in/out_time, notes, member  |
| `src/services/attendance_service.py`      | Completo | 4 métodos: get_by_date, search_member, check_in, check_out |
| `tests/test_attendance_service.py`        | Completo | 39 tests, 100% passing                                     |
| `src/views/ui/attendance_view.ui`         | Completo | Layout Qt Designer listo (ver detalles abajo)              |

### Lo que falta ❌
| Archivo                                      | Responsabilidad                                          |
|----------------------------------------------|----------------------------------------------------------|
| `src/views/attendance_view.py`               | QWidget que carga el .ui, señales, populate_table        |
| `src/presenters/attendance_presenter.py`     | Lógica UI: check-in, check-out, filtrar por fecha        |
| Wiring en `main_application.py`              | `open_attendance_form()` + señal en MainView/Presenter   |

### Layout del .ui (attendance_view.ui)
Widgets disponibles (nombres exactos del .ui):
- **Top bar:** `label_user_name`, `label_user_role`, `btn_close`
- **Registro:** `input_search` (QLineEdit, placeholder "Code or name..."), `btn_checkin`, `btn_checkout`
- **Filtro:** `date_filter` (QDateEdit, calendarPopup=true, format yyyy-MM-dd), `btn_today`, `label_status`
- **Tabla:** `attendance_table` (QTableWidget)
- **Splitter:** `splitter_main` (vertical, top=controles, bottom=tabla)

### Columnas propuestas para `attendance_table`
| # | Header        | Fuente                                |
|---|---------------|---------------------------------------|
| 0 | Member Code   | `attendance.member.member_code`       |
| 1 | Full Name     | `attendance.member.full_name`         |
| 2 | Check-in      | `attendance.check_in_time` (HH:MM)   |
| 3 | Check-out     | `attendance.check_out_time` (HH:MM)  |
| 4 | Duration      | diferencia check_out - check_in       |
| 5 | Notes         | `attendance.notes`                    |

### Flujo de Check-in
1. Usuario escribe en `input_search` (código o nombre).
2. Hace clic en `btn_checkin`.
3. Presenter llama `attendance_service.search_member_for_checkin(term)`.
4. Si hay 1 resultado → llama `check_in(member.id, current_user.id)`.
5. Si hay múltiples resultados → mostrar diálogo de selección (QListWidget o QMessageBox informativo).
6. Si not_found → mostrar error en `label_status`.
7. Al éxito → recargar tabla del día actual.

### Flujo de Check-out
1. Usuario selecciona fila en `attendance_table` (registro sin check-out).
2. Hace clic en `btn_checkout`.
3. Presenter llama `attendance_service.check_out(attendance_id)`.
4. Al éxito → recargar tabla.
5. Si no hay selección → error en `label_status`.
6. Si registro ya tiene check-out → error en `label_status`.

### Flujo de Filtro por Fecha
1. `date_filter` arranca con `QDate.currentDate()`.
2. Al cambiar la fecha → recargar tabla automáticamente (`dateChanged` signal).
3. `btn_today` → resetea `date_filter` a hoy y recarga.

---

## Historial de Cambios

### Bug Fix — Login bloqueante (KeyboardInterrupt en arranque en frío) ✅
**Archivos:** `src/presenters/login_presenter.py`, `src/views/login_view.py`

**Causa raíz:** `_handle_login()` corría en el UI thread. En el primer arranque del día,
`bcrypt.checkpw()` + la petición de red a Supabase tardaban varios segundos bloqueando
el event loop de Qt, que interpretaba la espera como `KeyboardInterrupt`.

**Solución:** QThread worker pattern.
- Agregada clase `LoginWorker(QThread)` en `login_presenter.py`.
  - `run()` ejecuta `auth_service.login()` en background.
  - Emite `login_success(User)` o `login_failed(str)` al terminar.
- `LoginPresenter._handle_login()` instancia el worker, conecta señales y lo arranca.
- `_on_worker_success()` / `_on_worker_failed()` manejan el resultado en el UI thread.
- Agregado `set_loading(bool)` en `LoginView`:
  - Deshabilita `btn_login`, `input_username`, `input_password` durante el login.
  - Cambia texto del botón a `"Logging in..."` mientras espera.

---

### Módulo Members — Historial completo

#### Sesión inicial de análisis
- Análisis completo del proyecto y feedback del módulo Members.
- Identificados 22 problemas entre bugs críticos, lógica incorrecta y deuda técnica.

#### Paso 2 — Conectar `btn_clear` ✅
- Agregada señal `clear_action_requested = pyqtSignal()` en la vista.
- Conectado `btn_clear.clicked` a `clear_action_requested.emit`.
- Conectada la señal en el presenter a `_handle_load_all()`.

#### Paso 1 — Corregir género en `set_form_data()` ✅
- Reemplazado `setCurrentText(data.get("gender"))` por `findData()` + `setCurrentIndex()`.

#### Paso 5 — Tratar "not found" como info ✅
- Agregado `StatusType.INFO` al enum y estilo azul en `status_bar_styles.py`.
- Búsqueda sin resultados muestra INFO en lugar de ERROR.

#### Paso 6 — Poblar `label_user_name` y `label_user_role` ✅
- Método `_load_user_information()` en presenter + `set_user_info(dict)` en vista.

#### Paso 8 — Control UI para mostrar/ocultar inactivos ✅
- `QCheckBox check_show_inactives` + señal `show_inactive_requested`.

#### Paso 10 — Validar permiso `MEMBERS_READ` al cargar tabla ✅
- Verificación de `PermissionService.has_permission(MEMBERS_READ)` en `_handle_load_all()`.

#### Paso 7 — Mover filtro `is_active` al query de Supabase ✅
- `search()` en `database/manager.py` acepta `filters` opcionales.
- `search_members()` pasa `filters={'is_active': True}` en lugar de filtrar en Python.

#### Paso 11 — Diálogo de confirmación antes de actualizar ✅
- `QMessageBox.question()` antes de `update_member()`.

#### Paso 12 — Corregir colores de tabla para tema oscuro ✅
- `set_format.py`: colores alternados `#2d2d2d` / `#353535`.

#### Paso 13 — Corregir ruta de ícono rota en `member_view.ui` ✅
- Eliminada ruta absoluta a otro proyecto. `btn_close` ahora muestra texto `"Close"`.

#### Paso 14 — Estandarizar idioma a inglés ✅
- Traducidos todos los botones del sidebar en `main_window.ui`.

#### Paso 16 — Sistema de íconos (Qt Resource System base64) ✅
- `scripts/build_resources.py` embebe íconos de `src/assets/icons/` como base64.
- `resources_rc.py` expone `get_icon(path) -> QIcon`. Asignados 12 íconos.
- `resources_rc.py` en `.gitignore` (archivo generado).

#### Paso E — `date_birthday` min/max + `get_form_data()` ✅
- `minimumDate` = 1900-01-01, `maximumDate` = hoy.
- `get_form_data()` devuelve `None` cuando fecha == minimumDate.

#### Paso F — Eliminar código muerto + import huérfano ✅
- Eliminado bloque comentado `setSectionResizeMode/setColumnWidth` + import `QHeaderView`.

#### Paso G — Centralizar mensajes en `ErrorMessages` ✅
- 13 constantes en sección `# Members module` de `error_messages.py`.
- Cero strings inline en `member_presenter.py`.

---

## Tests — Estado Actual

**Total: 172 tests, 100% passing.**

| Archivo de test               | Módulo cubierto                  | Tests |
|-------------------------------|----------------------------------|-------|
| `test_service_result.py`      | `services/result.py`             | 16    |
| `test_member_service.py`      | `services/member_service.py`     | 62    |
| `test_permissions.py`         | `domain/permissions*.py`         | 21    |
| `test_auth_service.py`        | `services/auth_service.py`       | 31    |
| `test_attendance_service.py`  | `services/attendance_service.py` | 39    |
| `conftest.py`                 | Fixtures compartidas             | —     |

**Estrategia de mocking:**
- `db_manager` parcheado con `unittest.mock.patch('src.services.*.db_manager')`.
- Helpers estáticos puros testeados directamente sin mocks.
- Ejecutar con: `python -m pytest tests/ -v`

---

## Próximos Pasos — Módulo Attendance

### Pendientes (en orden de implementación)
1. **`src/views/attendance_view.py`** — QWidget: cargar .ui, señales, `populate_table()`, `set_user_info()`, `set_loading()`, `set_status()`, `get_search_term()`, `get_selected_attendance_id()`
2. **`src/presenters/attendance_presenter.py`** — Presenter: check-in flow (search → confirm if multiple → check_in), check-out flow, filtro por fecha, permisos
3. **Wiring en `main_application.py`** — `open_attendance_form()` + señal `form_attendance_requested` en `MainView` y `MainPresenter`
4. **Íconos en `attendance_view.py`** — Asignar `IMG-Close.png` a `btn_close` (igual que en member_view)
5. **`tests/test_attendance_presenter.py`** (opcional, según decisión de cobertura)
