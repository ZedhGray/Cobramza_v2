import sys
import logging
import math
import time
import json
import os
import ctypes
from datetime import datetime, date
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QTableWidget, QTableWidgetItem, 
                            QMessageBox, QCheckBox, QLineEdit, QComboBox, QSplitter,
                            QDialog, QFormLayout, QMenu, QDateEdit, QInputDialog, 
                            QGridLayout, QMenuBar, QHeaderView, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QSize, QTimer, QDate, QRect, QEvent, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QIcon, QAction, QPixmap, QPainter, QPainterPath, QLinearGradient

# Importar funciones de database
from database import (get_clients_data, get_ventas_data, get_client_states, 
                     update_client_states, get_clients_without_credit, 
                     sync_clients_to_buro, validate_user, get_client_notes,
                     delete_client_states, update_client_states_wsp, 
                     update_promise_date, update_telefono3, format_phone_number, UserSession)

from cliente_detalle import ClienteDetalleWindow
from login_system import LoadingSplash

# IMPORTAR EL NUEVO SISTEMA DE TEMAS
from theme_manager import ThemeManager, SettingsDialog, ModernCard as ThemedCard, ModernButton as ThemedButton

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cobranza_log.log')
    ]
)

try:
    from updater_pyqt_ssh import UpdaterDialog
except ImportError:
    UpdaterDialog = None

version = "v2.4"

class ModernButton(QPushButton):
    """Botón moderno que se adapta al tema actual"""
    def __init__(self, text, theme_manager, parent=None):
        super().__init__(text, parent)
        self.theme_manager = theme_manager
        self.setFixedHeight(35)
        self.setFixedWidth(200)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        theme = self.theme_manager.get_current_theme()
        
        # Crear gradiente de fondo adaptativo
        gradient = QLinearGradient(0, 0, 0, self.height())
        
        if self.theme_manager.is_dark_theme():
            if self.isChecked():
                gradient.setColorAt(0, QColor(255, 255, 255, 25))
                gradient.setColorAt(1, QColor(255, 255, 255, 15))
                text_color = QColor(255, 255, 255, 230)
            else:
                gradient.setColorAt(0, QColor(255, 255, 255, 10))
                gradient.setColorAt(1, QColor(255, 255, 255, 5))
                text_color = QColor(255, 255, 255, 180)
            border_color = QColor(255, 255, 255, 30)
        else:
            if self.isChecked():
                gradient.setColorAt(0, QColor(25, 118, 210, 200))
                gradient.setColorAt(1, QColor(25, 118, 210, 150))
                text_color = QColor(255, 255, 255, 255)
            else:
                gradient.setColorAt(0, QColor(255, 255, 255, 200))
                gradient.setColorAt(1, QColor(248, 249, 250, 150))
                text_color = QColor(33, 37, 41, 200)
            border_color = QColor(0, 0, 0, 50)
        
        # Dibujar fondo con bordes redondeados
        painter.setBrush(gradient)
        painter.setPen(border_color)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        painter.drawPath(path)
        
        # Dibujar texto
        painter.setPen(text_color)
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())

class ModernCard(QFrame):
    """Tarjeta moderna que se adapta al tema actual"""
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setFrameStyle(QFrame.Shape.NoFrame)
        
        # Aplicar sombra
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        theme = self.theme_manager.get_current_theme()
        
        # Crear gradiente de fondo adaptativo
        gradient = QLinearGradient(0, 0, 0, self.height())
        
        if self.theme_manager.is_dark_theme():
            gradient.setColorAt(0, QColor(255, 255, 255, 30))
            gradient.setColorAt(1, QColor(255, 255, 255, 20))
            border_color = QColor(255, 255, 255, 60)
        else:
            gradient.setColorAt(0, QColor(255, 255, 255, 200))
            gradient.setColorAt(1, QColor(248, 249, 250, 180))
            border_color = QColor(0, 0, 0, 30)
        
        # Dibujar fondo con bordes redondeados
        painter.setBrush(gradient)
        painter.setPen(border_color)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        painter.drawPath(path)

class CobranzaApp(QWidget):
    def __init__(self):
        super().__init__()
        
        # INICIALIZAR THEME MANAGER
        self.theme_manager = ThemeManager()
        
        # ESTABLECER ÍCONO ESPECÍFICAMENTE PARA ESTA VENTANA
        try:
            icon_files = ['lga2.ico', 'lga.ico', 'logo.ico', 'icon.ico']
            
            for icon_file in icon_files:
                if os.path.exists(icon_file):
                    window_icon = QIcon(icon_file)
                    self.setWindowIcon(window_icon)
                    logging.info(f"Ícono de ventana establecido: {icon_file}")
                    break
            else:
                logging.warning("No se encontró archivo de ícono para la ventana")
                
        except Exception as e:
            logging.error(f"Error al establecer ícono de ventana: {e}")
        
        # Variable para controlar vista actual
        self.current_view = "clientes"
        
        # Datos
        self.clientes_data = {}
        self.ventas_data = {}
        self.client_states = {}
        self.clients_buro = {}
        self.last_update_time = time.time()
        
        self.data_loaded = False
        
        self.initUI()
        self.load_data()
        self.setup_auto_update()

    def get_current_colors(self):
        """Obtiene los colores del tema actual"""
        theme = self.theme_manager.get_current_theme()
        return {
            'DARK_BG': theme['DARK_BG'],
            'CARD_BG': theme['CARD_BG'],
            'ACCENT_BLUE': theme['ACCENT_BLUE'],
            'BRIGHT_CYAN': theme['BRIGHT_CYAN'],
            'TEXT_PRIMARY': theme['TEXT_PRIMARY'],
            'TEXT_SECONDARY': theme['TEXT_SECONDARY'],
            'TITLE_TEXT': theme['TITLE_TEXT'],
            'LOGO_FILE': theme['LOGO_FILE'],  # ← AGREGAR ESTA LÍNEA
            'SUCCESS_GREEN': theme['SUCCESS_GREEN'],
            'WARNING_ORANGE': theme['WARNING_ORANGE'],
            'DANGER_RED': theme['DANGER_RED'],
            'PROMISE_PURPLE': theme['PROMISE_PURPLE']
        }
    def initUI(self):
        self.setWindowTitle(f"Sistema de Cobranza {version}")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Aplicar tema
        self.apply_theme()
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header moderno (sin menú)
        self.create_modern_header(main_layout)
        
        # Botones de navegación modernos
        self.create_modern_navigation(main_layout)
        
        # Área principal de contenido
        self.create_main_content(main_layout)
        
        self.setLayout(main_layout)

    def apply_theme(self):
        """Aplica el tema actual a la aplicación"""
        theme = self.theme_manager.get_current_theme()
        colors = self.get_current_colors()
        
        # Estilo CSS adaptativo
        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {theme['gradient_start']}, stop:0.3 {theme['gradient_mid1']}, 
                    stop:0.7 {theme['gradient_mid2']}, stop:1 {theme['gradient_end']});
                color: {colors['TEXT_PRIMARY']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            
            QTableWidget {{
                background: {theme['card_bg_alpha']};
                border: 1px solid {theme['border_alpha']};
                border-radius: 12px;
                selection-background-color: {colors['BRIGHT_CYAN']};
                color: {colors['TEXT_PRIMARY']};
                gridline-color: {theme['border_alpha']};
                font-size: 14px;
                font-weight: 500;
                backdrop-filter: blur(10px);
            }}
            
            QTableWidget::item {{
                padding: 8px 6px;
                border-bottom: 1px solid {theme['border_alpha']};
                background: transparent;
            }}
            
            QTableWidget::item:selected {{
                background: rgba({self.hex_to_rgb(colors['BRIGHT_CYAN'])}, 0.3);
                color: white;
            }}
            
            QTableWidget::item:hover {{
                background: {theme['hover_alpha']};
            }}
            
            QTableWidget QHeaderView::section {{
                background: {theme['card_bg_alpha']};
                color: {colors['TEXT_PRIMARY']};
                padding: 8px 6px;
                border: none;
                border-right: 1px solid {theme['border_alpha']};
                border-bottom: 2px solid {colors['BRIGHT_CYAN']};
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            QScrollBar:vertical {{
                background: {theme['card_bg_alpha']};
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }}
            
            QScrollBar::handle:vertical {{
                background: {theme['border_alpha']};
                border-radius: 4px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: rgba({self.hex_to_rgb(colors['BRIGHT_CYAN'])}, 0.5);
            }}
        """)

    def hex_to_rgb(self, hex_color):
        """Convertir color hex a RGB"""
        hex_color = hex_color.lstrip('#')
        return ', '.join(str(int(hex_color[i:i+2], 16)) for i in (0, 2, 4))

    def create_modern_header(self, layout):
        """Crear header moderno con glassmorphism - tamaños optimizados"""
        colors = self.get_current_colors()
        
        header_frame = ModernCard(self.theme_manager)
        header_frame.setFixedHeight(120)
        header_frame.setContentsMargins(20, 15, 20, 15)
        
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)
        
        # Logo y título - EN FILA (horizontal)
        logo_section = QHBoxLayout()
        logo_section.setSpacing(20)
        
        # Intentar cargar logo
        try:
            logo_label = QLabel()
            logo_file = self.theme_manager.get_current_theme()['LOGO_FILE']
            pixmap = QPixmap(logo_file)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(200, 60, Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation)
                logo_label.setPixmap(scaled_pixmap)
            else:
                raise FileNotFoundError
        except:
            # Fallback si no hay logo
            logo_label = QLabel("GARCIA")
            logo_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
            logo_label.setStyleSheet(f"color: {colors['BRIGHT_CYAN']}; background: transparent;")
        
        title_label = QLabel("SISTEMA DE COBRANZA")
        title_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {colors['TITLE_TEXT']}; background: transparent;")
        
        logo_section.addWidget(logo_label)
        logo_section.addWidget(title_label)
        
        header_layout.addLayout(logo_section)
        header_layout.addStretch()
        
        # Panel de estadísticas más compacto
        self.create_compact_stats_panel(header_layout)
        
        # BOTONES DE CONFIGURACIÓN Y RECARGA
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(8)
        
        # Botón configuración más pequeño
        config_button = QPushButton("⚙️")
        config_button.setFont(QFont("Segoe UI", 12))
        config_button.setFixedSize(30, 30)
        config_button.setCursor(Qt.CursorShape.PointingHandCursor)
        config_button.setToolTip("Configuración")
        config_button.setStyleSheet(f"""
            QPushButton {{
                background: rgba({self.hex_to_rgb(colors['BRIGHT_CYAN'])}, 0.2);
                color: {colors['BRIGHT_CYAN']};
                border: 1px solid rgba({self.hex_to_rgb(colors['BRIGHT_CYAN'])}, 0.3);
                border-radius: 15px;
            }}
            QPushButton:hover {{
                background: rgba({self.hex_to_rgb(colors['BRIGHT_CYAN'])}, 0.3);
            }}
        """)
        config_button.clicked.connect(self.show_settings)
        
        # Botón recargar más pequeño
        reload_button = QPushButton("🔄")
        reload_button.setFont(QFont("Segoe UI", 12))
        reload_button.setFixedSize(30, 30)
        reload_button.setCursor(Qt.CursorShape.PointingHandCursor)
        reload_button.setToolTip("Actualizar Datos")
        reload_button.setStyleSheet(f"""
            QPushButton {{
                background: rgba({self.hex_to_rgb(colors['BRIGHT_CYAN'])}, 0.2);
                color: {colors['BRIGHT_CYAN']};
                border: 1px solid rgba({self.hex_to_rgb(colors['BRIGHT_CYAN'])}, 0.3);
                border-radius: 15px;
            }}
            QPushButton:hover {{
                background: rgba({self.hex_to_rgb(colors['BRIGHT_CYAN'])}, 0.3);
            }}
        """)
        reload_button.clicked.connect(self.reload_data)
        
        buttons_layout.addWidget(config_button)
        buttons_layout.addWidget(reload_button)
        header_layout.addLayout(buttons_layout)
        
        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)

    def create_compact_stats_panel(self, layout):
        """Crear panel de estadísticas compacto"""
        colors = self.get_current_colors()
        
        stats_container = QWidget()
        stats_container.setFixedWidth(600)
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        # Total general - más compacto
        total_section = QVBoxLayout()
        total_section.setSpacing(2)
        
        total_label = QLabel("💰 Deuda Total")
        total_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        total_label.setStyleSheet(f"color: {colors['TEXT_SECONDARY']};")
        
        self.amount_label = QLabel("Cargando...")
        self.amount_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.amount_label.setStyleSheet(f"color: {colors['BRIGHT_CYAN']};")
        
        total_section.addWidget(total_label)
        total_section.addWidget(self.amount_label)
        
        stats_layout.addLayout(total_section)
        
        # Separador vertical
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet(f"background: {colors['TEXT_SECONDARY']}; width: 1px;")
        stats_layout.addWidget(separator)
        
        # Desglose horizontal compacto
        breakdown_layout = QHBoxLayout()
        breakdown_layout.setSpacing(20)
        
        # Crear tarjetas compactas
        self.clientes_compact = self.create_compact_stat("👤", "Clientes", "--", colors['SUCCESS_GREEN'])
        self.empresas_compact = self.create_compact_stat("🏢", "Empresas", "--", colors['WARNING_ORANGE'])
        self.buro_compact = self.create_compact_stat("⚠️", "Buró", "--", colors['DANGER_RED'])
        
        breakdown_layout.addWidget(self.clientes_compact)
        breakdown_layout.addWidget(self.empresas_compact)
        breakdown_layout.addWidget(self.buro_compact)
        
        stats_layout.addLayout(breakdown_layout)
        
        stats_container.setLayout(stats_layout)
        layout.addWidget(stats_container)

    def create_compact_stat(self, icon, label, value, color):
        """Crear tarjeta de estadística compacta"""
        colors = self.get_current_colors()
        theme = self.theme_manager.get_current_theme()
        
        card = QWidget()
        card.setFixedSize(120, 70)
        card.setStyleSheet(f"""
            QWidget {{
                background: {theme['card_bg_alpha']};
                border: 1px solid {theme['border_alpha']};
                border-radius: 8px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)
        
        # Ícono y etiqueta en horizontal
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI", 10))
        
        text_label = QLabel(label)
        text_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        text_label.setStyleSheet(f"color: {colors['TEXT_SECONDARY']};")
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(text_label)
        header_layout.addStretch()
        
        # Valor
        value_label = QLabel(value)
        value_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {color};")
        
        layout.addLayout(header_layout)
        layout.addWidget(value_label)
        
        card.setLayout(layout)
        
        # Guardar referencia al label del valor
        if "Clientes" in label:
            self.clientes_label = value_label
        elif "Empresas" in label:
            self.empresas_label = value_label
        elif "Buró" in label:
            self.buro_label = value_label
        
        return card

    def create_modern_navigation(self, layout):
        """Crear navegación moderna con glassmorphism - más compacta"""
        nav_frame = ModernCard(self.theme_manager)
        nav_frame.setFixedHeight(55)
        nav_frame.setContentsMargins(20, 8, 20, 8)
        
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(12)
        
        # Botones de navegación más pequeños
        self.clientes_btn = ModernButton("CRÉDITOS PERSONALES", self.theme_manager)
        self.clientes_btn.setCheckable(True)
        self.clientes_btn.setChecked(True)
        self.clientes_btn.setFixedHeight(35)
        self.clientes_btn.setFixedWidth(200)
        self.clientes_btn.clicked.connect(lambda: self.switch_view("clientes"))
        
        self.empresas_btn = ModernButton("CRÉDITOS EMPRESARIALES", self.theme_manager)
        self.empresas_btn.setCheckable(True)
        self.empresas_btn.setFixedHeight(35)
        self.empresas_btn.setFixedWidth(220)
        self.empresas_btn.clicked.connect(lambda: self.switch_view("empresas"))
        
        self.buro_btn = ModernButton("BURÓ DE CRÉDITO", self.theme_manager)
        self.buro_btn.setCheckable(True)
        self.buro_btn.setFixedHeight(35)
        self.buro_btn.setFixedWidth(150)
        self.buro_btn.clicked.connect(lambda: self.switch_view("buro"))
        
        nav_layout.addWidget(self.clientes_btn)
        nav_layout.addWidget(self.empresas_btn)
        nav_layout.addWidget(self.buro_btn)
        nav_layout.addStretch()
        
        nav_frame.setLayout(nav_layout)
        layout.addWidget(nav_frame)

    def create_main_content(self, layout):
        """Crear área principal de contenido - más compacta"""
        self.main_frame = QWidget()
        self.main_frame.setContentsMargins(15, 15, 15, 15)
        
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(15)
        
        # Crear contenido inicial
        self.create_clientes_view()
        
        self.main_frame.setLayout(self.main_layout)
        layout.addWidget(self.main_frame)

    def show_settings(self):
        """Muestra el diálogo de configuración"""
        try:
            settings_dialog = SettingsDialog(self.theme_manager, self)
            settings_dialog.theme_changed.connect(self.on_theme_changed)
            settings_dialog.exec()
        except Exception as e:
            logging.error(f"Error mostrando configuración: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al abrir configuración: {str(e)}")
    def on_theme_changed(self, theme_name):
        """Maneja el cambio de tema"""
        try:
            logging.info(f"Cambiando tema a: {theme_name}")
            self.apply_theme()
            
            # ACTUALIZAR EL TÍTULO MANUALMENTE
            colors = self.get_current_colors()
            header_widgets = self.findChildren(QLabel)
            for widget in header_widgets:
                if widget.text() == "SISTEMA DE COBRANZA":
                    widget.setStyleSheet(f"color: {colors['TITLE_TEXT']}; background: transparent;")
                    break
            
            # ACTUALIZAR EL LOGO MANUALMENTE
            logo_file = colors['LOGO_FILE']
            for widget in header_widgets:
                if widget.pixmap() is not None:  # Es el logo
                    try:
                        pixmap = QPixmap(logo_file)
                        if not pixmap.isNull():
                            scaled_pixmap = pixmap.scaled(200, 60, Qt.AspectRatioMode.KeepAspectRatio,
                                                        Qt.TransformationMode.SmoothTransformation)
                            widget.setPixmap(scaled_pixmap)
                        else:
                            widget.setText("GARCIA")
                            widget.setStyleSheet(f"color: {colors['BRIGHT_CYAN']}; background: transparent;")
                    except:
                        widget.setText("GARCIA")
                        widget.setStyleSheet(f"color: {colors['BRIGHT_CYAN']}; background: transparent;")
                    break
            
            self.refresh_current_view()
            logging.info("Tema cambiado exitosamente")
            
        except Exception as e:
            logging.error(f"Error cambiando tema: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al cambiar tema: {str(e)}")

    def create_clientes_view(self):
        """Crear vista de clientes modernizada"""
        self.clear_layout(self.main_layout)
        colors = self.get_current_colors()
        
        # Verificar si los datos están cargados
        if not self.data_loaded or not self.clientes_data:
            loading_container = ModernCard(self.theme_manager)
            loading_container.setFixedHeight(200)
            loading_layout = QVBoxLayout()
            loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            loading_label = QLabel("⏳ Cargando datos de clientes...")
            loading_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Medium))
            loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            loading_label.setStyleSheet(f"color: {colors['TEXT_SECONDARY']}; margin: 30px;")
            
            loading_layout.addWidget(loading_label)
            loading_container.setLayout(loading_layout)
            self.main_layout.addWidget(loading_container)
            return
        
        # Grid de categorías moderno
        categories_widget = QWidget()
        categories_layout = QGridLayout()
        categories_layout.setSpacing(15)
        
        # Crear las 4 categorías con colores modernos
        self.create_modern_category_table(categories_layout, "PROMESA DE PAGO", colors['PROMISE_PURPLE'], 0, 0, "🤝")
        self.create_modern_category_table(categories_layout, "MENOS DE 30 DÍAS", colors['SUCCESS_GREEN'], 0, 1, "✅")
        self.create_modern_category_table(categories_layout, "30 A 60 DÍAS", colors['WARNING_ORANGE'], 1, 0, "⚠️")
        self.create_modern_category_table(categories_layout, "MÁS DE 60 DÍAS", colors['DANGER_RED'], 1, 1, "🚨")
        
        categories_widget.setLayout(categories_layout)
        self.main_layout.addWidget(categories_widget)

    def create_modern_category_table(self, layout, title, color, row, col, icon):
        """Crear tabla de categoría moderna - tamaños optimizados"""
        colors = self.get_current_colors()
        theme = self.theme_manager.get_current_theme()
        
        category_card = ModernCard(self.theme_manager)
        category_card.setMinimumHeight(320)
        category_card.setMaximumHeight(400)
        
        category_layout = QVBoxLayout()
        category_layout.setContentsMargins(15, 15, 15, 15)
        category_layout.setSpacing(10)
        
        # Header más compacto
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Ícono y título
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI", 14))
        icon_label.setStyleSheet("background: transparent;")
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {color}; background: transparent;")
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Total de la categoría
        total_categoria = self.calculate_category_total(title.lower())
        total_label = QLabel(f"${total_categoria:,.0f}")
        total_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        total_label.setStyleSheet(f"color: {color}; background: transparent;")
        
        header_layout.addWidget(total_label)
        category_layout.addLayout(header_layout)
        
        # Tabla moderna más compacta
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(['Cliente', 'Monto', 'Fecha', 'Días'])
        
        # Deshabilitar edición
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Configurar columnas con tamaños más pequeños
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        table.setColumnWidth(1, 100)
        table.setColumnWidth(2, 85)
        table.setColumnWidth(3, 60)
        
        table.setMaximumHeight(250)
        table.setMinimumHeight(180)
        
        # Estilo específico para esta tabla
        table.setStyleSheet(f"""
            QTableWidget {{
                background: {theme['card_bg_alpha']};
                border: 1px solid rgba({self.hex_to_rgb(color)}, 0.2);
                font-size: 11px;
            }}
            QTableWidget::item {{
                padding: 6px 4px;
            }}
            QTableWidget::item:selected {{
                background: rgba({self.hex_to_rgb(color)}, 0.3);
            }}
            QTableWidget QHeaderView::section {{
                border-bottom: 2px solid {color};
                padding: 6px 4px;
                font-size: 10px;
            }}
        """)
        
        # Poblar tabla
        self.populate_category_table(table, title, color)
        
        category_layout.addWidget(table)
        category_card.setLayout(category_layout)
        
        layout.addWidget(category_card, row, col)

    def create_buro_view(self):
        """Crear vista de buró moderna - optimizada"""
        self.clear_layout(self.main_layout)
        colors = self.get_current_colors()
        theme = self.theme_manager.get_current_theme()
        
        # Sincronizar clientes con buró
        try:
            sync_clients_to_buro()
            self.clients_buro = get_clients_without_credit()
        except Exception as e:
            logging.error(f"Error al sincronizar buró: {e}")
        
        # Contenedor principal más compacto
        buro_card = ModernCard(self.theme_manager)
        buro_layout = QVBoxLayout()
        buro_layout.setContentsMargins(20, 20, 20, 20)
        buro_layout.setSpacing(15)
        
        # Header con estadísticas compacto
        header_layout = QHBoxLayout()
        
        # Título e ícono
        title_section = QHBoxLayout()
        title_section.setSpacing(10)
        
        icon_label = QLabel("🚨")
        icon_label.setFont(QFont("Segoe UI", 18))
        
        title_label = QLabel("CLIENTES EN BURÓ DE CRÉDITO")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {colors['DANGER_RED']};")
        
        title_section.addWidget(icon_label)
        title_section.addWidget(title_label)
        
        header_layout.addLayout(title_section)
        header_layout.addStretch()
        
        # Estadísticas del buró compactas
        total_buro = sum(data.get('saldo', 0.0) for data in self.clients_buro.values())
        count_buro = len(self.clients_buro)
        
        stats_section = QVBoxLayout()
        stats_section.setAlignment(Qt.AlignmentFlag.AlignRight)
        stats_section.setSpacing(2)
        
        count_label = QLabel(f"{count_buro} Clientes")
        count_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        count_label.setStyleSheet(f"color: {colors['TEXT_SECONDARY']};")
        count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        total_label = QLabel(f"${total_buro:,.2f}")
        total_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        total_label.setStyleSheet(f"color: {colors['DANGER_RED']};")
        total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        stats_section.addWidget(count_label)
        stats_section.addWidget(total_label)
        
        header_layout.addLayout(stats_section)
        buro_layout.addLayout(header_layout)
        
        # Tabla de buró moderna y compacta
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(['ID', 'Cliente', 'Saldo', 'Última Compra', 'Días en Buró'])
        
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Configurar columnas más compactas
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        
        table.setColumnWidth(0, 60)
        table.setColumnWidth(2, 110)
        table.setColumnWidth(3, 100)
        table.setColumnWidth(4, 100)
        
        # Estilo específico para tabla de buró
        table.setStyleSheet(f"""
            QTableWidget {{
                background: rgba({self.hex_to_rgb(colors['DANGER_RED'])}, 0.05);
                border: 1px solid rgba({self.hex_to_rgb(colors['DANGER_RED'])}, 0.2);
                font-size: 9px;
            }}
            QTableWidget::item {{
                padding: 6px 4px;
            }}
            QTableWidget::item:selected {{
                background: rgba({self.hex_to_rgb(colors['DANGER_RED'])}, 0.3);
            }}
            QTableWidget QHeaderView::section {{
                border-bottom: 2px solid {colors['DANGER_RED']};
                padding: 6px 4px;
                font-size: 8px;
            }}
        """)
        
        # Poblar tabla con datos
        table.setRowCount(len(self.clients_buro))
        
        row = 0
        for client_id, client_data in self.clients_buro.items():
            oldest_date = self.get_oldest_sale_date(client_id)
            
            if oldest_date:
                days_in_buro = (datetime.now().date() - oldest_date).days
                fecha_str = oldest_date.strftime("%d/%m/%Y")
            else:
                days_in_buro = "N/A"
                fecha_str = "N/A"
            
            items = [
                QTableWidgetItem(client_id),
                QTableWidgetItem(client_data.get('nombre', 'Sin nombre')),
                QTableWidgetItem(f"${client_data.get('saldo', 0.0):,.0f}"),
                QTableWidgetItem(fecha_str),
                QTableWidgetItem(f"{days_in_buro}d" if days_in_buro != "N/A" else "N/A")
            ]
            
            for col, item in enumerate(items):
                if col == 1:  # Nombre
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    item.setData(Qt.ItemDataRole.UserRole, client_id)
                    item.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setFont(QFont("Segoe UI", 8))
                
                # Color de fondo para buró
                item.setBackground(QColor(239, 68, 68, 15))
                table.setItem(row, col, item)
            
            row += 1
        
        # Conectar evento de doble clic
        table.cellDoubleClicked.connect(lambda row, col: self.on_buro_client_double_click(table, row))
        
        buro_layout.addWidget(table)
        buro_card.setLayout(buro_layout)
        self.main_layout.addWidget(buro_card)

    # Resto de métodos existentes (sin cambios significativos, solo ajustando referencias de colores)
    def populate_category_table(self, table, category_title, color):
        """Poblar tabla con datos según la categoría - optimizado"""
        category_type = self.get_category_from_title(category_title)
        clients_in_category = []
        
        # Filtrar clientes por categoría
        for client_id, client_data in self.clientes_data.items():
            if client_id in self.clients_buro:
                continue
            
            if not self.should_show_client(client_id):
                continue
            
            if self.categorize_client(client_id) == category_type:
                oldest_date = self.get_oldest_sale_date(client_id)
                
                if oldest_date:
                    days_diff = (datetime.now().date() - oldest_date).days
                    fecha_str = oldest_date.strftime("%d/%m")
                else:
                    days_diff = "N/A"
                    fecha_str = "N/A"
                
                clients_in_category.append({
                    'id': client_id,
                    'nombre': client_data.get('nombre', 'Sin nombre'),
                    'saldo': client_data.get('saldo', 0.0),
                    'fecha': fecha_str,
                    'dias': days_diff
                })
        
        # Ordenar por saldo descendente
        clients_in_category.sort(key=lambda x: x['saldo'], reverse=True)
        
        # Poblar tabla
        table.setRowCount(len(clients_in_category))
        
        for row, client in enumerate(clients_in_category):
            # Nombre - truncar si es muy largo
            nombre = client['nombre']
            if len(nombre) > 25:
                nombre = nombre[:22] + "..."
            
            name_item = QTableWidgetItem(nombre)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            name_item.setData(Qt.ItemDataRole.UserRole, client['id'])
            name_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
            name_item.setToolTip(client['nombre'])
            table.setItem(row, 0, name_item)
            
            # Monto - formato más compacto
            monto_item = QTableWidgetItem(f"${client['saldo']:,.0f}")
            monto_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            monto_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            monto_item.setForeground(QColor(color))
            table.setItem(row, 1, monto_item)
            
            # Fecha
            fecha_item = QTableWidgetItem(client['fecha'])
            fecha_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            fecha_item.setFont(QFont("Segoe UI", 8))
            table.setItem(row, 2, fecha_item)
            
            # Días - formato más corto
            if client['dias'] != "N/A":
                dias_str = f"{client['dias']}d"
            else:
                dias_str = "N/A"
            dias_item = QTableWidgetItem(dias_str)
            dias_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            dias_item.setFont(QFont("Segoe UI", 8, QFont.Weight.Medium))
            table.setItem(row, 3, dias_item)
            
            # Color de fondo sutil
            bg_color = self.get_category_background_color(color)
            for col in range(4):
                item = table.item(row, col)
                if item:
                    item.setBackground(QColor(bg_color))
        
        # Conectar evento de doble clic
        table.cellDoubleClicked.connect(lambda row, col: self.on_client_double_click(table, row))

    def get_category_background_color(self, color):
        """Obtener color de fondo para las celdas"""
        colors = self.get_current_colors()
        if color == colors['PROMISE_PURPLE']:
            return "#a855f7"
        elif color == colors['SUCCESS_GREEN']:
            return "#4ade80"
        elif color == colors['WARNING_ORANGE']:
            return "#fb923c"
        elif color == colors['DANGER_RED']:
            return "#ef4444"
        return "#ffffff"

    def switch_view(self, view):
        """Cambiar entre vistas con transición"""
        if self.current_view != view:
            self.current_view = view
            
            # Actualizar botones
            self.clientes_btn.setChecked(view == "clientes")
            self.empresas_btn.setChecked(view == "empresas")
            self.buro_btn.setChecked(view == "buro")
            
            # Mostrar vista correspondiente
            if view == "buro":
                self.create_buro_view()
            else:
                self.create_clientes_view()

    def should_show_client(self, client_id):
        """Determinar si un cliente debe mostrarse en la vista actual"""
        client_state = self.client_states.get(client_id, {})
        is_company = client_state.get('company', False)
        
        if self.current_view == "empresas":
            return is_company
        elif self.current_view == "clientes":
            return not is_company
        else:
            return client_id in self.clients_buro

    def categorize_client(self, client_id):
        """Categorizar un cliente basado en su historial y estado"""
        try:
            # Verificar promesa de pago vigente
            client_state = self.client_states.get(client_id, {})
            promise_date = client_state.get('promiseDate')
            
            if promise_date:
                if isinstance(promise_date, str):
                    try:
                        promise_date = datetime.strptime(promise_date, "%Y-%m-%d").date()
                    except:
                        promise_date = None
                elif isinstance(promise_date, datetime):
                    promise_date = promise_date.date()
                
                if promise_date and promise_date >= datetime.now().date():
                    return "promesa"
            
            # Calcular días desde la venta más antigua
            oldest_sale_date = self.get_oldest_sale_date(client_id)
            if not oldest_sale_date:
                return "rojo"
            
            days_diff = (datetime.now().date() - oldest_sale_date).days
            
            if days_diff < 30:
                return "verde"
            elif days_diff < 60:
                return "amarillo"
            else:
                return "rojo"
                
        except Exception as e:
            logging.error(f"Error al categorizar cliente {client_id}: {e}")
            return "rojo"

    def get_oldest_sale_date(self, client_id):
        """Obtener la fecha de venta más antigua para un cliente"""
        oldest_date = None
        
        for venta_id, venta_data in self.ventas_data.items():
            if venta_data.get('cveCte') == client_id:
                fecha_str = venta_data.get('fecha')
                if fecha_str:
                    try:
                        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                        if oldest_date is None or fecha < oldest_date:
                            oldest_date = fecha
                    except:
                        continue
        
        return oldest_date

    def calculate_totals(self):
        """Calcular totales de deuda"""
        total_clientes = 0.0
        total_empresas = 0.0
        total_buro = 0.0
        
        try:
            # Total de buró
            for client_id, data in self.clients_buro.items():
                saldo = data.get('saldo', 0.0)
                if isinstance(saldo, (int, float)):
                    total_buro += saldo
                else:
                    try:
                        total_buro += float(saldo)
                    except (ValueError, TypeError):
                        continue
            
            # Totales de clientes y empresas
            for client_id, client_data in self.clientes_data.items():
                if client_id in self.clients_buro:
                    continue
                
                saldo = client_data.get('saldo', 0.0)
                
                if isinstance(saldo, str):
                    try:
                        saldo = float(saldo)
                    except (ValueError, TypeError):
                        continue
                elif not isinstance(saldo, (int, float)):
                    continue
                
                client_state = self.client_states.get(client_id, {})
                is_company = client_state.get('company', False)
                
                if is_company:
                    total_empresas += saldo
                else:
                    total_clientes += saldo
            
        except Exception as e:
            logging.error(f"Error al calcular totales: {e}")
            total_clientes = total_empresas = total_buro = 0.0
        
        return total_clientes, total_empresas, total_buro

    def calculate_category_total(self, category):
        """Calcular total para una categoría específica"""
        total = 0.0
        
        for client_id, client_data in self.clientes_data.items():
            if client_id in self.clients_buro:
                continue
            
            if not self.should_show_client(client_id):
                continue
            
            client_category = self.categorize_client(client_id)
            if self.get_category_from_title(category) == client_category:
                total += client_data.get('saldo', 0.0)
        
        return total

    def get_category_from_title(self, title):
        """Convertir título de categoría a identificador"""
        if "promesa" in title.lower():
            return "promesa"
        elif "30 días" in title.lower() and "menos" in title.lower():
            return "verde"
        elif "30 a 60" in title.lower():
            return "amarillo"
        elif "60 días" in title.lower() and "más" in title.lower():
            return "rojo"
        return "verde"

    def load_data(self):
        """Cargar datos desde la base de datos"""
        try:
            logging.info("Cargando datos desde la base de datos...")
            colors = self.get_current_colors()
            
            # Mostrar estado de carga
            self.amount_label.setText("⏳ Cargando...")
            self.clientes_label.setText("--")
            self.empresas_label.setText("--")
            self.buro_label.setText("--")
            
            # Cargar datos principales
            self.clientes_data = get_clients_data()
            self.ventas_data = get_ventas_data()
            self.client_states = get_client_states()
            self.clients_buro = get_clients_without_credit()
            
            logging.info(f"Datos cargados: {len(self.clientes_data)} clientes, "
                        f"{len(self.ventas_data)} ventas, "
                        f"{len(self.client_states)} estados, "
                        f"{len(self.clients_buro)} clientes en buró")
            
            self.data_loaded = True
            self.update_debt_info()
            self.last_update_time = time.time()
            self.refresh_current_view()
                            
        except Exception as e:
            logging.error(f"Error al cargar datos: {e}")
            self.clientes_data = {}
            self.ventas_data = {}
            self.client_states = {}
            self.clients_buro = {}
            self.data_loaded = False
            
            self.amount_label.setText("❌ Error")
            self.clientes_label.setText("Error")
            self.empresas_label.setText("Error")
            self.buro_label.setText("Error")

    def reload_data(self):
        """Recargar todos los datos"""
        try:
            logging.info("Recargando datos...")
            self.load_data()
            
            if self.current_view == "buro":
                self.create_buro_view()
            else:
                self.create_clientes_view()
            
            QMessageBox.information(self, "✅ Éxito", "Datos recargados correctamente")
            
        except Exception as e:
            logging.error(f"Error al recargar datos: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al recargar datos: {str(e)}")

    def refresh_current_view(self):
        """Actualizar la vista actual después de cargar datos"""
        if self.current_view == "buro":
            self.create_buro_view()
        else:
            self.create_clientes_view()

    def update_debt_info(self):
        """Actualizar la información de deuda en el header - formato compacto"""
        try:
            total_clientes, total_empresas, total_buro = self.calculate_totals()
            total_general = total_clientes + total_empresas + total_buro
            
            # Actualizar labels con formato compacto
            self.amount_label.setText(f"${total_general:,.0f}")
            self.clientes_label.setText(f"${total_clientes:,.0f}")
            self.empresas_label.setText(f"${total_empresas:,.0f}")
            self.buro_label.setText(f"${total_buro:,.0f}")
            
        except Exception as e:
            logging.error(f"Error al actualizar información de deuda: {e}")
            self.amount_label.setText("❌ Error")
            self.clientes_label.setText("Error")
            self.empresas_label.setText("Error")
            self.buro_label.setText("Error")

    def clear_layout(self, layout):
        """Limpiar un layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def setup_auto_update(self):
        """Configurar actualización automática"""
        self.update_timer = QTimer()
        self.update_timer.setInterval(300000)  # 5 minutos
        self.update_timer.timeout.connect(self.auto_update)
        self.update_timer.start()

    def auto_update(self):
        """Actualización automática periódica"""
        current_time = time.time()
        if current_time - self.last_update_time >= 300:
            self.load_data()
            self.last_update_time = current_time

    def on_client_double_click(self, table, row):
        """Maneja el doble clic en una celda de cliente"""
        try:
            name_item = table.item(row, 0)
            if name_item:
                client_id = name_item.data(Qt.ItemDataRole.UserRole)
                if client_id and client_id in self.clientes_data:
                    client_data = self.clientes_data[client_id]
                    self.detail_window = ClienteDetalleWindow(self, client_data, client_id)
                    self.detail_window.show()
                else:
                    QMessageBox.warning(self, "⚠️ Error", "No se pudo obtener la información del cliente")
        except Exception as e:
            logging.error(f"Error al abrir detalles del cliente: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al abrir detalles del cliente: {str(e)}")

    def on_buro_client_double_click(self, table, row):
        """Maneja el doble clic en un cliente de buró"""
        try:
            name_item = table.item(row, 1)
            if name_item:
                client_id = name_item.data(Qt.ItemDataRole.UserRole)
                if client_id:
                    if client_id in self.clientes_data:
                        client_data = self.clientes_data[client_id]
                    else:
                        client_data = self.clients_buro[client_id]
                    
                    self.detail_window = ClienteDetalleWindow(self, client_data, client_id)
                    self.detail_window.show()
                else:
                    QMessageBox.warning(self, "⚠️ Error", "No se pudo obtener la información del cliente")
        except Exception as e:
            logging.error(f"Error al abrir detalles del cliente de buró: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al abrir detalles del cliente: {str(e)}")

    def actualizar_app(self):
        """Actualizar la aplicación"""
        if UpdaterDialog is None:
            QMessageBox.warning(self, "⚠️ Error", "Módulo de actualización no disponible")
            return
        
        reply = QMessageBox.question(self, "🔄 Actualizar", 
            "¿Actualizar la aplicación?\nSe cerrará durante el proceso.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            import subprocess
            subprocess.Popen([sys.executable, "updater_pyqt_ssh.py"])
            self.close()
            QApplication.quit()

def main():
    try:
        # Sistema de login con Tkinter
        import tkinter as tk
        login_root = tk.Tk()
        login_root.iconbitmap('lga2.ico')
        splash = LoadingSplash(login_root)
        
        splash.start_progress()
        splash.update_status("Cargando sistema...")
        
        login_root.after(1500, lambda: [
            splash.stop_progress(),
            splash.show_login()
        ])
        
        login_root.mainloop()
        
        if not UserSession.is_logged_in():
            return
        
        login_root.destroy()
        
        # Configurar ID de aplicación para Windows
        try:
            myappid = 'garcia.cobranza.sistema.v1'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            logging.info("ID de aplicación establecido para Windows")
        except Exception as e:
            logging.warning(f"No se pudo establecer ID de aplicación Windows: {e}")
        
        # Crear aplicación PyQt6
        app = QApplication(sys.argv)
        
        # Configurar ícono de la aplicación
        try:
            icon_files = ['lga2.ico', 'lga.ico', 'logo.ico', 'icon.ico']
            app_icon = None
            
            for icon_file in icon_files:
                if os.path.exists(icon_file):
                    file_size = os.path.getsize(icon_file)
                    if file_size > 0:
                        app_icon = QIcon(icon_file)
                        
                        if not app_icon.isNull():
                            app.setWindowIcon(app_icon)
                            QApplication.setWindowIcon(app_icon)
                            
                            app.setApplicationDisplayName("Sistema de Cobranza")
                            app.setApplicationName("Cobranza")
                            app.setApplicationVersion("v2.4")
                            app.setOrganizationName("Garcia")
                            app.setOrganizationDomain("garcia.com")
                            
                            logging.info(f"Ícono establecido correctamente: {icon_file}")
                            break
                        
        except Exception as e:
            logging.error(f"Error al establecer ícono: {e}")
        
        # Crear aplicación principal
        cobranza = CobranzaApp()
        
        if app_icon:
            cobranza.setWindowIcon(app_icon)
            cobranza.app_icon = app_icon
        
        cobranza.show()
        
        # Configuración adicional para Windows
        if sys.platform == "win32":
            try:
                hwnd = int(cobranza.winId())
                
                for icon_file in icon_files:
                    if os.path.exists(icon_file):
                        hicon_small = ctypes.windll.user32.LoadImageW(
                            0, icon_file, 1, 16, 16, 0x00000010 | 0x00000040
                        )
                        
                        hicon_large = ctypes.windll.user32.LoadImageW(
                            0, icon_file, 1, 32, 32, 0x00000010 | 0x00000040
                        )
                        
                        if hicon_small and hicon_large:
                            ctypes.windll.user32.SendMessageW(
                                hwnd, 0x0080, 0, hicon_small
                            )
                            ctypes.windll.user32.SendMessageW(
                                hwnd, 0x0080, 1, hicon_large
                            )
                            
                            logging.info(f"Íconos de barra de tareas establecidos correctamente")
                            break
                
            except Exception as e:
                logging.warning(f"No se pudo configurar ícono de barra de tareas: {e}")
        
        sys.exit(app.exec())
        
    except Exception as e:
        with open("error_log.txt", "w", encoding="utf-8") as f:
            f.write(f"Error al iniciar la aplicación:\n{str(e)}")

if __name__ == "__main__":
    main()