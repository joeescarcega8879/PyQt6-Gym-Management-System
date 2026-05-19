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
├── config/                 # Lectura de .env (Settings), DATA_DIR, LOGS_DIR
├── database/               # Singleton DatabaseManager — SQL puro via psycopg2
├── domain/                 # Permisos por rol (PermissionService, Permissions)
├── models/                 # Dataclasses (Member, User, Class, etc.) y enums
├── presenters/             # Lógica de negocio UI (MemberPresenter, ClassPresenter, etc.)
├── services/               # Lógica de negocio pura (MemberService, SettingsService, etc.)
├── utils/                  # Helpers: StatusBar, SetFormat, ErrorMessages
└── views/
    ├── ui/                 # Archivos .ui de Qt Designer
    └── widgets/            # Componentes reutilizables (MemberSelectDialog)
data/
└── user_settings.json      # Preferencias de usuario — persistencia de tema [.gitignore]
scripts/
├── build_resources.py      # Embebe íconos en resources_rc.py
└── generate_themes.py      # Genera los 5 CSS de temas desde styles.css
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
| Dashboard   | Pendiente | —    | Requiere datos de Memberships y Payments                              |
| Instructors | Pendiente | —    | btn_instructors en sidebar, sin implementar                           |
| Equipment   | Pendiente | —    | btn_equipment en sidebar, sin implementar                             |
| Reports     | Pendiente | —    | btn_reports en sidebar, sin implementar                               |

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

## Tests — Estado Actual

**Total: 422 tests, 100% passing.**

| Archivo de test                  | Módulo cubierto                     | Tests |
|----------------------------------|-------------------------------------|-------|
| `test_service_result.py`         | `services/result.py`                | 16    |
| `test_member_service.py`         | `services/member_service.py`        | 62    |
| `test_permissions.py`            | `domain/permissions*.py`            | 21    |
| `test_auth_service.py`           | `services/auth_service.py`          | 31    |
| `test_attendance_service.py`     | `services/attendance_service.py`    | 46    |
| `test_payment_service.py`        | `services/payment_service.py`       | 43    |
| `test_membership_service.py`     | `services/membership_service.py`    | 94    |
| `test_class_service.py`          | `services/class_service.py`         | 75    |
| `test_settings_service.py`       | `services/settings_service.py`      | 31    |
| `conftest.py`                    | Fixtures compartidas                | —     |

**Estrategia de mocking:**
- `db_manager` parcheado con `unittest.mock.patch('src.services.*.db_manager')`.
- `settings_service`: `_SETTINGS_FILE` y `config` parcheados; tests de CSS leen archivos reales.
- Helpers estáticos puros testeados directamente sin mocks.
- Ejecutar con: `python -m pytest tests/ -v`

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

---

## Sidebar — Estado de Conexión

| Botón | Módulo | Estado |
|---|---|---|
| `btn_members` | Members | Conectado ✅ |
| `btn_attendance` | Attendance | Conectado ✅ |
| `btn_payments` | Payments | Conectado ✅ |
| `btn_memberships` | Memberships | Conectado ✅ |
| `btn_classes` | Classes | Conectado ✅ |
| `btn_settings` | Settings | Conectado ✅ |
| `btn_dashboard` | Dashboard | Sin implementar |
| `btn_instructors` | Instructors | Sin implementar |
| `btn_equipment` | Equipment | Sin implementar |
| `btn_reports` | Reports | Sin implementar |
| `btn_logout` | Logout | Sin implementar |

---

## Historial de Cambios Recientes

### Módulo Classes — Implementado ✅ (sesión actual)
- Servicio con 15 métodos públicos: CRUD clases, CRUD horarios, CRUD inscripciones
- Vista con 3 tabs: Classes / Schedules / Enrollments
- Validación de capacidad máxima al inscribir (llama `get_enrollment_count` antes del insert)
- Reutiliza `MemberSelectDialog` para búsqueda de miembro en inscripciones
- 75 tests, 100% passing

### Módulo Settings — Implementado ✅ (sesión actual)
- 5 temas dark generados desde `styles.css` via `scripts/generate_themes.py`
- Preview en vivo al seleccionar: `QApplication.setStyleSheet()` se llama instantáneamente
- Persistencia en `data/user_settings.json`; se carga al arrancar antes de mostrar ninguna ventana
- `btn_settings` conectado en sidebar; `btn_close` con ícono `IMG-Settings.png`
- 31 tests, 100% passing

### Documentación y Stack — Actualizado ✅ (sesión actual)
- `CONTEXT.md` corregido: `supabase-py` → `psycopg2-binary`, referencias a Supabase eliminadas
- `README.md` reescrito: instrucciones de instalación con PostgreSQL local, eliminadas referencias Supabase
- Verificado: código fuente 100% consistente en PostgreSQL via psycopg2; sin rastro de SQLite ni Supabase

---

## Próximos Pasos

| Módulo | Botón en sidebar | Prioridad | Notas |
|---|---|---|---|
| Dashboard | `btn_dashboard` | Alta | Datos fuente (Memberships, Payments, Attendance) ya disponibles |
| Logout | `btn_logout` | Alta | Cerrar sesión y volver al login |
| Instructors | `btn_instructors` | Media | Dataclass `Instructor` ya existe en `models.py` |
| Equipment | `btn_equipment` | Baja | Dataclass `Equipment` ya existe en `models.py` |
| Reports | `btn_reports` | Baja | Requiere definir qué reportes generar |
