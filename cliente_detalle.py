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

# Importar el theme manager
from theme_manager import ThemeManager

class ModernCard(QFrame):
    """Tarjeta moderna con efectos de glassmorphism que se adapta al tema"""
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
        
        # Crear gradiente de fondo glassmorphism adaptativo
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

class ModernButton(QPushButton):
    """Botón moderno con efectos de glassmorphism que se adapta al tema"""
    def __init__(self, text, theme_manager, parent=None):
        super().__init__(text, parent)
        self.theme_manager = theme_manager
        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Crear gradiente de fondo adaptativo
        gradient = QLinearGradient(0, 0, 0, self.height())
        
        if self.theme_manager.is_dark_theme():
            if self.property("class") == "danger":
                gradient.setColorAt(0, QColor(239, 68, 68, 200))
                gradient.setColorAt(1, QColor(220, 38, 38, 180))
                text_color = QColor(255, 255, 255, 240)
                border_color = QColor(239, 68, 68, 200)
            elif self.isChecked():
                gradient.setColorAt(0, QColor(255, 255, 255, 25))
                gradient.setColorAt(1, QColor(255, 255, 255, 15))
                text_color = QColor(255, 255, 255, 230)
                border_color = QColor(255, 255, 255, 30)
            else:
                gradient.setColorAt(0, QColor(255, 255, 255, 10))
                gradient.setColorAt(1, QColor(255, 255, 255, 5))
                text_color = QColor(255, 255, 255, 180)
                border_color = QColor(255, 255, 255, 30)
        else:
            if self.property("class") == "danger":
                gradient.setColorAt(0, QColor(220, 53, 69, 200))
                gradient.setColorAt(1, QColor(200, 35, 51, 180))
                text_color = QColor(255, 255, 255, 255)
                border_color = QColor(220, 53, 69, 200)
            elif self.isChecked():
                gradient.setColorAt(0, QColor(25, 118, 210, 200))
                gradient.setColorAt(1, QColor(25, 118, 210, 150))
                text_color = QColor(255, 255, 255, 255)
                border_color = QColor(25, 118, 210, 200)
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

class ClienteDetalleWindow(QWidget):
    def __init__(self, parent, client_data, client_id):
        super().__init__()
        self.parent = parent
        self.client_data = client_data
        self.client_id = client_id
        
        # OBTENER THEME MANAGER DEL PADRE
        if hasattr(parent, 'theme_manager'):
            self.theme_manager = parent.theme_manager
        else:
            # Fallback - crear nuevo theme manager
            self.theme_manager = ThemeManager()
        
        # ESTABLECER ÍCONO PARA LA VENTANA DE DETALLES
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
        
        # PRIMERO crear la UI
        self.initUI()
        
        # DESPUÉS cargar las notas (cuando ya existe notes_layout)
        self.load_client_notes()

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
            'SUCCESS_GREEN': theme['SUCCESS_GREEN'],
            'WARNING_ORANGE': theme['WARNING_ORANGE'],
            'DANGER_RED': theme['DANGER_RED'],
            'PROMISE_PURPLE': theme['PROMISE_PURPLE']
        }
        
    def initUI(self):
        """Inicializa la interfaz de usuario con estilo glassmorphism adaptativo"""
        self.setWindowTitle(f"Detalle Cliente - {self.client_data.get('nombre', 'Sin nombre')}")
        
        # Centrar la ventana correctamente
        window_width = 1600
        window_height = 950
        screen = self.screen()
        screen_width = screen.availableGeometry().width()
        screen_height = screen.availableGeometry().height()
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.setGeometry(x, y, window_width, window_height)
        self.setFixedSize(window_width, window_height)
        
        # Aplicar estilo glassmorphism moderno adaptativo
        self.apply_theme_styles()
        
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

    def apply_theme_styles(self):
        """Aplica los estilos según el tema actual"""
        theme = self.theme_manager.get_current_theme()
        colors = self.get_current_colors()
        
        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {theme['gradient_start']}, stop:0.3 {theme['gradient_mid1']}, 
                    stop:0.7 {theme['gradient_mid2']}, stop:1 {theme['gradient_end']});
                color: {colors['TEXT_PRIMARY']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            
            QLabel {{
                background: transparent;
                color: {colors['TEXT_PRIMARY']};
            }}
            
            QLabel.title {{
                font-size: 16px;
                font-weight: bold;
                color: {colors['BRIGHT_CYAN']};
                padding: 10px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            
            QLabel.field-label {{
                font-weight: 600;
                color: {colors['TEXT_SECONDARY']};
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            QLabel.field-value {{
                color: {colors['TEXT_PRIMARY']};
                font-size: 12px;
                font-weight: 500;
                padding: 2px 0;
            }}
            
            QScrollArea {{
                background: {theme['card_bg_alpha']};
                border: 1px solid {theme['border_alpha']};
                border-radius: 12px;
                backdrop-filter: blur(10px);
            }}
            
            QScrollArea QWidget {{
                background: transparent;
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
            
            QTextEdit {{
                background: {theme['card_bg_alpha']};
                border: 1px solid {theme['border_alpha']};
                border-radius: 8px;
                color: {colors['TEXT_PRIMARY']};
                padding: 8px;
                font-size: 11px;
                selection-background-color: {colors['BRIGHT_CYAN']};
            }}
            
            QTextEdit:focus {{
                border: 2px solid {colors['BRIGHT_CYAN']};
                background: {theme['hover_alpha']};
            }}
            
            QLineEdit {{
                background: {theme['card_bg_alpha']};
                border: 1px solid {theme['border_alpha']};
                border-radius: 8px;
                color: {colors['TEXT_PRIMARY']};
                padding: 8px;
                font-size: 11px;
                selection-background-color: {colors['BRIGHT_CYAN']};
            }}
            
            QLineEdit:focus {{
                border: 2px solid {colors['BRIGHT_CYAN']};
                background: {theme['hover_alpha']};
            }}
            
            QComboBox {{
                background: {theme['card_bg_alpha']};
                border: 1px solid {theme['border_alpha']};
                border-radius: 8px;
                color: {colors['TEXT_PRIMARY']};
                padding: 8px;
                font-size: 11px;
            }}
            
            QComboBox:hover {{
                border-color: {colors['BRIGHT_CYAN']};
                background: {theme['hover_alpha']};
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
                border-top: 5px solid {colors['TEXT_PRIMARY']};
            }}
            
            QComboBox QAbstractItemView {{
                background: {theme['CARD_BG']};
                color: {colors['TEXT_PRIMARY']};
                border: 1px solid {theme['border_alpha']};
                border-radius: 8px;
                selection-background-color: {colors['BRIGHT_CYAN']};
                selection-color: white;
            }}
            
            QCalendarWidget {{
                background: {theme['card_bg_alpha']};
                color: {colors['TEXT_PRIMARY']};
                border: 1px solid {theme['border_alpha']};
                border-radius: 8px;
            }}
            
            QCalendarWidget QTableView {{
                background: transparent;
                color: {colors['TEXT_PRIMARY']};
                gridline-color: {theme['border_alpha']};
                selection-background-color: {colors['BRIGHT_CYAN']};
                selection-color: white;
            }}
            
            QCalendarWidget QHeaderView::section {{
                background: {theme['card_bg_alpha']};
                color: {colors['TEXT_PRIMARY']};
                border: 1px solid {theme['border_alpha']};
                padding: 8px;
                font-weight: 600;
            }}
        """)

    def hex_to_rgb(self, hex_color):
        """Convertir color hex a RGB"""
        hex_color = hex_color.lstrip('#')
        return ', '.join(str(int(hex_color[i:i+2], 16)) for i in (0, 2, 4))
        
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
        colors = self.get_current_colors()
        
        cliente_frame = ModernCard(self.theme_manager)
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
                value.setStyleSheet(f"color: {colors['BRIGHT_CYAN']}; font-weight: bold; font-size: 14px;")
            
            info_layout.addWidget(label, row, 0)
            info_layout.addWidget(value, row, 1)
            row += 1
        
        info_widget.setLayout(info_layout)
        cliente_layout.addWidget(info_widget)
        
        cliente_frame.setLayout(cliente_layout)
        layout.addWidget(cliente_frame)
        
    def create_timeline_frame(self, layout):
        """Crea el frame de timeline con scroll usando ModernCard"""
        timeline_frame = ModernCard(self.theme_manager)
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
        
        scroll_area.setWidget(self.notes_widget)
        timeline_layout.addWidget(scroll_area)
        
        timeline_frame.setLayout(timeline_layout)
        layout.addWidget(timeline_frame)
        
    def create_adeudo_frame(self, layout):
        """Crea el frame de adeudos con altura fija y scroll usando ModernCard"""
        colors = self.get_current_colors()
        theme = self.theme_manager.get_current_theme()
        
        adeudo_frame = ModernCard(self.theme_manager)
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
            no_adeudos_label.setStyleSheet(f"color: {colors['TEXT_SECONDARY']}; font-style: italic; padding: 20px;")
            adeudos_layout.addWidget(no_adeudos_label)
        else:
            # Crear lista de adeudos
            total = 0
            for adeudo in adeudos:
                adeudo_row = QFrame()
                adeudo_row.setStyleSheet(f"""
                    QFrame {{
                        background: {theme['card_bg_alpha']};
                        border: 1px solid {theme['border_alpha']};
                        border-radius: 8px;
                        margin: 2px;
                        padding: 8px;
                    }}
                    QFrame:hover {{
                        background: {theme['hover_alpha']};
                        border-color: {colors['BRIGHT_CYAN']};
                    }}
                """)
                row_layout = QHBoxLayout()
                
                # Información del ticket
                ticket_info = QLabel(f"🎫 Ticket #{adeudo['ticket']} - {adeudo['fecha']}")
                ticket_info.setStyleSheet(f"color: {colors['BRIGHT_CYAN']}; text-decoration: underline; cursor: pointer; font-weight: 500;")
                ticket_info.mousePressEvent = lambda event, data=adeudo: self.show_ticket_detail(data)
                
                monto_label = QLabel(f"${adeudo['monto']:,.2f}")
                monto_label.setAlignment(Qt.AlignmentFlag.AlignRight)
                monto_label.setStyleSheet(f"color: {colors['DANGER_RED']}; font-weight: bold;")
                
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
                    background: rgba({self.hex_to_rgb(colors['DANGER_RED'])}, 0.2);
                    border: 2px solid {colors['DANGER_RED']};
                    border-radius: 8px;
                    padding: 10px;
                }}
            """)
            total_layout = QHBoxLayout()
            
            total_label = QLabel("💸 TOTAL ADEUDO:")
            total_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            total_label.setStyleSheet(f"color: {colors['TEXT_PRIMARY']};")
            
            total_amount = QLabel(f"${total:,.2f}")
            total_amount.setStyleSheet(f"color: {colors['DANGER_RED']}; font-weight: bold; font-size: 16px;")
            total_amount.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            total_layout.addWidget(total_label)
            total_layout.addWidget(total_amount)
            
            total_frame.setLayout(total_layout)
            adeudos_layout.addWidget(total_frame)
        
        scroll_area.setWidget(adeudos_widget)
        adeudo_layout.addWidget(scroll_area)
        
        adeudo_frame.setLayout(adeudo_layout)
        layout.addWidget(adeudo_frame)
        
    def create_control_panel(self, parent):
        """Crea el panel de control lateral usando ModernCard"""
        control_card = ModernCard(self.theme_manager)
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
        add_note_btn = ModernButton("📝 Agregar Nota", self.theme_manager)
        add_note_btn.clicked.connect(self.show_note_dialog)
        control_layout.addWidget(add_note_btn)
        
        # Botón agregar teléfono
        add_phone_btn = ModernButton("📞 Teléfono", self.theme_manager)
        add_phone_btn.clicked.connect(self.show_telefono_dialog)
        control_layout.addWidget(add_phone_btn)
        
        # Botones de notas rápidas
        quick_notes = [
            ("🔇 Buzón", "Mandó a buzón de voz"),
            ("❌ No disponible", "El número marcado no está disponible"),
            ("💬 WhatsApp", "Se le notificó vía WhatsApp")
        ]
        
        for btn_text, note_text in quick_notes:
            btn = ModernButton(btn_text, self.theme_manager)
            btn.clicked.connect(lambda checked, text=note_text: self.create_quick_note(text))
            control_layout.addWidget(btn)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background: rgba({self.hex_to_rgb(self.get_current_colors()['TEXT_SECONDARY'])}, 0.5); margin: 10px 0;")
        control_layout.addWidget(separator)
        
        # Botón fecha promesa
        calendar_btn = ModernButton("📅 Fecha Promesa", self.theme_manager)
        calendar_btn.clicked.connect(self.show_calendar_dialog)
        control_layout.addWidget(calendar_btn)
        
# Separador
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet(f"background: rgba({self.hex_to_rgb(self.get_current_colors()['TEXT_SECONDARY'])}, 0.5); margin: 10px 0;")
        control_layout.addWidget(separator2)
        
        # Botón empresa
        self.company_btn = ModernButton("🏢 Estado Empresa", self.theme_manager)
        self.update_company_button()
        self.company_btn.clicked.connect(self.toggle_company)
        control_layout.addWidget(self.company_btn)
        
        # Botón buró
        self.buro_btn = ModernButton("⚠️ Estado Buró", self.theme_manager)
        self.update_buro_button()
        self.buro_btn.clicked.connect(self.toggle_buro)
        control_layout.addWidget(self.buro_btn)
        
        # Separador
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.Shape.HLine)
        separator3.setStyleSheet(f"background: rgba({self.hex_to_rgb(self.get_current_colors()['TEXT_SECONDARY'])}, 0.5); margin: 10px 0;")
        control_layout.addWidget(separator3)
        
        # Botón WhatsApp
        whatsapp_btn = ModernButton("💬 WhatsApp", self.theme_manager)
        whatsapp_btn.clicked.connect(self.abrir_whatsapp)
        control_layout.addWidget(whatsapp_btn)
        
        # Botón llamada
        phone_btn = ModernButton("📞 Llamar", self.theme_manager)
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
            colors = self.get_current_colors()
            theme = self.theme_manager.get_current_theme()
            
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
                no_notes_label.setStyleSheet(f"color: {colors['TEXT_SECONDARY']}; font-style: italic; padding: 30px; font-size: 14px;")
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
                        background: {theme['card_bg_alpha']};
                        border: 1px solid {theme['border_alpha']};
                        border-radius: 10px;
                        margin: 4px;
                        padding: 12px;
                        backdrop-filter: blur(10px);
                    }}
                    QFrame:hover {{
                        background: {theme['hover_alpha']};
                        border-color: {colors['BRIGHT_CYAN']};
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
                header_label.setStyleSheet(f"color: {colors['BRIGHT_CYAN']};")
                
                # Ícono de usuario
                user_icon = QLabel("👤")
                user_icon.setFont(QFont("Segoe UI", 9))
                
                user_label = QLabel(usuario_str)
                user_label.setFont(QFont("Segoe UI", 9))
                user_label.setStyleSheet(f"color: {colors['TEXT_SECONDARY']}; font-style: italic;")
                
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
                    color: {colors['TEXT_PRIMARY']}; 
                    margin-top: 5px; 
                    padding: 8px; 
                    background: {theme['card_bg_alpha']}; 
                    border-radius: 6px;
                    border-left: 3px solid {colors['BRIGHT_CYAN']};
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
    
    def show_note_dialog(self):
        """Muestra el diálogo para agregar una nota con manejo completo de errores"""
        try:
            dialog = NoteDialog(self, self.theme_manager)
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
        dialog = TelefonoDialog(self, self.theme_manager, self.client_data.get('telefono3', ''))
        if dialog.exec() == QDialog.DialogCode.Accepted:
            nuevo_telefono = dialog.get_telefono()
            if nuevo_telefono and update_telefono3(self.client_id, nuevo_telefono):
                # Actualizar datos en memoria
                self.client_data['telefono3'] = format_phone_number(nuevo_telefono)
                
                QMessageBox.information(self, "Éxito", 
                    "Teléfono actualizado correctamente.\nLos cambios se verán al reabrir la ventana de detalles.")
                
                # Crear nota automática
                note_text = f"Teléfono adicional {'actualizado' if self.client_data.get('telefono3') else 'agregado'}: {format_phone_number(nuevo_telefono)}"
                if self.save_note_to_db(self.client_id, note_text):
                    self.load_client_notes()
                
            else:
                QMessageBox.warning(self, "Error", "No se pudo actualizar el teléfono")
                
    def show_calendar_dialog(self):
        """Muestra el diálogo para seleccionar fecha de promesa"""
        dialog = CalendarDialog(self, self.theme_manager)
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
        dialog = TicketDetailDialog(self, self.theme_manager, ticket_data)
        dialog.exec()


# Diálogos auxiliares con estilo glassmorphism adaptativo
class NoteDialog(QDialog):
    def __init__(self, parent, theme_manager):
        super().__init__(parent)
        self.parent = parent
        self.theme_manager = theme_manager
        self.setWindowTitle("Agregar Nota")
        self.setFixedSize(450, 250)
        
        # Centrar respecto al padre
        if parent:
            parent_geo = parent.geometry()
            x = parent_geo.x() + (parent_geo.width() - 450) // 2
            y = parent_geo.y() + (parent_geo.height() - 250) // 2
            self.move(x, y)
        
        self.apply_theme_styles()
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("📝 Agregar nueva nota")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {self.theme_manager.get_current_theme()['BRIGHT_CYAN']};")
        layout.addWidget(title_label)
        
        # Campo de texto
        layout.addWidget(QLabel("Nota:"))
        self.text_edit = QTextEdit()
        self.text_edit.setMaximumHeight(120)
        self.text_edit.setPlaceholderText("Escriba aquí los detalles de la nota...")
        layout.addWidget(self.text_edit)
        
        # Contador de caracteres
        self.char_count = QLabel("0 caracteres")
        self.char_count.setStyleSheet(f"color: {self.theme_manager.get_current_theme()['TEXT_SECONDARY']}; font-size: 10px;")
        layout.addWidget(self.char_count)
        
        # Conectar el contador
        self.text_edit.textChanged.connect(self.update_char_count)
        
        # Botones
        button_layout = QHBoxLayout()
        
        cancel_btn = ModernButton("❌ Cancelar", self.theme_manager)
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = ModernButton("💾 Guardar Nota", self.theme_manager)
        save_btn.clicked.connect(self.accept)
        save_btn.setProperty("class", "danger")
        save_btn.setDefault(True)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Enfocar el campo de texto
        self.text_edit.setFocus()

    def apply_theme_styles(self):
        """Aplica estilos según el tema actual"""
        theme = self.theme_manager.get_current_theme()
        
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {theme['gradient_start']}, stop:0.3 {theme['gradient_mid1']}, 
                    stop:0.7 {theme['gradient_mid2']}, stop:1 {theme['gradient_end']});
                color: {theme['TEXT_PRIMARY']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            
            QLabel {{
                background: transparent;
                color: {theme['TEXT_PRIMARY']};
            }}
            
            QTextEdit {{
                background: {theme['card_bg_alpha']};
                border: 1px solid {theme['border_alpha']};
                border-radius: 8px;
                color: {theme['TEXT_PRIMARY']};
                padding: 8px;
                font-size: 11px;
                selection-background-color: {theme['BRIGHT_CYAN']};
            }}
            
            QTextEdit:focus {{
                border: 2px solid {theme['BRIGHT_CYAN']};
                background: {theme['hover_alpha']};
            }}
        """)
    
    def update_char_count(self):
        count = len(self.text_edit.toPlainText())
        self.char_count.setText(f"{count} caracteres")
        
    def get_note_text(self):
        return self.text_edit.toPlainText().strip()


class TelefonoDialog(QDialog):
    def __init__(self, parent, theme_manager, current_phone=""):
        super().__init__(parent)
        self.parent = parent
        self.theme_manager = theme_manager
        self.setWindowTitle("Agregar/Actualizar Teléfono")
        self.setFixedSize(400, 180)
        
        # Centrar respecto al padre
        if parent:
            parent_geo = parent.geometry()
            x = parent_geo.x() + (parent_geo.width() - 400) // 2
            y = parent_geo.y() + (parent_geo.height() - 180) // 2
            self.move(x, y)
        
        self.apply_theme_styles()
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("📞 Agregar/Actualizar Teléfono")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {self.theme_manager.get_current_theme()['BRIGHT_CYAN']};")
        layout.addWidget(title_label)
        
        if current_phone and current_phone.strip():
            current_label = QLabel(f"Teléfono actual: {current_phone}")
            current_label.setStyleSheet(f"color: {self.theme_manager.get_current_theme()['WARNING_ORANGE']}; font-weight: bold;")
            layout.addWidget(current_label)
        
        layout.addWidget(QLabel("Nuevo teléfono:"))
        self.phone_edit = QLineEdit(current_phone)
        self.phone_edit.setPlaceholderText("Ej: 7551234567")
        layout.addWidget(self.phone_edit)
        
        # Botones
        button_layout = QHBoxLayout()
        
        cancel_btn = ModernButton("❌ Cancelar", self.theme_manager)
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = ModernButton("💾 Guardar", self.theme_manager)
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

    def apply_theme_styles(self):
        """Aplica estilos según el tema actual"""
        theme = self.theme_manager.get_current_theme()
        
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {theme['gradient_start']}, stop:0.3 {theme['gradient_mid1']}, 
                    stop:0.7 {theme['gradient_mid2']}, stop:1 {theme['gradient_end']});
                color: {theme['TEXT_PRIMARY']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            
            QLabel {{
                background: transparent;
                color: {theme['TEXT_PRIMARY']};
            }}
            
            QLineEdit {{
                background: {theme['card_bg_alpha']};
                border: 1px solid {theme['border_alpha']};
                border-radius: 8px;
                color: {theme['TEXT_PRIMARY']};
                padding: 8px;
                font-size: 11px;
                selection-background-color: {theme['BRIGHT_CYAN']};
            }}
            
            QLineEdit:focus {{
                border: 2px solid {theme['BRIGHT_CYAN']};
                background: {theme['hover_alpha']};
            }}
        """)
        
    def get_telefono(self):
        return self.phone_edit.text().strip()


class CalendarDialog(QDialog):
    def __init__(self, parent, theme_manager):
        super().__init__(parent)
        self.parent = parent
        self.theme_manager = theme_manager
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
        
        self.apply_theme_styles()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("📅 Seleccione la fecha de promesa")
        title_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {self.theme_manager.get_current_theme()['BRIGHT_CYAN']};")
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
        
        cancel_btn = ModernButton("❌ Cancelar", self.theme_manager)
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = ModernButton("✅ Guardar", self.theme_manager)
        save_btn.setProperty("class", "danger")
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Establecer foco en el calendario
        self.calendar.setFocus()

    def apply_theme_styles(self):
        """Aplica estilos según el tema actual"""
        theme = self.theme_manager.get_current_theme()
        is_dark = self.theme_manager.is_dark_theme()
        
        # Colores específicos para cada tema
        if is_dark:
            # Modo oscuro
            calendar_bg = theme['card_bg_alpha']
            calendar_border = theme['border_alpha']
            table_bg = "transparent"
            table_alternate_bg = "rgba(255, 255, 255, 0.02)"
            header_bg = theme['card_bg_alpha']
            header_text = theme['TEXT_PRIMARY']
            nav_button_bg = theme['card_bg_alpha']
            nav_button_hover = theme['hover_alpha']
            today_bg = "rgba(0, 180, 216, 0.3)"
            weekend_color = "#ff6b6b"
        else:
            # Modo claro
            calendar_bg = "rgba(255, 255, 255, 0.95)"
            calendar_border = "rgba(0, 0, 0, 0.1)"
            table_bg = "rgba(255, 255, 255, 0.9)"
            table_alternate_bg = "rgba(248, 249, 250, 0.8)"
            header_bg = "rgba(248, 249, 250, 0.9)"
            header_text = "#333333"
            nav_button_bg = "rgba(255, 255, 255, 0.8)"
            nav_button_hover = "rgba(25, 118, 210, 0.1)"
            today_bg = "rgba(25, 118, 210, 0.2)"
            weekend_color = "#d32f2f"
        
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {theme['gradient_start']}, stop:0.3 {theme['gradient_mid1']}, 
                    stop:0.7 {theme['gradient_mid2']}, stop:1 {theme['gradient_end']});
                color: {theme['TEXT_PRIMARY']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            
            QLabel {{
                color: {theme['TEXT_PRIMARY']};
                background-color: transparent;
            }}
            
            QComboBox {{
                background: {theme['card_bg_alpha']};
                color: {theme['TEXT_PRIMARY']};
                border: 1px solid {theme['border_alpha']};
                padding: 8px;
                border-radius: 8px;
                font-size: 11px;
                min-width: 120px;
            }}
            
            QComboBox:hover {{
                border-color: {theme['BRIGHT_CYAN']};
                background: {theme['hover_alpha']};
            }}
            
            QComboBox::drop-down {{
                border: none;
                background: transparent;
                width: 20px;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border: none;
                width: 0px;
                height: 0px;
            }}
            
            QComboBox QAbstractItemView {{
                background: {theme['CARD_BG']};
                color: {theme['TEXT_PRIMARY']};
                border: 1px solid {theme['border_alpha']};
                border-radius: 8px;
                selection-background-color: {theme['BRIGHT_CYAN']};
                selection-color: white;
                outline: none;
            }}
            
            /* Estilos principales del calendario */
            QCalendarWidget {{
                background: {calendar_bg};
                color: {theme['TEXT_PRIMARY']};
                border: 1px solid {calendar_border};
                border-radius: 12px;
                font-size: 11px;
                padding: 5px;
            }}
            
            /* Tabla principal del calendario */
            QCalendarWidget QTableView {{
                background: {table_bg};
                color: {theme['TEXT_PRIMARY']};
                gridline-color: {calendar_border};
                selection-background-color: {theme['BRIGHT_CYAN']};
                selection-color: white;
                border: none;
                outline: none;
            }}
            
            /* Alternancia de filas */
            QCalendarWidget QTableView::item {{
                background: {table_bg};
                color: {theme['TEXT_PRIMARY']};
                border: 1px solid {calendar_border};
                padding: 6px;
            }}
            
            QCalendarWidget QTableView::item:alternate {{
                background: {table_alternate_bg};
            }}
            
            /* Hover en días */
            QCalendarWidget QTableView::item:hover {{
                background: {theme['hover_alpha']};
                border-color: {theme['BRIGHT_CYAN']};
            }}
            
            /* Día seleccionado */
            QCalendarWidget QTableView::item:selected {{
                background: {theme['BRIGHT_CYAN']};
                color: white;
                border-color: {theme['BRIGHT_CYAN']};
                font-weight: bold;
            }}
            
            /* Día actual */
            QCalendarWidget QTableView::item:focus {{
                background: {today_bg};
                color: {theme['TEXT_PRIMARY']};
                border: 2px solid {theme['BRIGHT_CYAN']};
            }}
            
            /* Encabezado del calendario (días de la semana) */
            QCalendarWidget QHeaderView {{
                background: {header_bg};
                color: {header_text};
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 10px;
            }}
            
            QCalendarWidget QHeaderView::section {{
                background: {header_bg};
                color: {header_text};
                border: 1px solid {calendar_border};
                padding: 8px;
                font-weight: 600;
                font-size: 10px;
                text-align: center;
            }}
            
            /* Botones de navegación */
            QCalendarWidget QToolButton {{
                background: {nav_button_bg};
                color: {theme['TEXT_PRIMARY']};
                border: 1px solid {calendar_border};
                border-radius: 6px;
                padding: 4px;
                font-size: 12px;
                font-weight: bold;
            }}
            
            QCalendarWidget QToolButton:hover {{
                background: {nav_button_hover};
                border-color: {theme['BRIGHT_CYAN']};
            }}
            
            QCalendarWidget QToolButton:pressed {{
                background: {theme['BRIGHT_CYAN']};
                color: white;
            }}
            
            /* Menú desplegable del mes/año */
            QCalendarWidget QMenu {{
                background: {theme['CARD_BG']};
                color: {theme['TEXT_PRIMARY']};
                border: 1px solid {calendar_border};
                border-radius: 8px;
            }}
            
            QCalendarWidget QMenu::item {{
                background: transparent;
                color: {theme['TEXT_PRIMARY']};
                padding: 6px 12px;
            }}
            
            QCalendarWidget QMenu::item:selected {{
                background: {theme['BRIGHT_CYAN']};
                color: white;
            }}
            
            /* Separador */
            QFrame[frameShape="4"] {{
                background: {theme['border_alpha']};
                max-height: 1px;
                margin: 10px 0;
            }}
            
            /* Estilos específicos para días del weekend */
            QCalendarWidget QAbstractItemView:disabled {{
                color: {theme['TEXT_SECONDARY']};
            }}
        """)
        
        # Aplicar estilos adicionales programáticamente después de mostrar el widget
        try:
            self.calendar.setStyleSheet(f"""
                QCalendarWidget QWidget {{
                    background: {calendar_bg};
                    color: {theme['TEXT_PRIMARY']};
                }}
                
                QCalendarWidget QWidget#qt_calendar_navigationbar {{
                    background: {header_bg};
                    border-bottom: 1px solid {calendar_border};
                }}
                
                QCalendarWidget QSpinBox {{
                    background: {nav_button_bg};
                    color: {theme['TEXT_PRIMARY']};
                    border: 1px solid {calendar_border};
                    border-radius: 4px;
                    padding: 2px;
                    font-size: 11px;
                }}
                
                QCalendarWidget QSpinBox:hover {{
                    border-color: {theme['BRIGHT_CYAN']};
                }}
            """)
        except Exception as e:
            import logging
            logging.error(f"Error aplicando estilos adicionales al calendario: {e}")
            # Continuar sin fallar si no se pueden aplicar los estilos adicionales
    
    
    def get_selection(self):
        qdate = self.calendar.selectedDate()
        python_date = date(qdate.year(), qdate.month(), qdate.day())
        payment_method = self.payment_combo.currentText()
        return python_date, payment_method


class TicketDetailDialog(QDialog):
    def __init__(self, parent, theme_manager, ticket_data):
        super().__init__(parent)
        self.parent = parent
        self.theme_manager = theme_manager
        self.setWindowTitle(f"🎫 Ticket #{ticket_data['ticket']}")
        self.setFixedSize(450, 600)
        
        self.apply_theme_styles()
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel(f"🎫 Detalles del Ticket #{ticket_data['ticket']}")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {self.theme_manager.get_current_theme()['BRIGHT_CYAN']}; text-align: center;")
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
        colors = self.theme_manager.get_current_theme()
        
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
                line_label.setStyleSheet(f"color: {colors['BRIGHT_CYAN']}; font-weight: bold;")
            elif line.startswith("TICKET:") or line.startswith("CLIENTE:"):
                line_label.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
                line_label.setStyleSheet(f"color: {colors['SUCCESS_GREEN']}; font-weight: bold;")
            elif "CANT" in line and "DESCRIPCION" in line:
                line_label.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
                line_label.setStyleSheet(f"color: {colors['WARNING_ORANGE']}; font-weight: bold;")
            elif "ARTICULOS" in line or "IMPORTE:" in line or "ADEUDA:" in line:
                line_label.setAlignment(Qt.AlignmentFlag.AlignRight)
                line_label.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
                line_label.setStyleSheet(f"color: {colors['DANGER_RED']}; font-weight: bold;")
            elif "DEBO Y PAGARE" in line or "ACEPTO" in line:
                line_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                line_label.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
                line_label.setStyleSheet(f"color: {colors['PROMISE_PURPLE']}; font-weight: bold;")
            else:
                line_label.setStyleSheet(f"color: {colors['TEXT_PRIMARY']};")
            
            content_layout.addWidget(line_label)
        
        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        
        layout.addWidget(scroll_area)
        
        # Botón cerrar
        close_btn = ModernButton("🔒 Cerrar", self.theme_manager)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

    def apply_theme_styles(self):
        """Aplica estilos según el tema actual"""
        theme = self.theme_manager.get_current_theme()
        
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {theme['gradient_start']}, stop:0.3 {theme['gradient_mid1']}, 
                    stop:0.7 {theme['gradient_mid2']}, stop:1 {theme['gradient_end']});
                color: {theme['TEXT_PRIMARY']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            
            QLabel {{
                background: transparent;
                color: {theme['TEXT_PRIMARY']};
            }}
            
            QScrollArea {{
                background: {theme['card_bg_alpha']};
                border: 1px solid {theme['border_alpha']};
                border-radius: 12px;
            }}
            
            QScrollArea QWidget {{
                background: transparent;
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
        """)# cliente_detalle.py
