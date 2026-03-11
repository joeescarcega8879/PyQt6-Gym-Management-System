# Guía Rápida de Inicio

## Setup en 5 minutos

### 1. Instalar dependencias (2 min)

```bash
# Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar Supabase (2 min)

1. Crear cuenta en https://supabase.com
2. Crear nuevo proyecto
3. Ir a **SQL Editor** y ejecutar todo el contenido de `docs/database_schema.sql`
4. Ir a **Settings > API** y copiar:
   - Project URL
   - anon/public key

### 3. Configurar .env (1 min)

```bash
cp .env.example .env
nano .env  # o tu editor favorito
```

Pegar tus credenciales:
```env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_anon_key_de_supabase
```

### 4. Ejecutar

```bash
python main.py
```

### 5. Login

- **Usuario**: `admin`
- **Contraseña**: `admin123`

---

## Siguiente paso: Desarrollar módulo de Miembros

El login ya está funcionando. El próximo módulo a desarrollar es la gestión de miembros (CRUD completo).

### Estructura sugerida:

1. `src/services/member_service.py` - Lógica de negocio
2. `src/views/member_view.py` - Interfaz PyQt6
3. `src/presenters/member_presenter.py` - Presenter MVP
4. `src/views/main_window.py` - Ventana principal con menú

### Orden de desarrollo recomendado:

1. **MainWindow** - Ventana principal con menú lateral
2. **MemberService** - CRUD de miembros
3. **MemberListView** - Lista de miembros con búsqueda
4. **MemberFormView** - Formulario para crear/editar
5. **MemberDetailView** - Detalle de un miembro
6. **AttendanceView** - Check-in rápido por código

---

## Tips de desarrollo

### Usar el patrón MVP consistentemente

```python
# 1. Crear el servicio (lógica de negocio)
class MemberService:
    def get_all_members(self):
        return db_manager.select('members')
    
    def create_member(self, data):
        return db_manager.insert('members', data)

# 2. Crear la vista (UI)
class MemberView(QWidget):
    member_created = pyqtSignal(dict)
    
    def __init__(self):
        # Setup UI
        self.save_button.clicked.connect(self._on_save)
    
    def _on_save(self):
        data = self.get_form_data()
        self.member_created.emit(data)

# 3. Crear el presenter (conecta vista y servicio)
class MemberPresenter:
    def __init__(self, view, service):
        self.view = view
        self.service = service
        self.view.member_created.connect(self._handle_create)
    
    def _handle_create(self, data):
        self.service.create_member(data)
        self.view.show_success("Miembro creado")
```

### Reutilizar componentes

Crea widgets reutilizables en `src/views/widgets/`:
- `SearchBar` - Barra de búsqueda
- `DataTable` - Tabla con paginación
- `FormField` - Campo de formulario customizado
- `Card` - Tarjeta para mostrar información

### Testing

```bash
# Crear test para cada servicio
# tests/unit/test_member_service.py

def test_create_member():
    service = MemberService()
    data = {'first_name': 'Juan', 'last_name': 'Pérez'}
    result = service.create_member(data)
    assert result['id'] is not None
```

---

## Recursos útiles

- **PyQt6 Docs**: https://doc.qt.io/qtforpython-6/
- **Supabase Python Docs**: https://supabase.com/docs/reference/python/introduction
- **Patrón MVP**: https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93presenter

---

¿Necesitas ayuda con algún módulo específico? Abre un issue o contacta al desarrollador.
