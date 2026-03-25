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

| Módulo    | Estado       | Notas                                      |
|-----------|--------------|--------------------------------------------|
| Login     | Completo     | bcrypt, roles, sesión                      |
| Members   | Completo     | CRUD funcional, tests, código limpio       |
| Otros     | No iniciados | Sidebar conectado solo al módulo Members   |

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

## Historial de Cambios — Módulo Members

### Sesión inicial de análisis
- Análisis completo del proyecto y feedback del módulo Members.
- Identificados 22 problemas entre bugs críticos, lógica incorrecta y deuda técnica.

---

### Paso 2 — Conectar `btn_clear` ✅
**Archivos:** `member_view.py`, `member_presenter.py`

- Agregada señal `clear_action_requested = pyqtSignal()` en la vista.
- Conectado `btn_clear.clicked` a `clear_action_requested.emit`.
- Conectada la señal en el presenter a `_handle_load_all()`.

---

### Paso 1 — Corregir género en `set_form_data()` ✅
**Archivo:** `member_view.py` línea 108

- Reemplazado `setCurrentText(data.get("gender"))` por `findData()` + `setCurrentIndex()`.
- El género ahora se selecciona correctamente al cargar datos de edición.
- Pendiente: eliminar `print(index)` de la línea 110 antes de producción.

---

### Paso 5 — Tratar "not found" como info, no como error ✅
**Archivo:** `member_presenter.py` línea 93

- Agregado método `_emit_info()` que usa `StatusType.INFO`.
- En `_handle_search()`, bloque `elif result.is_not_found` ahora llama `_emit_info()`.
- Agregado `StatusType.INFO` al enum `status_type.py`.
- Agregado estilo azul para `INFO` en `status_bar_styles.py`.

---

### Paso 6 — Poblar `label_user_name` y `label_user_role` ✅
**Archivos:** `member_presenter.py`, `member_view.py`

- Agregado método `_load_user_information()` en el presenter.
- Agregado método `set_user_info(user_info: dict)` en la vista.
- Se muestra `username` y `role.value` del usuario logueado en la barra superior.
- Nota: se muestra `username` en lugar de `full_name` (decisión de diseño pendiente de confirmar).

---

### Paso 8 — Control UI para mostrar/ocultar miembros inactivos ✅
**Archivos:** `member_view.py`, `member_presenter.py`

- Agregado `QCheckBox` `check_show_inactives` en la zona del buscador.
- Agregada señal `show_inactive_requested` conectada a `_handle_load_all()`.
- `_handle_load_all()` lee `check_show_inactives.isChecked()` para pasar `include_inactive`.

---

### Paso 10 — Validar permiso `MEMBERS_READ` al cargar tabla ✅
**Archivo:** `member_presenter.py` — `_handle_load_all()`

- Agregada verificación de `PermissionService.has_permission(MEMBERS_READ)` antes de cargar.

---

### Paso 7 — Mover filtro `is_active` al query de Supabase ✅
**Archivos:** `src/database/manager.py`, `src/services/member_service.py`

**Problema resuelto:** `search_members()` traía todos los resultados de Supabase y luego
filtraba los inactivos en Python. Ineficiente para datasets grandes.

**Cambios en `database/manager.py`:**
- Agregado parámetro opcional `filters: Optional[Dict[str, Any]] = None` a `search()`.
- Los filtros se aplican con `.eq()` encadenado al query ILIKE, igual que en `select()`.

**Cambios en `services/member_service.py`:**
- `search_members()` ahora pasa `filters={'is_active': True}` a `db_manager.search()`.
- Eliminado el `if not row.get('is_active', True): continue` del loop Python.
- El loop ahora solo deduplica resultados por `id`.

### Paso 11 — Diálogo de confirmación antes de actualizar ✅
**Archivo:** `member_presenter.py` — `_handle_create()` bloque `if self._is_editing`

- Agregado `QMessageBox.question()` antes de ejecutar `member_service.update_member()`.
- Si el usuario cancela el diálogo, la operación se aborta sin modificar datos.

---

### Paso 12 — Corregir colores de tabla para tema oscuro ✅
**Archivo:** `src/utils/set_format.py` línea 45

- Reemplazados los colores claros (`#f0f0f0` / `#ffffff`) por colores oscuros (`#2d2d2d` / `#353535`).
- Las filas alternadas ahora son compatibles con el stylesheet oscuro global.

---

### Paso 13 — Corregir ruta de ícono en `member_view.ui` ✅
**Archivo:** `src/views/ui/member_view.ui`

- Eliminada la referencia al ícono externo con ruta absoluta a otro proyecto (`../../../../PyQt6-Warehouse-System/...`).
- `btn_close` ahora muestra el texto `"Close"` en lugar de un ícono roto.

---

### Paso 14 — Estandarizar idioma a inglés ✅
**Archivo:** `src/views/ui/main_window.ui`

- Traducidos todos los botones del sidebar de español a inglés:
  - `"Miembros"` → `"Members"`
  - `"Asistencia"` → `"Attendance"`
  - `"Pagos"` → `"Payments"`
  - `"Membresías"` → `"Memberships"`
  - `"Clases"` → `"Classes"`
  - `"Instructores"` → `"Instructors"`
  - `"Equipamiento"` → `"Equipment"`
  - `"Reportes"` → `"Reports"`
  - `"Configuración"` → `"Settings"`
  - `"Cerrar Sesión"` → `"Logout"`
- El `.ui` y `toggle_sidebar_frame()` en `main_view.py` ahora usan el mismo idioma (inglés).

---

### Paso 16 — Sistema de íconos (Qt Resource System) ✅
**Archivos:** `scripts/build_resources.py`, `src/assets/resources_rc.py` (generado), `main_application.py`, `src/views/member_view.py`, `src/views/main_view.py`, `.gitignore`

**Problema resuelto:** `pyrcc6` fue eliminado en PyQt6 6.x. No se puede compilar `.qrc` al estilo tradicional.

**Solución:**
- Creado `scripts/build_resources.py` que embebe los íconos de `src/assets/icons/` como base64 en `src/assets/resources_rc.py`.
- `resources_rc.py` expone `get_icon(path: str) -> QIcon`. Los íconos se asignan desde Python, no desde `.ui`.
- `main_application.py` importa `src.assets.resources_rc` (noqa) para asegurar disponibilidad global.
- `src/assets/resources_rc.py` agregado a `.gitignore` (archivo generado, no versionable).
- `src/assets/resources.qrc` **eliminado** — era el archivo de configuración del Qt Resource System clásico (usado por `pyrcc6`), quedó obsoleto e inactivo al adoptar el enfoque base64. No era importado por ningún módulo.

**Íconos asignados (12 en total):**
- `btn_close` en `member_view.py` → `IMG-Close.png` (20×20)
- Todos los botones del sidebar en `main_view.py` → tamaño 24×24:

| Botón | Ícono |
|---|---|
| `btn_dashboard` | `IMG-Dashboard.png` |
| `btn_members` | `IMG-Members.png` |
| `btn_attendance` | `IMG-Attendence.png` |
| `btn_payments` | `IMG-Pyments.png` |
| `btn_memberships` | `IMG-Memberships.png` |
| `btn_classes` | `IMG-Classes.png` |
| `btn_instructors` | `IMG-Instructors.png` |
| `btn_equipment` | `IMG-Equipment.png` |
| `btn_reports` | `IMG-Reports.png` |
| `btn_settings` | `IMG-Settings.png` |
| `btn_logout` | `IMG-Logout.png` |

**Nota cross-platform:** los íconos son portables en cualquier SO (Windows, macOS, Linux). Al estar embebidos como base64 no dependen de rutas en disco ni del sistema de archivos.

**Eliminado:** `print(index)` debug en `member_view.py` línea 115.

---

### Paso E — Corregir `date_birthday` min/max y `get_form_data()` ✅
**Archivo:** `src/views/member_view.py`

- `initialize_components()` ahora llama `setMinimumDate(QDate(1900, 1, 1))` y `setMaximumDate(QDate.currentDate())`.
- `get_form_data()` devuelve `None` para `date_of_birth` cuando la fecha es igual a `minimumDate` (usuario no ingresó fecha).
- `clear_form()` ya era correcto: llama `setDate(minimumDate())`, que ahora es 1900-01-01 en lugar del inválido 1752-09-14.

---

### Paso F — Eliminar código muerto y import huérfano ✅
**Archivo:** `src/views/member_view.py`

- Eliminado bloque de 4 líneas comentadas (`setSectionResizeMode` / `setColumnWidth`) que ya no se usaban.
- Eliminado import `QHeaderView` que quedó huérfano al comentar ese bloque.

---

### Paso G — Centralizar mensajes en `ErrorMessages` ✅
**Archivos:** `src/utils/error_messages.py`, `src/presenters/member_presenter.py`

- Agregadas 13 constantes en la sección `# Members module` de `ErrorMessages`.
- Todos los strings literales en `member_presenter.py` reemplazados por referencias a `ErrorMessages.*`.
- Verificado con grep: cero strings inline quedan en el presenter.
- 133 tests siguen pasando al 100%.

---

## Todo List — Estado Actual

### Completados ✅
- [x] 2. Conectar `btn_clear`
- [x] 1. Corregir `set_form_data()` — género
- [x] 5. Tratar "not found" como info
- [x] 6. Poblar `label_user_name` y `label_user_role`
- [x] 8. Control UI para mostrar/ocultar inactivos
- [x] 10. Validar permiso `MEMBERS_READ`
- [x] 7. Mover filtro `is_active` al query en `search_members()`
- [x] 11. Diálogo de confirmación antes de actualizar (refactorizado en sesión de revisión final)
- [x] 12. Corregir colores de tabla para tema oscuro
- [x] 13. Corregir ruta de ícono en `member_view.ui`
- [x] 14. Estandarizar idioma a inglés
- [x] 16. Sistema de íconos con Qt Resource System (base64)
- [x] 15. Agregar tests unitarios
- [x] A. Renombrar `_handle_update` → `_handle_edit_requested`
- [x] B. Validación sin selección — señal `no_selection_error` (Opción A)
- [x] C. Eliminar señal `search_option_changed` (no se consumía)
- [x] D. `btn_clear` limpia `input_search` y resetea `cbo_search_options` — método `clear_search()` en la view
- [x] E. `date_birthday` con `minimumDate` correcto + `get_form_data()` devuelve `None` cuando no hay fecha
- [x] F. Eliminar código comentado muerto + import huérfano `QHeaderView`
- [x] G. Centralizar 13 strings inline en `ErrorMessages` — sección `# Members module`

### Descartados por diseño ✋
- ~~3. Separar create y update en el presenter~~
- ~~9. Implementar funcionalidad Delete~~ (el soft-delete se hace via Update)

### Pendientes
_(ninguno — módulo Members completo)_

---

### Paso 15 — Tests Unitarios ✅
**Archivos:** `tests/__init__.py`, `tests/conftest.py`, `tests/test_service_result.py`, `tests/test_member_service.py`, `tests/test_permissions.py`, `tests/test_auth_service.py`, `pytest.ini`

**Cobertura:** 133 tests, 100% passing.

| Archivo de test               | Módulo cubierto              | Tests |
|-------------------------------|------------------------------|-------|
| `test_service_result.py`      | `services/result.py`         | 16    |
| `test_member_service.py`      | `services/member_service.py` | 62    |
| `test_permissions.py`         | `domain/permissions*.py`     | 21    |
| `test_auth_service.py`        | `services/auth_service.py`   | 31    |
| `conftest.py`                 | Fixtures compartidas         | —     |

**Estrategia de mocking:**
- `db_manager` parcheado con `unittest.mock.patch('src.services.*.db_manager')` en todos los tests que tocan la base de datos.
- Helpers estáticos puros (`_validate_member`, `_row_to_member`, `_member_to_row`, `_generate_member_code`, `hash_password`, `_verify_password`) testeados directamente sin mocks.
- Ejecutar con: `python -m pytest tests/ -v`
