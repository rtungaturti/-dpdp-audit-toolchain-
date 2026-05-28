"""
Universal Data Connector (UDC) - Agent 1
Connects to various data sources and executes queries
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import pandas as pd
from sqlalchemy import create_engine, text
import aiohttp
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DataSource:
    """Represents a configured data source"""
    name: str
    source_type: str  # 'mysql', 'postgresql', 'api'
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None

class UniversalDataConnector:
    """
    Universal Data Connector - Central hub for data access
    Currently supports: MySQL, PostgreSQL, REST APIs
    """
    
    def __init__(self):
        self.sources: Dict[str, DataSource] = {}
        self.engines: Dict[str, Any] = {}
        self.connected = False
    
    def add_source(self, source: DataSource):
        """Add a data source configuration"""
        self.sources[source.name] = source
        logger.info(f"Added source: {source.name} ({source.source_type})")
    
    def connect(self):
        """Establish connections to all configured sources"""
        for name, source in self.sources.items():
            try:
                if source.source_type in ['mysql', 'postgresql']:
                    self._connect_database(source)
                elif source.source_type == 'api':
                    self._test_api_connection(source)
                logger.info(f"Connected to {name}")
            except Exception as e:
                logger.error(f"Failed to connect to {name}: {e}")
        self.connected = True
    
    def _connect_database(self, source: DataSource):
        """Create database connection engine"""
        if source.source_type == 'mysql':
            connection_string = f"mysql+pymysql://{source.username}:{source.password}@{source.host}:{source.port}/{source.database}"
        elif source.source_type == 'postgresql':
            connection_string = f"postgresql://{source.username}:{source.password}@{source.host}:{source.port}/{source.database}"
        else:
            raise ValueError(f"Unsupported database type: {source.source_type}")
        
        self.engines[source.name] = create_engine(
            connection_string,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True
        )
    
    def _test_api_connection(self, source: DataSource):
        """Test API connection"""
        # Just store the config for now
        self.engines[source.name] = source
    
    def query(self, source_name: str, query: str, params: Dict = None) -> pd.DataFrame:
        """
        Execute a query on the specified source
        
        Args:
            source_name: Name of the configured source
            query: SQL query or API endpoint path
            params: Query parameters
        
        Returns:
            DataFrame with results
        """
        if source_name not in self.engines:
            raise ValueError(f"Source '{source_name}' not found. Available: {list(self.engines.keys())}")
        
        engine = self.engines[source_name]
        source = self.sources[source_name]
        
        try:
            if source.source_type in ['mysql', 'postgresql']:
                # SQL Database query
                with engine.connect() as conn:
                    result = pd.read_sql(text(query), conn, params=params)
                    logger.info(f"Query on {source_name} returned {len(result)} rows")
                    return result
            
            elif source.source_type == 'api':
                # API query (simplified - in production use async)
                import requests
                url = f"{source.api_endpoint}{query}"
                headers = {}
                if source.api_key:
                    headers["Authorization"] = f"Bearer {source.api_key}"
                
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Convert to DataFrame
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                elif isinstance(data, dict) and 'data' in data:
                    df = pd.DataFrame(data['data'])
                else:
                    df = pd.DataFrame([data])
                
                logger.info(f"API query on {source_name} returned {len(df)} rows")
                return df
            
            else:
                raise ValueError(f"Unsupported source type: {source.source_type}")
                
        except Exception as e:
            logger.error(f"Query failed on {source_name}: {e}")
            raise
    # Add this to your udc.py

def _create_sql_engine(self, config: DataSourceConfig):
    """Create SQLAlchemy engine with Supabase SSL support"""
    import urllib.parse
    
    # Handle Supabase SSL requirement
    ssl_mode = "require"  # Supabase requires SSL/TLS encryption
    
    if config.source_type == SourceType.POSTGRESQL:
        # URL encode password to handle special characters (@, #, $, etc.)
        encoded_password = urllib.parse.quote_plus(config.password)
        
        # Build connection string with SSL
        connection_string = (
            f"postgresql://{config.username}:{encoded_password}"
            f"@{config.host}:{config.port}/{config.database}"
            f"?sslmode={ssl_mode}"
        )
        
        # For Supabase connection pooler (port 6543), add pgbouncer parameter
        if config.port == 6543:
            connection_string += "&pgbouncer=true"
        
        # Create engine with SSL configuration
        return create_engine(
            connection_string,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            connect_args={
                "sslmode": "require",
                "sslrootcert": None  # Accept Supabase self-signed cert
            }
        )
    # ... rest of your existing code
    def list_tables(self, source_name: str) -> List[str]:
        """List all tables in a database source"""
        if source_name not in self.engines:
            raise ValueError(f"Source '{source_name}' not found")
        
        source = self.sources[source_name]
        if source.source_type in ['mysql', 'postgresql']:
            from sqlalchemy import inspect
            inspector = inspect(self.engines[source_name])
            return inspector.get_table_names()
        else:
            return []
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all connections"""
        status = {}
        for name, engine in self.engines.items():
            try:
                if self.sources[name].source_type in ['mysql', 'postgresql']:
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                status[name] = True
            except Exception:
                status[name] = False
        return status


# Singleton instance for use across the application
_udc_instance = None

def get_udc() -> UniversalDataConnector:
    """Get the global UDC instance"""
    global _udc_instance
    if _udc_instance is None:
        _udc_instance = UniversalDataConnector()
    return _udc_instance

def configure_udc_from_json(config_json: dict):
    """Configure UDC from JSON configuration"""
    udc = get_udc()
    
    for source_config in config_json.get('sources', []):
        source = DataSource(
            name=source_config['name'],
            source_type=source_config['type'],
            host=source_config.get('host'),
            port=source_config.get('port'),
            database=source_config.get('database'),
            username=source_config.get('username'),
            password=source_config.get('password'),
            api_endpoint=source_config.get('api_endpoint'),
            api_key=source_config.get('api_key')
        )
        udc.add_source(source)
    
    udc.connect()
    return udc
