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

| Módulo      | Estado       | Notas                                                                                      |
|-------------|--------------|--------------------------------------------------------------------------------------------|
| Login       | Completo     | bcrypt, roles, sesión. Login en QThread (no bloquea UI)                                    |
| Members     | Completo     | CRUD funcional, tests, código limpio                                                       |
| Attendance  | Completo     | CRUD completo, check-in/out por búsqueda o selección, MemberSelectDialog, 46 tests         |
| Payments    | Completo     | Registro de cobros, filtros por status/método/fecha/búsqueda, 43 tests                     |
| Memberships | Completo     | Planes + membresías asignadas, CRUD, transiciones de estado, 94 tests                      |
| Otros       | No iniciados | Sidebar conectado a Members, Attendance, Payments y Memberships                            |

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

## Módulo Attendance — Archivos Clave

| Archivo | Notas |
|---|---|
| `src/models/models.py` — `Attendance` | Dataclass con member_id, check_in/out_time, notes, member |
| `src/services/attendance_service.py` | 5 métodos: get_by_date, search_member, check_in, check_out, find_open_checkin_for_member |
| `src/views/ui/attendance_view.ui` | Layout Qt Designer |
| `src/views/attendance_view.py` | Señales, populate_table (hora local 12h, Duration, UserRole) |
| `src/views/widgets/member_select_dialog.py` | QDialog reutilizable para seleccionar miembro de lista múltiple |
| `src/presenters/attendance_presenter.py` | check-in/out por búsqueda o selección, filtro por fecha, btn_today |
| `tests/test_attendance_service.py` | 46 tests, 100% passing |

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

## Módulo Payments — Archivos Clave

| Archivo | Notas |
|---|---|
| `src/models/models.py` — `Payment` | Dataclass con member_id, amount, payment_method, payment_date, status, reference_number |
| `src/models/enums.py` — `PaymentMethod`, `PaymentStatus` | cash / card / transfer / other · completed / pending / cancelled / refunded |
| `src/services/payment_service.py` | get_payments, get_payments_by_member, create_payment, update_payment |
| `src/views/ui/payment_view.ui` | Layout Qt Designer (1060×700) |
| `src/views/payment_view.py` | Señales, populate_table, filtros por status/método/fecha/búsqueda |
| `src/presenters/payment_presenter.py` | Búsqueda de miembro + MemberSelectDialog, permisos, filtros |
| `tests/test_payment_service.py` | 43 tests, 100% passing |

### Permisos de Payments

| Permiso | Roles |
|---|---|
| `PAYMENTS_READ` | ADMIN, RECEPTIONIST, ACCOUNTANT |
| `PAYMENTS_CREATE` | ADMIN, RECEPTIONIST |
| `PAYMENTS_UPDATE` | ADMIN |

### Columnas de `payments_table`

| # | Header | Fuente |
|---|---|---|
| 0 | Code | `payment.member.member_code` + UUID en `UserRole` |
| 1 | Member Name | `payment.member.full_name` |
| 2 | Amount | `f"${payment.amount:.2f}"` |
| 3 | Method | `payment.payment_method.value.capitalize()` |
| 4 | Date | `payment_date.strftime("%Y-%m-%d %I:%M %p")` |
| 5 | Status | `payment.status.value.capitalize()` |
| 6 | Notes | `payment.notes or ""` |

---

## Módulo Memberships — Archivos Implementados ✅

| Archivo | Notas |
|---|---|
| `src/domain/permissions_definitions.py` | PLANS_CREATE, PLANS_UPDATE, MEMBERSHIPS_READ/CREATE/UPDATE/DELETE |
| `src/domain/permissions.py` | PLANS_* → ADMIN; MEMBERSHIPS_READ → ADMIN/RECEPTIONIST/ACCOUNTANT; MEMBERSHIPS_CREATE/UPDATE → ADMIN/RECEPTIONIST |
| `src/utils/error_messages.py` | 13 constantes Plans + 14 constantes Memberships |
| `src/services/membership_service.py` | 9 métodos públicos, 5 helpers privados |
| `src/views/ui/membership_view.ui` | QTabWidget 2 tabs, 1200×750 |
| `src/views/membership_view.py` | 10 señales, getters/setters para ambas tabs |
| `src/presenters/membership_presenter.py` | Plans CRUD + toggle_status + Memberships assign/suspend/cancel/reactivate |
| `tests/test_membership_service.py` | 94 tests, 100% passing |

### Service — Métodos públicos

| Método | Descripción |
|---|---|
| `get_all_plans(include_inactive)` | SELECT con filtro opcional `is_active`, ordenado por `name` |
| `get_plan_by_id(plan_id)` | SELECT por `id`, retorna `not_found` si no existe |
| `create_plan(plan)` | Valida → inserta → retorna plan creado |
| `update_plan(plan)` | Valida id + campos → verifica existencia → actualiza (`updated_at` incluido) |
| `toggle_plan_status(plan_id, is_active)` | UPDATE solo campo `is_active` |
| `get_memberships(status, search_term, date_from, date_to, expiring_days)` | 3 ramas de query; búsqueda por miembro en Python |
| `get_memberships_by_member(member_id)` | SELECT con JOIN, ordenado por `start_date` |
| `assign_membership(member_id, plan_id, start_date, notes, created_by)` | Valida activa existente → calcula `end_date` → inserta |
| `change_status(membership_id, new_status)` | Verifica existencia → valida transición → actualiza |

### Transiciones de status permitidas

- `ACTIVE` → `SUSPENDED`, `CANCELLED`
- `SUSPENDED` → `ACTIVE`, `CANCELLED`
- `EXPIRED` → `ACTIVE` (renovación manual)
- `CANCELLED` → ninguna

### Notas de implementación

- `end_date = start_date + timedelta(days=plan.duration_days)` calculado en `assign_membership`
- `start_date` / `end_date` son tipo `date` → `select_range` recibe `date.isoformat()` (sin timezone)
- `search_term` en `get_memberships` filtra en Python sobre `member.full_name` y `member.member_code`
- `_plan_to_row` no incluye `id` (lo genera Supabase en insert; en update va en `filters`)
- `expiring_days` tiene prioridad sobre `date_from`/`date_to` en el presenter

### View — Señales

| Señal | Tab | Origen |
|---|---|---|
| `save_plan_requested` | Plans | `btn_save_plan` |
| `new_plan_requested` | Plans | `btn_new_plan` |
| `cancel_plan_requested` | Plans | `btn_cancel_plan` |
| `toggle_status_requested` | Plans | `btn_toggle_status` |
| `plan_selected` | Plans | `plans_table.itemSelectionChanged` |
| `filter_requested` | Memberships | `btn_filter` + `btn_clear_filters` |
| `assign_requested` | Memberships | `btn_assign` |
| `suspend_requested` | Memberships | `btn_suspend` |
| `cancel_membership_requested` | Memberships | `btn_cancel_membership` |
| `reactivate_requested` | Memberships | `btn_reactivate` |

### Presenter — Decisiones de diseño

- `_selected_plan_id: Optional[str]` distingue modo create (None) vs update (UUID)
- `_handle_save_plan` delega a `_create_plan()` o `_update_plan()` según el estado
- `_change_membership_status(new_status)` es compartido por suspend / cancel / reactivate
- `_handle_load_plans()` popula tabla (activos + inactivos) y combo_plan (solo activos)
- `combo_plan` usa `addItem(name, plan.id)` → `currentData()` retorna UUID directamente
- `get_max_classes()` retorna `None` cuando `spin_max_classes == 0` (Unlimited)
- `get_expiring_days()` parsea número del texto del combo ("7 days" → 7)

### Columnas de `plans_table`

| # | Header | Fuente |
|---|---|---|
| 0 | Name | `plan.name` + UUID en `UserRole` |
| 1 | Duration | `f"{plan.duration_days} days"` |
| 2 | Price | `f"${plan.price:.2f}"` |
| 3 | Class Access | `"Yes"` / `"No"` |
| 4 | Max Classes/Week | `str(plan.max_classes_per_week)` o `"Unlimited"` |
| 5 | Status | `"Active"` / `"Inactive"` |

### Columnas de `memberships_table`

| # | Header | Fuente |
|---|---|---|
| 0 | Member Code | `membership.member.member_code` + UUID en `UserRole` |
| 1 | Member Name | `membership.member.full_name` |
| 2 | Plan | `membership.plan.name` |
| 3 | Start Date | `membership.start_date.strftime("%Y-%m-%d")` |
| 4 | End Date | `membership.end_date.strftime("%Y-%m-%d")` |
| 5 | Status | `membership.status.value.capitalize()` |
| 6 | Days Left | `(end_date - today).days` o `"Expired"` si negativo |

---

## Tests — Estado Actual

**Total: 316 tests, 100% passing.**

| Archivo de test                  | Módulo cubierto                     | Tests |
|----------------------------------|-------------------------------------|-------|
| `test_service_result.py`         | `services/result.py`                | 16    |
| `test_member_service.py`         | `services/member_service.py`        | 62    |
| `test_permissions.py`            | `domain/permissions*.py`            | 21    |
| `test_auth_service.py`           | `services/auth_service.py`          | 31    |
| `test_attendance_service.py`     | `services/attendance_service.py`    | 46    |
| `test_payment_service.py`        | `services/payment_service.py`       | 43    |
| `test_membership_service.py`     | `services/membership_service.py`    | 94    |
| `conftest.py`                    | Fixtures compartidas                | —     |

**Estrategia de mocking:**
- `db_manager` parcheado con `unittest.mock.patch('src.services.*.db_manager')`.
- Helpers estáticos puros testeados directamente sin mocks.
- Ejecutar con: `python -m pytest tests/ -v`

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

## Próximos Pasos

| Módulo | Botón en sidebar | Prioridad |
|---|---|---|
| Dashboard | `btn_dashboard` | Alta — requiere datos de Memberships y Payments para ser útil |
| Instructors | `btn_instructors` | Media |
| Classes | `btn_classes` | Media |
| Equipment | `btn_equipment` | Baja |
| Reports | `btn_reports` | Baja |
| Settings | `btn_settings` | Baja |
