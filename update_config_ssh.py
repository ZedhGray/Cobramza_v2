# update_config_ssh.py
import os

# CONFIGURACIÓN DE GITHUB CON SSH
GITHUB_USER = "ZedhGray"
REPO_NAME = "Cobramza_v2"
SSH_KEY_PATH = r"C:\Users\Garcia Desing\.ssh\deploy_key_cobranza"

# CONFIGURACIÓN DE LA APLICACIÓN
MAIN_APP_FILE = "main.pyw"
MAIN_APP_ALT = "main.pyw"

# ARCHIVOS A IGNORAR
IGNORE_FILES = [
    'updater_pyqt.py',
    'updater_pyqt_ssh.py',
    'update_config_ssh.py',
    'deploy_key_cobranza',
    'deploy_key_cobranza.pub',
    '__pycache__',
    '.git',
    '*.log',
    '*.ico',
]

# CONFIGURACIÓN DE INTERFAZ
COLORS = {
    'primary': '#E31837',
    'white': '#ffffff',
    'text': '#333333',
}

# LOGS
UPDATE_LOG_FILE = "update_ssh_log.txt"
LOG_FORMAT = "%(asctime)s - %(levelname)s - [SSH] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# TIEMPOS
CLOSE_WAIT_TIME = 3
RESTART_WAIT_TIME = 2

# INTERFAZ
UPDATER_WINDOW_SIZE = (550, 450)

# FUNCIONES
def get_app_info():
    return {
        'name': 'Sistema de Cobranza',
        'company': 'Garcia Automotriz',
        'version': '1.2.0',
        'year': '2025',
        'developer': 'Garcia Company'
    }

def validate_config():
    errors = []
    if not os.path.exists(SSH_KEY_PATH):
        errors.append(f"Clave SSH no encontrada en: {SSH_KEY_PATH}")
    return errors