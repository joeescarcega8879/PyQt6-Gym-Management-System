# Contexto del Proyecto — PyQt6 Gym Management System

> Archivo de seguimiento interno. NO agregar a git.

---

## Descripción General

Aplicación de escritorio para gestión de gimnasios construida con PyQt6 y PostgreSQL local.

- **Patrón de arquitectura:** MVP (Model-View-Presenter)
- **Base de datos:** PostgreSQL local (driver `psycopg2-binary`)
- **UI:** PyQt6 con archivos `.ui` de Qt Designer
- **Autenticación:** bcrypt + tabla `users` propia en PostgreSQL

---

## Estructura Principal

```
src/
├── assets/
│   ├── styles.css          # Stylesheet base (dark theme, accent azul)
│   ├── icons/              # 12 íconos PNG embebidos como base64
│   ├── resources_rc.py     # Generado — get_icon(path) -> QIcon  [.gitignore]
│   └── themes/             # 5 archivos CSS de temas (dark_blue, green, purple, orange, cyan)
├── config/                 # Lectura de .env (Settings), DATA_DIR, LOGS_DIR, EXPORTS_DIR
├── database/               # Singleton DatabaseManager — SQL puro via psycopg2
├── domain/                 # Permisos por rol (PermissionService, Permissions)
├── models/                 # Dataclasses (Member, User, Class, etc.) y enums
├── presenters/             # Lógica de negocio UI (MemberPresenter, ClassPresenter, etc.)
├── services/               # Lógica de negocio pura (MemberService, SettingsService, etc.)
├── utils/                  # Helpers: StatusBar, SetFormat, ErrorMessages, PdfExporter
└── views/
    ├── ui/                 # Archivos .ui de Qt Designer
    └── widgets/            # Componentes reutilizables (MemberSelectDialog)
data/
└── user_settings.json      # Preferencias de usuario — persistencia de tema [.gitignore]
exports/                    # PDFs generados por el módulo Reports [.gitignore]
docs/
└── database_schema.sql     # Único archivo de docs/ versionado (el resto es [.gitignore])
scripts/
├── build_resources.py      # Embebe íconos en resources_rc.py
├── generate_themes.py      # Genera los 5 CSS de temas desde styles.css
├── seed_members.py         # Datos de ejemplo para desarrollo local
└── seed_attendance.py      # Datos de ejemplo para desarrollo local
```

---

## Módulos Implementados

| Módulo      | Estado   | Tests | Notas                                                                 |
|-------------|----------|-------|-----------------------------------------------------------------------|
| Login       | Completo | 31    | bcrypt, roles, sesión. Login en QThread (no bloquea UI)               |
| Members     | Completo | 62    | CRUD funcional, permisos, íconos, código limpio                       |
| Attendance  | Completo | 46    | Check-in/out por búsqueda o selección, MemberSelectDialog, timezone   |
| Payments    | Completo | 43    | Registro de cobros, filtros por status/método/fecha/búsqueda          |
| Memberships | Completo | 94    | Planes + membresías asignadas, CRUD, transiciones de estado           |
| Classes     | Completo | 75    | CRUD clases + horarios + inscripciones, 3 tabs, capacidad máxima      |
| Settings    | Completo | 31    | Cambio de tema en vivo, 5 temas dark, persistencia en JSON            |
| Dashboard   | Completo | 17    | KPIs + tablas de detalle, agrega datos de otros servicios, refresh manual |
| Instructors | Completo | 51    | CRUD funcional, permisos, specialties como TEXT[], sin vínculo a users |
| Equipment   | Completo | 57    | 2 tabs (Equipment + Maintenance), CRUD equipo + historial insert-only |
| Reports     | Completo | 27    | 4 tabs de solo lectura (Financial/Memberships/Attendance/Operational), agrega datos de otros servicios, export a PDF con reportlab |

---

## Módulo Members — Archivos Clave

| Archivo                              | Responsabilidad                              |
|--------------------------------------|----------------------------------------------|
| `src/models/models.py`               | Dataclass `Member`                           |
| `src/services/member_service.py`     | CRUD + búsqueda + validación                 |
| `src/presenters/member_presenter.py` | Señales, permisos, coordinación view↔service |
| `src/views/member_view.py`           | UI pura, señales, populate_table             |
| `src/views/ui/member_view.ui`        | Layout Qt Designer                           |
| `src/database/manager.py`            | select / insert / update / delete / search / select_range |

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
- `_plan_to_row` no incluye `id` (lo genera PostgreSQL en insert; en update va en `filters`)
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

## Módulo Classes — Archivos Implementados ✅

| Archivo | Notas |
|---|---|
| `src/models/models.py` — `Class`, `ClassSchedule`, `ClassEnrollment` | Dataclasses completos, ya existían |
| `src/models/enums.py` — `DifficultyLevel`, `EnrollmentStatus` | all/beginner/intermediate/advanced · enrolled/attended/absent/cancelled |
| `src/domain/permissions_definitions.py` | CLASSES_READ/CREATE/UPDATE, SCHEDULES_READ/CREATE/UPDATE, ENROLLMENTS_READ/CREATE/UPDATE |
| `src/domain/permissions.py` | CLASSES/SCHEDULES_* → ADMIN; ENROLLMENTS_* → ADMIN/RECEPTIONIST |
| `src/utils/error_messages.py` | 15 constantes Classes + 12 constantes Schedules + 12 constantes Enrollments |
| `src/services/class_service.py` | 11 métodos públicos: CRUD clases, CRUD horarios, CRUD inscripciones |
| `src/views/ui/class_view.ui` | QTabWidget 3 tabs, 1200×750 |
| `src/views/class_view.py` | 16 señales, getters/setters para las 3 tabs |
| `src/presenters/class_presenter.py` | Classes CRUD + Schedules CRUD + Enrollments con MemberSelectDialog |
| `tests/test_class_service.py` | 75 tests, 100% passing |

### Service — Métodos públicos

| Método | Descripción |
|---|---|
| `get_all_classes(include_inactive)` | SELECT con filtro opcional `is_active`, ordenado por `name` |
| `get_class_by_id(class_id)` | SELECT por `id`, retorna `not_found` si no existe |
| `create_class(gym_class)` | Valida → inserta con `created_at`/`updated_at` |
| `update_class(gym_class)` | Valida id + campos → verifica existencia → actualiza |
| `toggle_class_status(class_id, is_active)` | UPDATE `is_active` + `updated_at` |
| `get_schedules(class_id, day_of_week, include_inactive)` | SELECT con JOIN a `classes`, filtros opcionales |
| `get_schedule_by_id(schedule_id)` | SELECT con JOIN, retorna `not_found` si no existe |
| `create_schedule(schedule)` | Valida → inserta |
| `update_schedule(schedule)` | Valida id + campos → verifica existencia → actualiza |
| `toggle_schedule_status(schedule_id, is_active)` | UPDATE `is_active` + `updated_at` |
| `get_enrollments(schedule_id, class_date, status, search_term)` | SELECT con JOINs; búsqueda por miembro en Python |
| `get_enrollments_by_member(member_id)` | SELECT con JOINs, ordenado por `class_date` |
| `enroll_member(schedule_id, member_id, class_date, notes, created_by)` | Valida duplicado + capacidad → inserta |
| `update_enrollment_status(enrollment_id, new_status)` | Verifica existencia → UPDATE status |
| `get_enrollment_count(schedule_id, class_date)` | Cuenta inscripciones no canceladas para validar capacidad |

### Notas de implementación

- `day_of_week`: 0 = Sunday, 6 = Saturday (igual que JS)
- `start_time` / `end_time`: strings `"HH:MM"` — `_validate_schedule` exige start < end
- `max_capacity = None` → ilimitado; `max_capacity = 0` → inválido (falla validación)
- Capacidad verificada en Python antes del insert, consultando `get_enrollment_count()`
- `search_term` en `get_enrollments` filtra en Python por `member.full_name` y `member.member_code`
- Tablas BD requeridas: `classes`, `class_schedules`, `class_enrollments`

### Columnas de `classes_table`

| # | Header | Fuente |
|---|---|---|
| 0 | Name | `c.name` + UUID en `UserRole` |
| 1 | Duration | `f"{c.duration_minutes} min"` |
| 2 | Capacity | `str(c.max_capacity)` o `"Unlimited"` |
| 3 | Difficulty | `c.difficulty_level.value.capitalize()` |
| 4 | Status | `"Active"` / `"Inactive"` |

### Columnas de `schedules_table`

| # | Header | Fuente |
|---|---|---|
| 0 | Class | `s.class_info.name` + UUID en `UserRole` |
| 1 | Day | `_DAY_LABELS[s.day_of_week]` |
| 2 | Start | `str(s.start_time)[:5]` |
| 3 | End | `str(s.end_time)[:5]` |
| 4 | Room | `s.room or ""` |
| 5 | Status | `"Active"` / `"Inactive"` |

### Columnas de `enrollments_table`

| # | Header | Fuente |
|---|---|---|
| 0 | Member Code | `e.member.member_code` + UUID en `UserRole` |
| 1 | Member Name | `e.member.full_name` |
| 2 | Class | `e.schedule.class_info.name` |
| 3 | Date | `e.class_date.strftime("%Y-%m-%d")` |
| 4 | Start | `str(e.schedule.start_time)[:5]` |
| 5 | Room | `e.schedule.room or ""` |
| 6 | Status | `e.status.value.capitalize()` |

---

## Módulo Settings — Archivos Implementados ✅

| Archivo | Notas |
|---|---|
| `src/assets/themes/dark_blue.css` | Tema default — accent `#2196F3` |
| `src/assets/themes/dark_green.css` | Accent `#4CAF50` |
| `src/assets/themes/dark_purple.css` | Accent `#9C27B0` |
| `src/assets/themes/dark_orange.css` | Accent `#FF9800` |
| `src/assets/themes/dark_cyan.css` | Accent `#00BCD4` |
| `src/services/settings_service.py` | `load()`, `save()`, `load_theme_css()`, `get_available_themes()` |
| `src/views/ui/settings_view.ui` | 2 columnas: lista de temas + preview panel, 900×600 |
| `src/views/settings_view.py` | 3 señales, `populate_theme_list()`, `update_preview()`, íconos de color |
| `src/presenters/settings_presenter.py` | Preview en vivo + guardar + descartar, `_original_theme_key` para revert |
| `tests/test_settings_service.py` | 31 tests, 100% passing |
| `scripts/generate_themes.py` | Genera los 5 CSS reemplazando tokens de color del base |

### Service — Métodos públicos

| Método | Descripción |
|---|---|
| `load()` | Lee `data/user_settings.json`; retorna defaults si no existe |
| `save(settings)` | Escribe `data/user_settings.json` como JSON indentado |
| `get_theme_css_path(theme_key)` | Retorna `Path` al CSS del tema, o `None` si no existe |
| `load_theme_css(theme_key)` | Lee el CSS; fallback a `dark_blue` si la clave es inválida |
| `get_available_themes()` | Lista de `(key, display_name, accent_hex)` tuples |

### Notas de implementación

- Persistencia en `data/user_settings.json` (creado por `config.setup_directories()`)
- El archivo JSON se crea al primer `save()`; si no existe `load()` retorna `_DEFAULTS`
- `load()` hace merge con `_DEFAULTS` para preservar compatibilidad con versiones futuras
- `main_application.load_stylesheet(theme_key)` aplica el CSS con `QApplication.instance().setStyleSheet()`
- Al arrancar, `main_application.__init__` lee el tema guardado antes de mostrar ninguna ventana
- Discard revierte al tema que estaba activo cuando se abrió el panel (no al guardado en disco)
- Los 5 CSS de temas son generados por `scripts/generate_themes.py` a partir de `styles.css`

### Flujo de tema en runtime

```
Usuario selecciona tema → theme_selected(key) signal
  → SettingsPresenter._handle_theme_selected()
    → main_app.load_stylesheet(key)        # aplica CSS globalmente, preview inmediato
    → view.update_preview(name, accent)    # actualiza panel derecho

Usuario presiona Save
  → settings_service.save({"theme": key}) # persiste en JSON
  → _original_theme_key = key             # actualiza el punto de revert

Usuario presiona Discard
  → main_app.load_stylesheet(_original_theme_key)  # revierte
  → view.set_current_theme(_original_theme_key)    # resalta el item correcto
```

---

## Módulo Dashboard — Archivos Implementados ✅

| Archivo | Notas |
|---|---|
| `src/models/models.py` — `DashboardSummary` | Dataclass: active_members, monthly_revenue, today_checkins, expiring_memberships_count, today_schedules, expiring_memberships |
| `src/domain/permissions_definitions.py` | `DASHBOARD_READ` |
| `src/domain/permissions.py` | `DASHBOARD_READ` → ADMIN, RECEPTIONIST, INSTRUCTOR, ACCOUNTANT (todos los roles autenticados) |
| `src/utils/error_messages.py` | 3 constantes Dashboard |
| `src/services/dashboard_service.py` | `DashboardService.get_summary()` — no accede a `db_manager` directamente, agrega datos de los demás servicios |
| `src/views/ui/dashboard_view.ui` | 4 tarjetas KPI + 2 tablas de detalle, 1200×750 |
| `src/views/dashboard_view.py` | Señal `refresh_requested`, `set_summary()`, 2 métodos `populate_*_table` |
| `src/presenters/dashboard_presenter.py` | Carga automática al abrir + refresh manual, valida `DASHBOARD_READ` |
| `tests/test_dashboard_service.py` | 17 tests, 100% passing |

### Service — Diseño

- `DashboardService` es una capa de agregación pura: reutiliza `member_service`, `payment_service`, `attendance_service`, `membership_service` y `class_service` en vez de tocar `db_manager` directamente, evitando duplicar SQL/joins ya existentes.
- Cada sub-consulta (`_get_active_members_count`, `_get_monthly_revenue`, etc.) atrapa el fallo del sub-servicio con un `logger.warning` y retorna un valor por defecto (0 / lista vacía) — un módulo caído no tumba todo el Dashboard.
- `get_summary()` sí propaga una excepción inesperada (no controlada dentro de los helpers) como `ServiceResult.fail(...)`.

### KPIs y fuentes de datos

| KPI / Tabla | Fuente |
|---|---|
| Active Members | `member_service.get_all_members(include_inactive=False)` → `len()` |
| Revenue This Month | `payment_service.get_payments(status=COMPLETED, date_from=1er día del mes, date_to=hoy)` → `sum(amount)` |
| Check-ins Today | `attendance_service.get_attendance_by_date(date.today())` → `len()` |
| Memberships Expiring (7 days) | `membership_service.get_memberships(expiring_days=7)` → `len()` / lista |
| Today's Classes (tabla) | `class_service.get_schedules(day_of_week=hoy, include_inactive=False)` |

- Conversión de día de la semana: `ClassSchedule.day_of_week` usa 0=Domingo…6=Sábado; `date.weekday()` de Python usa 0=Lunes…6=Domingo → fórmula `(date.today().weekday() + 1) % 7`.
- Sin gráficos (matplotlib/pyqtgraph no instalados en el entorno actual); solo tarjetas numéricas + tablas.
- Refresh manual vía `btn_refresh` (sin `QTimer`, consistente con el resto de módulos).

---

## Módulo Instructors — Archivos Implementados ✅

| Archivo | Notas |
|---|---|
| `src/models/models.py` — `Instructor` | Dataclass ya existía: id, user_id, first_name, last_name, email, phone, specialties (List[str]), certifications, hire_date, photo_url, is_active, created_at, updated_at + property `full_name` |
| `docs/database_schema.sql` | Tabla `instructors` ya existía (columnas 1:1 con el dataclass); `specialties` es `TEXT[]` nativo de Postgres |
| `src/domain/permissions_definitions.py` | `INSTRUCTORS_CREATE/READ/UPDATE` (sin DELETE — mismo patrón que Classes, soft-delete vía `is_active`) |
| `src/domain/permissions.py` | `INSTRUCTORS_READ` → ADMIN/RECEPTIONIST/INSTRUCTOR; `INSTRUCTORS_CREATE/UPDATE` → ADMIN |
| `src/utils/error_messages.py` | 12 constantes Instructors |
| `src/services/instructor_service.py` | 5 métodos públicos: get_all/get_by_id/search/create/update |
| `src/views/ui/instructor_view.ui` | Layout Qt Designer, adaptado de `member_view.ui`, 1060×700 |
| `src/views/instructor_view.py` | 7 señales, populate_table, define `show_error()` (ver nota abajo) |
| `src/presenters/instructor_presenter.py` | CRUD + búsqueda, validación de permisos |
| `tests/test_instructor_service.py` | 51 tests, 100% passing |

### Diferencias con Members (a propósito)

- Sin `member_code`/`created_by`: la tabla `instructors` no tiene esas columnas.
- Sin `INSTRUCTORS_DELETE`: ningún módulo del proyecto implementa delete real; todos usan el toggle `is_active` vía update (igual que Members/Classes a pesar de que sus permisos `_DELETE` existen como constantes sin uso).
- `specialties` es `TEXT[]` — psycopg2 + `RealDictCursor` lo mapea de forma nativa a `list[str]`, sin serialización manual. En la UI se edita como texto separado por comas (`input_specialties`) y se parsea con `InstructorView._parse_specialties()`.
- `user_id` y `photo_url` existen en el dataclass pero no se exponen en el formulario (igual que `photo_url` en Members) — quedan disponibles para una futura vinculación con `users`.
- Búsqueda: solo por First Name / Last Name / Email (no hay campo tipo "código" como en Members).

### Bug corregido — `MemberView.show_error` faltante

`member_presenter.py` llamaba a `self.view.show_error(...)` en varias rutas de error, pero `MemberView` no definía ese método — lanzaba `AttributeError` en producción cuando fallaba una carga/búsqueda. Corregido agregando `show_error()` a `MemberView` (mismo patrón que `InstructorView`: `QMessageBox.critical(self, "Error", message)`).

### Columnas de `table_instructors`

| # | Header | Fuente |
|---|---|---|
| 0 | First Name | `i.first_name` + UUID en `UserRole` |
| 1 | Last Name | `i.last_name` |
| 2 | Email | `i.email or ""` |
| 3 | Phone | `i.phone or ""` |
| 4 | Specialties | `", ".join(i.specialties)` |
| 5 | Certifications | `i.certifications or ""` |
| 6 | Hire Date | `str(i.hire_date)` o `""` |
| 7 | Status | `"Active"` / `"Inactive"` |

---

## Módulo Equipment — Archivos Implementados ✅

| Archivo | Notas |
|---|---|
| `src/models/models.py` — `Equipment`, `EquipmentMaintenance` | Dataclasses ya existían; `EquipmentMaintenance` no tiene `updated_at` (tabla insert-only) |
| `src/models/enums.py` — `EquipmentCondition`, `MaintenanceType` | excellent/good/fair/poor/out_of_service · preventive/corrective/inspection |
| `docs/database_schema.sql` | Tablas `equipment` y `equipment_maintenance` ya existían; `equipment_maintenance.performed_by` es `VARCHAR` libre, no FK a `users` |
| `src/domain/permissions_definitions.py` | `EQUIPMENT_CREATE/READ/UPDATE`, `MAINTENANCE_CREATE/READ` |
| `src/domain/permissions.py` | `EQUIPMENT_READ`/`MAINTENANCE_READ` → ADMIN/RECEPTIONIST/INSTRUCTOR; `EQUIPMENT_CREATE/UPDATE`/`MAINTENANCE_CREATE` → ADMIN |
| `src/utils/error_messages.py` | 13 constantes Equipment + 6 constantes Maintenance |
| `src/services/equipment_service.py` | 9 métodos públicos: CRUD equipo (5) + consulta/registro de mantenimiento (4) |
| `src/views/ui/equipment_view.ui` | QTabWidget 2 tabs, 1200×750 — mismo patrón que `membership_view.ui` |
| `src/views/equipment_view.py` | 9 señales, getters/setters para ambos tabs |
| `src/presenters/equipment_presenter.py` | Equipment CRUD (patrón "Save" único como Plans) + Maintenance filter/log |
| `tests/test_equipment_service.py` | 57 tests, 100% passing |

### Diseño — por qué sigue el patrón de Memberships y no el de Members/Instructors

- `Equipment` + `EquipmentMaintenance` son dos entidades relacionadas (1:N vía `equipment_id`), igual que Plans + Memberships → un servicio, un presenter, una vista con `QTabWidget` de 2 tabs, en vez del patrón CRUD plano de un solo formulario.
- Tab "Equipment": `btn_new_equipment` / `btn_save_equipment` / `btn_cancel_equipment` — un solo botón "Save" decide crear o actualizar según `_selected_equipment_id` en el presenter (igual que `_handle_save_plan` en `MembershipPresenter`), no dos botones separados como en Members/Instructors.
- Tab "Maintenance": solo lectura + creación (`get_maintenance_records` + `log_maintenance`) — sin update ni delete, porque `equipment_maintenance` es una tabla de historial insert-only (sin `updated_at`), igual que Payments/Attendance.
- `_MAINTENANCE_COLUMNS` + `_MAINTENANCE_JOINS` hacen `LEFT JOIN equipment` para traer `equipment.name AS equipment_name` denormalizado en cada fila, igual que `_MEMBERSHIP_COLUMNS`/`_MEMBERSHIP_JOINS` en `membership_service.py`.
- `get_maintenance_records()` usa `db_manager.select_range()` cuando se pasan `date_from`/`date_to`, y `db_manager.select()` en el resto de los casos — misma rama condicional que `get_memberships()`.
- `log_maintenance()` inserta y luego adjunta manualmente `equipment_name` a la fila devuelta por `insert()` (que no lleva el join), antes de convertirla con `_row_to_maintenance` — mismo truco usado en `assign_membership()`.

### Columnas de `equipment_table`

| # | Header | Fuente |
|---|---|---|
| 0 | Name | `e.name` + UUID en `UserRole` |
| 1 | Category | `e.category or ""` |
| 2 | Brand | `e.brand or ""` |
| 3 | Model | `e.model or ""` |
| 4 | Serial Number | `e.serial_number or ""` |
| 5 | Condition | `e.condition.value.replace("_"," ").capitalize()` |
| 6 | Location | `e.location or ""` |
| 7 | Status | `"Active"` / `"Inactive"` |

### Columnas de `maintenance_table`

| # | Header | Fuente |
|---|---|---|
| 0 | Equipment | `r.equipment.name` (join denormalizado) |
| 1 | Date | `r.maintenance_date.strftime("%Y-%m-%d")` |
| 2 | Type | `r.maintenance_type.value.capitalize()` |
| 3 | Description | `r.description or ""` |
| 4 | Cost | `f"${r.cost:.2f}"` o `""` |
| 5 | Performed By | `r.performed_by or ""` |
| 6 | Next Maintenance | `r.next_maintenance_date.strftime("%Y-%m-%d")` o `""` |

---

## Módulo Reports — Archivos Implementados ✅

| Archivo | Notas |
|---|---|
| `src/models/models.py` — `FinancialReport`, `MembershipReport`, `AttendanceReport`, `OperationalReport` | Dataclasses de agregación, una por tab |
| `src/services/reports_service.py` | Agregación pura (no toca `db_manager`), reutiliza payment/membership/attendance/class/equipment/instructor service — mismo patrón que `DashboardService` |
| `src/services/attendance_service.py` | Nuevo método `get_attendance_by_range(date_from, date_to)` — antes solo existía `get_attendance_by_date` (un solo día) |
| `src/utils/pdf_exporter.py` | `export_table_report()` — utilidad pura con `reportlab.platypus` (primer uso real de `reportlab` en el proyecto, ya estaba en `requirements.txt` sin usarse) |
| `src/config/settings.py` | Nuevo `EXPORTS_DIR` (destino por defecto de los PDF exportados) |
| `src/domain/permissions_definitions.py` / `permissions.py` | `REPORTS_READ` → solo ADMIN + ACCOUNTANT (único permiso, cubre los 4 tabs) |
| `src/views/ui/reports_view.ui` | QTabWidget 4 tabs, 1200×750 — módulo de solo lectura, sin formularios de creación |
| `src/views/reports_view.py` | 8 señales, getters de filtros, `populate_*_table()` por tabla, `prompt_save_pdf_path()` (QFileDialog), `show_export_success()` |
| `src/presenters/reports_presenter.py` | Carga las 4 tabs al abrir, guarda el último reporte de cada tipo para exportar sin repetir la consulta |
| `tests/test_reports_service.py` | 24 tests, 100% passing |
| `tests/test_pdf_exporter.py` | 3 tests — genera un PDF real en `tmp_path` y verifica la firma `%PDF-` (sin mockear reportlab) |

### Los 4 tabs

| Tab | Contenido | Fuente |
|---|---|---|
| Financial | Total revenue, transacciones, % vs periodo anterior, tabla de pagos | `payment_service.get_payments()` — revenue siempre sobre pagos COMPLETED, independiente del filtro de status elegido |
| Memberships | Conteo por status, conteo por plan, tasa de retención, expiring soon (7 días) | `membership_service.get_memberships()` / `get_all_plans()` |
| Attendance | Total check-ins, check-ins por hora, top 10 miembros más frecuentes | `attendance_service.get_attendance_by_range()` (nuevo) |
| Operational | Equipo por condición, equipo próximo a mantenimiento (7 días), ocupación de clases hoy, carga de instructores | `equipment_service` + `class_service` + `instructor_service` |

### Notas de implementación

- **Retention rate (aproximación)**: `active / (active + expired)`. No es una tasa de renovación real — el esquema no tiene un flag que distinga una renovación de un alta nueva. Documentado en el docstring de `MembershipReport.retention_rate_pct`.
- **Instructor workload**: cuenta *todos* los schedules activos (no solo los de hoy), agrupados por `instructor_id` y resueltos a nombre vía `instructor_service.get_all_instructors()`.
- **Equipment due maintenance**: por cada equipo se toma solo el registro de mantenimiento más reciente (`maintenance_date` mayor); si su `next_maintenance_date` cae dentro de los próximos 7 días, se considera "due".
- **Class occupancy**: solo para los schedules de hoy (`day_of_week` calculado igual que en Dashboard); `pct` es `None` cuando `max_capacity` es `None` (ilimitado).
- Cada handler de exportación reutiliza el último reporte cargado en el presenter (`_last_*_report`) — no vuelve a golpear los servicios al exportar.
- Verificado con Qt en modo `offscreen`: carga de las 4 tabs, filtros/refresh, exportación real a PDF (firma `%PDF-` verificada) para los 4 tabs, y gating de permisos correcto (ADMIN/ACCOUNTANT pasan, RECEPTIONIST/INSTRUCTOR bloqueados).

---

## Tests — Estado Actual

**Total: 581 tests, 100% passing.**

| Archivo de test                  | Módulo cubierto                     | Tests |
|----------------------------------|-------------------------------------|-------|
| `test_service_result.py`         | `services/result.py`                | 16    |
| `test_member_service.py`         | `services/member_service.py`        | 62    |
| `test_permissions.py`            | `domain/permissions*.py`            | 22    |
| `test_auth_service.py`           | `services/auth_service.py`          | 31    |
| `test_attendance_service.py`     | `services/attendance_service.py`    | 52    |
| `test_payment_service.py`        | `services/payment_service.py`       | 44    |
| `test_membership_service.py`     | `services/membership_service.py`    | 94    |
| `test_class_service.py`          | `services/class_service.py`         | 75    |
| `test_settings_service.py`       | `services/settings_service.py`      | 31    |
| `test_dashboard_service.py`      | `services/dashboard_service.py`     | 17    |
| `test_instructor_service.py`     | `services/instructor_service.py`    | 51    |
| `test_equipment_service.py`      | `services/equipment_service.py`     | 57    |
| `test_reports_service.py`        | `services/reports_service.py`       | 24    |
| `test_pdf_exporter.py`           | `utils/pdf_exporter.py`             | 3     |
| `conftest.py`                    | Fixtures compartidas                | —     |

**Estrategia de mocking:**
- `db_manager` parcheado con `unittest.mock.patch('src.services.*.db_manager')`.
- `settings_service`: `_SETTINGS_FILE` y `config` parcheados; tests de CSS leen archivos reales.
- `dashboard_service`: se parchean los sub-servicios (`member_service`, `payment_service`, etc.) tal como se importan en `src.services.dashboard_service`, no `db_manager`.
- Helpers estáticos puros testeados directamente sin mocks.
- Ejecutar con: `conda run -n MainEnvironment python -m pytest tests/ -v` (entorno conda `MainEnvironment`)

---

## Permisos — Estado Actual

| Grupo | Permisos | Roles |
|---|---|---|
| Members | READ | ADMIN, RECEPTIONIST, INSTRUCTOR, ACCOUNTANT |
| Members | CREATE, UPDATE | ADMIN, RECEPTIONIST |
| Members | DELETE | ADMIN |
| Attendance | READ | ADMIN, RECEPTIONIST, INSTRUCTOR |
| Attendance | CREATE | ADMIN, RECEPTIONIST |
| Plans | CREATE, UPDATE | ADMIN |
| Memberships | READ | ADMIN, RECEPTIONIST, ACCOUNTANT |
| Memberships | CREATE, UPDATE, DELETE | ADMIN, RECEPTIONIST |
| Payments | READ | ADMIN, RECEPTIONIST, ACCOUNTANT |
| Payments | CREATE, UPDATE | ADMIN, RECEPTIONIST |
| Classes | READ | ADMIN, RECEPTIONIST, INSTRUCTOR |
| Classes | CREATE, UPDATE | ADMIN |
| Schedules | READ | ADMIN, RECEPTIONIST, INSTRUCTOR |
| Schedules | CREATE, UPDATE | ADMIN |
| Enrollments | READ | ADMIN, RECEPTIONIST, INSTRUCTOR |
| Enrollments | CREATE, UPDATE | ADMIN, RECEPTIONIST |
| Dashboard | READ | ADMIN, RECEPTIONIST, INSTRUCTOR, ACCOUNTANT |
| Instructors | READ | ADMIN, RECEPTIONIST, INSTRUCTOR |
| Instructors | CREATE, UPDATE | ADMIN |
| Equipment | READ | ADMIN, RECEPTIONIST, INSTRUCTOR |
| Equipment | CREATE, UPDATE | ADMIN |
| Maintenance | READ | ADMIN, RECEPTIONIST, INSTRUCTOR |
| Maintenance | CREATE | ADMIN |
| Reports | READ | ADMIN, ACCOUNTANT |

---

## Sidebar — Estado de Conexión

| Botón | Módulo | Estado |
|---|---|---|
| `btn_dashboard` | Dashboard | Conectado ✅ |
| `btn_members` | Members | Conectado ✅ |
| `btn_attendance` | Attendance | Conectado ✅ |
| `btn_payments` | Payments | Conectado ✅ |
| `btn_memberships` | Memberships | Conectado ✅ |
| `btn_classes` | Classes | Conectado ✅ |
| `btn_settings` | Settings | Conectado ✅ |
| `btn_instructors` | Instructors | Conectado ✅ |
| `btn_equipment` | Equipment | Conectado ✅ |
| `btn_reports` | Reports | Conectado ✅ |
| `btn_logout` | Logout | Conectado ✅ |

---

## Historial de Cambios Recientes

### Verificación end-to-end contra PostgreSQL real + limpieza del repo ✅ (sesión actual)
- Se levantó PostgreSQL 18 local (cluster ya instalado en el sistema), se creó la base `Gym-System` y se cargó `docs/database_schema.sql` completo desde pgAdmin (15 tablas, índices, triggers, seed data con usuario `admin`/`admin123`)
- `.env` creado (no versionado) con las credenciales reales; `.env.example` agregado al repo como plantilla
- Recorrido completo probado contra la BD real (no mocks): login → crear miembro → registrar pago → check-in → Dashboard → los 4 tabs de Reports → exportar PDF real (verificada la firma `%PDF-`) — todo vía `main_application.MainApplication` en modo Qt `offscreen`
- **Bug real encontrado y corregido**: `PaymentService.get_payments()` usaba `date_to.isoformat()` (sin hora) para filtrar la columna `payment_date` (`TIMESTAMPTZ`), lo que excluía silenciosamente todos los pagos del día actual — un pago de $800 registrado a las 13:xx no aparecía ni en el Dashboard ("Revenue This Month") ni en el tab Financial de Reports, ambos mostrando `$0.00`. Corregido expandiendo `date_to` al final del día local antes de convertir a UTC, mismo patrón que ya usaba `AttendanceService`. Bug preexistente (afectaba Dashboard desde antes), nunca detectado por los tests unitarios porque mockean `db_manager` por completo — solo lo reveló una prueba real contra base de datos.
- Limpieza de archivos innecesarios para GitHub: `.claude/settings.local.json` (config local de otra máquina, con rutas de Windows), `docs/PROJECT_STRUCTURE.md`/`QUICKSTART.md` (ya borrados del disco, faltaba destrackearlos), `test_connection.py` (script de diagnóstico manual en la raíz, no parte de la app ni de la suite de tests), `src/config/logger_config.py` y `src/domain/roles.py` (código muerto, sin ningún import en el proyecto)
- `.gitignore` actualizado: `exports/` (nuevo directorio de PDFs del módulo Reports), `.claude/settings.local.json`, y excepción explícita `!docs/database_schema.sql` (el resto de `docs/` sigue ignorado, pero el schema es necesario para las instrucciones de instalación del README)
- 1 test nuevo (`test_date_range_spans_full_local_days`) + 1 test actualizado en `test_payment_service.py` — 581 tests totales, 100% passing

### Módulo Reports — Implementado ✅
- Único módulo pendiente del proyecto — ahora los 11 módulos están completos
- `ReportsService`: agregación pura (mismo patrón que `DashboardService`), 4 métodos públicos (`get_financial_report`, `get_membership_report`, `get_attendance_report`, `get_operational_report`), reutiliza payment/membership/attendance/class/equipment/instructor service
- Nuevo método `AttendanceService.get_attendance_by_range()` — el servicio solo tenía consulta de un día
- Primer uso real de `reportlab` en el proyecto (`src/utils/pdf_exporter.py`) — estaba en `requirements.txt` sin usarse; se instaló en el entorno conda `MainEnvironment`
- Módulo de solo lectura: 4 tabs sin formularios de creación, cada uno con su botón "Export PDF"
- Permiso único `REPORTS_READ` → ADMIN + ACCOUNTANT (datos financieros, se excluye RECEPTIONIST/INSTRUCTOR a diferencia del resto de módulos)
- De paso, corregido un bug latente en `MemberView` (`show_error` faltante, ver nota en la sección de Members) detectado en una sesión anterior
- `btn_reports` conectado en sidebar; wiring completo `MainView` → `MainPresenter` → `MainApplication.open_reports_form()`
- 27 tests nuevos (24 `ReportsService` + 3 `PdfExporter`) + 6 tests nuevos de `AttendanceService.get_attendance_by_range`, 100% passing (580 tests totales en el proyecto)
- Verificado con Qt en modo `offscreen`: carga de las 4 tabs, filtros/refresh, exportación real a PDF (firma `%PDF-` verificada) por cada tab, gating de permisos correcto para los 4 roles

### Módulo Equipment — Implementado ✅
- Sigue el patrón de Memberships (2 entidades relacionadas → 1 servicio, 1 presenter, 1 vista con `QTabWidget`) en vez del patrón CRUD plano de Members/Instructors
- `EquipmentService`: CRUD de `Equipment` (5 métodos) + `get_maintenance_records`/`get_maintenance_by_equipment`/`log_maintenance` para `EquipmentMaintenance` (insert-only, sin update/delete)
- Tab "Equipment": un solo botón Save decide crear/actualizar según `_selected_equipment_id` (como Plans); Tab "Maintenance": filtro + tabla + formulario de registro
- `_MAINTENANCE_COLUMNS`/`_MAINTENANCE_JOINS` con `LEFT JOIN equipment` para denormalizar `equipment.name` en cada fila de mantenimiento
- Permisos: `EQUIPMENT_READ`/`MAINTENANCE_READ` → ADMIN/RECEPTIONIST/INSTRUCTOR; `EQUIPMENT_CREATE/UPDATE`/`MAINTENANCE_CREATE` → ADMIN
- `btn_equipment` conectado en sidebar; wiring completo `MainView` → `MainPresenter` → `MainApplication.open_equipment_form()`
- 57 tests nuevos, 100% passing (547 tests totales en el proyecto)
- Verificado con Qt en modo `offscreen`: carga de la vista (2 tabs), poblar ambas tablas, combos de equipo, selección de fila con recuperación de UUID, round-trip de formulario, clicks de `btn_save_equipment`/`btn_log_maintenance`/`btn_equipment` emitiendo sus señales

### Módulo Instructors — Implementado ✅
- `InstructorService`: 5 métodos públicos (get_all/get_by_id/search/create/update), mismo patrón que `MemberService` pero sin `member_code`/`created_by`
- `specialties` (`TEXT[]` en Postgres) mapeado nativamente por psycopg2/`RealDictCursor`; en la UI se edita como texto separado por comas
- Permisos: `INSTRUCTORS_READ` → ADMIN/RECEPTIONIST/INSTRUCTOR; `INSTRUCTORS_CREATE/UPDATE` → ADMIN (sin DELETE, igual que el resto de módulos que usan soft-delete vía `is_active`)
- `instructor_view.ui` nuevo, adaptado de `member_view.ui`; `InstructorView` corrige un bug que sí existe en `MemberView` (falta el método `show_error`, ver nota en la sección del módulo)
- `btn_instructors` conectado en sidebar; wiring completo `MainView` → `MainPresenter` → `MainApplication.open_instructors_form()`
- 51 tests nuevos, 100% passing (490 tests totales en el proyecto)
- Verificado con Qt en modo `offscreen`: carga de la vista, poblar tabla, selección de fila con recuperación de UUID, `set_form_data`/`get_form_data` round-trip, click de `btn_instructors` emitiendo la señal

### Logout — Implementado ✅
- `MainView`: señal `logout_requested`; `btn_logout` conectado a `confirm_logout()`, que muestra `QMessageBox.question` y solo emite la señal si el usuario confirma (mismo patrón que la confirmación de update en `member_view.py`)
- `MainPresenter` conecta `logout_requested` → `MainApplication.logout()`
- `MainApplication.logout()`: cierra `main_view` (cierra en cascada las sub-ventanas MDI abiertas), limpia `current_user` y vuelve a mostrar el login vía `_init_login()`
- Sin tests dedicados (wiring de UI puro, sin lógica de servicio); verificado manualmente con Qt en modo `offscreen` simulando clicks Yes/No sobre el diálogo de confirmación
- `btn_logout` conectado en sidebar

### Módulo Dashboard — Implementado ✅
- `DashboardService.get_summary()` agrega datos de member/payment/attendance/membership/class service (sin SQL nuevo)
- 4 tarjetas KPI (Active Members, Revenue This Month, Check-ins Today, Memberships Expiring) + 2 tablas de detalle (Today's Classes, Expiring Memberships)
- Refresh manual (`btn_refresh`), carga automática al abrir
- Permiso `DASHBOARD_READ` asignado a los 4 roles
- `btn_dashboard` conectado en sidebar; entorno de desarrollo/test: conda `MainEnvironment`
- 17 tests, 100% passing (439 tests totales en el proyecto)

### Módulo Classes — Implementado ✅
- Servicio con 15 métodos públicos: CRUD clases, CRUD horarios, CRUD inscripciones
- Vista con 3 tabs: Classes / Schedules / Enrollments
- Validación de capacidad máxima al inscribir (llama `get_enrollment_count` antes del insert)
- Reutiliza `MemberSelectDialog` para búsqueda de miembro en inscripciones
- 75 tests, 100% passing

### Módulo Settings — Implementado ✅
- 5 temas dark generados desde `styles.css` via `scripts/generate_themes.py`
- Preview en vivo al seleccionar: `QApplication.setStyleSheet()` se llama instantáneamente
- Persistencia en `data/user_settings.json`; se carga al arrancar antes de mostrar ninguna ventana
- `btn_settings` conectado en sidebar; `btn_close` con ícono `IMG-Settings.png`
- 31 tests, 100% passing

### Documentación y Stack — Actualizado ✅
- `CONTEXT.md` corregido: `supabase-py` → `psycopg2-binary`, referencias a Supabase eliminadas
- `README.md` reescrito: instrucciones de instalación con PostgreSQL local, eliminadas referencias Supabase
- Verificado: código fuente 100% consistente en PostgreSQL via psycopg2; sin rastro de SQLite ni Supabase

---

## Próximos Pasos

Los 11 módulos planeados están completos. Sin pendientes identificados actualmente.
