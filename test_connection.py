
import sys
import io
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent))
from src.config import config
from src.database import db_manager
def print_header(text):
    """Imprime un encabezado decorado"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)
def print_success(text):
    """Imprime un mensaje de éxito"""
    print(f"[OK]    {text}")
def print_error(text):
    """Imprime un mensaje de error"""
    print(f"[ERROR] {text}")
def print_info(text, indent=2):
    """Imprime información con indentación"""
    print(" " * indent + f"-> {text}")
def main():
    """Función principal de prueba"""
    
    print_header("VERIFICACIÓN DE CONFIGURACIÓN Y CONEXIÓN")
    
    # ============================================
    # 1. Verificar que el archivo .env existe
    # ============================================
    print("\n[*] Paso 1: Verificando archivo .env...")
    env_file = Path(__file__).parent / '.env'
    
    if env_file.exists():
        print_success("Archivo .env encontrado")
        print_info(f"Ubicación: {env_file}")
    else:
        print_error("Archivo .env NO encontrado")
        print_info("Crea el archivo .env en la raíz del proyecto")
        return False
    
    # ============================================
    # 2. Validar configuración
    # ============================================
    print("\n[*] Paso 2: Validando configuración...")
    
    is_valid, messages = config.validate()
    
    if is_valid:
        print_success("Configuración válida")
        print_info(f"App Name: {config.APP_NAME}")
        print_info(f"Version: {config.APP_VERSION}")
        print_info(f"Debug Mode: {config.DEBUG_MODE}")
        for warning in messages:
            print_info(f"[!] AVISO: {warning}", indent=4)
    else:
        print_error("Configuración inválida")
        for error in messages:
            print_info(f"ERROR: {error}", indent=4)
        return False
    
    # ============================================
    # 3. Verificar credenciales de Supabase
    # ============================================
    print("\n[*] Paso 3: Verificando credenciales de Supabase...")
    
    if config.SUPABASE_URL:
        print_success("SUPABASE_URL configurada")
        # Mostrar solo parte de la URL por seguridad
        url_preview = config.SUPABASE_URL[:40] + "..." if len(config.SUPABASE_URL) > 40 else config.SUPABASE_URL
        print_info(f"URL: {url_preview}")
    else:
        print_error("SUPABASE_URL no configurada")
        return False
    
    if config.SUPABASE_KEY:
        print_success("SUPABASE_KEY configurada")
        # Mostrar solo los primeros caracteres por seguridad
        key_preview = config.SUPABASE_KEY[:30] + "..." if len(config.SUPABASE_KEY) > 30 else config.SUPABASE_KEY
        print_info(f"Key: {key_preview}")
    else:
        print_error("SUPABASE_KEY no configurada")
        return False
    
    # ============================================
    # 4. Probar conexión a Supabase
    # ============================================
    print("\n[*] Paso 4: Probando conexión a Supabase...")
    
    try:
        if db_manager.is_connected():
            print_success("Conexión establecida exitosamente")
        else:
            print_error("No se pudo establecer conexión")
            return False
    except Exception as e:
        print_error(f"Error al conectar: {str(e)}")
        return False
    
    # ============================================
    # 5. Probar consulta a la base de datos
    # ============================================
    print("\n[*] Paso 5: Probando consulta a la base de datos...")
    
    try:
        # Intentar obtener usuarios
        users = db_manager.select('users', limit=5)
        print_success(f"Consulta exitosa - {len(users)} usuario(s) encontrado(s)")
        
        if users:
            print_info("Usuarios en la base de datos:")
            for user in users:
                print_info(f"• {user['username']} ({user['full_name']}) - Rol: {user['role']}", indent=4)
        else:
            print_info("[!]  No hay usuarios en la base de datos", indent=4)
            print_info("Verifica que ejecutaste el script database_schema.sql", indent=4)
            
    except Exception as e:
        print_error(f"Error en consulta: {str(e)}")
        print_info("Posibles causas:", indent=4)
        print_info("1. El script SQL no se ejecutó correctamente", indent=6)
        print_info("2. Las credenciales no tienen permisos de lectura", indent=6)
        print_info("3. La tabla 'users' no existe", indent=6)
        return False
    
    # ============================================
    # 6. Verificar usuario admin
    # ============================================
    print("\n[*] Paso 6: Verificando usuario administrador...")
    
    try:
        admin_users = db_manager.select('users', filters={'username': 'admin'})
        
        if admin_users:
            print_success("Usuario 'admin' encontrado")
            admin = admin_users[0]
            print_info(f"Email: {admin['email']}")
            print_info(f"Nombre: {admin['full_name']}")
            print_info(f"Rol: {admin['role']}")
            print_info(f"Activo: {'Sí' if admin['is_active'] else 'No'}")
        else:
            print_error("Usuario 'admin' NO encontrado")
            print_info("El script SQL debería haber creado este usuario", indent=4)
            return False
            
    except Exception as e:
        print_error(f"Error al buscar admin: {str(e)}")
        return False
    
    # ============================================
    # 7. Verificar tablas principales
    # ============================================
    print("\n[*] Paso 7: Verificando tablas principales...")
    
    tables_to_check = [
        'users', 'members', 'membership_plans', 'payments', 
        'attendance', 'instructors', 'classes'
    ]
    
    tables_ok = 0
    for table in tables_to_check:
        try:
            result = db_manager.select(table, limit=1)
            print_success(f"Tabla '{table}' existe")
            tables_ok += 1
        except Exception as e:
            print_error(f"Tabla '{table}' - Error: {str(e)}")
    
    print_info(f"{tables_ok}/{len(tables_to_check)} tablas verificadas correctamente", indent=2)
    
    if tables_ok < len(tables_to_check):
        print_info("[!]  Algunas tablas no existen o tienen problemas", indent=4)
        print_info("Asegúrate de ejecutar el script database_schema.sql completo", indent=4)
    
    # ============================================
    # RESUMEN FINAL
    # ============================================
    print_header("RESUMEN")
    
    print("\nEstado del sistema:")
    print_success("Configuracion: OK")
    print_success("Conexion a Supabase: OK")
    print_success("Base de datos: OK")
    print_success("Usuario admin: OK")
    print_success(f"Tablas principales: {tables_ok}/{len(tables_to_check)}")
    
    print("\n>> TODO ESTA LISTO!")
    print("\nCredenciales para el login:")
    print_info("Usuario: admin")
    print_info("Contrasena: admin123")
    
    print("\nSiguiente paso:")
    print_info("Ejecuta la aplicacion con: python main.py")
    
    print("\n" + "="*60 + "\n")
    
    return True
if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[!] Prueba interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)