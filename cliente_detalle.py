# cliente_detalle.py
import os
import sys
import logging
import webbrowser
import re
from datetime import datetime, date
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QFrame, QScrollArea, QTextEdit, QDialog, 
                            QFormLayout, QLineEdit, QComboBox, QCalendarWidget,
                            QMessageBox, QSplitter, QGridLayout, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QIcon, QPainter, QPainterPath, QLinearGradient

# Importar funciones de database
from database import (get_db_connection, get_client_notes, update_promise_date, 
                     update_telefono3, format_phone_number, UserSession)

class ModernCard(QFrame):
    """Tarjeta moderna con efectos de glassmorphism para cliente detalle"""
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
        gradient.setColorAt(0, QColor(255, 255, 255, 30))
        gradient.setColorAt(1, QColor(255, 255, 255, 20))
        
        # Dibujar fondo con bordes redondeados
        painter.setBrush(gradient)
        painter.setPen(QColor(255, 255, 255, 60))
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        painter.drawPath(path)

class ModernButton(QPushButton):
    """Botón moderno con efectos de glassmorphism"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Crear gradiente de fondo
        gradient = QLinearGradient(0, 0, 0, self.height())
        if self.property("class") == "danger":
            gradient.setColorAt(0, QColor(239, 68, 68, 200))
            gradient.setColorAt(1, QColor(220, 38, 38, 180))
        elif self.isChecked():
            gradient.setColorAt(0, QColor(255, 255, 255, 25))
            gradient.setColorAt(1, QColor(255, 255, 255, 15))
        else:
            gradient.setColorAt(0, QColor(255, 255, 255, 10))
            gradient.setColorAt(1, QColor(255, 255, 255, 5))
        
        # Dibujar fondo con bordes redondeados
        painter.setBrush(gradient)
        painter.setPen(QColor(255, 255, 255, 30))
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        painter.drawPath(path)
        
        # Dibujar texto
        if self.property("class") == "danger":
            painter.setPen(QColor(255, 255, 255, 240))
        else:
            painter.setPen(QColor(255, 255, 255, 230) if self.isChecked() else QColor(255, 255, 255, 180))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())

class ClienteDetalleWindow(QWidget):
    def __init__(self, parent, client_data, client_id):
        super().__init__()
        self.parent = parent
        self.client_data = client_data
        self.client_id = client_id
        
        # ESTABLECER ÍCONO PARA LA VENTANA DE DETALLES TAMBIÉN
        try:
            icon_files = ['lga2.ico', 'lga.ico', 'logo.ico', 'icon.ico']
            
            for icon_file in icon_files:
                if os.path.exists(icon_file):
                    detail_icon = QIcon(icon_file)
                    self.setWindowIcon(detail_icon)
                    logging.info(f"Ícono de ventana de detalles establecido: {icon_file}")
                    break
            else:
                logging.warning("No se encontró archivo de ícono para ventana de detalles")
                
        except Exception as e:
            logging.error(f"Error al establecer ícono de ventana de detalles: {e}")
        
        # Paleta de colores moderna - SIGUIENDO EL ESTILO DE MAIN
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
        
        # PRIMERO crear la UI
        self.initUI()
        
        # DESPUÉS cargar las notas (cuando ya existe notes_layout)
        self.load_client_notes()
        
        # Debug: verificar que notes_layout existe después de crear la UI
        logging.info(f"Al final de __init__, notes_layout existe: {hasattr(self, 'notes_layout')}")
        if hasattr(self, 'notes_layout'):
            logging.info(f"notes_layout es None: {self.notes_layout is None}")
            logging.info(f"notes_layout count: {self.notes_layout.count()}")
        
    def initUI(self):
        """Inicializa la interfaz de usuario con estilo glassmorphism"""
        self.setWindowTitle(f"Detalle Cliente - {self.client_data.get('nombre', 'Sin nombre')}")
        
        # Centrar la ventana correctamente
        window_width = 1600
        window_height = 1000
        screen = self.screen()
        screen_width = screen.availableGeometry().width()
        screen_height = screen.availableGeometry().height()
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.setGeometry(x, y, window_width, window_height)
        self.setFixedSize(window_width, window_height)
        
        # Aplicar estilo glassmorphism moderno - SIGUIENDO MAIN
        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {self.DARK_BG}, stop:0.3 #1a1a2e, 
                    stop:0.7 #16213e, stop:1 {self.DARK_BG});
                color: {self.TEXT_PRIMARY};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            
            QLabel {{
                background: transparent;
                color: {self.TEXT_PRIMARY};
            }}
            
            QLabel.title {{
                font-size: 16px;
                font-weight: bold;
                color: {self.BRIGHT_CYAN};
                padding: 10px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            
            QLabel.field-label {{
                font-weight: 600;
                color: {self.TEXT_SECONDARY};
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            QLabel.field-value {{
                color: {self.TEXT_PRIMARY};
                font-size: 12px;
                font-weight: 500;
                padding: 2px 0;
            }}
            
            QScrollArea {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                backdrop-filter: blur(10px);
            }}
            
            QScrollArea QWidget {{
                background: transparent;
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
            
            QTextEdit {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                color: {self.TEXT_PRIMARY};
                padding: 8px;
                font-size: 11px;
                selection-background-color: {self.BRIGHT_CYAN};
            }}
            
            QLineEdit {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                color: {self.TEXT_PRIMARY};
                padding: 8px;
                font-size: 11px;
                selection-background-color: {self.BRIGHT_CYAN};
            }}
            
            QLineEdit:focus, QTextEdit:focus {{
                border: 2px solid {self.BRIGHT_CYAN};
                background: rgba(255, 255, 255, 0.12);
            }}
            
            QComboBox {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                color: {self.TEXT_PRIMARY};
                padding: 8px;
                font-size: 11px;
            }}
            
            QComboBox:hover {{
                border-color: {self.BRIGHT_CYAN};
                background: rgba(255, 255, 255, 0.12);
            }}
            
            QComboBox::drop-down {{
                border: none;
                background: transparent;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border: none;
                width: 0px;
                height: 0px;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {self.TEXT_PRIMARY};
            }}
            
            QComboBox QAbstractItemView {{
                background: rgba(16, 33, 62, 0.95);
                color: {self.TEXT_PRIMARY};
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                selection-background-color: {self.BRIGHT_CYAN};
                selection-color: white;
            }}
            
            QCalendarWidget {{
                background: rgba(255, 255, 255, 0.08);
                color: {self.TEXT_PRIMARY};
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
            }}
            
            QCalendarWidget QTableView {{
                background: transparent;
                color: {self.TEXT_PRIMARY};
                gridline-color: rgba(255, 255, 255, 0.1);
                selection-background-color: {self.BRIGHT_CYAN};
                selection-color: white;
            }}
            
            QCalendarWidget QHeaderView::section {{
                background: rgba(255, 255, 255, 0.1);
                color: {self.TEXT_PRIMARY};
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 8px;
                font-weight: 600;
            }}
        """)
        
        # Layout principal horizontal
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Splitter para dividir contenido principal y panel lateral
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Área de contenido principal (izquierda)
        self.create_main_content_area(splitter)
        
        # Panel de control lateral (derecha)
        self.create_control_panel(splitter)
        
        # Configurar proporciones del splitter
        splitter.setSizes([1000, 300])
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        
    def create_main_content_area(self, parent):
        """Crea el área principal de contenido"""
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)
        
        # Frame de información del cliente
        self.create_cliente_frame(main_layout)
        
        # Frame de timeline con scroll
        self.create_timeline_frame(main_layout)
        
        # Frame de adeudos
        self.create_adeudo_frame(main_layout)
        
        main_widget.setLayout(main_layout)
        parent.addWidget(main_widget)
        
    def create_cliente_frame(self, layout):
        """Crea el frame con información del cliente usando ModernCard"""
        cliente_frame = ModernCard()
        cliente_frame.setMinimumHeight(280)
        cliente_layout = QVBoxLayout()
        cliente_layout.setContentsMargins(20, 15, 20, 15)

        
        # Título con ícono
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        
        icon_label = QLabel("👤")
        icon_label.setFont(QFont("Segoe UI", 16))
        
        title_label = QLabel("INFORMACIÓN DEL CLIENTE")
        title_label.setProperty("class", "title")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        cliente_layout.addLayout(title_layout)
        
        # Grid para información del cliente
        info_widget = QWidget()
        info_layout = QGridLayout()
        info_layout.setSpacing(15)
        info_layout.setColumnStretch(1, 2)
        
        # Crear campos de información con estilo moderno
        fields = [
            ("Número de Cliente:", str(self.client_id)),
            ("Nombre:", self.client_data.get('nombre', 'N/A')),
            ("Teléfono:", self.client_data.get('telefono1', 'N/A')),
            ("Teléfono Referencia:", self.client_data.get('telefono2', 'N/A')),
            ("Teléfono Adicional:", self.client_data.get('telefono3', 'N/A')),
            ("Dirección:", self.client_data.get('direccion', 'N/A')),
            ("Saldo:", f"${self.client_data.get('saldo', 0):,.2f}"),
            ("Crédito:", "Sí" if self.client_data.get('credito') else "No"),
            ("Estado:", self.client_data.get('estado', 'ACTIVO'))
        ]
        
        row = 0
        for label_text, value_text in fields:
            label = QLabel(label_text)
            label.setProperty("class", "field-label")
            label.setMinimumWidth(150)
            
            value = QLabel(str(value_text))
            value.setProperty("class", "field-value")
            value.setWordWrap(True)
            value.setMinimumHeight(25)
            
            # Color especial para el saldo
            if "Saldo:" in label_text:
                value.setStyleSheet(f"color: {self.BRIGHT_CYAN}; font-weight: bold; font-size: 14px;")
            
            info_layout.addWidget(label, row, 0)
            info_layout.addWidget(value, row, 1)
            row += 1
        
        info_widget.setLayout(info_layout)
        cliente_layout.addWidget(info_widget)
        
        cliente_frame.setLayout(cliente_layout)
        layout.addWidget(cliente_frame)
        
    def create_timeline_frame(self, layout):
        """Crea el frame de timeline con scroll usando ModernCard"""
        timeline_frame = ModernCard()
        timeline_layout = QVBoxLayout()
        timeline_layout.setContentsMargins(20, 15, 20, 15)
        timeline_layout.setSpacing(15)
        
        # Título con ícono
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        
        icon_label = QLabel("📋")
        icon_label.setFont(QFont("Segoe UI", 16))
        
        title_label = QLabel("LÍNEA DE TIEMPO")
        title_label.setProperty("class", "title")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        timeline_layout.addLayout(title_layout)
        
        # Área de scroll para las notas
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(300)
        scroll_area.setMaximumHeight(400)
        
        # Widget contenedor para las notas - ESTE ES EL IMPORTANTE
        self.notes_widget = QWidget()
        self.notes_layout = QVBoxLayout()  # AQUÍ SE CREA notes_layout
        self.notes_widget.setLayout(self.notes_layout)
        
        # Verificar que se creó correctamente
        logging.info(f"notes_layout creado: {self.notes_layout}")
        logging.info(f"notes_widget creado: {self.notes_widget}")
        
        scroll_area.setWidget(self.notes_widget)
        timeline_layout.addWidget(scroll_area)
        
        timeline_frame.setLayout(timeline_layout)
        layout.addWidget(timeline_frame)
        
    def create_adeudo_frame(self, layout):
        """Crea el frame de adeudos con altura fija y scroll usando ModernCard"""
        adeudo_frame = ModernCard()
        adeudo_layout = QVBoxLayout()
        adeudo_layout.setContentsMargins(20, 15, 20, 15)
        adeudo_layout.setSpacing(15)
        
        # Título con ícono
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        
        icon_label = QLabel("💰")
        icon_label.setFont(QFont("Segoe UI", 16))
        
        title_label = QLabel("ADEUDOS")
        title_label.setProperty("class", "title")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        adeudo_layout.addLayout(title_layout)
        
        # Área de scroll con altura fija para adeudos
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedHeight(200)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Widget contenedor para los adeudos
        adeudos_widget = QWidget()
        adeudos_layout = QVBoxLayout()
        adeudos_widget.setLayout(adeudos_layout)
        
        # Obtener y mostrar adeudos
        adeudos = self.get_adeudos_from_db()
        
        if not adeudos:
            no_adeudos_label = QLabel("📝 No hay adeudos registrados")
            no_adeudos_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_adeudos_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-style: italic; padding: 20px;")
            adeudos_layout.addWidget(no_adeudos_label)
        else:
            # Crear lista de adeudos
            total = 0
            for adeudo in adeudos:
                adeudo_row = QFrame()
                adeudo_row.setStyleSheet(f"""
                    QFrame {{
                        background: rgba(255, 255, 255, 0.05);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        border-radius: 8px;
                        margin: 2px;
                        padding: 8px;
                    }}
                    QFrame:hover {{
                        background: rgba(255, 255, 255, 0.08);
                        border-color: {self.BRIGHT_CYAN};
                    }}
                """)
                row_layout = QHBoxLayout()
                
                # Información del ticket
                ticket_info = QLabel(f"🎫 Ticket #{adeudo['ticket']} - {adeudo['fecha']}")
                ticket_info.setStyleSheet(f"color: {self.BRIGHT_CYAN}; text-decoration: underline; cursor: pointer; font-weight: 500;")
                ticket_info.mousePressEvent = lambda event, data=adeudo: self.show_ticket_detail(data)
                
                monto_label = QLabel(f"${adeudo['monto']:,.2f}")
                monto_label.setAlignment(Qt.AlignmentFlag.AlignRight)
                monto_label.setStyleSheet(f"color: {self.DANGER_RED}; font-weight: bold;")
                
                row_layout.addWidget(ticket_info)
                row_layout.addWidget(monto_label)
                
                adeudo_row.setLayout(row_layout)
                adeudos_layout.addWidget(adeudo_row)
                
                total += adeudo['monto']
            
            # Espaciador para empujar el total hacia abajo
            adeudos_layout.addStretch()
            
            # Total al final
            total_frame = QFrame()
            total_frame.setStyleSheet(f"""
                QFrame {{
                    background: rgba({self.hex_to_rgb(self.DANGER_RED)}, 0.2);
                    border: 2px solid {self.DANGER_RED};
                    border-radius: 8px;
                    padding: 10px;
                }}
            """)
            total_layout = QHBoxLayout()
            
            total_label = QLabel("💸 TOTAL ADEUDO:")
            total_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            total_label.setStyleSheet(f"color: {self.TEXT_PRIMARY};")
            
            total_amount = QLabel(f"${total:,.2f}")
            total_amount.setStyleSheet(f"color: {self.DANGER_RED}; font-weight: bold; font-size: 16px;")
            total_amount.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            total_layout.addWidget(total_label)
            total_layout.addWidget(total_amount)
            
            total_frame.setLayout(total_layout)
            adeudos_layout.addWidget(total_frame)
        
        scroll_area.setWidget(adeudos_widget)
        adeudo_layout.addWidget(scroll_area)
        
        adeudo_frame.setLayout(adeudo_layout)
        layout.addWidget(adeudo_frame)

    def hex_to_rgb(self, hex_color):
        """Convertir color hex a RGB"""
        hex_color = hex_color.lstrip('#')
        return ', '.join(str(int(hex_color[i:i+2], 16)) for i in (0, 2, 4))
        
    def create_control_panel(self, parent):
        """Crea el panel de control lateral usando ModernCard"""
        control_card = ModernCard()
        control_card.setFixedWidth(320)
        control_layout = QVBoxLayout()
        control_layout.setContentsMargins(20, 15, 20, 15)
        control_layout.setSpacing(12)
        
        # Título del panel con ícono
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        
        icon_label = QLabel("🎛️")
        icon_label.setFont(QFont("Segoe UI", 16))
        
        title_label = QLabel("CONTROLES")
        title_label.setProperty("class", "title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        control_layout.addLayout(title_layout)
        
        # Botón agregar nota
        add_note_btn = ModernButton("📝 Agregar Nota")
        add_note_btn.clicked.connect(self.show_note_dialog)
        control_layout.addWidget(add_note_btn)
        
        # Botón agregar teléfono
        add_phone_btn = ModernButton("📞 Teléfono")
        add_phone_btn.clicked.connect(self.show_telefono_dialog)
        control_layout.addWidget(add_phone_btn)
        
        # Botones de notas rápidas
        quick_notes = [
            ("🔇 Buzón", "Mandó a buzón de voz"),
            ("❌ No disponible", "El número marcado no está disponible"),
            ("💬 WhatsApp", "Se le notificó vía WhatsApp")
        ]
        
        for btn_text, note_text in quick_notes:
            btn = ModernButton(btn_text)
            btn.clicked.connect(lambda checked, text=note_text: self.create_quick_note(text))
            control_layout.addWidget(btn)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background: rgba(255, 255, 255, 0.2); margin: 10px 0;")
        control_layout.addWidget(separator)
        
        # Botón fecha promesa
        calendar_btn = ModernButton("📅 Fecha Promesa")
        calendar_btn.clicked.connect(self.show_calendar_dialog)
        control_layout.addWidget(calendar_btn)
        
        # Separador
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet("background: rgba(255, 255, 255, 0.2); margin: 10px 0;")
        control_layout.addWidget(separator2)
        
        # Botón empresa
        self.company_btn = ModernButton("🏢 Estado Empresa")
        self.update_company_button()
        self.company_btn.clicked.connect(self.toggle_company)
        control_layout.addWidget(self.company_btn)
        
        # Botón buró
        self.buro_btn = ModernButton("⚠️ Estado Buró")
        self.update_buro_button()
        self.buro_btn.clicked.connect(self.toggle_buro)
        control_layout.addWidget(self.buro_btn)
        
        # Separador
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.Shape.HLine)
        separator3.setStyleSheet("background: rgba(255, 255, 255, 0.2); margin: 10px 0;")
        control_layout.addWidget(separator3)
        
        # Botón WhatsApp
        whatsapp_btn = ModernButton("💬 WhatsApp")
        whatsapp_btn.clicked.connect(self.abrir_whatsapp)
        control_layout.addWidget(whatsapp_btn)
        
        # Botón llamada
        phone_btn = ModernButton("📞 Llamar")
        phone_btn.clicked.connect(self.realizar_llamada)
        control_layout.addWidget(phone_btn)
        
        # Espaciador
        control_layout.addStretch()
        
        control_card.setLayout(control_layout)
        parent.addWidget(control_card)
    
    def load_client_notes(self):
        """Carga las notas del cliente - VERSIÓN ULTRA SIMPLE"""
        try:
            logging.info(f"=== CARGANDO NOTAS PARA CLIENTE: {self.client_id} ===")
            
            # Consulta directa a la base de datos
            conn = get_db_connection()
            if not conn:
                logging.error("No se pudo conectar a la base de datos")
                return
            
            cursor = conn.cursor()
            query = """
                SELECT note_text, created_at, ISNULL(user_name, 'Sistema') as user_name
                FROM Notes
                WHERE client_id = ?
                ORDER BY created_at DESC
            """
            
            cursor.execute(query, (self.client_id,))
            rows = cursor.fetchall()
            conn.close()
            
            logging.info(f"ENCONTRADAS {len(rows)} NOTAS EN LA BASE DE DATOS")
            
            # Limpiar el layout de notas
            while self.notes_layout.count():
                child = self.notes_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            # Si no hay notas, mostrar mensaje
            if not rows:
                no_notes_label = QLabel("📝 No hay notas para este cliente")
                no_notes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_notes_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-style: italic; padding: 30px; font-size: 14px;")
                self.notes_layout.addWidget(no_notes_label)
                logging.info("No hay notas - mostrando mensaje")
                return
            
            # Agregar cada nota con estilo glassmorphism
            for i, row in enumerate(rows):
                logging.info(f"Agregando nota {i+1}: {row[0][:30]}...")
                
                # Frame para la nota con estilo moderno
                note_frame = QFrame()
                note_frame.setStyleSheet(f"""
                    QFrame {{
                        background: rgba(255, 255, 255, 0.08);
                        border: 1px solid rgba(255, 255, 255, 0.15);
                        border-radius: 10px;
                        margin: 4px;
                        padding: 12px;
                        backdrop-filter: blur(10px);
                    }}
                    QFrame:hover {{
                        background: rgba(255, 255, 255, 0.12);
                        border-color: {self.BRIGHT_CYAN};
                    }}
                """)
                
                note_layout = QVBoxLayout()
                note_layout.setSpacing(8)
                
                # Header con fecha y usuario
                header_layout = QHBoxLayout()
                header_layout.setSpacing(10)
                
                # Fecha y usuario
                fecha_str = row[1].strftime('%d/%m/%Y %H:%M') if row[1] else 'Sin fecha'
                usuario_str = row[2] if row[2] else 'Sistema'
                
                # Ícono de fecha
                date_icon = QLabel("📅")
                date_icon.setFont(QFont("Segoe UI", 10))
                
                header_label = QLabel(f"{fecha_str}")
                header_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                header_label.setStyleSheet(f"color: {self.BRIGHT_CYAN};")
                
                # Ícono de usuario
                user_icon = QLabel("👤")
                user_icon.setFont(QFont("Segoe UI", 9))
                
                user_label = QLabel(usuario_str)
                user_label.setFont(QFont("Segoe UI", 9))
                user_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-style: italic;")
                
                header_layout.addWidget(date_icon)
                header_layout.addWidget(header_label)
                header_layout.addStretch()
                header_layout.addWidget(user_icon)
                header_layout.addWidget(user_label)
                
                # Texto de la nota
                text_label = QLabel(row[0])
                text_label.setWordWrap(True)
                text_label.setFont(QFont("Segoe UI", 11))
                text_label.setStyleSheet(f"""
                    color: {self.TEXT_PRIMARY}; 
                    margin-top: 5px; 
                    padding: 8px; 
                    background: rgba(255, 255, 255, 0.05); 
                    border-radius: 6px;
                    border-left: 3px solid {self.BRIGHT_CYAN};
                """)
                
                note_layout.addLayout(header_layout)
                note_layout.addWidget(text_label)
                note_frame.setLayout(note_layout)
                
                self.notes_layout.addWidget(note_frame)
                logging.info(f"Nota {i+1} agregada al layout")
            
            # Espaciador al final
            self.notes_layout.addStretch()
            
            logging.info(f"=== CARGA COMPLETADA: {len(rows)} NOTAS MOSTRADAS ===")
            
        except Exception as e:
            logging.error(f"ERROR EN load_client_notes: {e}")
            import traceback
            logging.error(traceback.format_exc())
        
    def create_timeline_frame_if_missing(self):
        """Crea el componente de timeline si no existe"""
        if not hasattr(self, 'notes_widget') or not hasattr(self, 'notes_layout'):
            logging.warning("Recreando componente de timeline que faltaba")
            
            # Buscar el frame de timeline en el layout principal
            main_widget = self.findChild(QWidget)
            if main_widget:
                layout = main_widget.layout()
                if layout and layout.count() >= 2:
                    # Asumir que timeline es el segundo item
                    self.create_timeline_frame(layout)
        
    def refresh_notes_display(self, notes):
        """Actualiza la visualización de las notas - VERSIÓN MEJORADA"""
        try:
            logging.info(f"refresh_notes_display llamada con {len(notes)} notas")
            
            # Verificación doble de notes_layout
            if not hasattr(self, 'notes_layout') or not self.notes_layout:
                logging.error("notes_layout no existe en refresh_notes_display")
                return
            
            # Limpiar notas existentes de forma segura
            while self.notes_layout.count():
                child = self.notes_layout.takeAt(0)
                if child and child.widget():
                    widget = child.widget()
                    widget.setParent(None)
                    widget.deleteLater()
            
            # Verificar que tenemos notas para mostrar
            if not notes:
                # Mostrar mensaje de "no hay notas"
                no_notes_label = QLabel("📝 No hay notas registradas para este cliente")
                no_notes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_notes_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-style: italic; padding: 30px; font-size: 14px;")
                self.notes_layout.addWidget(no_notes_label)
                self.notes_layout.addStretch()
                return
            
            # Agregar nuevas notas
            for idx, note in enumerate(notes):
                try:
                    logging.info(f"Agregando nota {idx}: {note.get('text', 'Sin texto')[:50]}...")
                    
                    note_frame = QFrame()
                    note_frame.setStyleSheet(f"""
                        QFrame {{
                            background: rgba(255, 255, 255, 0.08);
                            border: 1px solid rgba(255, 255, 255, 0.15);
                            border-radius: 10px;
                            margin: 4px;
                            padding: 12px;
                            backdrop-filter: blur(10px);
                        }}
                        QFrame:hover {{
                            background: rgba(255, 255, 255, 0.12);
                            border-color: {self.BRIGHT_CYAN};
                        }}
                    """)
                    
                    note_layout = QVBoxLayout()
                    note_layout.setContentsMargins(8, 8, 8, 8)
                    note_layout.setSpacing(8)
                    
                    # Header con fecha y usuario
                    header_layout = QHBoxLayout()
                    
                    # Formatear timestamp
                    timestamp = note.get('timestamp', datetime.now())
                    if isinstance(timestamp, datetime):
                        timestamp_str = timestamp.strftime('%d/%m/%Y %H:%M')
                    else:
                        timestamp_str = str(timestamp)
                    
                    date_label = QLabel(f"📅 {timestamp_str}")
                    date_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                    date_label.setStyleSheet(f"color: {self.BRIGHT_CYAN};")
                    
                    user_label = QLabel(f"👤 {note.get('user_name', 'Sistema')}")
                    user_label.setFont(QFont("Segoe UI", 9))
                    user_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-style: italic;")
                    
                    header_layout.addWidget(date_label)
                    header_layout.addStretch()
                    header_layout.addWidget(user_label)
                    
                    # Texto de la nota
                    text_label = QLabel(note.get('text', 'Sin texto'))
                    text_label.setWordWrap(True)
                    text_label.setFont(QFont("Segoe UI", 11))
                    text_label.setStyleSheet(f"""
                        color: {self.TEXT_PRIMARY}; 
                        margin-top: 5px; 
                        padding: 8px; 
                        background: rgba(255, 255, 255, 0.05); 
                        border-radius: 6px;
                        border-left: 3px solid {self.BRIGHT_CYAN};
                    """)
                    
                    note_layout.addLayout(header_layout)
                    note_layout.addWidget(text_label)
                    
                    note_frame.setLayout(note_layout)
                    self.notes_layout.addWidget(note_frame)
                    
                    logging.info(f"Nota {idx} agregada correctamente")
                    
                except Exception as e:
                    logging.error(f"Error agregando nota {idx}: {e}")
                    continue
            
            # Agregar espaciador al final
            self.notes_layout.addStretch()
            
            # Forzar actualización visual
            if hasattr(self, 'notes_widget'):
                self.notes_widget.updateGeometry()
                self.notes_widget.update()
            
            logging.info("refresh_notes_display completado exitosamente")
                
        except Exception as e:
            logging.error(f"Error en refresh_notes_display: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")

    def show_note_dialog(self):
        """Muestra el diálogo para agregar una nota con manejo completo de errores"""
        try:
            dialog = NoteDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                note_text = dialog.get_note_text()
                if not note_text or not note_text.strip():
                    QMessageBox.warning(self, "Advertencia", "Por favor ingrese una nota válida")
                    return
                        
                # Guardar la nota
                if self.save_note_to_db(self.client_id, note_text.strip()):
                    # Recargar notas después de guardar
                    self.load_client_notes()
                    QMessageBox.information(self, "Éxito", "Nota guardada correctamente")
                else:
                    QMessageBox.warning(self, "Error", "No se pudo guardar la nota")
                    
        except Exception as e:
            logging.error(f"Error en diálogo de nota: {e}")
            QMessageBox.critical(self, "Error", f"Error inesperado: {str(e)}")
    
    def create_quick_note(self, note_text):
        """Crea una nota rápida - VERSIÓN MEJORADA"""
        try:
            if not note_text or not note_text.strip():
                logging.warning("Intento de crear nota rápida vacía")
                return
                
            if self.save_note_to_db(self.client_id, note_text.strip()):
                self.load_client_notes()
                logging.info(f"Nota rápida creada: {note_text[:50]}...")
            else:
                QMessageBox.warning(self, "Error", "No se pudo guardar la nota rápida")
                
        except Exception as e:
            logging.error(f"Error en nota rápida: {e}")
            QMessageBox.critical(self, "Error", f"Error inesperado: {str(e)}")
        
    def show_telefono_dialog(self):
        """Muestra el diálogo para agregar/actualizar teléfono"""
        dialog = TelefonoDialog(self, self.client_data.get('telefono3', ''))
        if dialog.exec() == QDialog.DialogCode.Accepted:
            nuevo_telefono = dialog.get_telefono()
            if nuevo_telefono and update_telefono3(self.client_id, nuevo_telefono):
                # Actualizar datos en memoria
                self.client_data['telefono3'] = format_phone_number(nuevo_telefono)
                
                # En lugar de recrear el frame, simplemente informar al usuario
                # que el cambio se verá al reabrir la ventana
                QMessageBox.information(self, "Éxito", 
                    "Teléfono actualizado correctamente.\nLos cambios se verán al reabrir la ventana de detalles.")
                
                # Crear nota automática
                note_text = f"Teléfono adicional {'actualizado' if self.client_data.get('telefono3') else 'agregado'}: {format_phone_number(nuevo_telefono)}"
                if self.save_note_to_db(self.client_id, note_text):
                    self.load_client_notes()
                
            else:
                QMessageBox.warning(self, "Error", "No se pudo actualizar el teléfono")
    
    def recreate_cliente_frame(self):
        """Recrear el frame del cliente para mostrar los cambios"""
        try:
            # Buscar el layout principal y recrear el frame del cliente
            main_widget = None
            splitter = self.layout().itemAt(0).widget()
            
            if splitter and hasattr(splitter, 'widget'):
                main_widget = splitter.widget(0)
            
            if main_widget and hasattr(main_widget, 'layout'):
                main_layout = main_widget.layout()
                
                # Remover el frame del cliente existente (primer item)
                if main_layout and main_layout.count() > 0:
                    old_widget = main_layout.itemAt(0)
                    if old_widget and old_widget.widget():
                        widget_to_remove = old_widget.widget()
                        widget_to_remove.setParent(None)
                        widget_to_remove.deleteLater()
                
                # Recrear el frame del cliente al inicio del layout
                self.create_cliente_frame(main_layout)
                
        except Exception as e:
            logging.error(f"Error en recreate_cliente_frame: {e}")
            # Si hay error, mostrar mensaje pero no crashear
            QMessageBox.information(self, "Información", "Información del cliente actualizada (requiere reabrir ventana para ver cambios)")
                
    def show_calendar_dialog(self):
        """Muestra el diálogo para seleccionar fecha de promesa"""
        dialog = CalendarDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_date, payment_method = dialog.get_selection()
            if update_promise_date(self.client_id, selected_date):
                note_text = f"Promesa de pago generada para el día {selected_date.strftime('%d/%m/%Y')}. Método de pago: {payment_method}"
                if self.save_note_to_db(self.client_id, note_text):
                    self.load_client_notes()
                QMessageBox.information(self, "Éxito", "Fecha de promesa guardada correctamente")
            else:
                QMessageBox.warning(self, "Error", "No se pudo guardar la fecha de promesa")
            
    def abrir_whatsapp(self):
        """Abre WhatsApp con el número del cliente"""
        telefono = self.client_data.get('telefono1', '')
        numero_limpio = self.limpiar_numero(telefono)
        url = f"https://wa.me/{numero_limpio}"
        webbrowser.open(url)
        
    def realizar_llamada(self):
        """Realiza una llamada (abre la app de teléfono)"""
        telefono = self.client_data.get('telefono1', '')
        numero_limpio = self.limpiar_numero(telefono)
        
        try:
            url = f"tel://{numero_limpio}"
            webbrowser.open(url)
            self.create_quick_note(f"Se inició llamada al número {telefono}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo realizar la llamada: {str(e)}")
            
    def limpiar_numero(self, telefono):
        """Limpia el número de teléfono"""
        numero_limpio = re.sub(r'\D', '', telefono)
        if not numero_limpio.startswith('52'):
            if numero_limpio.startswith('0'):
                numero_limpio = numero_limpio[1:]
            numero_limpio = '52' + numero_limpio
        return numero_limpio
        
    def update_company_button(self):
        """Actualiza el botón de empresa"""
        is_company = self.get_company_state(self.client_id)
        if is_company:
            self.company_btn.setText("🏢 No es empresa")
            self.company_btn.setProperty("class", "danger")
        else:
            self.company_btn.setText("🏢 Empresa")
            self.company_btn.setProperty("class", "")
        self.company_btn.style().polish(self.company_btn)
        
    def update_buro_button(self):
        """Actualiza el botón de buró"""
        is_buro = self.get_buro_state(self.client_id)
        if is_buro:
            self.buro_btn.setText("⚠️ En Buró")
            self.buro_btn.setProperty("class", "danger")
        else:
            self.buro_btn.setText("⚠️ Buró")
            self.buro_btn.setProperty("class", "")
        self.buro_btn.style().polish(self.buro_btn)
        
    def toggle_company(self):
        """Alterna el estado de empresa"""
        conn = get_db_connection()
        if not conn:
            return
            
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT company FROM dbo.ClientsStates WHERE client_id = ?", (self.client_id,))
            current_state = cursor.fetchone()
            
            if current_state is not None:
                new_state = not bool(current_state.company)
                cursor.execute("""
                    UPDATE dbo.ClientsStates 
                    SET company = ?
                    WHERE client_id = ?
                """, (new_state, self.client_id))
                conn.commit()
                self.update_company_button()
                
                # Crear nota automática
                status_text = "empresa" if new_state else "cliente personal"
                note_text = f"Cliente marcado como {status_text}"
                if self.save_note_to_db(self.client_id, note_text):
                    self.load_client_notes()
                    
        except Exception as e:
            logging.error(f"Error al actualizar estado de empresa: {e}")
        finally:
            conn.close()
            
    def toggle_buro(self):
        """Alterna el estado de buró"""
        conn = get_db_connection()
        if not conn:
            return
            
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT credit FROM dbo.ClientsBuro WHERE client_id = ?", (self.client_id,))
            current_state = cursor.fetchone()
            
            if current_state is not None:
                new_state = not bool(current_state.credit)
                cursor.execute("""
                    UPDATE dbo.ClientsBuro 
                    SET credit = ?
                    WHERE client_id = ?
                """, (new_state, self.client_id))
                conn.commit()
                self.update_buro_button()
                
                # Crear nota automática
                status_text = "agregado al buró de crédito" if new_state else "removido del buró de crédito"
                note_text = f"Cliente {status_text}"
                if self.save_note_to_db(self.client_id, note_text):
                    self.load_client_notes()
                    
        except Exception as e:
            logging.error(f"Error al actualizar estado de buró: {e}")
        finally:
            conn.close()
    
    # Métodos de base de datos (simplificados)
    def get_company_state(self, client_id):
        """Obtiene el estado de empresa"""
        try:
            conn = get_db_connection()
            if not conn:
                return False
            cursor = conn.cursor()
            cursor.execute("SELECT company FROM dbo.ClientsStates WHERE client_id = ?", (client_id,))
            result = cursor.fetchone()
            return bool(result.company) if result else False
        except:
            return False
        finally:
            if conn:
                conn.close()
                
    def get_buro_state(self, client_id):
        """Obtiene el estado de buró"""
        try:
            conn = get_db_connection()
            if not conn:
                return False
            cursor = conn.cursor()
            cursor.execute("SELECT credit FROM dbo.ClientsBuro WHERE client_id = ?", (client_id,))
            result = cursor.fetchone()
            return bool(result.credit) if result else False
        except:
            return False
        finally:
            if conn:
                conn.close()
            
    def ensure_notes_table_exists(self):
        """Asegura que la tabla Notes exista, la crea si es necesario"""
        conn = get_db_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            
            # Verificar si la tabla existe
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'Notes'
            """)
            table_exists = cursor.fetchone()[0] > 0
            
            if not table_exists:
                # Crear la tabla
                create_table_query = """
                CREATE TABLE Notes (
                    id int IDENTITY(1,1) PRIMARY KEY,
                    client_id varchar(50) NOT NULL,
                    note_text nvarchar(max) NOT NULL,
                    user_name varchar(100) NULL,
                    created_at datetime DEFAULT GETDATE()
                )
                """
                cursor.execute(create_table_query)
                
                # Crear índices
                cursor.execute("CREATE INDEX IX_Notes_ClientId ON Notes(client_id)")
                cursor.execute("CREATE INDEX IX_Notes_CreatedAt ON Notes(created_at DESC)")
                
                conn.commit()
                logging.info("Tabla Notes creada exitosamente")
                return True
            else:
                return True
                
        except Exception as e:
            logging.error(f"Error creando tabla Notes: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def save_note_to_db(self, client_id, note_text):
        """Guarda una nota en la base de datos directamente"""
        # Asegurar que la tabla existe
        if not self.ensure_notes_table_exists():
            logging.error("No se pudo crear/verificar la tabla Notes")
            return False
            
        conn = get_db_connection()
        if not conn:
            logging.error("No se pudo conectar a la base de datos")
            return False
            
        try:
            cursor = conn.cursor()
            
            # Obtener el usuario actual desde UserSession
            try:
                current_user = UserSession.get_user()
                user_name = current_user if current_user else "Sistema"
            except Exception as e:
                logging.warning(f"Error obteniendo usuario: {e}")
                user_name = "Sistema"
            
            # Insertar la nota directamente
            query = """
                INSERT INTO Notes (client_id, note_text, user_name, created_at)
                VALUES (?, ?, ?, GETDATE())
            """
            cursor.execute(query, (client_id, note_text, user_name))
            conn.commit()
            
            logging.info(f"Nota guardada exitosamente para cliente {client_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error al guardar nota: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
            
    def get_adeudos_from_db(self):
        """Obtiene los adeudos del cliente"""
        conn = get_db_connection()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor()
            query = """
                SELECT 
                    Folio as ticket,
                    Fecha,
                    Restante as monto,
                    Ticket as datos
                FROM Ventas
                WHERE Estado != 'PAGADA'
                AND Estado != 'CANCELADA'
                AND Estado IS NOT NULL
                AND Restante > 0
                AND CveCte = ?
            """
            cursor.execute(query, (self.client_id,))
            results = cursor.fetchall()
            
            adeudos = []
            for row in results:
                adeudo = {
                    'ticket': row.ticket,
                    'fecha': row.Fecha.strftime('%Y-%m-%d') if row.Fecha else '',
                    'monto': float(row.monto),
                    'datos': row.datos
                }
                adeudos.append(adeudo)
            
            return adeudos
        except Exception as e:
            logging.error(f"Error al obtener adeudos: {e}")
            return []
        finally:
            conn.close()
            
    def show_ticket_detail(self, ticket_data):
        """Muestra los detalles del ticket"""
        dialog = TicketDetailDialog(self, ticket_data)
        dialog.exec()


# Diálogos auxiliares con estilo glassmorphism
class NoteDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Agregar Nota")
        self.setFixedSize(450, 250)
        
        # Centrar respecto al padre
        if parent:
            parent_geo = parent.geometry()
            x = parent_geo.x() + (parent_geo.width() - 450) // 2
            y = parent_geo.y() + (parent_geo.height() - 250) // 2
            self.move(x, y)
        
        # Aplicar estilo glassmorphism
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0a0a0a, stop:0.3 #1a1a2e, 
                    stop:0.7 #16213e, stop:1 #0a0a0a);
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            
            QLabel {{
                background: transparent;
                color: #ffffff;
            }}
            
            QTextEdit {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                color: #ffffff;
                padding: 8px;
                font-size: 11px;
                selection-background-color: #00b4d8;
            }}
            
            QTextEdit:focus {{
                border: 2px solid #00b4d8;
                background: rgba(255, 255, 255, 0.12);
            }}
            
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
            }}
            
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.15);
                border-color: #00b4d8;
            }}
            
            QPushButton[class="danger"] {{
                background: rgba(239, 68, 68, 0.8);
                border-color: #ef4444;
            }}
            
            QPushButton[class="danger"]:hover {{
                background: rgba(239, 68, 68, 0.9);
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("📝 Agregar nueva nota")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #00b4d8;")
        layout.addWidget(title_label)
        
        # Campo de texto
        layout.addWidget(QLabel("Nota:"))
        self.text_edit = QTextEdit()
        self.text_edit.setMaximumHeight(120)
        self.text_edit.setPlaceholderText("Escriba aquí los detalles de la nota...")
        layout.addWidget(self.text_edit)
        
        # Contador de caracteres
        self.char_count = QLabel("0 caracteres")
        self.char_count.setStyleSheet("color: #a0a0a0; font-size: 10px;")
        layout.addWidget(self.char_count)
        
        # Conectar el contador
        self.text_edit.textChanged.connect(self.update_char_count)
        
        # Botones
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("💾 Guardar Nota")
        save_btn.clicked.connect(self.accept)
        save_btn.setProperty("class", "danger")
        save_btn.setDefault(True)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Enfocar el campo de texto
        self.text_edit.setFocus()
    
    def update_char_count(self):
        count = len(self.text_edit.toPlainText())
        self.char_count.setText(f"{count} caracteres")
        
    def get_note_text(self):
        return self.text_edit.toPlainText().strip()


class TelefonoDialog(QDialog):
    def __init__(self, parent, current_phone=""):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Agregar/Actualizar Teléfono")
        self.setFixedSize(400, 180)
        
        # Centrar respecto al padre
        if parent:
            parent_geo = parent.geometry()
            x = parent_geo.x() + (parent_geo.width() - 400) // 2
            y = parent_geo.y() + (parent_geo.height() - 180) // 2
            self.move(x, y)
        
        # Aplicar estilo glassmorphism
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0a0a0a, stop:0.3 #1a1a2e, 
                    stop:0.7 #16213e, stop:1 #0a0a0a);
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            
            QLabel {{
                background: transparent;
                color: #ffffff;
            }}
            
            QLineEdit {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                color: #ffffff;
                padding: 8px;
                font-size: 11px;
                selection-background-color: #00b4d8;
            }}
            
            QLineEdit:focus {{
                border: 2px solid #00b4d8;
                background: rgba(255, 255, 255, 0.12);
            }}
            
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
            }}
            
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.15);
                border-color: #00b4d8;
            }}
            
            QPushButton[class="danger"] {{
                background: rgba(239, 68, 68, 0.8);
                border-color: #ef4444;
            }}
            
            QPushButton[class="danger"]:hover {{
                background: rgba(239, 68, 68, 0.9);
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("📞 Agregar/Actualizar Teléfono")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #00b4d8;")
        layout.addWidget(title_label)
        
        if current_phone and current_phone.strip():
            current_label = QLabel(f"Teléfono actual: {current_phone}")
            current_label.setStyleSheet("color: #fb923c; font-weight: bold;")
            layout.addWidget(current_label)
        
        layout.addWidget(QLabel("Nuevo teléfono:"))
        self.phone_edit = QLineEdit(current_phone)
        self.phone_edit.setPlaceholderText("Ej: 7551234567")
        layout.addWidget(self.phone_edit)
        
        # Botones
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("💾 Guardar")
        save_btn.clicked.connect(self.accept)
        save_btn.setProperty("class", "danger")
        save_btn.setDefault(True)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Seleccionar todo el texto al abrir
        self.phone_edit.selectAll()
        self.phone_edit.setFocus()
        
    def get_telefono(self):
        return self.phone_edit.text().strip()


class TicketDetailDialog(QDialog):
    def __init__(self, parent, ticket_data):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle(f"🎫 Ticket #{ticket_data['ticket']}")
        self.setFixedSize(450, 600)
        
        # Aplicar estilo glassmorphism
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0a0a0a, stop:0.3 #1a1a2e, 
                    stop:0.7 #16213e, stop:1 #0a0a0a);
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            
            QLabel {{
                background: transparent;
                color: #ffffff;
            }}
            
            QScrollArea {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }}
            
            QScrollArea QWidget {{
                background: transparent;
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
            
            QPushButton {{
                background: rgba(239, 68, 68, 0.8);
                color: #ffffff;
                border: 1px solid #ef4444;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
            }}
            
            QPushButton:hover {{
                background: rgba(239, 68, 68, 0.9);
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel(f"🎫 Detalles del Ticket #{ticket_data['ticket']}")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #00b4d8; text-align: center;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Área de scroll para el contenido del ticket
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Widget contenedor
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(5)
        
        # Procesar y mostrar el contenido del ticket
        lines = ticket_data['datos'].split('\r\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Crear etiqueta para cada línea
            line_label = QLabel(line)
            line_label.setFont(QFont("Courier New", 9))
            line_label.setWordWrap(True)
            line_label.setStyleSheet("background: transparent;")
            
            # Estilos especiales para diferentes tipos de líneas
            if "GARCIA RINES" in line:
                line_label.setFont(QFont("Courier New", 11, QFont.Weight.Bold))
                line_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                line_label.setStyleSheet("color: #00b4d8; font-weight: bold;")
            elif line.startswith("TICKET:") or line.startswith("CLIENTE:"):
                line_label.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
                line_label.setStyleSheet("color: #4ade80; font-weight: bold;")
            elif "CANT" in line and "DESCRIPCION" in line:
                line_label.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
                line_label.setStyleSheet("color: #fb923c; font-weight: bold;")
            elif "ARTICULOS" in line or "IMPORTE:" in line or "ADEUDA:" in line:
                line_label.setAlignment(Qt.AlignmentFlag.AlignRight)
                line_label.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
                line_label.setStyleSheet("color: #ef4444; font-weight: bold;")
            elif "DEBO Y PAGARE" in line or "ACEPTO" in line:
                line_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                line_label.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
                line_label.setStyleSheet("color: #a855f7; font-weight: bold;")
            else:
                line_label.setStyleSheet("color: #ffffff;")
            
            content_layout.addWidget(line_label)
        
        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        
        layout.addWidget(scroll_area)
        
        # Botón cerrar
        close_btn = QPushButton("🔒 Cerrar")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

class CalendarDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("📅 Seleccionar Fecha de Promesa")
        self.setFixedSize(400, 480)
        
        # ESTABLECER ÍCONO PARA EL DIÁLOGO TAMBIÉN
        try:
            icon_files = ['lga2.ico', 'lga.ico', 'logo.ico', 'icon.ico']
            for icon_file in icon_files:
                if os.path.exists(icon_file):
                    self.setWindowIcon(QIcon(icon_file))
                    break
        except Exception as e:
            logging.error(f"Error al establecer ícono de diálogo: {e}")
        
        # Centrar respecto al padre
        if parent:
            parent_geo = parent.geometry()
            x = parent_geo.x() + (parent_geo.width() - 400) // 2
            y = parent_geo.y() + (parent_geo.height() - 480) // 2
            self.move(x, y)
        
        # APLICAR ESTILO GLASSMORPHISM
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0a0a0a, stop:0.3 #1a1a2e, 
                    stop:0.7 #16213e, stop:1 #0a0a0a);
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            
            QLabel {{
                color: #ffffff;
                background-color: transparent;
            }}
            
            QComboBox {{
                background: rgba(255, 255, 255, 0.08);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.2);
                padding: 8px;
                border-radius: 8px;
                font-size: 11px;
            }}
            
            QComboBox:hover {{
                border-color: #00b4d8;
                background: rgba(255, 255, 255, 0.12);
            }}
            
            QComboBox::drop-down {{
                border: none;
                background: transparent;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border: none;
                width: 0px;
                height: 0px;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
            }}
            
            QComboBox QAbstractItemView {{
                background: rgba(16, 33, 62, 0.95);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                selection-background-color: #00b4d8;
                selection-color: white;
            }}
            
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.2);
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 11px;
            }}
            
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.15);
                border-color: #00b4d8;
            }}
            
            QPushButton[class="danger"] {{
                background: rgba(239, 68, 68, 0.8);
                color: white;
                border-color: #ef4444;
            }}
            
            QPushButton[class="danger"]:hover {{
                background: rgba(239, 68, 68, 0.9);
            }}
            
            QCalendarWidget {{
                background: rgba(255, 255, 255, 0.08);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                selection-background-color: #00b4d8;
            }}
            
            QCalendarWidget QWidget#qt_calendar_navigationbar {{
                background: rgba(255, 255, 255, 0.1);
                color: #ffffff;
            }}
            
            QCalendarWidget QToolButton {{
                background: rgba(255, 255, 255, 0.1);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.2);
                padding: 6px;
                margin: 2px;
                border-radius: 6px;
                font-weight: bold;
            }}
            
            QCalendarWidget QToolButton:hover {{
                background: rgba(0, 180, 216, 0.8);
                color: white;
                border-color: #00b4d8;
            }}
            
            QCalendarWidget QSpinBox {{
                background: rgba(255, 255, 255, 0.08);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.2);
                padding: 4px;
                border-radius: 4px;
            }}
            
            QCalendarWidget QTableView {{
                background: transparent;
                color: #ffffff;
                gridline-color: rgba(255, 255, 255, 0.1);
                selection-background-color: #00b4d8;
                selection-color: white;
            }}
            
            QCalendarWidget QHeaderView::section {{
                background: rgba(255, 255, 255, 0.1);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 8px;
                font-weight: 600;
                font-size: 10px;
            }}
            
            QCalendarWidget QAbstractItemView::item {{
                color: #ffffff;
                background: transparent;
                padding: 8px;
            }}
            
            QCalendarWidget QAbstractItemView::item:hover {{
                background: rgba(0, 180, 216, 0.3);
                color: #ffffff;
            }}
            
            QCalendarWidget QAbstractItemView::item:selected {{
                background: #00b4d8;
                color: white;
                font-weight: bold;
            }}
            
            QCalendarWidget QAbstractItemView::item:disabled {{
                color: #666666;
                background: rgba(255, 255, 255, 0.05);
            }}
            
            QFrame[frameShape="4"] {{
                background: rgba(255, 255, 255, 0.2);
                max-height: 1px;
                margin: 10px 0;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("📅 Seleccione la fecha de promesa")
        title_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #00b4d8;")
        layout.addWidget(title_label)
        
        # Calendario
        self.calendar = QCalendarWidget()
        self.calendar.setMinimumDate(QDate.currentDate())
        self.calendar.setMinimumSize(350, 280)
        layout.addWidget(self.calendar)
        
        # Separador visual
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(separator)
        
        # Método de pago
        payment_frame = QFrame()
        payment_layout = QHBoxLayout()
        payment_layout.setSpacing(10)
        
        payment_label = QLabel("💳 Método de pago:")
        payment_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        payment_layout.addWidget(payment_label)
        
        self.payment_combo = QComboBox()
        self.payment_combo.addItems([
            "No especificado", "Efectivo", "Tarjeta", 
            "Transferencia", "Cheque"
        ])
        payment_layout.addWidget(self.payment_combo)
        
        payment_frame.setLayout(payment_layout)
        layout.addWidget(payment_frame)
        
        # Botones
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("✅ Guardar")
        save_btn.setProperty("class", "danger")
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Establecer foco en el calendario
        self.calendar.setFocus()
    
    def get_selection(self):
        qdate = self.calendar.selectedDate()
        python_date = date(qdate.year(), qdate.month(), qdate.day())
        payment_method = self.payment_combo.currentText()
        return python_date, payment_method