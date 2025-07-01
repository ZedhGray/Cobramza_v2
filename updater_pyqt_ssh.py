import os
import sys
import time
import subprocess
import shutil
import tempfile
import logging
import git
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QProgressBar, QTextEdit, 
                            QMessageBox, QDialog)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont, QIcon
from threading import Thread

# Importar configuración
try:
    from update_config_ssh import *
except ImportError:
    # Valores por defecto si no existe el archivo de configuración
    GITHUB_USER = "GarciaCompany"
    REPO_NAME = "Cobramza_v2"
    SSH_KEY_PATH = os.path.expanduser("~/.ssh/deploy_key_cobranza")
    MAIN_APP_FILE = "main.py"
    IGNORE_FILES = ['updater_pyqt.py', '__pycache__', '.git']
    COLORS = {'primary': '#E31837', 'white': '#ffffff'}
    UPDATE_LOG_FILE = "update_log.txt"
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    CLOSE_WAIT_TIME = 3
    RESTART_WAIT_TIME = 2
    UPDATER_WINDOW_SIZE = (500, 400)

class UpdateWorker(QThread):
    """Worker thread para manejar la actualización en background usando SSH"""
    status_updated = pyqtSignal(str)
    detail_added = pyqtSignal(str)
    progress_started = pyqtSignal()
    progress_stopped = pyqtSignal()
    update_completed = pyqtSignal(bool, str)  # success, message
    
    def __init__(self):
        super().__init__()
        self.setup_logging()
        
        # Usar SSH en lugar de HTTPS
        self.REPO_URL = f"git@github.com:{GITHUB_USER}/{REPO_NAME}.git"
        
        # Ruta de la aplicación
        self.app_path = os.getcwd()
        self.main_app = os.path.join(self.app_path, MAIN_APP_FILE)
        
        # Verificar si existe archivo alternativo
        if not os.path.exists(self.main_app):
            alt_file = getattr(sys.modules[__name__], 'MAIN_APP_ALT', 'main.pyw')
            alt_path = os.path.join(self.app_path, alt_file)
            if os.path.exists(alt_path):
                self.main_app = alt_path
        
        # Usar archivos a ignorar de la configuración
        self.ignore_files = IGNORE_FILES
        
        # Ruta de la clave SSH
        self.ssh_key_path = SSH_KEY_PATH

    def setup_logging(self):
        logging.basicConfig(
            filename=UPDATE_LOG_FILE,
            level=getattr(logging, getattr(sys.modules[__name__], 'LOG_LEVEL', 'INFO')),
            format=LOG_FORMAT,
            datefmt=LOG_DATE_FORMAT
        )
        self.logger = logging.getLogger("PyQtUpdaterSSH")

    def setup_ssh_environment(self):
        """Configurar entorno SSH para usar la deploy key"""
        try:
            # Verificar que la clave SSH existe
            if not os.path.exists(self.ssh_key_path):
                raise Exception(f"Clave SSH no encontrada en: {self.ssh_key_path}")
            
            # Configurar SSH para usar la clave específica
            ssh_command = f'ssh -i "{self.ssh_key_path}" -o StrictHostKeyChecking=no'
            
            # Establecer la variable de entorno para git
            os.environ['GIT_SSH_COMMAND'] = ssh_command
            
            self.detail_added.emit(f"🔑 SSH configurado: {os.path.basename(self.ssh_key_path)}")
            return True
            
        except Exception as e:
            self.detail_added.emit(f"❌ Error configurando SSH: {str(e)}")
            return False

    def test_ssh_connection(self):
        """Probar la conexión SSH con GitHub"""
        try:
            self.detail_added.emit("🔍 Probando conexión SSH...")
            
            # Comando para probar conexión SSH
            ssh_test_cmd = f'ssh -i "{self.ssh_key_path}" -o StrictHostKeyChecking=no -T git@github.com'
            
            result = subprocess.run(
                ssh_test_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # GitHub SSH siempre retorna código 1, pero con mensaje de éxito
            if "successfully authenticated" in result.stderr.lower():
                self.detail_added.emit("✅ Conexión SSH exitosa")
                return True
            else:
                self.detail_added.emit(f"⚠️ Respuesta SSH: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.detail_added.emit("⏰ Timeout en conexión SSH")
            return False
        except Exception as e:
            self.detail_added.emit(f"❌ Error probando SSH: {str(e)}")
            return False

    def run(self):
        """Proceso principal de actualización con SSH"""
        try:
            # Paso 1: Configurar SSH
            self.status_updated.emit("🔑 Configurando acceso SSH...")
            if not self.setup_ssh_environment():
                self.update_completed.emit(False, "Error configurando SSH")
                return
            
            # Paso 2: Probar conexión SSH
            self.status_updated.emit("🔍 Verificando conexión...")
            if not self.test_ssh_connection():
                self.update_completed.emit(False, "No se pudo conectar via SSH a GitHub")
                return
            
            # Paso 3: Verificar si la aplicación principal está ejecutándose
            self.status_updated.emit("🔍 Verificando aplicación principal...")
            self.detail_added.emit("Comprobando procesos activos...")
            
            if self.is_app_running():
                self.status_updated.emit("🔄 Cerrando aplicación principal...")
                self.close_main_app()
                time.sleep(CLOSE_WAIT_TIME)  # Esperar cierre completo
            
            # Paso 4: Crear respaldo si está habilitado
            if getattr(sys.modules[__name__], 'ENABLE_AUTO_BACKUP', False):
                self.status_updated.emit("💾 Creando respaldo...")
                self.create_backup()
            
            # Paso 5: Iniciar descarga
            self.progress_started.emit()
            self.status_updated.emit("🌐 Conectando con GitHub via SSH...")
            temp_dir = tempfile.mkdtemp()
            
            try:
                # Paso 6: Clonar repositorio via SSH
                self.status_updated.emit("⬇️ Descargando archivos actualizados...")
                self.detail_added.emit(f"📡 Clonando: {GITHUB_USER}/{REPO_NAME}")
                
                # Clonar con SSH
                try:
                    git.Repo.clone_from(self.REPO_URL, temp_dir, depth=1)
                    self.detail_added.emit("✅ Repositorio clonado exitosamente")
                except git.exc.GitCommandError as e:
                    if "permission denied" in str(e).lower():
                        raise Exception("Permiso denegado. Verifique que la deploy key esté configurada correctamente.")
                    elif "repository not found" in str(e).lower():
                        raise Exception("Repositorio no encontrado. Verifique el nombre del repositorio.")
                    elif "host key verification failed" in str(e).lower():
                        raise Exception("Verificación de host falló. La clave SSH podría no estar configurada.")
                    else:
                        raise Exception(f"Error al clonar repositorio: {str(e)}")
                
                # Paso 7: Actualizar archivos
                self.status_updated.emit("📝 Actualizando archivos...")
                updated_count = self.update_files(temp_dir)
                
                # Paso 8: Completar
                self.status_updated.emit("✅ ¡Actualización completada con éxito!")
                self.detail_added.emit(f"🎉 {updated_count} elementos actualizados correctamente.")
                
                # Paso 9: Reiniciar aplicación
                self.status_updated.emit("🚀 Reiniciando aplicación...")
                time.sleep(RESTART_WAIT_TIME)
                self.restart_main_app()
                
                self.update_completed.emit(True, f"Actualización completada exitosamente.\n{updated_count} archivos actualizados.")
                
            except Exception as e:
                error_msg = f"Error durante la actualización: {str(e)}"
                self.logger.error(error_msg)
                self.detail_added.emit(f"❌ {error_msg}")
                self.update_completed.emit(False, error_msg)
            
            finally:
                # Limpiar directorio temporal
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
                # Limpiar variable de entorno SSH
                if 'GIT_SSH_COMMAND' in os.environ:
                    del os.environ['GIT_SSH_COMMAND']
                self.progress_stopped.emit()
        
        except Exception as e:
            self.logger.error(f"Error crítico: {str(e)}")
            self.update_completed.emit(False, f"Error crítico: {str(e)}")
            self.progress_stopped.emit()

    def create_backup(self):
        """Crea un respaldo de la aplicación actual"""
        try:
            backup_folder = getattr(sys.modules[__name__], 'BACKUP_FOLDER', 'backups')
            max_backups = getattr(sys.modules[__name__], 'MAX_BACKUPS', 5)
            
            if not os.path.exists(backup_folder):
                os.makedirs(backup_folder)
            
            # Crear nombre del respaldo con timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
            backup_path = os.path.join(backup_folder, backup_name)
            
            # Copiar archivos importantes
            important_files = [f for f in os.listdir(self.app_path) 
                             if f.endswith(('.py', '.pyw')) and f not in self.ignore_files]
            
            os.makedirs(backup_path)
            for file in important_files:
                src = os.path.join(self.app_path, file)
                dst = os.path.join(backup_path, file)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
            
            self.detail_added.emit(f"💾 Respaldo creado: {backup_name}")
            
            # Limpiar respaldos antiguos
            self.cleanup_old_backups(backup_folder, max_backups)
            
        except Exception as e:
            self.detail_added.emit(f"⚠️ Error creando respaldo: {str(e)}")

    def cleanup_old_backups(self, backup_folder, max_backups):
        """Limpia respaldos antiguos"""
        try:
            backups = [d for d in os.listdir(backup_folder) if d.startswith('backup_')]
            backups.sort(reverse=True)  # Más recientes primero
            
            for old_backup in backups[max_backups:]:
                old_path = os.path.join(backup_folder, old_backup)
                shutil.rmtree(old_path, ignore_errors=True)
                self.detail_added.emit(f"🗑️ Respaldo antiguo eliminado: {old_backup}")
                
        except Exception as e:
            self.detail_added.emit(f"⚠️ Error limpiando respaldos: {str(e)}")

    def is_app_running(self):
        """Verifica si la aplicación principal está ejecutándose"""
        process_names = getattr(sys.modules[__name__], 'PROCESS_NAMES', ['python.exe', 'pythonw.exe'])
        
        if sys.platform == 'win32':
            try:
                for process_name in process_names:
                    result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {process_name}'], 
                                          capture_output=True, text=True)
                    if process_name in result.stdout:
                        return True
                return False
            except:
                return False
        else:
            try:
                output = subprocess.check_output(['ps', 'aux'], universal_newlines=True)
                return any(proc in output for proc in ['main.py', 'main.pyw'])
            except:
                return False

    def close_main_app(self):
        """Cierra la aplicación principal"""
        process_names = getattr(sys.modules[__name__], 'PROCESS_NAMES', ['python.exe', 'pythonw.exe'])
        
        if sys.platform == 'win32':
            try:
                for process_name in process_names:
                    subprocess.run(['taskkill', '/F', '/IM', process_name], 
                                  shell=True, check=False)
                    self.detail_added.emit(f"🔄 Cerrando proceso: {process_name}")
            except Exception as e:
                self.logger.error(f"Error al cerrar aplicación: {str(e)}")
        else:
            try:
                os.system("pkill -f 'python.*main.py'")
                self.detail_added.emit("🔄 Procesos cerrados en Linux/macOS")
            except Exception as e:
                self.logger.error(f"Error al cerrar aplicación: {str(e)}")

    def update_files(self, temp_dir):
        """Actualiza los archivos de la aplicación"""
        updated_count = 0
        
        for item in os.listdir(temp_dir):
            source_path = os.path.join(temp_dir, item)
            dest_path = os.path.join(self.app_path, item)
            
            # Ignorar archivos especificados
            if item in self.ignore_files:
                self.detail_added.emit(f"⏩ Ignorando: {item}")
                continue
            
            try:
                if os.path.isdir(source_path):
                    if os.path.exists(dest_path):
                        shutil.rmtree(dest_path)
                    shutil.copytree(source_path, dest_path)
                    self.detail_added.emit(f"📁 Carpeta actualizada: {item}")
                    updated_count += 1
                else:
                    # Verificar si el archivo realmente cambió
                    if self.file_needs_update(source_path, dest_path):
                        if os.path.exists(dest_path):
                            os.remove(dest_path)
                        shutil.copy2(source_path, dest_path)
                        self.detail_added.emit(f"📄 Archivo actualizado: {item}")
                        updated_count += 1
                    else:
                        self.detail_added.emit(f"✅ Sin cambios: {item}")
            
            except Exception as e:
                self.logger.error(f"Error actualizando {item}: {str(e)}")
                self.detail_added.emit(f"❌ Error al actualizar {item}: {str(e)}")
        
        return updated_count

    def file_needs_update(self, source_path, dest_path):
        """Verifica si un archivo necesita actualización comparando fechas de modificación"""
        if not os.path.exists(dest_path):
            return True
        
        try:
            source_mtime = os.path.getmtime(source_path)
            dest_mtime = os.path.getmtime(dest_path)
            return source_mtime > dest_mtime
        except:
            return True  # Si hay error, actualizar por seguridad

    def restart_main_app(self):
        """Reinicia la aplicación principal"""
        try:
            if sys.platform == 'win32':
                os.startfile(self.main_app)
            else:
                subprocess.Popen(['python3', self.main_app])
            
            self.detail_added.emit("🚀 Aplicación reiniciada correctamente")
            
        except Exception as e:
            self.logger.error(f"Error al reiniciar: {str(e)}")
            self.detail_added.emit(f"❌ Error al reiniciar: {str(e)}")


class UpdaterDialog(QDialog):
    """Diálogo principal del actualizador con SSH"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.setup_ui()
        self.setup_styles()
        
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Usar configuración para el título
        app_info = getattr(sys.modules[__name__], 'get_app_info', lambda: {'name': 'Sistema de Cobranza'})()
        self.setWindowTitle(f"Actualizador SSH - {app_info.get('name', 'Sistema de Cobranza')}")
        
        # Usar tamaño de ventana de la configuración
        window_size = getattr(sys.modules[__name__], 'UPDATER_WINDOW_SIZE', (500, 400))
        self.setFixedSize(*window_size)
        
        # Establecer ícono si existe
        try:
            icon_files = ['lga2.ico', 'lga.ico', 'logo.ico', 'icon.ico']
            for icon_file in icon_files:
                if os.path.exists(icon_file):
                    self.setWindowIcon(QIcon(icon_file))
                    break
        except Exception:
            pass
        
        # Layout principal
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título dinámico
        title_label = QLabel(f"🔑 Actualizador SSH del {app_info.get('name', 'Sistema')}")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Subtítulo dinámico
        company_name = app_info.get('company', 'Garcia Automotriz')
        subtitle_label = QLabel(f"{app_info.get('name', 'Sistema de Cobranza')} - {company_name}")
        subtitle_label.setFont(QFont("Arial", 11))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # Información SSH
        ssh_info_label = QLabel("🔐 Conexión segura via SSH Deploy Key")
        ssh_info_label.setFont(QFont("Arial", 10))
        ssh_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ssh_info_label.setStyleSheet("color: #28a745; background-color: #f8f9fa; padding: 4px; border-radius: 3px;")
        layout.addWidget(ssh_info_label)
        
        # Información de versión
        version_label = QLabel(f"Versión: {app_info.get('version', '1.0.0')}")
        version_label.setFont(QFont("Arial", 9))
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #666666;")
        layout.addWidget(version_label)
        
        # Estado
        self.status_label = QLabel("🔧 Listo para actualizar via SSH")
        self.status_label.setFont(QFont("Arial", 12))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Información del repositorio
        try:
            repo_info = f"📡 Repositorio: {GITHUB_USER}/{REPO_NAME} (SSH)"
            repo_label = QLabel(repo_info)
            repo_label.setFont(QFont("Arial", 9))
            repo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            repo_label.setStyleSheet("color: #888888;")
            layout.addWidget(repo_label)
        except:
            pass
        
        # Barra de progreso
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminada
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        # Área de detalles
        details_label = QLabel("📋 Detalles de la actualización:")
        details_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(details_label)
        
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(150)
        self.details_text.setReadOnly(True)
        self.details_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.details_text)
        
        # Información adicional
        info_text = self.get_update_info()
        if info_text:
            info_label = QLabel(info_text)
            info_label.setFont(QFont("Arial", 8))
            info_label.setStyleSheet("color: #666666; background-color: #f8f9fa; padding: 8px; border-radius: 4px;")
            info_label.setWordWrap(True)
            layout.addWidget(info_label)
        
        # Botones
        button_layout = QHBoxLayout()
        
        self.update_button = QPushButton("🚀 Iniciar Actualización SSH")
        self.update_button.clicked.connect(self.start_update)
        self.update_button.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        self.close_button = QPushButton("❌ Cerrar")
        self.close_button.clicked.connect(self.close_dialog)
        self.close_button.setFont(QFont("Arial", 10))
        
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Centrar ventana
        self.center_window()

    def get_update_info(self):
        """Obtiene información adicional sobre la actualización"""
        try:
            info_parts = []
            
            # Información de SSH
            info_parts.append("🔑 Autenticación SSH segura")
            
            # Información de archivos ignorados
            if hasattr(sys.modules[__name__], 'IGNORE_FILES'):
                ignore_count = len(IGNORE_FILES)
                info_parts.append(f"🛡️ {ignore_count} archivos protegidos")
            
            # Información de respaldo
            if getattr(sys.modules[__name__], 'ENABLE_AUTO_BACKUP', False):
                info_parts.append("💾 Respaldo automático")
            
            return " • ".join(info_parts) if info_parts else ""
            
        except:
            return ""

    def setup_styles(self):
        """Aplica estilos CSS al diálogo usando la configuración"""
        primary_color = COLORS.get('primary', '#E31837')
        white_color = COLORS.get('white', '#ffffff')
        text_color = COLORS.get('text', '#333333')
        border_color = COLORS.get('border', '#dee2e6')
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {white_color};
                color: {text_color};
            }}
            
            QLabel {{
                color: {text_color};
            }}
            
            QPushButton {{
                background-color: {white_color};
                color: {text_color};
                border: 2px solid {primary_color};
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
                min-width: 120px;
            }}
            
            QPushButton:hover {{
                background-color: {primary_color};
                color: white;
                transform: translateY(-1px);
            }}
            
            QPushButton:pressed {{
                background-color: {COLORS.get('error', '#C41230')};
                transform: translateY(0px);
            }}
            
            QPushButton:disabled {{
                background-color: #f5f5f5;
                color: #999999;
                border-color: #cccccc;
            }}
            
            QTextEdit {{
                background-color: #f8f9fa;
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9px;
                selection-background-color: {primary_color};
                selection-color: white;
            }}
            
            QProgressBar {{
                border: 1px solid {border_color};
                border-radius: 4px;
                text-align: center;
                background-color: #f8f9fa;
                height: 20px;
            }}
            
            QProgressBar::chunk {{
                background-color: {primary_color};
                border-radius: 3px;
            }}
            
            QProgressBar:indeterminate {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f8f9fa, stop:0.4 {primary_color}, 
                    stop:0.6 {primary_color}, stop:1 #f8f9fa);
            }}
        """)

    def center_window(self):
        """Centra la ventana en la pantalla o respecto al padre"""
        if self.parent():
            parent_geo = self.parent().geometry()
            x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            y = parent_geo.y() + (parent_geo.height() - self.height()) // 2
            self.move(x, y)
        else:
            # Centrar en pantalla
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)

    def start_update(self):
        """Inicia el proceso de actualización"""
        self.update_button.setEnabled(False)
        self.close_button.setText("⏹️ Cancelar")
        self.details_text.clear()
        
        # Mostrar información inicial
        self.add_detail("🚀 Iniciando actualización via SSH...")
        self.add_detail(f"📍 Directorio de trabajo: {os.getcwd()}")
        self.add_detail(f"🔑 Clave SSH: {SSH_KEY_PATH}")
        
        # Crear y configurar worker
        self.worker = UpdateWorker()
        self.worker.status_updated.connect(self.update_status)
        self.worker.detail_added.connect(self.add_detail)
        self.worker.progress_started.connect(self.start_progress)
        self.worker.progress_stopped.connect(self.stop_progress)
        self.worker.update_completed.connect(self.update_completed)
        
        # Iniciar worker
        self.worker.start()

    def update_status(self, message):
        """Actualiza el estado mostrado"""
        self.status_label.setText(message)

    def add_detail(self, message):
        """Añade un detalle al área de texto con timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.details_text.append(formatted_message)
        
        # Auto-scroll al final
        scrollbar = self.details_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def start_progress(self):
        """Inicia la barra de progreso"""
        self.progress.setVisible(True)

    def stop_progress(self):
        """Detiene la barra de progreso"""
        self.progress.setVisible(False)

    def update_completed(self, success, message):
        """Maneja la finalización de la actualización"""
        self.update_button.setEnabled(True)
        self.close_button.setText("✅ Cerrar")
        
        if success:
            self.status_label.setText("✅ ¡Actualización SSH completada!")
            self.add_detail("🎉 Proceso finalizado exitosamente via SSH")
            
            # Mostrar mensaje de éxito
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle("Actualización SSH Exitosa")
            msg_box.setText("✅ ¡Actualización SSH completada con éxito!")
            msg_box.setDetailedText(message)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()
            
            # Auto-cerrar después de 3 segundos
            QTimer.singleShot(3000, self.close_dialog)
        else:
            self.status_label.setText("❌ Error en la actualización SSH")
            self.add_detail("💥 Proceso finalizado con errores")
            
            # Mostrar mensaje de error
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Error de Actualización SSH")
            msg_box.setText("❌ Error durante la actualización SSH")
            msg_box.setDetailedText(message)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()

    def close_dialog(self):
        """Cierra el diálogo"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(self, "Confirmar", 
                                       "⚠️ ¿Está seguro de cancelar la actualización en progreso?",
                                       QMessageBox.StandardButton.Yes | 
                                       QMessageBox.StandardButton.No,
                                       QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.add_detail("⏹️ Cancelando actualización SSH...")
                self.worker.terminate()
                self.worker.wait(3000)  # Esperar máximo 3 segundos
                self.accept()
        else:
            self.accept()

    def closeEvent(self, event):
        """Maneja el evento de cierre de ventana"""
        self.close_dialog()
        event.accept()


def main():
    """Función principal para ejecutar el actualizador independiente"""
    app = QApplication(sys.argv)
    
    # Establecer estilo de aplicación
    app.setStyle('Fusion')
    
    # Aplicar tema si está disponible
    try:
        app.setStyleSheet(f"""
            QApplication {{
                background-color: {COLORS.get('white', '#ffffff')};
                color: {COLORS.get('text', '#333333')};
            }}
        """)
    except:
        pass
    
    # Verificar que la clave SSH existe
    try:
        if not os.path.exists(SSH_KEY_PATH):
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Icon.Critical)
            error_dialog.setWindowTitle("Error de SSH")
            error_dialog.setText("❌ Clave SSH no encontrada")
            error_dialog.setDetailedText(f"No se encontró la clave SSH en: {SSH_KEY_PATH}\n\nGenere la clave SSH y configúrela como Deploy Key en GitHub.")
            error_dialog.exec()
            sys.exit(1)
    except:
        pass
    
    dialog = UpdaterDialog()
    dialog.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()