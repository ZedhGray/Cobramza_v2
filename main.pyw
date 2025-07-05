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

version = "v2.3"

class ModernButton(QPushButton):
    """Botón moderno con efectos de glassmorphism - tamaño optimizado"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(35)  # Más pequeño
        self.setFixedWidth(200)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Crear gradiente de fondo
        gradient = QLinearGradient(0, 0, 0, self.height())
        if self.isChecked():
            gradient.setColorAt(0, QColor(255, 255, 255, 25))
            gradient.setColorAt(1, QColor(255, 255, 255, 15))
        else:
            gradient.setColorAt(0, QColor(255, 255, 255, 10))
            gradient.setColorAt(1, QColor(255, 255, 255, 5))
        
        # Dibujar fondo con bordes redondeados
        painter.setBrush(gradient)
        painter.setPen(QColor(255, 255, 255, 30))
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)  # Bordes más pequeños
        painter.drawPath(path)
        
        # Dibujar texto
        painter.setPen(QColor(255, 255, 255, 230) if self.isChecked() else QColor(255, 255, 255, 180))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))  # Fuente más pequeña
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())

class ModernCard(QFrame):
    """Tarjeta moderna con efectos de glassmorphism"""
    def __init__(self, parent=None):
        super().__init__(parent)
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
        
        # Crear gradiente de fondo glassmorphism
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(255, 255, 255, 30))  # ← Más opaco
        gradient.setColorAt(1, QColor(255, 255, 255, 20))  # ← Más visible
        painter.setPen(QColor(255, 255, 255, 60))          # ← Borde más visible
        
        # Dibujar fondo con bordes redondeados
        painter.setBrush(gradient)
        painter.setPen(QColor(255, 255, 255, 30))  # ← CAMBIAR este valor también
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        painter.drawPath(path)

class CobranzaApp(QWidget):
    def __init__(self):
        super().__init__()
        
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
        
        # Paleta de colores moderna
        self.DARK_BG = "#0a0a0a"          # Fondo principal oscuro
        self.CARD_BG = "#16213e"          # Fondo de tarjetas
        self.ACCENT_BLUE = "#0f3460"      # Azul oscuro para acentos
        self.BRIGHT_CYAN = "#00b4d8"      # Cian brillante
        self.TEXT_PRIMARY = "#ffffff"      # Texto principal
        self.TEXT_SECONDARY = "#a0a0a0"   # Texto secundario
        self.SUCCESS_GREEN = "#4ade80"    # Verde éxito
        self.WARNING_ORANGE = "#fb923c"   # Naranja advertencia
        self.DANGER_RED = "#ef4444"       # Rojo peligro
        self.PROMISE_PURPLE = "#a855f7"   # Morado para promesas
        
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

    def initUI(self):
        self.setWindowTitle(f"Sistema de Cobranza {version}")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Estilo CSS moderno con glassmorphism - tamaños ajustados
        self.setStyleSheet(f"""

            
            QTableWidget {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                selection-background-color: {self.BRIGHT_CYAN};
                color: {self.TEXT_PRIMARY};
                gridline-color: rgba(255, 255, 255, 0.1);
                font-size: 14px;
                font-weight: 500;
                backdrop-filter: blur(10px);
            }}
            
            QTableWidget::item {{
                padding: 8px 6px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                background: transparent;
            }}
            
            QTableWidget::item:selected {{
                background: rgba(0, 180, 216, 0.3);
                color: white;
            }}
            
            QTableWidget::item:hover {{
                background: rgba(255, 255, 255, 0.05);
            }}
            
            QTableWidget QHeaderView::section {{
                background: rgba(255, 255, 255, 0.1);
                color: {self.TEXT_PRIMARY};
                padding: 8px 6px;
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.1);
                border-bottom: 2px solid {self.BRIGHT_CYAN};
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            QScrollBar:vertical {{
                background: rgba(255, 255, 255, 0.05);
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }}
            
            QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: rgba(255, 255, 255, 0.3);
            }}
        """)
        
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

    def create_modern_header(self, layout):
        """Crear header moderno con glassmorphism - tamaños optimizados"""
        header_frame = ModernCard()
        header_frame.setFixedHeight(120)
        header_frame.setContentsMargins(20, 15, 20, 15)
        
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)
        
        # Logo y título - EN FILA (horizontal)
        logo_section = QHBoxLayout()  # ← CAMBIO: QVBoxLayout() por QHBoxLayout()
        logo_section.setSpacing(20)  # ← CAMBIO: spacing de 15 a 20 para separar logo del texto
        
        # Intentar cargar logo
        try:
            logo_label = QLabel()
            pixmap = QPixmap("Logo-Blanco.png")
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(200, 60, Qt.AspectRatioMode.KeepAspectRatio,  # ← CAMBIO: tamaño más grande
                                            Qt.TransformationMode.SmoothTransformation)
                logo_label.setPixmap(scaled_pixmap)
            else:
                raise FileNotFoundError
        except:
            # Fallback si no hay logo
            logo_label = QLabel("GARCIA")
            logo_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
            logo_label.setStyleSheet(f"color: {self.BRIGHT_CYAN}; background: transparent;")
        
        title_label = QLabel("SISTEMA DE COBRANZA")
        title_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {self.TEXT_PRIMARY}; background: transparent;")  # sistema de cobranza
        
        logo_section.addWidget(logo_label)
        logo_section.addWidget(title_label)
        
        header_layout.addLayout(logo_section)
        header_layout.addStretch()
        
        # Panel de estadísticas más compacto
        self.create_compact_stats_panel(header_layout)
        
        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)

    def create_compact_stats_panel(self, layout):
        """Crear panel de estadísticas compacto"""
        stats_container = QWidget()
        stats_container.setFixedWidth(600)
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        # Total general - más compacto
        total_section = QVBoxLayout()
        total_section.setSpacing(2)
        
        total_label = QLabel("💰 Deuda Total")
        total_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        total_label.setStyleSheet(f"color: {self.TEXT_SECONDARY};")
        
        self.amount_label = QLabel("Cargando...")
        self.amount_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.amount_label.setStyleSheet(f"color: {self.BRIGHT_CYAN};")
        
        total_section.addWidget(total_label)
        total_section.addWidget(self.amount_label)
        
        stats_layout.addLayout(total_section)
        
        # Separador vertical
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("background: rgba(255, 255, 255, 0.1); width: 1px;")
        stats_layout.addWidget(separator)
        
        # Desglose horizontal compacto
        breakdown_layout = QHBoxLayout()
        breakdown_layout.setSpacing(20)
        
        # Crear tarjetas compactas
        self.clientes_compact = self.create_compact_stat("👤", "Clientes", "--", self.SUCCESS_GREEN, )
        self.empresas_compact = self.create_compact_stat("🏢", "Empresas", "--", self.WARNING_ORANGE)
        self.buro_compact = self.create_compact_stat("⚠️", "Buró", "--", self.DANGER_RED)
        
        breakdown_layout.addWidget(self.clientes_compact)
        breakdown_layout.addWidget(self.empresas_compact)
        breakdown_layout.addWidget(self.buro_compact)
        
        stats_layout.addLayout(breakdown_layout)
        
        # Botón recargar más pequeño
        reload_button = QPushButton("🔄")
        reload_button.setFont(QFont("Segoe UI", 12))
        reload_button.setFixedSize(30, 30)
        reload_button.setCursor(Qt.CursorShape.PointingHandCursor)
        reload_button.setToolTip("Actualizar Datos")
        reload_button.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0, 180, 216, 0.2);
                color: {self.BRIGHT_CYAN};
                border: 1px solid rgba(0, 180, 216, 0.3);
                border-radius: 15px;
            }}
            QPushButton:hover {{
                background: rgba(0, 180, 216, 0.3);
            }}
        """)
        reload_button.clicked.connect(self.reload_data)
        stats_layout.addWidget(reload_button)
        
        stats_container.setLayout(stats_layout)
        layout.addWidget(stats_container)

    def create_compact_stat(self, icon, label, value, color):
        """Crear tarjeta de estadística compacta"""
        card = QWidget()
        card.setFixedSize(80, 50)
        card.setStyleSheet(f"""
            QWidget {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
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
        text_label.setFont(QFont("Segoe UI", 7, QFont.Weight.Medium))
        text_label.setStyleSheet(f"color: {self.TEXT_SECONDARY};")
        
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
        nav_frame = ModernCard()
        nav_frame.setFixedHeight(55)
        nav_frame.setContentsMargins(20, 8, 20, 8)
        
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(12)
        
        # Botones de navegación más pequeños
        self.clientes_btn = ModernButton("CRÉDITOS PERSONALES")
        self.clientes_btn.setCheckable(True)
        self.clientes_btn.setChecked(True)
        self.clientes_btn.setFixedHeight(35)
        self.clientes_btn.setFixedWidth(200)
        self.clientes_btn.clicked.connect(lambda: self.switch_view("clientes"))
        
        self.empresas_btn = ModernButton("CRÉDITOS EMPRESARIALES")
        self.empresas_btn.setCheckable(True)
        self.empresas_btn.setFixedHeight(35)
        self.empresas_btn.setFixedWidth(220)
        self.empresas_btn.clicked.connect(lambda: self.switch_view("empresas"))
        
        self.buro_btn = ModernButton("BURÓ DE CRÉDITO")
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

    def create_clientes_view(self):
        """Crear vista de clientes modernizada"""
        self.clear_layout(self.main_layout)
        
        # Verificar si los datos están cargados
        if not self.data_loaded or not self.clientes_data:
            loading_container = ModernCard()
            loading_container.setFixedHeight(200)
            loading_layout = QVBoxLayout()
            loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            loading_label = QLabel("⏳ Cargando datos de clientes...")
            loading_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Medium))
            loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            loading_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; margin: 30px;")
            
            loading_layout.addWidget(loading_label)
            loading_container.setLayout(loading_layout)
            self.main_layout.addWidget(loading_container)
            return
        
        # Grid de categorías moderno
        categories_widget = QWidget()
        categories_layout = QGridLayout()
        categories_layout.setSpacing(15)
        
        # Crear las 4 categorías con colores modernos
        self.create_modern_category_table(categories_layout, "PROMESA DE PAGO", self.PROMISE_PURPLE, 0, 0, "🤝")
        self.create_modern_category_table(categories_layout, "MENOS DE 30 DÍAS", self.SUCCESS_GREEN, 0, 1, "✅")
        self.create_modern_category_table(categories_layout, "30 A 60 DÍAS", self.WARNING_ORANGE, 1, 0, "⚠️")
        self.create_modern_category_table(categories_layout, "MÁS DE 60 DÍAS", self.DANGER_RED, 1, 1, "🚨")
        
        categories_widget.setLayout(categories_layout)
        self.main_layout.addWidget(categories_widget)

    def create_modern_category_table(self, layout, title, color, row, col, icon):
        """Crear tabla de categoría moderna - tamaños optimizados"""
        category_card = ModernCard()
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
        
        table.setColumnWidth(1, 100)  # Monto más estrecho
        table.setColumnWidth(2, 85)   # Fecha más estrecha
        table.setColumnWidth(3, 60)   # Días más estrecho
        
        table.setMaximumHeight(250)
        table.setMinimumHeight(180)
        
        # Estilo específico para esta tabla
        table.setStyleSheet(f"""
            QTableWidget {{
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba({self.hex_to_rgb(color)}, 0.2);
                font-size: 9px;
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
                font-size: 8px;
            }}
        """)
        
        # Poblar tabla
        self.populate_category_table(table, title, color)
        
        category_layout.addWidget(table)
        category_card.setLayout(category_layout)
        
        layout.addWidget(category_card, row, col)

    def hex_to_rgb(self, hex_color):
        """Convertir color hex a RGB"""
        hex_color = hex_color.lstrip('#')
        return ', '.join(str(int(hex_color[i:i+2], 16)) for i in (0, 2, 4))

    def create_buro_view(self):
        """Crear vista de buró moderna - optimizada"""
        self.clear_layout(self.main_layout)
        
        # Sincronizar clientes con buró
        try:
            sync_clients_to_buro()
            self.clients_buro = get_clients_without_credit()
        except Exception as e:
            logging.error(f"Error al sincronizar buró: {e}")
        
        # Contenedor principal más compacto
        buro_card = ModernCard()
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
        title_label.setStyleSheet(f"color: {self.DANGER_RED};")
        
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
        count_label.setStyleSheet(f"color: {self.TEXT_SECONDARY};")
        count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        total_label = QLabel(f"${total_buro:,.2f}")
        total_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        total_label.setStyleSheet(f"color: {self.DANGER_RED};")
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
        
        table.setColumnWidth(0, 60)   # ID más estrecho
        table.setColumnWidth(2, 110)  # Saldo más estrecho
        table.setColumnWidth(3, 100)  # Fecha más estrecha
        table.setColumnWidth(4, 100)  # Días más estrecho
        
        # Estilo específico para tabla de buró
        table.setStyleSheet(f"""
            QTableWidget {{
                background: rgba(239, 68, 68, 0.05);
                border: 1px solid rgba(239, 68, 68, 0.2);
                font-size: 9px;
            }}
            QTableWidget::item {{
                padding: 6px 4px;
            }}
            QTableWidget::item:selected {{
                background: rgba(239, 68, 68, 0.3);
            }}
            QTableWidget QHeaderView::section {{
                border-bottom: 2px solid {self.DANGER_RED};
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
                    fecha_str = oldest_date.strftime("%d/%m")  # Formato más corto
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
            name_item.setToolTip(client['nombre'])  # Tooltip con nombre completo
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
        if color == self.PROMISE_PURPLE:
            return "#a855f7"  # Morado transparente
        elif color == self.SUCCESS_GREEN:
            return "#4ade80"  # Verde transparente
        elif color == self.WARNING_ORANGE:
            return "#fb923c"  # Naranja transparente
        elif color == self.DANGER_RED:
            return "#ef4444"  # Rojo transparente
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
                            app.setApplicationVersion("v2.3")
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