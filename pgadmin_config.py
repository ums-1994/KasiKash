import os
from support import PGADMIN_CONNECTION_STRING

# pgAdmin configuration
PGADMIN_CONFIG = {
    'connection_string': PGADMIN_CONNECTION_STRING,
    'server_name': 'KasiKash',
    'host': 'localhost',
    'port': 5432,
    'database': 'kasikash_db',
    'username': 'kasikash_user',
    'password': 'jackwinter1'
}

# Export configuration for pgAdmin
def export_pgadmin_config():
    """
    Exports the database configuration for pgAdmin.
    """
    config = {
        'name': PGADMIN_CONFIG['server_name'],
        'host': PGADMIN_CONFIG['host'],
        'port': PGADMIN_CONFIG['port'],
        'database': PGADMIN_CONFIG['database'],
        'username': PGADMIN_CONFIG['username'],
        'password': PGADMIN_CONFIG['password']
    }
    return config 