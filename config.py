# Estructura del proyecto:
#
# mercadolibre_stock_updater/
# ├── config.py
# ├── database.py
# ├── mercadolibre_api.py
# ├── stock_updater.py
# ├── ml_stock_sync.py
# └── main.py

# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración existente
SQL_SERVER = os.getenv('SQL_SERVER', 'localhost\\SQLEXPRESS')
DATABASE = os.getenv('DATABASE', 'TuBaseDeDatos')
USERNAME = os.getenv('DB_USERNAME', 'TuUsuario')
PASSWORD = os.getenv('DB_PASSWORD', 'TuContraseña')


