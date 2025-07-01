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
                            QGridLayout, QMenuBar, QHeaderView, QFrame)
from PyQt6.QtCore import Qt, QSize, QTimer, QDate, QRect, QEvent
from PyQt6.QtGui import QFont, QColor, QIcon, QAction, QPixmap
from PyQt6.QtSvg import QSvgRenderer

# Importar funciones de database
from database import (get_clients_data, get_ventas_data, get_client_states, 
                     update_client_states, get_clients_without_credit, 
                     sync_clients_to_buro, validate_user, get_client_notes,
                     delete_client_states, update_client_states_wsp, 
                     update_promise_date, update_telefono3, format_phone_number, UserSession)
#
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

version = "v1.0"

class CobranzaApp(QWidget):
    def __init__(self):
        super().__init__()
        
        # ESTABLECER ÍCONO ESPECÍFICAMENTE PARA ESTA VENTANA
        try:
            # Buscar archivos de ícono disponibles
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
        
        # Colores corporativos
        self.COLOR_ROJO = "#E31837"
        self.COLOR_NEGRO = "#333333"
        self.COLOR_BLANCO = "#FFFFFF"
        self.COLOR_GRIS = "#F5F5F5"
        
        # Colores para categorías
        self.COLOR_VERDE = "#4CAF50"
        self.COLOR_AMARILLO = "#FFC107"
        self.COLOR_AZUL = "#87CEEB"
        
        # Variable para controlar vista actual
        self.current_view = "clientes"
        
        # Datos
        self.clientes_data = {}
        self.ventas_data = {}
        self.client_states = {}
        self.clients_buro = {}
        self.last_update_time = time.time()
        
        self.initUI()
        self.load_data()
        self.setup_auto_update()

    def initUI(self):
        self.setWindowTitle(f"Sistema de Cobranza {version}")
        self.setGeometry(100, 100, 1400, 900)
        
        # Estilo CSS
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.COLOR_BLANCO};
                color: {self.COLOR_NEGRO};
                font-family: Arial;
            }}
            
            QTableWidget {{
                background-color: white;
                selection-background-color: {self.COLOR_ROJO};
                color: black;
                gridline-color: #E0E0E0;
                font-size: 11px;
            }}
            
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid #E0E0E0;
            }}
            
            QTableWidget QHeaderView::section {{
                background-color: #F5F5F5;
                color: black;
                padding: 8px;
                border: 1px solid #E0E0E0;
                font-weight: bold;
            }}
            
            QFrame[frameShape="4"] {{
                background-color: {self.COLOR_ROJO};
                border: none;
                max-height: 2px;
            }}
            
            .header-frame {{
                background-color: {self.COLOR_ROJO};
            }}
            
            .tab-button {{
                background-color: {self.COLOR_ROJO};
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }}
            
            .tab-button:checked {{
                background-color: white;
                color: {self.COLOR_NEGRO};
            }}
            
            .tab-button:hover {{
                background-color: #C41E32;
            }}
            
            .category-frame {{
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin: 5px;
                padding: 5px;
            }}
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header con logo
        self.create_header(main_layout)
        
        # Botones de pestañas
        self.create_tab_buttons(main_layout)
        
        # Área principal de contenido
        self.create_main_content(main_layout)
        
        self.setLayout(main_layout)

    def create_header(self, layout):
        """Crear el header con logo y título"""
        header_frame = QFrame()
        header_frame.setStyleSheet(f"background-color: {self.COLOR_ROJO};")
        header_frame.setFixedHeight(140)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # Logo (intentar cargar, si no existe usar texto)
        try:
            logo_label = QLabel()
            pixmap = QPixmap("Logo-Blanco.png")
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(200, 60, Qt.AspectRatioMode.KeepAspectRatio, 
                                            Qt.TransformationMode.SmoothTransformation)
                logo_label.setPixmap(scaled_pixmap)
            else:
                raise FileNotFoundError
        except:
            # Fallback si no hay logo
            logo_label = QLabel("GARCIA")
            logo_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
            logo_label.setStyleSheet("color: white; background-color: transparent;")
        
        header_layout.addWidget(logo_label)
        
        # Título
        title_label = QLabel("SISTEMA DE COBRANZA")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white; background-color: transparent;")
        header_layout.addWidget(title_label)
        
        # Información de deuda total
        self.create_debt_info(header_layout)
        
        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)

    def create_debt_info(self, layout):
        """Crear la información de deuda total en el header"""
        debt_frame = QFrame()
        debt_frame.setStyleSheet("background-color: transparent;")
        debt_layout = QVBoxLayout()
        debt_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Labels de deuda (inicialmente vacíos, se llenarán cuando lleguen los datos)
        total_label = QLabel("Deuda Total:")
        total_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        total_label.setStyleSheet("color: white;")
        debt_layout.addWidget(total_label)

        self.amount_label = QLabel("Cargando...")
        self.amount_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.amount_label.setStyleSheet("color: white;")
        debt_layout.addWidget(self.amount_label)

        # Desglose
        breakdown_layout = QHBoxLayout()
        breakdown_layout.setSpacing(15)

        # Clientes
        self.clientes_label = QLabel("Clientes: --")
        self.clientes_label.setFont(QFont("Arial", 10))
        self.clientes_label.setStyleSheet("color: white;")
        breakdown_layout.addWidget(self.clientes_label)

        # Empresas
        self.empresas_label = QLabel("Empresas: --")
        self.empresas_label.setFont(QFont("Arial", 10))
        self.empresas_label.setStyleSheet("color: white;")
        breakdown_layout.addWidget(self.empresas_label)

        # Buró
        self.buro_label = QLabel("Buró: --")
        self.buro_label.setFont(QFont("Arial", 10))
        self.buro_label.setStyleSheet("color: white;")
        breakdown_layout.addWidget(self.buro_label)
        
        debt_layout.addLayout(breakdown_layout)
        
        # Botón recargar
        reload_button = QPushButton("⟳ Recargar")
        reload_button.setFont(QFont("Arial", 10))
        reload_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: white;
                border: 1px solid white;
                padding: 5px 10px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: rgba(255,255,255,0.2);
            }}
        """)
        reload_button.clicked.connect(self.reload_data)
        debt_layout.addWidget(reload_button)
        
        debt_frame.setLayout(debt_layout)
        layout.addWidget(debt_frame)

    def create_tab_buttons(self, layout):
        """Crear los botones de pestañas"""
        tab_frame = QFrame()
        tab_frame.setStyleSheet(f"background-color: {self.COLOR_ROJO};")
        tab_frame.setFixedHeight(50)
        
        tab_layout = QHBoxLayout()
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(2)
        
        # Botón CREDITOS PERSONALES
        self.clientes_btn = QPushButton("CREDITOS PERSONALES")
        self.clientes_btn.setCheckable(True)
        self.clientes_btn.setChecked(True)
        self.clientes_btn.clicked.connect(lambda: self.switch_view("clientes"))
        
        # Botón CREDITOS EMPRESARIALES
        self.empresas_btn = QPushButton("CREDITOS EMPRESARIALES")
        self.empresas_btn.setCheckable(True)
        self.empresas_btn.clicked.connect(lambda: self.switch_view("empresas"))
        
        # Botón BURO DE CREDITO
        self.buro_btn = QPushButton("BURO DE CREDITO")
        self.buro_btn.setCheckable(True)
        self.buro_btn.clicked.connect(lambda: self.switch_view("buro"))
        
        # Aplicar estilo a todos los botones
        buttons = [self.clientes_btn, self.empresas_btn, self.buro_btn]
        for btn in buttons:
            btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            btn.setFixedHeight(40)
            self.update_button_style(btn)
        
        tab_layout.addWidget(self.clientes_btn)
        tab_layout.addWidget(self.empresas_btn)
        tab_layout.addWidget(self.buro_btn)
        tab_layout.addStretch()
        
        tab_frame.setLayout(tab_layout)
        layout.addWidget(tab_frame)

    def update_button_style(self, button):
        """Actualizar el estilo de los botones de pestaña"""
        if button.isChecked():
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: white;
                    color: {self.COLOR_NEGRO};
                    border: none;
                    padding: 10px 20px;
                    font-weight: bold;
                }}
            """)
        else:
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.COLOR_ROJO};
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #C41E32;
                }}
            """)

    def create_main_content(self, layout):
        """Crear el área principal de contenido"""
        # Frame contenedor principal
        self.main_frame = QFrame()
        self.main_frame.setStyleSheet("background-color: white;")
        
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Crear contenido inicial (CREDITOS PERSONALES)
        self.create_clientes_view()
        
        self.main_frame.setLayout(self.main_layout)
        layout.addWidget(self.main_frame)

    def create_clientes_view(self):
        """Crear la vista de créditos personales/empresariales"""
        # Limpiar layout actual
        self.clear_layout(self.main_layout)
        
        # Título
        title = "CLIENTES PERSONALES" if self.current_view == "clientes" else "CLIENTES EMPRESARIALES"
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(title_label)
        
        # Grid para las 4 categorías
        categories_widget = QWidget()
        categories_layout = QGridLayout()
        categories_layout.setSpacing(10)
        
        # Crear las 4 categorías
        self.create_category_table(categories_layout, "PROMESA DE PAGO", self.COLOR_AZUL, 0, 0)
        self.create_category_table(categories_layout, "MENOS DE 30 DÍAS", self.COLOR_VERDE, 0, 1)
        self.create_category_table(categories_layout, "30 A 60 DÍAS", self.COLOR_AMARILLO, 1, 0)
        self.create_category_table(categories_layout, "MÁS DE 60 DÍAS", self.COLOR_ROJO, 1, 1)
        
        categories_widget.setLayout(categories_layout)
        self.main_layout.addWidget(categories_widget)

    def create_category_table(self, layout, title, color, row, col):
        """Crear una tabla de categoría"""
        # Frame contenedor
        category_frame = QFrame()
        category_frame.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {color};
                border-radius: 8px;
                background-color: white;
            }}
        """)
        
        category_layout = QVBoxLayout()
        category_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header con título y total
        header_layout = QHBoxLayout()
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {color}; border: none;")
        header_layout.addWidget(title_label)
        
        # Calcular total para esta categoría
        total_categoria = self.calculate_category_total(title.lower())
        total_label = QLabel(f"Total: ${total_categoria:,.2f}")
        total_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        total_label.setStyleSheet(f"color: {color}; border: none;")
        header_layout.addWidget(total_label)
        
        category_layout.addLayout(header_layout)
        
        # Tabla
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(['Nombre', 'Monto', 'Fecha', 'Días'])
        
        # Deshabilitar edición de celdas
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Configurar tabla
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Nombre
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)    # Monto
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # Fecha
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)    # Días
        
        table.setColumnWidth(1, 100)  # Monto
        table.setColumnWidth(2, 100)  # Fecha
        table.setColumnWidth(3, 80)   # Días
        
        table.setMaximumHeight(300)
        table.setMinimumHeight(200)
        
        # Poblar tabla con datos
        self.populate_category_table(table, title, color)
        
        category_layout.addWidget(table)
        category_frame.setLayout(category_layout)
        
        layout.addWidget(category_frame, row, col)

    def populate_category_table(self, table, category_title, color):
        """Poblar tabla con datos según la categoría - CON DOBLE CLIC"""
        category_type = self.get_category_from_title(category_title)
        clients_in_category = []
        
        # Filtrar clientes por categoría
        for client_id, client_data in self.clientes_data.items():
            # Verificar si está en buró
            if client_id in self.clients_buro:
                continue
            
            # Verificar si debe mostrarse en la vista actual
            if not self.should_show_client(client_id):
                continue
            
            # Verificar si pertenece a esta categoría
            if self.categorize_client(client_id) == category_type:
                # Obtener fecha de venta más antigua
                oldest_date = self.get_oldest_sale_date(client_id)
                
                if oldest_date:
                    days_diff = (datetime.now().date() - oldest_date).days
                    fecha_str = oldest_date.strftime("%Y-%m-%d")
                else:
                    days_diff = "N/A"
                    fecha_str = "N/A"
                
                clients_in_category.append({
                    'id': client_id,  # AGREGAR ID DEL CLIENTE
                    'nombre': client_data.get('nombre', 'Sin nombre'),
                    'saldo': client_data.get('saldo', 0.0),
                    'fecha': fecha_str,
                    'dias': days_diff
                })
        
        # Ordenar por saldo descendente
        clients_in_category.sort(key=lambda x: x['saldo'], reverse=True)
        
        # Poblar tabla
        table.setRowCount(len(clients_in_category))
        
        # Definir color de selección más oscuro para cada categoría
        if color == self.COLOR_AZUL:
            selection_color = "#B3D9FF"  # Azul más oscuro
        elif color == self.COLOR_VERDE:
            selection_color = "#C8E6C8"  # Verde más oscuro
        elif color == self.COLOR_AMARILLO:
            selection_color = "#FFEB99"  # Amarillo más oscuro
        elif color == self.COLOR_ROJO:
            selection_color = "#FFB3B3"  # Rojo más oscuro
        else:
            selection_color = "#E0E0E0"  # Gris por defecto

        # Aplicar estilo de selección a la tabla
        table.setStyleSheet(f"""
            QTableWidget::item:selected {{
                background-color: {selection_color};
                color: black;
            }}
        """)
        
        for row, client in enumerate(clients_in_category):
            # Nombre
            name_item = QTableWidgetItem(client['nombre'])
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            # GUARDAR EL ID DEL CLIENTE EN EL ITEM
            name_item.setData(Qt.ItemDataRole.UserRole, client['id'])
            table.setItem(row, 0, name_item)
            
            # Monto
            monto_item = QTableWidgetItem(f"${client['saldo']:,.2f}")
            monto_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 1, monto_item)
            
            # Fecha
            fecha_item = QTableWidgetItem(client['fecha'])
            fecha_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 2, fecha_item)
            
            # Días
            dias_str = str(client['dias']) if client['dias'] != "N/A" else "N/A"
            dias_item = QTableWidgetItem(dias_str)
            dias_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 3, dias_item)
            
            # Color de fondo según categoría
            bg_color = self.get_category_background_color(color)
            for col in range(4):
                item = table.item(row, col)
                if item:
                    item.setBackground(QColor(bg_color))
        
        # CONECTAR EL EVENTO DE DOBLE CLIC
        table.cellDoubleClicked.connect(lambda row, col: self.on_client_double_click(table, row))

    def get_category_background_color(self, color):
        """Obtener color de fondo para las celdas según la categoría"""
        if color == self.COLOR_AZUL:
            return "#E6F3FF"  # Azul muy claro
        elif color == self.COLOR_VERDE:
            return "#E8F5E8"  # Verde muy claro
        elif color == self.COLOR_AMARILLO:
            return "#FFF9E6"  # Amarillo muy claro
        elif color == self.COLOR_ROJO:
            return "#FFE6E6"  # Rojo muy claro
        return "#FFFFFF"

    def create_buro_view(self):
        """Crear la vista de buró de crédito - CON DOBLE CLIC"""
        # Limpiar layout actual
        self.clear_layout(self.main_layout)
        
        # Sincronizar clientes con buró antes de mostrar
        try:
            sync_clients_to_buro()
            # Recargar datos de buró
            self.clients_buro = get_clients_without_credit()
        except Exception as e:
            logging.error(f"Error al sincronizar buró: {e}")
        
        # Título
        title_label = QLabel("CLIENTES EN BURÓ DE CRÉDITO")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(title_label)
        
        # Información total
        total_buro = sum(data.get('saldo', 0.0) for data in self.clients_buro.values())
        total_label = QLabel(f"Deuda Total en Buró: ${total_buro:,.2f}")
        total_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        total_label.setStyleSheet(f"color: {self.COLOR_ROJO}; margin: 10px;")
        total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(total_label)
        
        # Tabla de buró
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(['ID', 'Nombre', 'Saldo', 'Última Compra', 'Días en Buró'])
        
        # Deshabilitar edición de celdas
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Aplicar estilo de selección para tabla de buró
        table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #FF9999;
                color: black;
            }
        """)
        
        # Configurar tabla
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)    # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Nombre
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # Saldo
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)    # Fecha
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)    # Días
        
        table.setColumnWidth(0, 80)   # ID
        table.setColumnWidth(2, 120)  # Saldo
        table.setColumnWidth(3, 120)  # Fecha
        table.setColumnWidth(4, 100)  # Días
        
        # Poblar tabla con datos reales
        table.setRowCount(len(self.clients_buro))
        
        row = 0
        for client_id, client_data in self.clients_buro.items():
            # Obtener fecha de venta más antigua
            oldest_date = self.get_oldest_sale_date(client_id)
            
            if oldest_date:
                days_in_buro = (datetime.now().date() - oldest_date).days
                fecha_str = oldest_date.strftime("%Y-%m-%d")
            else:
                days_in_buro = "N/A"
                fecha_str = "N/A"
            
            items = [
                QTableWidgetItem(client_id),
                QTableWidgetItem(client_data.get('nombre', 'Sin nombre')),
                QTableWidgetItem(f"${client_data.get('saldo', 0.0):,.2f}"),
                QTableWidgetItem(fecha_str),
                QTableWidgetItem(f"{days_in_buro} días" if days_in_buro != "N/A" else "N/A")
            ]
            
            for col, item in enumerate(items):
                if col == 1:  # Nombre alineado a la izquierda
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    # GUARDAR ID DEL CLIENTE EN EL ITEM DE NOMBRE
                    item.setData(Qt.ItemDataRole.UserRole, client_id)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setBackground(QColor("#FFB6C1"))  # Rojo claro para buró
                table.setItem(row, col, item)
            
            row += 1
        
        # CONECTAR EVENTO DE DOBLE CLIC PARA BURÓ
        table.cellDoubleClicked.connect(lambda row, col: self.on_buro_client_double_click(table, row))
        
        self.main_layout.addWidget(table)
    
    def on_buro_client_double_click(self, table, row):
        """Maneja el doble clic en un cliente de buró"""
        try:
            # Obtener el item de la columna de nombre (columna 1) que contiene el ID del cliente
            name_item = table.item(row, 1)
            if name_item:
                client_id = name_item.data(Qt.ItemDataRole.UserRole)
                if client_id:
                    # Para clientes de buró, necesitamos obtener los datos completos desde clientes_data
                    if client_id in self.clientes_data:
                        client_data = self.clientes_data[client_id]
                    else:
                        # Si no está en clientes_data, crear datos básicos desde clients_buro
                        client_data = self.clients_buro[client_id]
                    
                    # Crear y mostrar la ventana de detalles
                    self.detail_window = ClienteDetalleWindow(self, client_data, client_id)
                    self.detail_window.show()
                else:
                    QMessageBox.warning(self, "Error", "No se pudo obtener la información del cliente")
        except Exception as e:
            logging.error(f"Error al abrir detalles del cliente de buró: {e}")
            QMessageBox.critical(self, "Error", f"Error al abrir detalles del cliente: {str(e)}")
    
    
    def switch_view(self, view):
        """Cambiar entre vistas"""
        if self.current_view != view:
            self.current_view = view
            
            # Actualizar botones
            self.clientes_btn.setChecked(view == "clientes")
            self.empresas_btn.setChecked(view == "empresas")
            self.buro_btn.setChecked(view == "buro")
            
            for btn in [self.clientes_btn, self.empresas_btn, self.buro_btn]:
                self.update_button_style(btn)
            
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
        else:  # vista buro
            return client_id in self.clients_buro
    
    def categorize_client(self, client_id):
        """Categorizar un cliente basado en su historial y estado"""
        try:
            # Verificar si tiene promesa de pago vigente
            client_state = self.client_states.get(client_id, {})
            promise_date = client_state.get('promiseDate')
            
            if promise_date:
                # Si la promesa es hoy o en el futuro
                if isinstance(promise_date, str):
                    try:
                        promise_date = datetime.strptime(promise_date, "%Y-%m-%d").date()
                    except:
                        promise_date = None
                elif isinstance(promise_date, datetime):
                    promise_date = promise_date.date()
                
                if promise_date and promise_date >= datetime.now().date():
                    return "promesa"
            
            # Obtener la fecha de venta más antigua para este cliente
            oldest_sale_date = self.get_oldest_sale_date(client_id)
            if not oldest_sale_date:
                return "rojo"  # Sin ventas = más crítico
            
            # Calcular días desde la venta más antigua
            days_diff = (datetime.now().date() - oldest_sale_date).days
            
            if days_diff < 30:
                return "verde"
            elif days_diff < 60:
                return "amarillo"
            else:
                return "rojo"
                
        except Exception as e:
            logging.error(f"Error al categorizar cliente {client_id}: {e}")
            return "rojo"  # Default a rojo en caso de error
    
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
        """Calcular totales de deuda para clientes personales, empresariales y buró"""
        total_clientes = 0.0
        total_empresas = 0.0
        total_buro = 0.0
        
        try:
            # Calcular total de buró
            for client_id, data in self.clients_buro.items():
                saldo = data.get('saldo', 0.0)
                if isinstance(saldo, (int, float)):
                    total_buro += saldo
                else:
                    # Intentar convertir si es string
                    try:
                        total_buro += float(saldo)
                    except (ValueError, TypeError):
                        logging.warning(f"Saldo inválido para cliente buró {client_id}: {saldo}")
            
            # Calcular totales de clientes y empresas (excluyendo los que están en buró)
            for client_id, client_data in self.clientes_data.items():
                # Verificar si está en buró primero
                if client_id in self.clients_buro:
                    continue  # Skip si está en buró para evitar doble conteo
                
                saldo = client_data.get('saldo', 0.0)
                
                # Convertir saldo a float si es necesario
                if isinstance(saldo, str):
                    try:
                        saldo = float(saldo)
                    except (ValueError, TypeError):
                        logging.warning(f"Saldo inválido para cliente {client_id}: {saldo}")
                        continue
                elif not isinstance(saldo, (int, float)):
                    logging.warning(f"Tipo de saldo inválido para cliente {client_id}: {type(saldo)}")
                    continue
                
                # Verificar si es empresa
                client_state = self.client_states.get(client_id, {})
                is_company = client_state.get('company', False)
                
                if is_company:
                    total_empresas += saldo
                else:
                    total_clientes += saldo
            
            logging.info(f"Totales calculados - Clientes: {total_clientes}, "
                        f"Empresas: {total_empresas}, Buró: {total_buro}")
            
        except Exception as e:
            logging.error(f"Error al calcular totales: {e}")
            total_clientes = 0.0
            total_empresas = 0.0
            total_buro = 0.0
        
        return total_clientes, total_empresas, total_buro

    def calculate_category_total(self, category):
        """Calcular total para una categoría específica"""
        total = 0.0
        
        for client_id, client_data in self.clientes_data.items():
            # Verificar si está en buró
            if client_id in self.clients_buro:
                continue
            
            # Verificar si debe mostrarse en la vista actual
            if not self.should_show_client(client_id):
                continue
            
            # Verificar si pertenece a esta categoría
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
        return "verde"  # Default

    def load_data(self):
        """Cargar datos desde la base de datos"""
        try:
            logging.info("Cargando datos desde la base de datos...")
            
            # Mostrar estado de carga
            self.amount_label.setText("Cargando...")
            self.clientes_label.setText("Clientes: --")
            self.empresas_label.setText("Empresas: --")
            self.buro_label.setText("Buró: --")
            
            # Cargar datos principales
            self.clientes_data = get_clients_data()
            self.ventas_data = get_ventas_data()
            self.client_states = get_client_states()
            self.clients_buro = get_clients_without_credit()
            
            logging.info(f"Datos cargados: {len(self.clientes_data)} clientes, "
                        f"{len(self.ventas_data)} ventas, "
                        f"{len(self.client_states)} estados, "
                        f"{len(self.clients_buro)} clientes en buró")
            
            # Actualizar información de deuda en el header
            self.update_debt_info()
            
            # Marcar tiempo de última actualización
            self.last_update_time = time.time()
                            
        except Exception as e:
            logging.error(f"Error al cargar datos: {e}")
            # Inicializar con datos vacíos si hay error
            self.clientes_data = {}
            self.ventas_data = {}
            self.client_states = {}
            self.clients_buro = {}
            
            # Mostrar error en el header
            self.amount_label.setText("Error al cargar")
            self.clientes_label.setText("Clientes: Error")
            self.empresas_label.setText("Empresas: Error")
            self.buro_label.setText("Buró: Error")

    def reload_data(self):
        """Recargar todos los datos"""
        try:
            logging.info("Recargando datos...")
            
            # Cargar datos
            self.load_data()
            
            # Actualizar vista actual
            if self.current_view == "buro":
                self.create_buro_view()
            else:
                self.create_clientes_view()
            
            QMessageBox.information(self, "Éxito", "Datos recargados correctamente")
            
        except Exception as e:
            logging.error(f"Error al recargar datos: {e}")
            QMessageBox.critical(self, "Error", f"Error al recargar datos: {str(e)}")
    
    def update_debt_info(self):
        """Actualizar la información de deuda en el header"""
        try:
            # Calcular totales
            total_clientes, total_empresas, total_buro = self.calculate_totals()
            total_general = total_clientes + total_empresas + total_buro
            
            # Actualizar labels con formato de moneda
            self.amount_label.setText(f"${total_general:,.2f}")
            self.clientes_label.setText(f"Clientes: ${total_clientes:,.2f}")
            self.empresas_label.setText(f"Empresas: ${total_empresas:,.2f}")
            self.buro_label.setText(f"Buró: ${total_buro:,.2f}")
            
            logging.info(f"Totales actualizados - General: ${total_general:,.2f}, "
                        f"Clientes: ${total_clientes:,.2f}, "
                        f"Empresas: ${total_empresas:,.2f}, "
                        f"Buró: ${total_buro:,.2f}")
            
        except Exception as e:
            logging.error(f"Error al actualizar información de deuda: {e}")
            self.amount_label.setText("Error")
            self.clientes_label.setText("Clientes: Error")
            self.empresas_label.setText("Empresas: Error")
            self.buro_label.setText("Buró: Error")
    
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
        if current_time - self.last_update_time >= 300:  # 5 minutos
            self.load_data()
            self.last_update_time = current_time
    
    def on_client_double_click(self, table, row):
        """Maneja el doble clic en una celda de cliente"""
        try:
            # Obtener el item de la primera columna (nombre) que contiene el ID del cliente
            name_item = table.item(row, 0)
            if name_item:
                client_id = name_item.data(Qt.ItemDataRole.UserRole)
                if client_id and client_id in self.clientes_data:
                    # Obtener los datos completos del cliente
                    client_data = self.clientes_data[client_id]
                    
                    # Crear y mostrar la ventana de detalles
                    self.detail_window = ClienteDetalleWindow(self, client_data, client_id)
                    self.detail_window.show()
                else:
                    QMessageBox.warning(self, "Error", "No se pudo obtener la información del cliente")
        except Exception as e:
            logging.error(f"Error al abrir detalles del cliente: {e}")
            QMessageBox.critical(self, "Error", f"Error al abrir detalles del cliente: {str(e)}")

def main():
    try:
        # PRIMERO: Crear el sistema de login con Tkinter
        import tkinter as tk
        login_root = tk.Tk()
        login_root.iconbitmap('lga2.ico')  # Ícono para el login también
        splash = LoadingSplash(login_root)
        
        # Simular carga de datos
        splash.start_progress()
        splash.update_status("Cargando sistema...")
        
        # Después de 2 segundos, mostrar el login
        login_root.after(2000, lambda: [
            splash.stop_progress(),
            splash.show_login()
        ])
        
        # Ejecutar el loop del login
        login_root.mainloop()
        
        # Verificar si el usuario se autenticó correctamente
        if not UserSession.is_logged_in():
            return  # Salir si no se autenticó
        
        # Destruir ventana de login
        login_root.destroy()
        
        # SEGUNDO: Crear la aplicación PyQt6
        app = QApplication(sys.argv)
        
        # CONFIGURAR ÍCONO DE LA APLICACIÓN (para toda la app y barra de tareas)
        try:
            # Probar con diferentes formatos por si uno no funciona
            icon_files = ['lga2.ico', 'lga.ico', 'logo.ico', 'icon.ico']
            
            for icon_file in icon_files:
                if os.path.exists(icon_file):
                    app_icon = QIcon(icon_file)
                    
                    # Establecer ícono para TODA la aplicación
                    app.setWindowIcon(app_icon)
                    QApplication.setWindowIcon(app_icon)
                    
                    logging.info(f"Ícono establecido: {icon_file}")
                    break
            else:
                logging.warning("No se encontró ningún archivo de ícono")
                
        except Exception as e:
            logging.error(f"Error al establecer ícono: {e}")
        
        # Crear y mostrar la aplicación principal
        cobranza = CobranzaApp()
        cobranza.show()
        
        sys.exit(app.exec())
        
    except Exception as e:
        with open("error_log.txt", "w", encoding="utf-8") as f:
            f.write(f"Error al iniciar la aplicación:\n{str(e)}")

if __name__ == "__main__":
    main()