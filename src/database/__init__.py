"""
Gestor de conexión a Supabase.
Proporciona una interfaz unificada para todas las operaciones de base de datos.
"""
from typing import Optional, Any, Dict, List
from supabase import create_client, Client
from src.config import config
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Gestor centralizado de base de datos.
    Implementa el patrón Singleton para garantizar una única conexión.
    """
    
    _instance: Optional['DatabaseManager'] = None
    _client: Optional[Client] = None
    
    def __new__(cls):
        """Implementación del patrón Singleton"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa el gestor de base de datos"""
        if self._client is None:
            self.connect()
    
    def connect(self) -> bool:
        """
        Establece conexión con Supabase.
        
        Returns:
            bool: True si la conexión fue exitosa, False en caso contrario
        """
        try:
            # Validar configuración
            is_valid, errors = config.validate()
            if not is_valid:
                for error in errors:
                    logger.error(f"Error de configuración: {error}")
                return False
            
            # Crear cliente de Supabase
            db_config = config.get_database_config()
            self._client = create_client(db_config['url'], db_config['key'])
            
            logger.info("Conexión a Supabase establecida exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error al conectar con Supabase: {str(e)}")
            return False
    
    def disconnect(self):
        """Cierra la conexión con la base de datos"""
        self._client = None
        logger.info("Conexión a Supabase cerrada")
    
    @property
    def client(self) -> Client:
        """
        Retorna el cliente de Supabase.
        
        Returns:
            Client: Cliente de Supabase
            
        Raises:
            ConnectionError: Si no hay conexión establecida
        """
        if self._client is None:
            raise ConnectionError("No hay conexión establecida con la base de datos")
        return self._client
    
    def is_connected(self) -> bool:
        """
        Verifica si hay una conexión activa.
        
        Returns:
            bool: True si hay conexión, False en caso contrario
        """
        return self._client is not None
    
    # ============================================
    # MÉTODOS GENÉRICOS CRUD
    # ============================================
    
    def select(self, table: str, columns: str = "*", 
               filters: Optional[Dict[str, Any]] = None,
               order_by: Optional[str] = None,
               limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Realiza una consulta SELECT en una tabla.
        
        Args:
            table: Nombre de la tabla
            columns: Columnas a seleccionar (por defecto todas)
            filters: Diccionario con filtros {columna: valor}
            order_by: Columna por la cual ordenar
            limit: Límite de registros a retornar
            
        Returns:
            List[Dict]: Lista de registros encontrados
        """
        try:
            query = self.client.table(table).select(columns)
            
            # Aplicar filtros
            if filters:
                for column, value in filters.items():
                    query = query.eq(column, value)
            
            # Aplicar ordenamiento
            if order_by:
                query = query.order(order_by)
            
            # Aplicar límite
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            return response.data
            
        except Exception as e:
            logger.error(f"Error en SELECT de {table}: {str(e)}")
            raise
    
    def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserta un registro en una tabla.
        
        Args:
            table: Nombre de la tabla
            data: Diccionario con los datos a insertar
            
        Returns:
            Dict: Registro insertado con su ID
        """
        try:
            response = self.client.table(table).insert(data).execute()
            logger.info(f"Registro insertado en {table}")
            return response.data[0] if response.data else {}
            
        except Exception as e:
            logger.error(f"Error en INSERT de {table}: {str(e)}")
            raise
    
    def update(self, table: str, data: Dict[str, Any], 
               filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Actualiza registros en una tabla.
        
        Args:
            table: Nombre de la tabla
            data: Diccionario con los datos a actualizar
            filters: Diccionario con filtros {columna: valor}
            
        Returns:
            List[Dict]: Registros actualizados
        """
        try:
            query = self.client.table(table).update(data)
            
            # Aplicar filtros
            for column, value in filters.items():
                query = query.eq(column, value)
            
            response = query.execute()
            logger.info(f"Registro(s) actualizado(s) en {table}")
            return response.data
            
        except Exception as e:
            logger.error(f"Error en UPDATE de {table}: {str(e)}")
            raise
    
    def delete(self, table: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Elimina registros de una tabla.
        
        Args:
            table: Nombre de la tabla
            filters: Diccionario con filtros {columna: valor}
            
        Returns:
            List[Dict]: Registros eliminados
        """
        try:
            query = self.client.table(table).delete()
            
            # Aplicar filtros
            for column, value in filters.items():
                query = query.eq(column, value)
            
            response = query.execute()
            logger.info(f"Registro(s) eliminado(s) de {table}")
            return response.data
            
        except Exception as e:
            logger.error(f"Error en DELETE de {table}: {str(e)}")
            raise
    
    def execute_rpc(self, function_name: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Ejecuta una función almacenada en PostgreSQL.
        
        Args:
            function_name: Nombre de la función
            params: Parámetros de la función
            
        Returns:
            Any: Resultado de la función
        """
        try:
            response = self.client.rpc(function_name, params or {}).execute()
            return response.data
            
        except Exception as e:
            logger.error(f"Error ejecutando RPC {function_name}: {str(e)}")
            raise
    
    # ============================================
    # MÉTODOS DE BÚSQUEDA AVANZADA
    # ============================================
    
    def search(self, table: str, column: str, search_term: str,
               columns: str = "*") -> List[Dict[str, Any]]:
        """
        Realiza una búsqueda por texto en una columna.
        
        Args:
            table: Nombre de la tabla
            column: Columna donde buscar
            search_term: Término a buscar
            columns: Columnas a retornar
            
        Returns:
            List[Dict]: Registros encontrados
        """
        try:
            response = self.client.table(table).select(columns).ilike(
                column, f"%{search_term}%"
            ).execute()
            return response.data
            
        except Exception as e:
            logger.error(f"Error en búsqueda de {table}: {str(e)}")
            raise


# Instancia global del gestor de base de datos
db_manager = DatabaseManager()
