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

| Módulo      | Estado          | Notas                                                                               |
|-------------|-----------------|-------------------------------------------------------------------------------------|
| Login       | Completo        | bcrypt, roles, sesión. Login en QThread (no bloquea UI)                             |
| Members     | Completo        | CRUD funcional, tests, código limpio                                                |
| Attendance  | Completo        | CRUD completo, check-in/out por búsqueda o selección, MemberSelectDialog, 46 tests |
| Memberships | En progreso     | Fase 1 y 2 completas. Faltan: tests, .ui, view, presenter, navegación               |
| Otros       | No iniciados    | Sidebar conectado solo a Members y Attendance                                       |

---

## Módulo Members — Archivos Clave

| Archivo                              | Responsabilidad                              |
|--------------------------------------|----------------------------------------------|
| `src/models/models.py`               | Dataclass `Member`                           |
| `src/services/member_service.py`     | CRUD + búsqueda + validación                 |
| `src/presenters/member_presenter.py` | Señales, permisos, coordinación view↔service |
| `src/views/member_view.py`           | UI pura, señales, populate_table             |
| `src/views/ui/member_view.ui`        | Layout Qt Designer                           |
| `src/database/manager.py`            | select / insert / update / delete / search   |

---

## Módulo Attendance — Estado Actual

### Archivos implementados ✅

| Archivo | Estado | Notas |
|---|---|---|
| `src/models/models.py` — `Attendance` | Completo | Dataclass con member_id, check_in/out_time, notes, member |
| `src/services/attendance_service.py` | Completo | 5 métodos: get_by_date, search_member, check_in, check_out, find_open_checkin_for_member |
| `src/views/ui/attendance_view.ui` | Completo | Layout Qt Designer |
| `src/views/attendance_view.py` | Completo | Señales, populate_table (hora local 12h, Duration, UserRole), get_search_term, get_selected_attendance_id, get_current_date |
| `src/views/widgets/member_select_dialog.py` | Completo | QDialog reutilizable para seleccionar miembro de lista múltiple |
| `src/presenters/attendance_presenter.py` | Completo | check-in, check-out (por búsqueda o selección), filtro por fecha, btn_today, permisos, user info |
| `main_application.py` | Completo | `open_attendance_form()` implementado |
| `main_view.py` | Completo | Señal `form_attendance_requested` conectada |
| `main_presenter.py` | Completo | Señal conectada a `open_attendance_form` |
| `src/database/manager.py` | Completo | Nuevo método `select_range()` (gte/lte en Supabase) |
| `tests/test_attendance_service.py` | Completo | 46 tests, 100% passing |

### Deuda técnica pendiente ⚠️

Ninguna. Módulo finalizado.

### Columnas de `attendance_table`

| # | Header | Fuente |
|---|---|---|
| 0 | Code | `attendance.member.member_code` + UUID en `UserRole` |
| 1 | Member Name | `attendance.member.full_name` |
| 2 | Check-in | `check_in_time.astimezone().strftime("%I:%M %p")` |
| 3 | Check-out | `check_out_time.astimezone().strftime("%I:%M %p")` o `""` |
| 4 | Duration | diferencia check_out - check_in (`Xh Ym`) |
| 5 | Notes | `attendance.notes` |

---

## Módulo Memberships — Estado Actual

### Fases completadas ✅

#### Fase 1 — Permisos y mensajes de error ✅

**`src/domain/permissions_definitions.py`**
- `PLANS_CREATE = "plans.create"`
- `PLANS_UPDATE = "plans.update"`
- `MEMBERSHIPS_READ = "memberships.read"`
- `MEMBERSHIPS_CREATE = "memberships.create"`
- `MEMBERSHIPS_UPDATE = "memberships.update"`
- `MEMBERSHIPS_DELETE = "memberships.delete"`

**`src/domain/permissions.py`**
- `PLANS_CREATE` → `{ADMIN}`
- `PLANS_UPDATE` → `{ADMIN}`
- `MEMBERSHIPS_READ` → `{ADMIN, RECEPTIONIST, ACCOUNTANT}`
- `MEMBERSHIPS_CREATE` → `{ADMIN, RECEPTIONIST}`
- `MEMBERSHIPS_UPDATE` → `{ADMIN, RECEPTIONIST}`
- `MEMBERSHIPS_DELETE` → `{ADMIN}`

**`src/utils/error_messages.py`**
- 13 constantes en sección `# Memberships module — Plans`
- 14 constantes en sección `# Memberships module — Member Memberships`

#### Fase 2 — Service ✅

**`src/services/membership_service.py`** — archivo nuevo (373 líneas)

Tablas: `_PLANS_TABLE = 'membership_plans'`, `_MEMBERSHIPS_TABLE = 'member_memberships'`

| Método | Descripción |
|---|---|
| `get_all_plans(include_inactive)` | SELECT con filtro opcional `is_active`, ordenado por `name` |
| `get_plan_by_id(plan_id)` | SELECT por `id`, retorna `not_found` si no existe |
| `create_plan(plan)` | Valida → inserta → retorna plan creado |
| `update_plan(plan)` | Valida id + campos → verifica existencia → actualiza |
| `toggle_plan_status(plan_id, is_active)` | UPDATE solo campo `is_active` |
| `get_memberships(status, search_term, date_from, date_to, expiring_days)` | 3 ramas de query según filtros; búsqueda por miembro en Python |
| `get_memberships_by_member(member_id)` | SELECT con JOIN, ordenado por `start_date` |
| `assign_membership(member_id, plan_id, start_date, notes, created_by)` | Valida activa existente → calcula `end_date` → inserta |
| `change_status(membership_id, new_status)` | Verifica existencia → valida transición → actualiza |

Helpers privados: `_validate_plan`, `_plan_to_row`, `_row_to_plan`, `_row_to_membership`, `_validate_status_transition`

**Transiciones de status permitidas:**
- `ACTIVE` → `SUSPENDED`, `CANCELLED`
- `SUSPENDED` → `ACTIVE`, `CANCELLED`
- `EXPIRED` → `ACTIVE` (renovación manual)
- `CANCELLED` → ninguna

**JOIN columns usadas en queries de membresías:**
```
"*, members(member_code, first_name, last_name), membership_plans(name, duration_days, price)"
```

**Notas de implementación:**
- `end_date` se calcula como `start_date + timedelta(days=plan.duration_days)` en `assign_membership`
- `end_date` / `start_date` son tipo `date` en Supabase → `select_range` recibe `date.isoformat()` (sin timezone)
- `search_term` en `get_memberships` filtra en Python sobre `member.full_name` y `member.member_code`
- `_plan_to_row` no incluye `id` (lo genera Supabase en insert; en update va en `filters`)

### Fases pendientes ⏳

| Fase | Descripción | Estado |
|---|---|---|
| Fase 3 | Tests — `tests/test_membership_service.py` | Pendiente |
| Fase 4 | UI file — `src/views/ui/membership_view.ui` | Pendiente |
| Fase 5 | View — `src/views/membership_view.py` | Pendiente |
| Fase 6 | Presenter — `src/presenters/membership_presenter.py` | Pendiente |
| Fase 7 | Navegación — 5 touch points (main_view, main_presenter, main_application) | Pendiente |
| Fase 8 | Actualizar CONTEXT.md como módulo completo | Pendiente |

### Diseño de UI planeado

**QTabWidget con 2 tabs:**

**Tab 1 — Plans:**
- Tabla izquierda: `plans_table` (Name, Duration, Price, Class Access, Max Classes/Week, Status)
- Form derecho: `input_plan_name`, `input_description`, `spin_duration_days`, `spin_price`, `check_has_class_access`, `spin_max_classes`, `check_is_active`
- Botones: `btn_new_plan`, `btn_save_plan`, `btn_cancel_plan`, `btn_toggle_status`

**Tab 2 — Memberships:**
- Fila de filtros: `input_search_member`, `combo_status`, `date_from`, `date_to`, `combo_expiring`, `btn_filter`, `btn_clear_filters`
- Tabla: `memberships_table` (Member Code, Member Name, Plan, Start Date, End Date, Status, Days Left)
- Sección asignación: `input_assign_search`, `combo_plan`, `date_start`, `input_notes`, `btn_assign`
- Botones de status: `btn_suspend`, `btn_cancel_membership`, `btn_reactivate`

**Columnas de tablas:**

Tab Plans:
| # | Header | Fuente |
|---|---|---|
| 0 | Name | `plan.name` + UUID en `UserRole` |
| 1 | Duration | `f"{plan.duration_days} days"` |
| 2 | Price | `f"${plan.price:.2f}"` |
| 3 | Class Access | `"Yes"` / `"No"` |
| 4 | Max Classes/Week | `str(plan.max_classes_per_week)` o `"Unlimited"` |
| 5 | Status | `"Active"` / `"Inactive"` |

Tab Memberships:
| # | Header | Fuente |
|---|---|---|
| 0 | Member Code | `membership.member.member_code` + UUID en `UserRole` |
| 1 | Member Name | `membership.member.full_name` |
| 2 | Plan | `membership.plan.name` |
| 3 | Start Date | `membership.start_date.strftime("%Y-%m-%d")` |
| 4 | End Date | `membership.end_date.strftime("%Y-%m-%d")` |
| 5 | Status | `membership.status.value` |
| 6 | Days Left | `(end_date - today).days` o `"Expired"` si negativo |

### Tests planeados (`test_membership_service.py`)

| Clase | Casos |
|---|---|
| `TestGetAllPlans` | retorna activos, incluye inactivos con flag, lista vacía, error de DB |
| `TestGetPlanById` | encontrado, not_found, error de DB |
| `TestCreatePlan` | éxito, nombre vacío, precio negativo, duración < 1 |
| `TestUpdatePlan` | éxito, plan no existe, id requerido |
| `TestTogglePlanStatus` | activa, desactiva |
| `TestAssignMembership` | éxito con `end_date` correcto, ya tiene activa, plan no existe, error de DB |
| `TestChangeStatus` | transiciones válidas, transiciones inválidas rechazadas, not_found |
| `TestGetMemberships` | sin filtros, por status, por search_term, por rango de fechas, expiring_days |

---

## Historial de Cambios

### Módulo Attendance — Historial completo

#### Implementación de `attendance_view.py` ✅
- Señales: `checkin_requested`, `checkout_requested`, `date_changed`, `today_requested`
- `initialize_components()`: conecta botones, inicializa `date_filter` a `QDate.currentDate()`, asigna ícono a `btn_close`
- `get_search_term()`: retorna `input_search.text().strip() or None`
- `get_selected_attendance_id()`: lee UUID desde `Qt.ItemDataRole.UserRole` de celda 0
- `get_current_date()`: retorna `date_filter.date().toPyDate()`
- `populate_table()`: 6 columnas, horas en formato 12h hora local (`.astimezone()`), Duration calculada, UUID guardado en `UserRole`
- `set_user_info()`: escribe en `label_user_name` y `label_user_role`

#### Implementación de `attendance_presenter.py` ✅
- `_connect_signals()`: conecta los 4 signals de la vista
- `_handle_load_attendance(filter_date)`: verifica permiso READ, llama service, popula tabla
- `_handle_checkin()`: busca miembro → toma `members[0]` → `check_in(member.id, current_user.id)` → recarga tabla
- `_handle_checkout()`: lee selección → verifica permiso → `check_out(attendance_id)` → recarga tabla
- `_handle_date_changed(qdate)`: recarga tabla con la fecha seleccionada
- `_handle_today()`: resetea `date_filter` (el `dateChanged` dispara recarga automáticamente)
- `_load_user_information()`: construye dict y llama `view.set_user_info()`

#### Bug Fix — Import incorrecto de permisos ✅
- Reemplazado `from tests.test_permissions import PermissionService, Permissions`
- Por `from src.domain.permissions_service import PermissionService` y `from src.domain.permissions_definitions import Permissions`

#### Bug Fix — `created_by` enviaba username en lugar de UUID ✅
- `check_in(member_id, self._current_user.username)` → `check_in(member.id, self._current_user.id)`
- La columna `created_by` en Supabase es de tipo `uuid`, no acepta strings de texto

#### Bug Fix — `get_attendance_by_date` retornaba lista vacía ✅
- **Causa:** comparación de strings sin timezone. `start/end` eran naive, `check_in_time` de Supabase tiene `+00:00`
- **Solución:** agregar `select_range()` a `DatabaseManager` (usa `.gte()` / `.lte()` de Supabase). El filtrado se hace en la BD, no en Python

#### Bug Fix — Registros no aparecían por diferencia UTC vs hora local ✅
- **Causa:** `datetime.combine(filter_date, ...).replace(tzinfo=timezone.utc)` asumía que la fecha local == fecha UTC
- En Ciudad Juárez (UTC-6), un check-in a las 7PM local se guarda como `01:xx UTC del día siguiente`
- **Solución:** detectar timezone local con `datetime.now().astimezone().tzinfo` y convertir los límites del día local a UTC antes de enviar a Supabase
- Mismo fix aplicado en `_validate_no_open_checkin()`

#### Bug Fix — Horas mostradas en UTC en lugar de hora local ✅
- `record.check_in_time.strftime("%H:%M")` → `record.check_in_time.astimezone().strftime("%I:%M %p")`
- `.astimezone()` convierte el datetime UTC al timezone local del sistema
- Formato cambiado a 12h (`%I:%M %p` → `07:41 PM`)

#### Actualización de tests — `test_attendance_service.py` ✅
- `make_attendance_row()` y `make_closed_row()`: timestamps actualizados a formato ISO con `+00:00`
- `TestGetAttendanceByDate`: migrado de `mock_db.select` a `mock_db.select_range`
- Eliminado `test_excludes_records_from_other_dates` (ya no aplica — el filtrado lo hace Supabase)
- Agregado `test_filters_by_check_in_time_column`: verifica que `select_range` recibe `column="check_in_time"` y timestamps con timezone
- `TestCheckIn`: migrado de `mock_db.select` a `mock_db.select_range` en todos los tests de validación

---

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

**Total: 179 tests, 100% passing.**
*(`test_membership_service.py` pendiente — se agregará en Fase 3)*

| Archivo de test               | Módulo cubierto                  | Tests |
|-------------------------------|----------------------------------|-------|
| `test_service_result.py`      | `services/result.py`             | 16    |
| `test_member_service.py`      | `services/member_service.py`     | 62    |
| `test_permissions.py`         | `domain/permissions*.py`         | 21    |
| `test_auth_service.py`        | `services/auth_service.py`       | 31    |
| `test_attendance_service.py`  | `services/attendance_service.py` | 46    |
| `conftest.py`                 | Fixtures compartidas             | —     |

**Estrategia de mocking:**
- `db_manager` parcheado con `unittest.mock.patch('src.services.*.db_manager')`.
- Helpers estáticos puros testeados directamente sin mocks.
- Ejecutar con: `python -m pytest tests/ -v`

---

## Próximos Pasos

### Módulo Memberships — Fases pendientes

| Fase | Tarea | Archivo |
|---|---|---|
| Fase 3 | Tests del service | `tests/test_membership_service.py` (nuevo) |
| Fase 4 | UI file (.ui) | `src/views/ui/membership_view.ui` (nuevo) |
| Fase 5 | View Python | `src/views/membership_view.py` (nuevo) |
| Fase 6 | Presenter | `src/presenters/membership_presenter.py` (nuevo) |
| Fase 7 | Navegación | `main_view.py`, `main_presenter.py`, `main_application.py` (modificar) |
| Fase 8 | Documentación | `CONTEXT.md` (actualizar) |

### Módulos siguientes (después de Memberships)

| Módulo | Botón en sidebar | Prioridad |
|---|---|---|
| Dashboard | `btn_dashboard` | Alta — requiere datos de Memberships para ser útil |
| Payments | `btn_payments` | Alta — registro de cobros |
| Instructors | `btn_instructors` | Media |
| Classes | `btn_classes` | Media |
| Equipment | `btn_equipment` | Baja |
| Reports | `btn_reports` | Baja |
| Settings | `btn_settings` | Baja |
