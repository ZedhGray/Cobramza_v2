# update_config.py
"""
Configuración para el sistema de actualización
Personaliza estos valores según tu repositorio y configuración
"""

# =============================================================================
# CONFIGURACIÓN DE GITHUB
# =============================================================================

# Tu usuario de GitHub
GITHUB_USER = "GarciaCompany"

# Token de acceso personal de GitHub
# Para generar un token:
# 1. Ve a GitHub > Settings > Developer settings > Personal access tokens
# 2. Genera un nuevo token con permisos de "repo"
# 3. Copia el token aquí
GITHUB_TOKEN = "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"

# Nombre del repositorio
REPO_NAME = "Cobramza_v2"

# URL completa del repositorio
REPO_URL = f"https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{REPO_NAME}.git"

# =============================================================================
# CONFIGURACIÓN DE LA APLICACIÓN
# =============================================================================

# Nombre del archivo principal de tu aplicación
MAIN_APP_FILE = "main.py"  # o "main.pyw"

# Nombre alternativo (si usas .pyw)
MAIN_APP_ALT = "main.pyw"

# =============================================================================
# ARCHIVOS Y CARPETAS A IGNORAR DURANTE LA ACTUALIZACIÓN
# =============================================================================

IGNORE_FILES = [
    # Archivos del actualizador
    'updater_pyqt.py',
    'updater_pyqt.pyw',
    'update_config.py',
    
    # Archivos de log
    'error_log.txt',
    'update_log.txt',
    'app.log',
    'debug.log',
    
    # Archivos de configuración sensibles
    '.env',
    'config.json',
    'database_config.py',
    
    # Carpetas del sistema
    '__pycache__',
    '.git',
    '.gitignore',
    '.vscode',
    '.idea',
    
    # Archivos de íconos (opcional, coméntalo si quieres actualizar íconos)
    'lga.ico',
    'lga2.ico',
    'logo.ico',
    'icon.ico',
    
    # Archivos de respaldo
    '*.bak',
    '*.backup',
    'backup_*',
    
    # Archivos temporales
    '*.tmp',
    '*.temp',
    'temp_*',
    
    # Archivos de base de datos locales (si tienes)
    '*.db',
    '*.sqlite',
    '*.mdb',
]

# =============================================================================
# CONFIGURACIÓN DE CONTACTO Y SOPORTE
# =============================================================================

# Número de WhatsApp para soporte (incluye código de país)
WHATSAPP_SUPPORT = "5217551285755"  # Cambia por tu número real

# Mensaje predeterminado para WhatsApp
WHATSAPP_MESSAGE = "Hola, necesito ayuda con el Sistema de Cobranza"

# =============================================================================
# INFORMACIÓN DE LA APLICACIÓN
# =============================================================================

APP_NAME = "Sistema de Cobranza"
APP_COMPANY = "Garcia Automotriz"
APP_VERSION = "1.2.0"
APP_YEAR = "2025"
APP_DEVELOPER = "Tu Empresa"

# =============================================================================
# CONFIGURACIÓN DE PROCESOS
# =============================================================================

# Nombres de procesos a cerrar durante la actualización
PROCESS_NAMES = [
    'python.exe',
    'pythonw.exe',
    'Sistema_Cobranza.exe',  # Si compilas a .exe
]

# Tiempo de espera para cerrar procesos (segundos)
CLOSE_WAIT_TIME = 3

# Tiempo de espera para reiniciar (segundos)
RESTART_WAIT_TIME = 2

# =============================================================================
# CONFIGURACIÓN DE LOGS
# =============================================================================

# Archivo de log del actualizador
UPDATE_LOG_FILE = "update_log.txt"

# Nivel de logging
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

# Formato de logs
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Formato de fecha en logs
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# =============================================================================
# CONFIGURACIÓN DE INTERFAZ
# =============================================================================

# Colores de la aplicación (en formato hexadecimal)
COLORS = {
    'primary': '#E31837',      # Rojo principal
    'secondary': '#f8f9fa',    # Gris claro
    'text': '#333333',         # Texto principal
    'error': '#d93025',        # Color de error
    'success': '#28a745',      # Color de éxito
    'warning': '#ffc107',      # Color de advertencia
    'white': '#ffffff',        # Blanco
    'border': '#dee2e6',       # Borde
}

# Tamaño de la ventana del actualizador
UPDATER_WINDOW_SIZE = (500, 400)

# Tamaño fijo de ventana
UPDATER_FIXED_SIZE = True

# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

def get_app_info():
    """Retorna información completa de la aplicación"""
    return {
        'name': APP_NAME,
        'company': APP_COMPANY,
        'version': APP_VERSION,
        'year': APP_YEAR,
        'developer': APP_DEVELOPER
    }

def get_github_config():
    """Retorna configuración de GitHub"""
    return {
        'user': GITHUB_USER,
        'token': GITHUB_TOKEN,
        'repo': REPO_NAME,
        'url': REPO_URL
    }

def get_contact_info():
    """Retorna información de contacto"""
    return {
        'whatsapp': WHATSAPP_SUPPORT,
        'message': WHATSAPP_MESSAGE
    }

# =============================================================================
# VALIDACIONES
# =============================================================================

def validate_config():
    """Valida que la configuración esté completa"""
    errors = []
    
    if GITHUB_USER == "TuUsuarioGitHub":
        errors.append("GITHUB_USER no está configurado")
    
    if GITHUB_TOKEN == "ghp_TuTokenAqui":
        errors.append("GITHUB_TOKEN no está configurado")
    
    if REPO_NAME == "TuRepositorio":
        errors.append("REPO_NAME no está configurado")
    
    if WHATSAPP_SUPPORT == "5217551234567":
        errors.append("WHATSAPP_SUPPORT no está configurado")
    
    return errors

# =============================================================================
# CONFIGURACIÓN AVANZADA (OPCIONAL)
# =============================================================================

# Habilitar verificación de checksums (requiere archivos .hash en el repo)
ENABLE_CHECKSUM_VERIFICATION = False

# Habilitar actualización incremental (solo archivos modificados)
ENABLE_INCREMENTAL_UPDATE = False

# Habilitar respaldo automático antes de actualizar
ENABLE_AUTO_BACKUP = True

# Carpeta para respaldos
BACKUP_FOLDER = "backups"

# Máximo número de respaldos a mantener
MAX_BACKUPS = 5

# Habilitar notificaciones del sistema
ENABLE_SYSTEM_NOTIFICATIONS = True

# Habilitar modo debug (más información en logs)
DEBUG_MODE = False