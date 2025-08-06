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
                     update_promise_date, update_telefono3, format_phone_number, UserSession, get_all_clients_data,
                    get_all_ventas_data, 
                    get_all_clients_credit_scores,
                    get_credit_statistics,
                    get_clients_by_credit_level,
                    calculate_client_credit_score,
                    get_credit_level)

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

class CreditDetailWindow(QDialog):
    """Ventana de detalle del historial crediticio de un cliente"""
    
    def __init__(self, parent, client_credit_data, client_id):
        super().__init__(parent)
        self.parent = parent
        self.client_credit_data = client_credit_data
        self.client_id = client_id
        self.theme_manager = parent.theme_manager
        
        # CALCULAR TOTAL GASTADO
        self.total_spent = self.calculate_total_spent()
        
        self.setWindowTitle(f"Historial Crediticio - {client_credit_data['client_data'].get('nombre', 'Cliente')}")
        self.setGeometry(200, 200, 850, 650)  # Un poco más ancho para acomodar la nueva info
        self.setModal(True)
        
        self.init_ui()
        self.apply_theme()
    
    def calculate_total_spent(self):
        """Calcular el total gastado por el cliente en la tienda"""
        total_spent = 0.0
        
        try:
            transactions = self.client_credit_data.get('transaction_details', [])
            
            for transaction in transactions:
                # Buscar en los datos del ticket como en TicketDetailDialog
                ticket_data = transaction.get('datos', '')
                
                if ticket_data:
                    # Procesar el contenido del ticket línea por línea
                    lines = ticket_data.split('\r\n')
                    
                    for line in lines:
                        line = line.strip()
                        
                        # Buscar líneas que contengan "IMPORTE:" 
                        if "IMPORTE:" in line:
                            try:
                                # Extraer el monto después de "IMPORTE:"
                                # Ejemplo: "IMPORTE: $1,234.56"
                                importe_part = line.split("IMPORTE:")[-1].strip()
                                # Limpiar el texto para obtener solo el número
                                importe_clean = importe_part.replace('$', '').replace(',', '').strip()
                                
                                # Convertir a float
                                monto = float(importe_clean)
                                total_spent += monto
                                break  # Solo tomar el primer IMPORTE encontrado en este ticket
                                
                            except (ValueError, IndexError):
                                # Si no se puede extraer el monto de esta línea, continuar
                                continue
                
                # Si no encontramos datos en 'datos', intentar con los campos originales como fallback
                else:
                    monto = transaction.get('monto', 0) or transaction.get('importe', 0) or transaction.get('total', 0)
                    
                    if isinstance(monto, (int, float)):
                        total_spent += monto
                    elif isinstance(monto, str):
                        try:
                            total_spent += float(monto.replace(',', '').replace('$', ''))
                        except (ValueError, AttributeError):
                            continue
            
            # Si aún no encontramos montos, buscar en ventas_data como último recurso
            if total_spent == 0 and hasattr(self.parent, 'all_ventas_data'):
                for venta_id, venta_data in self.parent.all_ventas_data.items():
                    if venta_data.get('cveCte') == self.client_id:
                        monto = venta_data.get('importe', 0) or venta_data.get('total', 0)
                        if isinstance(monto, (int, float)):
                            total_spent += monto
                        elif isinstance(monto, str):
                            try:
                                total_spent += float(monto.replace(',', '').replace('$', ''))
                            except (ValueError, AttributeError):
                                continue
            
        except Exception as e:
            import logging
            logging.error(f"Error calculando total gastado para cliente {self.client_id}: {e}")
            total_spent = 0.0
        
        return total_spent

    def extract_amount_from_ticket_data(self, ticket_data):
        """Extraer el monto de los datos del ticket (método auxiliar)"""
        if not ticket_data:
            return 0.0
        
        try:
            lines = ticket_data.split('\r\n')
            
            for line in lines:
                line = line.strip()
                
                # Buscar líneas que contengan "IMPORTE:" 
                if "IMPORTE:" in line:
                    try:
                        # Extraer el monto después de "IMPORTE:"
                        importe_part = line.split("IMPORTE:")[-1].strip()
                        # Limpiar el texto para obtener solo el número
                        importe_clean = importe_part.replace('$', '').replace(',', '').strip()
                        
                        # Convertir a float
                        return float(importe_clean)
                        
                    except (ValueError, IndexError):
                        continue
        except Exception:
            pass
        
        return 0.0
    
    
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header con información del cliente
        self.create_client_header(layout)
        
        # Información del puntaje Y TOTAL GASTADO
        self.create_score_info(layout)
        
        # Tabla de transacciones
        self.create_transactions_table(layout)
        
        # Botones
        self.create_buttons(layout)
        
        self.setLayout(layout)
    
    def create_client_header(self, layout):
        """Crear header con información del cliente"""
        colors = self.parent.get_current_colors()
        
        header_frame = ModernCard(self.theme_manager)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(15, 15, 15, 15)
        
        # Información del cliente
        client_info = QVBoxLayout()
        
        name_label = QLabel(self.client_credit_data['client_data'].get('nombre', 'Sin nombre'))
        name_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {colors['TEXT_PRIMARY']};")
        
        id_label = QLabel(f"ID: {self.client_id}")
        id_label.setFont(QFont("Segoe UI", 10))
        id_label.setStyleSheet(f"color: {colors['TEXT_SECONDARY']};")
        
        client_info.addWidget(name_label)
        client_info.addWidget(id_label)
        
        header_layout.addLayout(client_info)
        header_layout.addStretch()
        
        # AGREGAR TOTAL GASTADO EN EL HEADER
        spent_section = QVBoxLayout()
        spent_section.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        spent_label = QLabel("💰 Total Gastado")
        spent_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        spent_label.setStyleSheet(f"color: {colors['TEXT_SECONDARY']};")
        spent_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        spent_amount = QLabel(f"${self.total_spent:,.2f}")
        spent_amount.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        spent_amount.setStyleSheet(f"color: {colors['SUCCESS_GREEN']};")
        spent_amount.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        spent_section.addWidget(spent_label)
        spent_section.addWidget(spent_amount)
        
        header_layout.addLayout(spent_section)
        
        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)
    
    def create_score_info(self, layout):
        """Crear información del puntaje crediticio con estadísticas extendidas"""
        colors = self.parent.get_current_colors()
        
        score_frame = ModernCard(self.theme_manager)
        score_layout = QHBoxLayout()
        score_layout.setContentsMargins(15, 15, 15, 15)
        score_layout.setSpacing(20)
        
        credit_level = self.client_credit_data['credit_level']
        
        # Puntaje principal
        score_section = QVBoxLayout()
        
        score_label = QLabel(str(self.client_credit_data['credit_score']))
        score_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        score_label.setStyleSheet(f"color: {credit_level['color']};")
        score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        score_text = QLabel("PUNTOS")
        score_text.setFont(QFont("Segoe UI", 10))
        score_text.setStyleSheet(f"color: {colors['TEXT_SECONDARY']};")
        score_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        score_section.addWidget(score_label)
        score_section.addWidget(score_text)
        
        # Nivel de crédito
        level_section = QVBoxLayout()
        
        level_icon = QLabel(credit_level['icon'])
        level_icon.setFont(QFont("Segoe UI", 20))
        level_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        level_name = QLabel(credit_level['name'])
        level_name.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        level_name.setStyleSheet(f"color: {credit_level['color']};")
        level_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        level_desc = QLabel(credit_level['description'])
        level_desc.setFont(QFont("Segoe UI", 9))
        level_desc.setStyleSheet(f"color: {colors['TEXT_SECONDARY']};")
        level_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        level_section.addWidget(level_icon)
        level_section.addWidget(level_name)
        level_section.addWidget(level_desc)
        
        # Estadísticas básicas
        stats_section = QVBoxLayout()
        
        trans_label = QLabel(f"📊 {self.client_credit_data['transactions']} Transacciones")
        trans_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        trans_label.setStyleSheet(f"color: {colors['TEXT_SECONDARY']};")
        
        avg_label = QLabel(f"⏱️ Promedio: {self.client_credit_data['avg_payment_days']} días")
        avg_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        avg_label.setStyleSheet(f"color: {colors['TEXT_SECONDARY']};")
        
        stats_section.addWidget(trans_label)
        stats_section.addWidget(avg_label)
        
        # NUEVAS ESTADÍSTICAS FINANCIERAS
        financial_section = QVBoxLayout()
        
        # Promedio por compra
        if self.client_credit_data['transactions'] > 0:
            avg_per_purchase = self.total_spent / self.client_credit_data['transactions']
            avg_purchase_label = QLabel(f"💳 Promedio por compra: ${avg_per_purchase:,.0f}")
        else:
            avg_purchase_label = QLabel("💳 Promedio por compra: $0")
        
        avg_purchase_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        avg_purchase_label.setStyleSheet(f"color: {colors['TEXT_SECONDARY']};")
        
        # Saldo actual (si tiene deuda)
        current_debt = self.client_credit_data['client_data'].get('saldo', 0)
        if current_debt > 0:
            debt_label = QLabel(f"⚠️ Saldo pendiente: ${current_debt:,.2f}")
            debt_label.setStyleSheet(f"color: {colors['WARNING_ORANGE']};")
        else:
            debt_label = QLabel("✅ Sin saldo pendiente")
            debt_label.setStyleSheet(f"color: {colors['SUCCESS_GREEN']};")
        
        debt_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        
        financial_section.addWidget(avg_purchase_label)
        financial_section.addWidget(debt_label)
        
        score_layout.addLayout(score_section)
        score_layout.addLayout(level_section)
        score_layout.addLayout(stats_section)
        score_layout.addLayout(financial_section)
        score_layout.addStretch()
        
        score_frame.setLayout(score_layout)
        layout.addWidget(score_frame)
    
    def create_transactions_table(self, layout):
        """Crear tabla de transacciones con columna de monto"""
        colors = self.parent.get_current_colors()
        
        # Título con total de transacciones
        title_layout = QHBoxLayout()
        
        title_label = QLabel("📋 Historial de Transacciones")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {colors['TEXT_PRIMARY']};")
        
        count_label = QLabel(f"({len(self.client_credit_data.get('transaction_details', []))} registros)")
        count_label.setFont(QFont("Segoe UI", 10))
        count_label.setStyleSheet(f"color: {colors['TEXT_SECONDARY']};")
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(count_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Tabla con nueva columna de MONTO
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(7)  # Agregamos una columna más
        self.transactions_table.setHorizontalHeaderLabels([
            'Folio', 'Fecha Venta', 'Fecha Pago', 'Monto', 'Días', 'Puntos', 'Estado'
        ])
        
        self.transactions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.transactions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Configurar columnas
        header = self.transactions_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Folio
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Fecha Venta
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Fecha Pago
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Monto
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Días
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Puntos
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch) # Estado
        
        self.transactions_table.setColumnWidth(0, 80)   # Folio
        self.transactions_table.setColumnWidth(1, 90)   # Fecha Venta
        self.transactions_table.setColumnWidth(2, 90)   # Fecha Pago
        self.transactions_table.setColumnWidth(3, 100)  # Monto
        self.transactions_table.setColumnWidth(4, 60)   # Días
        self.transactions_table.setColumnWidth(5, 70)   # Puntos
        
        # Poblar tabla
        self.populate_transactions_table()
        
        layout.addWidget(self.transactions_table)
    
    def populate_transactions_table(self):
        """Poblar tabla con transacciones del cliente incluyendo montos"""
        from datetime import datetime
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont, QColor
        from PyQt6.QtWidgets import QTableWidgetItem
        
        transactions = self.client_credit_data.get('transaction_details', [])
        
        self.transactions_table.setRowCount(len(transactions))
        
        for row, transaction in enumerate(transactions):
            try:
                # Folio
                folio_item = QTableWidgetItem(transaction.get('folio', 'N/A'))
                folio_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                folio_item.setFont(QFont("Segoe UI", 9))
                self.transactions_table.setItem(row, 0, folio_item)
                
                # Fecha venta
                fecha_venta = transaction.get('fecha_venta', 'N/A')
                if fecha_venta != 'N/A':
                    try:
                        fecha_dt = datetime.strptime(fecha_venta, '%Y-%m-%d')
                        fecha_venta = fecha_dt.strftime('%d/%m/%Y')
                    except:
                        pass
                
                fecha_venta_item = QTableWidgetItem(fecha_venta)
                fecha_venta_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                fecha_venta_item.setFont(QFont("Segoe UI", 9))
                self.transactions_table.setItem(row, 1, fecha_venta_item)
                
                # Fecha pago
                fecha_pago = transaction.get('fecha_pago', 'Pendiente')
                if fecha_pago != 'Pendiente' and fecha_pago != 'N/A':
                    try:
                        fecha_dt = datetime.strptime(fecha_pago, '%Y-%m-%d')
                        fecha_pago = fecha_dt.strftime('%d/%m/%Y')
                    except:
                        pass
                
                fecha_pago_item = QTableWidgetItem(fecha_pago)
                fecha_pago_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                fecha_pago_item.setFont(QFont("Segoe UI", 9))
                self.transactions_table.setItem(row, 2, fecha_pago_item)
                
                # MONTO DE LA TRANSACCIÓN - extraer de los datos del ticket
                monto = self.extract_amount_from_ticket_data(transaction.get('datos', ''))
                
                # Si no se pudo extraer de los datos del ticket, usar los campos originales
                if monto == 0:
                    monto = transaction.get('monto', 0) or transaction.get('importe', 0) or transaction.get('total', 0)
                    if isinstance(monto, str):
                        try:
                            monto = float(monto.replace(',', '').replace('$', ''))
                        except (ValueError, AttributeError):
                            monto = 0
                
                monto_item = QTableWidgetItem(f"${monto:,.0f}")
                monto_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                monto_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
                monto_item.setForeground(QColor('#22C55E'))  # Verde para montos
                self.transactions_table.setItem(row, 3, monto_item)
                
                # Días
                days_item = QTableWidgetItem(str(transaction.get('days', 'N/A')))
                days_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                days_item.setFont(QFont("Segoe UI", 9))
                self.transactions_table.setItem(row, 4, days_item)
                
                # Puntos
                points = transaction.get('points', 0)
                points_item = QTableWidgetItem(str(points))
                points_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                points_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                
                # Color según puntos
                if points > 0:
                    points_item.setForeground(QColor('#22C55E'))
                elif points < 0:
                    points_item.setForeground(QColor('#EF4444'))
                else:
                    points_item.setForeground(QColor('#6B7280'))
                
                self.transactions_table.setItem(row, 5, points_item)
                
                # Estado
                estado_item = QTableWidgetItem(transaction.get('estado', 'N/A'))
                estado_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                estado_item.setFont(QFont("Segoe UI", 9))
                self.transactions_table.setItem(row, 6, estado_item)
                
            except Exception as e:
                import logging
                logging.error(f"Error poblando transacción {row}: {e}")
                continue
    
    def create_buttons(self, layout):
        """Crear botones de la ventana"""
        buttons_layout = QHBoxLayout()
        
        # Botón para exportar historial (opcional)
        export_button = QPushButton("📊 Exportar Historial")
        export_button.setFixedHeight(35)
        export_button.clicked.connect(self.export_history)
        
        close_button = QPushButton("Cerrar")
        close_button.setFixedHeight(35)
        close_button.clicked.connect(self.close)
        
        buttons_layout.addWidget(export_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(close_button)
        
        layout.addLayout(buttons_layout)
    
    def export_history(self):
        """Exportar historial del cliente (función opcional)"""
        try:
            client_name = self.client_credit_data['client_data'].get('nombre', 'Cliente')
            filename = f"historial_crediticio_{client_name}_{self.client_id}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"HISTORIAL CREDITICIO - {client_name}\n")
                f.write(f"ID Cliente: {self.client_id}\n")
                f.write(f"Puntaje Crediticio: {self.client_credit_data['credit_score']} puntos\n")
                f.write(f"Nivel: {self.client_credit_data['credit_level']['name']}\n")
                f.write(f"Total Gastado: ${self.total_spent:,.2f}\n")
                f.write(f"Transacciones: {self.client_credit_data['transactions']}\n")
                f.write(f"Promedio de pago: {self.client_credit_data['avg_payment_days']} días\n")
                f.write("\n" + "="*50 + "\n")
                f.write("DETALLE DE TRANSACCIONES\n")
                f.write("="*50 + "\n")
                
                for transaction in self.client_credit_data.get('transaction_details', []):
                    f.write(f"Folio: {transaction.get('folio', 'N/A')}\n")
                    f.write(f"Fecha Venta: {transaction.get('fecha_venta', 'N/A')}\n")
                    f.write(f"Fecha Pago: {transaction.get('fecha_pago', 'Pendiente')}\n")
                    f.write(f"Monto: ${transaction.get('monto', 0):,.2f}\n")
                    f.write(f"Días: {transaction.get('days', 'N/A')}\n")
                    f.write(f"Puntos: {transaction.get('points', 0)}\n")
                    f.write("-" * 30 + "\n")
            
            QMessageBox.information(self, "✅ Éxito", f"Historial exportado a:\n{filename}")
            
        except Exception as e:
            logging.error(f"Error exportando historial: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al exportar historial:\n{str(e)}")
    
    def apply_theme(self):
        """Aplicar tema a la ventana"""
        colors = self.parent.get_current_colors()
        theme = self.theme_manager.get_current_theme()
        
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {theme['gradient_start']}, stop:0.3 {theme['gradient_mid1']}, 
                    stop:0.7 {theme['gradient_mid2']}, stop:1 {theme['gradient_end']});
                color: {colors['TEXT_PRIMARY']};
            }}
            
            QTableWidget {{
                background: {theme['card_bg_alpha']};
                border: 1px solid {theme['border_alpha']};
                border-radius: 8px;
                font-size: 10px;
            }}
            
            QTableWidget::item {{
                padding: 6px 4px;
                border-bottom: 1px solid {theme['border_alpha']};
            }}
            
            QTableWidget QHeaderView::section {{
                background: {theme['card_bg_alpha']};
                color: {colors['TEXT_PRIMARY']};
                padding: 6px 4px;
                border: none;
                border-right: 1px solid {theme['border_alpha']};
                border-bottom: 2px solid {colors['BRIGHT_CYAN']};
                font-weight: 600;
                font-size: 9px;
            }}
            
            QPushButton {{
                background: {colors['BRIGHT_CYAN']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }}
            
            QPushButton:hover {{
                background: rgba({self.parent.hex_to_rgb(colors['BRIGHT_CYAN'])}, 0.8);
            }}
        """)

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
        
        #credits
        self.all_clients_data = {}
        self.all_ventas_data = {}
        self.clients_credit_scores = {}
        self.credit_statistics = {}
        self.credit_data_loaded = False  # ← NUEVA BANDERA
        self.credit_data_loading = False  # ← EVITAR CARGAS MÚLTIPLES
        self.top_clients_data_loaded = False
        self.top_clients_data_loading = False
        self.all_clients_spending = {}  # {client_id: total_spent}
        self.current_top_view = "clientes"  # clientes o empresas
        
        self.current_credit_view = "clientes"
        self.last_update_time = time.time()
        self.data_loaded = False
        
        self.initUI()
        self.load_data()  # Solo carga datos principales
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
        
        # Botones existentes
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
        
        self.creditos_btn = ModernButton("SISTEMA DE CRÉDITOS", self.theme_manager)
        self.creditos_btn.setCheckable(True)
        self.creditos_btn.setFixedHeight(35)
        self.creditos_btn.setFixedWidth(180)
        self.creditos_btn.clicked.connect(lambda: self.switch_view("creditos"))
        
        # NUEVO BOTÓN TOP CLIENTES
        self.top_btn = ModernButton("TOP CLIENTES", self.theme_manager)
        self.top_btn.setCheckable(True)
        self.top_btn.setFixedHeight(35)
        self.top_btn.setFixedWidth(140)
        self.top_btn.clicked.connect(lambda: self.switch_view("top"))
        
        self.buro_btn = ModernButton("BURÓ DE CRÉDITO", self.theme_manager)
        self.buro_btn.setCheckable(True)
        self.buro_btn.setFixedHeight(35)
        self.buro_btn.setFixedWidth(150)
        self.buro_btn.clicked.connect(lambda: self.switch_view("buro"))
        
        nav_layout.addWidget(self.clientes_btn)
        nav_layout.addWidget(self.empresas_btn)
        nav_layout.addWidget(self.creditos_btn)
        nav_layout.addWidget(self.top_btn)  # AGREGAR AQUÍ
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

    def create_creditos_view(self):
        """Crear vista del sistema de créditos - CON CARGA BAJO DEMANDA"""
        # PRIMER PASO: Verificar si necesitamos cargar datos de créditos
        if not self.credit_data_loaded:
            # Mostrar indicador de carga
            self.show_credit_loading_indicator()
            
            # Procesar eventos para mostrar la interfaz
            QApplication.processEvents()
            
            # Cargar datos en segundo plano
            if not self.load_credit_data():
                # Si falla la carga, mostrar error y volver a vista anterior
                self.switch_view("clientes")
                return
        
        # SEGUNDO PASO: Crear la vista normalmente
        self.clear_layout(self.main_layout)
        colors = self.get_current_colors()
        
        # Verificar si los datos están disponibles
        if not self.clients_credit_scores:
            error_container = ModernCard(self.theme_manager)
            error_container.setFixedHeight(200)
            error_layout = QVBoxLayout()
            error_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            error_label = QLabel("❌ No se pudieron cargar los datos crediticios")
            error_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Medium))
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet(f"color: {colors['DANGER_RED']}; margin: 30px;")
            
            retry_button = QPushButton("🔄 Reintentar")
            retry_button.setFont(QFont("Segoe UI", 12))
            retry_button.clicked.connect(self.retry_credit_data_load)
            
            error_layout.addWidget(error_label)
            error_layout.addWidget(retry_button)
            error_container.setLayout(error_layout)
            self.main_layout.addWidget(error_container)
            return
        
        # Sub-navegación FIJA (se crea una sola vez)
        self.create_credit_sub_navigation()
        
        # Contenido que cambia según la vista
        self.create_credit_content()
    
    def retry_credit_data_load(self):
        """Reintentar carga de datos crediticios"""
        self.credit_data_loaded = False
        self.credit_data_loading = False
        self.create_creditos_view()
    
   
    def create_credit_statistics_header(self):
        """Crear header con estadísticas del sistema de créditos"""
        colors = self.get_current_colors()
        theme = self.theme_manager.get_current_theme()
        
        header_card = ModernCard(self.theme_manager)
        header_card.setFixedHeight(120)
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(20, 15, 20, 15)
        header_layout.setSpacing(10)
        
        # Título principal
        title_layout = QHBoxLayout()
        
        title_layout.addStretch()
        
        # Estadísticas generales
        stats = self.credit_statistics
        
        stats_section = QHBoxLayout()
        stats_section.setSpacing(20)
        
        
        title_layout.addLayout(stats_section)
        
        header_layout.addLayout(title_layout)
        
        # Distribución por niveles (compacta)
        distribution_layout = QHBoxLayout()
        distribution_layout.setSpacing(15)
        
        by_level = stats.get('by_level', {})
        
        # Crear indicadores compactos para cada nivel
        levels = [
            ('DORADO', '🥇', '#FFD700'),
            ('VERDE', '✅', '#22C55E'),
            ('AMARILLO', '⚠️', '#EAB308'),
            ('NARANJA', '🔶', '#F97316'),
            ('ROJO', '🚫', '#EF4444')
        ]
        
        for level_name, icon, color in levels:
            count = by_level.get(level_name, 0)
            
            level_widget = QWidget()
            level_widget.setFixedWidth(80)
            level_layout = QVBoxLayout()
            level_layout.setContentsMargins(5, 5, 5, 5)
            level_layout.setSpacing(2)
            
            icon_label = QLabel(icon)
            icon_label.setFont(QFont("Segoe UI", 12))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            count_label = QLabel(str(count))
            count_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            count_label.setStyleSheet(f"color: {color};")
            count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            name_label = QLabel(level_name[:3])  # Solo primeras 3 letras
            name_label.setFont(QFont("Segoe UI", 8))
            name_label.setStyleSheet(f"color: {colors['TEXT_SECONDARY']};")
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            level_layout.addWidget(icon_label)
            level_layout.addWidget(count_label)
            level_layout.addWidget(name_label)
            
            level_widget.setLayout(level_layout)
            distribution_layout.addWidget(level_widget)
        
        distribution_layout.addStretch()
        header_layout.addLayout(distribution_layout)
        
        header_card.setLayout(header_layout)
        self.main_layout.addWidget(header_card)

    def create_credit_levels_grid(self):
        """Crear grid con las 5 categorías de crédito"""
        colors = self.get_current_colors()
        
        # Contenedor principal
        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)
        
        # Definir los niveles de crédito
        levels = [
            {
                'name': 'DORADO',
                'icon': '🥇',
                'color': '#FFD700',
                'description': 'Crédito Alto',
                'range': '1000+ pts',
                'position': (0, 0)
            },
            {
                'name': 'VERDE', 
                'icon': '✅',
                'color': '#22C55E',
                'description': 'Crédito Normal',
                'range': '600-999 pts',
                'position': (0, 1)
            },
            {
                'name': 'AMARILLO',
                'icon': '⚠️', 
                'color': '#EAB308',
                'description': 'Crédito a Revisión',
                'range': '400-599 pts',
                'position': (0, 2)
            },
            {
                'name': 'NARANJA',
                'icon': '🔶',
                'color': '#F97316', 
                'description': 'Crédito de Riesgo',
                'range': '200-399 pts',
                'position': (1, 0)
            },
            {
                'name': 'ROJO',
                'icon': '🚫',
                'color': '#EF4444',
                'description': 'Sin Crédito - Buró',
                'range': '0-199 pts',
                'position': (1, 1)
            }
        ]
        
        # Crear tabla para cada nivel
        for level in levels:
            self.create_credit_level_table(
                grid_layout, 
                level['name'],
                level['icon'], 
                level['color'],
                level['description'],
                level['range'],
                level['position'][0],
                level['position'][1]
            )
        
        # Espacio vacío en la última posición
        empty_widget = QWidget()
        grid_layout.addWidget(empty_widget, 1, 2)
        
        grid_widget.setLayout(grid_layout)
        self.main_layout.addWidget(grid_widget)

    def create_credit_level_table(self, layout, level_name, icon, color, description, point_range, row, col):
        """Crear tabla para un nivel de crédito específico"""
        colors = self.get_current_colors()
        theme = self.theme_manager.get_current_theme()
        
        # Filtrar clientes por nivel
        clients_in_level = {
            client_id: data for client_id, data in self.clients_credit_scores.items()
            if data['credit_level']['name'] == level_name
        }
        
        # Crear card
        level_card = ModernCard(self.theme_manager)
        level_card.setMinimumHeight(350)
        level_card.setMaximumHeight(450)
        
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(10)
        
        # Header del nivel
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)
        
        # Título con ícono
        title_layout = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI", 16))
        
        name_label = QLabel(level_name)
        name_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {color};")
        
        count_label = QLabel(f"({len(clients_in_level)})")
        count_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        count_label.setStyleSheet(f"color: {colors['TEXT_SECONDARY']};")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(name_label)
        title_layout.addWidget(count_label)
        title_layout.addStretch()
        
        # Descripción y rango
        desc_label = QLabel(f"{description} • {point_range}")
        desc_label.setFont(QFont("Segoe UI", 9))
        desc_label.setStyleSheet(f"color: {colors['TEXT_SECONDARY']};")
        
        header_layout.addLayout(title_layout)
        header_layout.addWidget(desc_label)
        
        card_layout.addLayout(header_layout)
        
        # Tabla de clientes
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(['Cliente', 'Puntaje', 'Transacciones', 'Promedio Días'])
        
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Configurar columnas
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        table.setColumnWidth(1, 80)
        table.setColumnWidth(2, 90)
        table.setColumnWidth(3, 90)
        
        table.setMaximumHeight(250)
        table.setMinimumHeight(180)
        
        # Estilo específico
        table.setStyleSheet(f"""
            QTableWidget {{
                background: rgba({self.hex_to_rgb(color)}, 0.05);
                border: 1px solid rgba({self.hex_to_rgb(color)}, 0.2);
                font-size: 10px;
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
                font-size: 9px;
            }}
        """)
        
        # Poblar tabla
        self.populate_credit_level_table(table, clients_in_level, color)
        
        card_layout.addWidget(table)
        level_card.setLayout(card_layout)
        
        layout.addWidget(level_card, row, col)

    def populate_credit_level_table(self, table, clients_in_level, color):
        """Poblar tabla con clientes del nivel específico"""
        # Ordenar clientes por puntaje descendente
        sorted_clients = sorted(
            clients_in_level.items(), 
            key=lambda x: x[1]['credit_score'], 
            reverse=True
        )
        
        table.setRowCount(len(sorted_clients))
        
        for row, (client_id, client_data) in enumerate(sorted_clients):
            try:
                # Nombre del cliente (truncado)
                nombre = client_data['client_data'].get('nombre', 'Sin nombre')
                if len(nombre) > 20:
                    nombre = nombre[:17] + "..."
                
                name_item = QTableWidgetItem(nombre)
                name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                name_item.setData(Qt.ItemDataRole.UserRole, client_id)
                name_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
                name_item.setToolTip(client_data['client_data'].get('nombre', 'Sin nombre'))
                table.setItem(row, 0, name_item)
                
                # Puntaje
                score_item = QTableWidgetItem(str(client_data['credit_score']))
                score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                score_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                score_item.setForeground(QColor(color))
                table.setItem(row, 1, score_item)
                
                # Número de transacciones
                trans_item = QTableWidgetItem(str(client_data['transactions']))
                trans_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                trans_item.setFont(QFont("Segoe UI", 8))
                table.setItem(row, 2, trans_item)
                
                # Promedio de días
                avg_days = client_data['avg_payment_days']
                avg_item = QTableWidgetItem(f"{avg_days}d")
                avg_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                avg_item.setFont(QFont("Segoe UI", 8))
                table.setItem(row, 3, avg_item)
                
                # Color de fondo sutil
                bg_color = QColor(color)
                bg_color.setAlpha(20)
                
                for col_idx in range(4):
                    item = table.item(row, col_idx)
                    if item:
                        item.setBackground(bg_color)
                        
            except Exception as e:
                logging.error(f"Error poblando fila {row}: {e}")
                continue
        
        # Conectar evento de doble clic
        table.cellDoubleClicked.connect(lambda row, col: self.on_credit_client_double_click(table, row))

    def on_credit_client_double_click(self, table, row):
        """Maneja el doble clic en un cliente de la vista de créditos"""
        try:
            name_item = table.item(row, 0)
            if name_item:
                client_id = name_item.data(Qt.ItemDataRole.UserRole)
                if client_id and client_id in self.clients_credit_scores:
                    client_credit_data = self.clients_credit_scores[client_id]
                    self.credit_detail_window = CreditDetailWindow(self, client_credit_data, client_id)
                    self.credit_detail_window.show()
                else:
                    QMessageBox.warning(self, "⚠️ Error", "No se pudo obtener la información crediticia del cliente")
        except Exception as e:
            logging.error(f"Error al abrir detalles crediticios del cliente: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al abrir detalles crediticios: {str(e)}")
        
    def create_credit_sub_navigation(self):
        """Crear sub-navegación SIMPLE con buscador - TODO EN UNA LÍNEA"""
        colors = self.get_current_colors()
        
        nav_frame = ModernCard(self.theme_manager)
        nav_frame.setFixedHeight(70)  # Reducir altura ya que solo hay una fila
        nav_frame.setContentsMargins(20, 15, 20, 15)
        
        # UN SOLO LAYOUT HORIZONTAL - TODO EN UNA LÍNEA
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(25)  # Buen espaciado entre elementos
        
        # Botón Clientes
        self.credit_clientes_btn = ModernButton("👤 CLIENTES", self.theme_manager)
        self.credit_clientes_btn.setCheckable(True)
        self.credit_clientes_btn.setChecked(self.current_credit_view == "clientes")
        self.credit_clientes_btn.setFixedHeight(40)
        self.credit_clientes_btn.setFixedWidth(160)
        self.credit_clientes_btn.clicked.connect(lambda: self.switch_credit_view("clientes"))
        
        # Botón Empresas
        self.credit_empresas_btn = ModernButton("🏢 EMPRESAS", self.theme_manager)
        self.credit_empresas_btn.setCheckable(True)
        self.credit_empresas_btn.setChecked(self.current_credit_view == "empresas")
        self.credit_empresas_btn.setFixedHeight(40)
        self.credit_empresas_btn.setFixedWidth(160)
        self.credit_empresas_btn.clicked.connect(lambda: self.switch_credit_view("empresas"))
        
        # Separador visual (opcional)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFixedHeight(30)
        separator.setStyleSheet(f"background: rgba({self.hex_to_rgb(colors['TEXT_SECONDARY'])}, 0.3); width: 1px;")
        
        # BUSCADOR EN LA MISMA LÍNEA - MÁS COMPACTO
        search_section = QHBoxLayout()
        search_section.setSpacing(10)
        
        # Ícono de búsqueda
        #search_icon = QLabel("🔍")
        #search_icon.setFont(QFont("Segoe UI", 14))
        #search_icon.setStyleSheet("padding: 5px;")
        
        # Campo de búsqueda optimizado
        self.credit_search_input = QLineEdit()
        self.credit_search_input.setPlaceholderText("Buscar cliente por nombre...")
        self.credit_search_input.setFixedWidth(300)  # Un poco más compacto
        self.credit_search_input.setFixedHeight(35)
        self.credit_search_input.setStyleSheet(f"""
            QLineEdit {{
                background: rgba({self.hex_to_rgb(colors['CARD_BG'])}, 0.9);
                border: 2px solid rgba({self.hex_to_rgb(colors['BRIGHT_CYAN'])}, 0.4);
                border-radius: 17px;
                padding: 6px 16px;
                color: {colors['TEXT_PRIMARY']};
                font-size: 12px;
                font-weight: 500;
            }}
            QLineEdit:focus {{
                border: 2px solid {colors['BRIGHT_CYAN']};
                background: rgba({self.hex_to_rgb(colors['CARD_BG'])}, 1.0);
                box-shadow: 0 0 8px rgba({self.hex_to_rgb(colors['BRIGHT_CYAN'])}, 0.3);
            }}
            QLineEdit:hover {{
                border: 2px solid rgba({self.hex_to_rgb(colors['BRIGHT_CYAN'])}, 0.6);
            }}
        """)
        
        # Conectar búsqueda en tiempo real
        self.credit_search_input.textChanged.connect(self.on_credit_search_changed)
        
        # Botón limpiar búsqueda más pequeño
        clear_btn = QPushButton("✕")
        clear_btn.setFixedSize(30, 30)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba({self.hex_to_rgb(colors['TEXT_SECONDARY'])}, 0.4);
                color: {colors['TEXT_SECONDARY']};
                border: none;
                border-radius: 15px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba({self.hex_to_rgb(colors['DANGER_RED'])}, 0.6);
                color: white;
            }}
            QPushButton:pressed {{
                background: rgba({self.hex_to_rgb(colors['DANGER_RED'])}, 0.8);
            }}
        """)
        clear_btn.clicked.connect(self.clear_credit_search)
        clear_btn.setToolTip("Limpiar búsqueda")
        
        # Agregar elementos del buscador al layout de búsqueda
        #search_section.addWidget(search_icon)
        search_section.addWidget(self.credit_search_input)
        search_section.addWidget(clear_btn)
        
        # AGREGAR TODO AL LAYOUT PRINCIPAL HORIZONTAL
        nav_layout.addWidget(self.credit_clientes_btn)
        nav_layout.addWidget(self.credit_empresas_btn)
        nav_layout.addWidget(separator)
        nav_layout.addLayout(search_section)
        nav_layout.addStretch()  # Empujar todo hacia la izquierda
        
        nav_frame.setLayout(nav_layout)
        self.main_layout.addWidget(nav_frame)


    def on_credit_search_changed(self, text):
        """Manejar cambios en el campo de búsqueda de créditos"""
        # Buscar en tiempo real mientras el usuario escribe
        self.current_search_text = text.strip().lower()
        
        # Solo buscar si hay al menos 2 caracteres o está vacío (mostrar todo)
        if len(self.current_search_text) >= 2 or self.current_search_text == "":
            self.recreate_only_credit_content()

    def clear_credit_search(self):
        """Limpiar el campo de búsqueda"""
        self.credit_search_input.clear()
        self.current_search_text = ""
        self.recreate_only_credit_content()
    
    def switch_credit_view(self, view):
        """Cambiar vista de créditos - SIMPLIFICADO sin estadísticas"""
        if self.current_credit_view != view:
            self.current_credit_view = view
            
            # Solo actualizar botones
            self.credit_clientes_btn.setChecked(view == "clientes")
            self.credit_empresas_btn.setChecked(view == "empresas")
            
            # Limpiar búsqueda al cambiar de vista
            if hasattr(self, 'credit_search_input'):
                self.credit_search_input.clear()
                self.current_search_text = ""
            
            # Solo recrear el contenido (no la navegación)
            self.recreate_only_credit_content()
    
    def recreate_only_credit_content(self):
        """Recrear SOLO el contenido, mantener navegación intacta"""
        # Encontrar el widget de contenido (debería ser el último)
        layout_count = self.main_layout.count()
        
        # Eliminar solo el último widget (el contenido)
        if layout_count > 1:
            last_item = self.main_layout.itemAt(layout_count - 1)
            if last_item and last_item.widget():
                last_item.widget().deleteLater()
                self.main_layout.removeWidget(last_item.widget())
        
        # Crear nuevo contenido
        self.create_credit_content()
    
    def create_credit_content(self):
        """Crear contenido filtrado según vista actual"""
        # Contenedor principal para las tablas
        content_widget = QWidget()
        content_layout = QGridLayout()
        content_layout.setSpacing(15)
        
        # Definir niveles de crédito
        levels = [
            ('DORADO', '🥇', '#FFD700', 'Crédito Alto', '1000+ pts', (0, 0)),
            ('VERDE', '✅', '#22C55E', 'Crédito Normal', '600-999 pts', (0, 1)),
            ('AMARILLO', '⚠️', '#EAB308', 'Crédito a Revisión', '400-599 pts', (0, 2)),
            ('NARANJA', '🔶', '#F97316', 'Crédito de Riesgo', '200-399 pts', (1, 0)),
            ('ROJO', '🚫', '#EF4444', 'Sin Crédito - Buró', '0-199 pts', (1, 1))
        ]
        
        # Crear tabla para cada nivel
        for level_name, icon, color, description, range_text, (row, col) in levels:
            # Filtrar datos para este nivel y tipo actual
            filtered_clients = self.filter_clients_for_level(level_name)
            
            # Crear tabla
            level_table = self.create_simple_credit_table(
                level_name, icon, color, description, range_text, filtered_clients
            )
            
            content_layout.addWidget(level_table, row, col)
        
        # Widget vacío en la última posición
        content_layout.addWidget(QWidget(), 1, 2)
        
        content_widget.setLayout(content_layout)
        self.main_layout.addWidget(content_widget)
        
    def create_simple_credit_table(self, level_name, icon, color, description, range_text, clients_data):
        """Crear tabla simple para un nivel de crédito CON indicador de resultados - ESPACIADO MEJORADO"""
        colors = self.get_current_colors()
        theme = self.theme_manager.get_current_theme()
        
        # Card contenedor con mejor espaciado
        card = ModernCard(self.theme_manager)
        card.setMinimumHeight(380)  # Más altura
        card.setMaximumHeight(480)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(18, 18, 18, 18)  # Más padding
        layout.setSpacing(12)  # Más espacio entre elementos
        
        # Header con indicador de búsqueda - MEJOR ORGANIZACION
        header_container = QWidget()
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        
        # Primera línea: Título principal
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI", 18))  # Ícono más grande
        
        # Título con contador y indicador de búsqueda
        search_text = getattr(self, 'current_search_text', '')
        if search_text:
            title_text = f"{level_name} ({len(clients_data)})"
            search_indicator = " 🔍"
            tooltip_text = f"Filtrando por: '{search_text}'"
        else:
            title_text = f"{level_name} ({len(clients_data)})"
            search_indicator = ""
            tooltip_text = f"Mostrando todos los {level_name.lower()}"
        
        title_label = QLabel(title_text + search_indicator)
        title_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {color}; padding: 2px;")
        title_label.setToolTip(tooltip_text)
        
        type_indicator = QLabel("👤" if self.current_credit_view == "clientes" else "🏢")
        type_indicator.setFont(QFont("Segoe UI", 14))
        type_indicator.setToolTip("Clientes" if self.current_credit_view == "clientes" else "Empresas")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addWidget(type_indicator)
        title_layout.addStretch()
        
        # Segunda línea: Descripción
        desc_label = QLabel(f"{description} • {range_text}")
        desc_label.setFont(QFont("Segoe UI", 10))
        desc_label.setStyleSheet(f"color: {colors['TEXT_SECONDARY']}; padding: 2px;")
        
        header_layout.addLayout(title_layout)
        header_layout.addWidget(desc_label)
        header_container.setLayout(header_layout)
        
        layout.addWidget(header_container)
        
        # Tabla con mejor espaciado
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(['Cliente', 'Puntaje', 'Transacciones', 'Promedio Días'])
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Configurar columnas
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        table.setColumnWidth(1, 85)  # Más ancho
        table.setColumnWidth(2, 95)  # Más ancho
        table.setColumnWidth(3, 95)  # Más ancho
        
        table.setMaximumHeight(280)  # Más altura para la tabla
        table.setMinimumHeight(220)
        
        # Estilo con indicador de búsqueda mejorado
        border_color = color
        if search_text:
            border_color = colors['BRIGHT_CYAN']  # Cambiar borde cuando hay búsqueda activa
        
        table.setStyleSheet(f"""
            QTableWidget {{
                background: rgba({self.hex_to_rgb(color)}, 0.06);
                border: 2px solid rgba({self.hex_to_rgb(border_color)}, 0.5);
                border-radius: 8px;
                font-size: 11px;
                gridline-color: rgba({self.hex_to_rgb(border_color)}, 0.2);
            }}
            QTableWidget::item {{
                padding: 8px 6px;
                border-bottom: 1px solid rgba({self.hex_to_rgb(border_color)}, 0.1);
            }}
            QTableWidget::item:selected {{
                background: rgba({self.hex_to_rgb(color)}, 0.4);
                color: white;
            }}
            QTableWidget::item:hover {{
                background: rgba({self.hex_to_rgb(color)}, 0.2);
            }}
            QTableWidget QHeaderView::section {{
                background: rgba({self.hex_to_rgb(color)}, 0.1);
                border: none;
                border-right: 1px solid rgba({self.hex_to_rgb(border_color)}, 0.3);
                border-bottom: 2px solid {border_color};
                padding: 10px 6px;
                font-size: 10px;
                font-weight: bold;
                text-transform: uppercase;
            }}
            QScrollBar:vertical {{
                background: rgba({self.hex_to_rgb(color)}, 0.1);
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba({self.hex_to_rgb(color)}, 0.5);
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba({self.hex_to_rgb(color)}, 0.7);
            }}
        """)
        
        # Poblar tabla
        self.populate_simple_credit_table(table, clients_data, color)
        
        layout.addWidget(table)
        card.setLayout(layout)
        
        return card

    
    def populate_simple_credit_table(self, table, clients_data, color):
        """Poblar tabla con datos simples"""
        # Ordenar por puntaje
        sorted_clients = sorted(
            clients_data.items(), 
            key=lambda x: x[1]['credit_score'], 
            reverse=True
        )
        
        table.setRowCount(len(sorted_clients))
        
        for row, (client_id, client_data) in enumerate(sorted_clients):
            try:
                # Nombre
                nombre = client_data['client_data'].get('nombre', 'Sin nombre')
                if len(nombre) > 25:
                    nombre = nombre[:22] + "..."
                
                name_item = QTableWidgetItem(nombre)
                name_item.setData(Qt.ItemDataRole.UserRole, client_id)
                name_item.setToolTip(client_data['client_data'].get('nombre', 'Sin nombre'))
                table.setItem(row, 0, name_item)
                
                # Puntaje
                score_item = QTableWidgetItem(str(client_data['credit_score']))
                score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                score_item.setForeground(QColor(color))
                table.setItem(row, 1, score_item)
                
                # Transacciones
                trans_item = QTableWidgetItem(str(client_data['transactions']))
                trans_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 2, trans_item)
                
                # Promedio días
                avg_item = QTableWidgetItem(f"{client_data['avg_payment_days']}d")
                avg_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 3, avg_item)
                
            except Exception as e:
                logging.error(f"Error poblando fila {row}: {e}")
                continue
        
        # Conectar doble clic
        table.cellDoubleClicked.connect(lambda row, col: self.on_credit_client_double_click(table, row))
    
    def filter_clients_for_level(self, level_name):
        """Filtrar clientes por nivel Y tipo actual Y búsqueda"""
        filtered = {}
        
        # Obtener texto de búsqueda actual
        search_text = getattr(self, 'current_search_text', '').lower()
        
        for client_id, credit_data in self.clients_credit_scores.items():
            # Verificar si es del nivel correcto
            if credit_data['credit_level']['name'] != level_name:
                continue
            
            # Verificar si es del tipo correcto (cliente/empresa)
            client_state = self.client_states.get(client_id, {})
            is_company = client_state.get('company', False)
            
            if self.current_credit_view == "clientes" and is_company:
                continue
            elif self.current_credit_view == "empresas" and not is_company:
                continue
            
            # FILTRAR POR BÚSQUEDA DE NOMBRE
            if search_text:
                client_name = credit_data['client_data'].get('nombre', '').lower()
                if search_text not in client_name:
                    continue
            
            filtered[client_id] = credit_data
        
        return filtered
    
    def clear_layout_from_index(self, start_index):
        """Limpiar layout desde un índice específico"""
        while self.main_layout.count() > start_index:
            child = self.main_layout.takeAt(start_index)
            if child.widget():
                child.widget().deleteLater()
    
    def get_current_credit_stats(self):
        """Obtener estadísticas para la vista actual (clientes o empresas)"""
        current_stats = {}
        
        for client_id, credit_data in self.clients_credit_scores.items():
            # Determinar si es cliente o empresa
            client_state = self.client_states.get(client_id, {})
            is_company = client_state.get('company', False)
            
            # Filtrar según vista actual
            if self.current_credit_view == "clientes" and is_company:
                continue
            elif self.current_credit_view == "empresas" and not is_company:
                continue
            
            # Contar por nivel
            level_name = credit_data['credit_level']['name']
            current_stats[level_name] = current_stats.get(level_name, 0) + 1
        
        return current_stats

    def create_client_credit_content(self):
        """Crear contenido de créditos para clientes"""
        self.create_filtered_credit_levels_grid("clientes")

    def create_company_credit_content(self):
        """Crear contenido de créditos para empresas"""
        self.create_filtered_credit_levels_grid("empresas")
    
    def create_company_credit_content(self):
        """Crear contenido de créditos para empresas"""
        self.create_filtered_credit_levels_grid("empresas")

    def create_filtered_credit_levels_grid(self, filter_type):
        """Crear grid de niveles de crédito filtrado por tipo"""
        colors = self.get_current_colors()
        
        # Contenedor principal
        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)
        
        # Definir los niveles de crédito
        levels = [
            {
                'name': 'DORADO',
                'icon': '🥇',
                'color': '#FFD700',
                'description': 'Crédito Alto',
                'range': '1000+ pts',
                'position': (0, 0)
            },
            {
                'name': 'VERDE', 
                'icon': '✅',
                'color': '#22C55E',
                'description': 'Crédito Normal',
                'range': '600-999 pts',
                'position': (0, 1)
            },
            {
                'name': 'AMARILLO',
                'icon': '⚠️', 
                'color': '#EAB308',
                'description': 'Crédito a Revisión',
                'range': '400-599 pts',
                'position': (0, 2)
            },
            {
                'name': 'NARANJA',
                'icon': '🔶',
                'color': '#F97316', 
                'description': 'Crédito de Riesgo',
                'range': '200-399 pts',
                'position': (1, 0)
            },
            {
                'name': 'ROJO',
                'icon': '🚫',
                'color': '#EF4444',
                'description': 'Sin Crédito - Buró',
                'range': '0-199 pts',
                'position': (1, 1)
            }
        ]
        
        # Crear tabla para cada nivel
        for level in levels:
            self.create_filtered_credit_level_table(
                grid_layout, 
                level['name'],
                level['icon'], 
                level['color'],
                level['description'],
                level['range'],
                level['position'][0],
                level['position'][1],
                filter_type
            )
        
        # Espacio vacío en la última posición
        empty_widget = QWidget()
        grid_layout.addWidget(empty_widget, 1, 2)
        
        grid_widget.setLayout(grid_layout)
        self.main_layout.addWidget(grid_widget)

    def create_filtered_credit_level_table(self, layout, level_name, icon, color, description, point_range, row, col, filter_type):
        """Crear tabla para un nivel de crédito específico con filtro"""
        colors = self.get_current_colors()
        theme = self.theme_manager.get_current_theme()
        
        # Filtrar clientes por nivel Y tipo (cliente/empresa)
        clients_in_level = {}
        
        for client_id, data in self.clients_credit_scores.items():
            if data['credit_level']['name'] != level_name:
                continue
            
            # Aplicar filtro de tipo
            client_state = self.client_states.get(client_id, {})
            is_company = client_state.get('company', False)
            
            if filter_type == "clientes" and is_company:
                continue
            elif filter_type == "empresas" and not is_company:
                continue
            
            clients_in_level[client_id] = data
        
        # Crear card
        level_card = ModernCard(self.theme_manager)
        level_card.setMinimumHeight(350)
        level_card.setMaximumHeight(450)
        
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(10)
        
        # Header del nivel
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)
        
        # Título con ícono
        title_layout = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI", 16))
        
        name_label = QLabel(level_name)
        name_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {color};")
        
        count_label = QLabel(f"({len(clients_in_level)})")
        count_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        count_label.setStyleSheet(f"color: {colors['TEXT_SECONDARY']};")
        
        # Indicador de tipo
        type_label = QLabel("👤" if filter_type == "clientes" else "🏢")
        type_label.setFont(QFont("Segoe UI", 12))
        type_label.setToolTip("Clientes" if filter_type == "clientes" else "Empresas")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(name_label)
        title_layout.addWidget(count_label)
        title_layout.addWidget(type_label)
        title_layout.addStretch()
        
        # Descripción y rango
        desc_label = QLabel(f"{description} • {point_range}")
        desc_label.setFont(QFont("Segoe UI", 9))
        desc_label.setStyleSheet(f"color: {colors['TEXT_SECONDARY']};")
        
        header_layout.addLayout(title_layout)
        header_layout.addWidget(desc_label)
        
        card_layout.addLayout(header_layout)
        
        # Tabla de clientes
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(['Cliente', 'Puntaje', 'Transacciones', 'Promedio Días'])
        
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Configurar columnas
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        table.setColumnWidth(1, 80)
        table.setColumnWidth(2, 90)
        table.setColumnWidth(3, 90)
        
        table.setMaximumHeight(250)
        table.setMinimumHeight(180)
        
        # Estilo específico
        table.setStyleSheet(f"""
            QTableWidget {{
                background: rgba({self.hex_to_rgb(color)}, 0.05);
                border: 1px solid rgba({self.hex_to_rgb(color)}, 0.2);
                font-size: 10px;
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
                font-size: 9px;
            }}
        """)
        
        # Poblar tabla
        self.populate_credit_level_table(table, clients_in_level, color)
        
        card_layout.addWidget(table)
        level_card.setLayout(card_layout)
        
        layout.addWidget(level_card, row, col)
    
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
        """Cambiar entre vistas con manejo de errores mejorado"""
        if self.current_view != view:
            self.current_view = view
            
            # Actualizar botones
            self.clientes_btn.setChecked(view == "clientes")
            self.empresas_btn.setChecked(view == "empresas")
            self.creditos_btn.setChecked(view == "creditos")
            self.top_btn.setChecked(view == "top")
            self.buro_btn.setChecked(view == "buro")
            
            try:
                if view == "top":
                    self.create_top_clientes_view_safe()  # Usar versión segura
                elif view == "buro":
                    self.create_buro_view()
                elif view == "creditos":
                    self.create_creditos_view()
                else:
                    self.create_clientes_view()
                    
            except Exception as e:
                logging.error(f"Error cambiando a vista {view}: {e}")
                # Volver a vista segura
                self.current_view = "clientes"
                self.clientes_btn.setChecked(True)
                self.create_clientes_view()
                QMessageBox.critical(self, "❌ Error", f"Error cambiando vista: {str(e)}")

    def create_top_clientes_view_safe(self):
        """Crear vista de top clientes con manejo de errores robusto"""
        try:
            self.create_top_clientes_view()
        except Exception as e:
            logging.error(f"Error en vista de top clientes: {e}")
            
            # Crear vista de error simple
            self.clear_layout(self.main_layout)
            colors = self.get_current_colors()
            
            error_container = ModernCard(self.theme_manager)
            error_container.setFixedHeight(200)
            error_layout = QVBoxLayout()
            error_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            error_label = QLabel("❌ Error al cargar Top Clientes")
            error_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Medium))
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet(f"color: {colors['DANGER_RED']}; margin: 30px;")
            
            detail_label = QLabel(f"Detalles: {str(e)}")
            detail_label.setFont(QFont("Segoe UI", 10))
            detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            detail_label.setStyleSheet(f"color: {colors['TEXT_SECONDARY']};")
            detail_label.setWordWrap(True)
            
            retry_button = QPushButton("🔄 Volver a Intentar")
            retry_button.setFont(QFont("Segoe UI", 12))
            retry_button.clicked.connect(lambda: self.switch_view("top"))
            
            back_button = QPushButton("← Volver a Clientes")
            back_button.setFont(QFont("Segoe UI", 12))
            back_button.clicked.connect(lambda: self.switch_view("clientes"))
            
            buttons_layout = QHBoxLayout()
            buttons_layout.addWidget(retry_button)
            buttons_layout.addWidget(back_button)
            
            error_layout.addWidget(error_label)
            error_layout.addWidget(detail_label)
            error_layout.addLayout(buttons_layout)
            error_container.setLayout(error_layout)
            self.main_layout.addWidget(error_container)


    def create_top_clientes_view(self):
        """Crear vista de top clientes con carga bajo demanda"""
        # Verificar si necesitamos cargar datos
        if not self.top_clients_data_loaded:
            self.show_top_loading_indicator()
            QApplication.processEvents()
            
            if not self.load_top_clients_data():
                self.switch_view("clientes")
                return
        
        self.clear_layout(self.main_layout)
        colors = self.get_current_colors()
        
        # Verificar si los datos están disponibles
        if not self.all_clients_spending:
            error_container = ModernCard(self.theme_manager)
            error_container.setFixedHeight(200)
            error_layout = QVBoxLayout()
            error_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            error_label = QLabel("❌ No se pudieron cargar los datos de gastos")
            error_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Medium))
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet(f"color: {colors['DANGER_RED']}; margin: 30px;")
            
            retry_button = QPushButton("🔄 Reintentar")
            retry_button.setFont(QFont("Segoe UI", 12))
            retry_button.clicked.connect(self.retry_top_data_load)
            
            error_layout.addWidget(error_label)
            error_layout.addWidget(retry_button)
            error_container.setLayout(error_layout)
            self.main_layout.addWidget(error_container)
            return
        
        # Sub-navegación
        self.create_top_sub_navigation()
        
        # Contenido
        self.create_top_content()
    
    def show_top_loading_indicator(self):
        """Mostrar indicador de carga para top clientes"""
        self.clear_layout(self.main_layout)
        colors = self.get_current_colors()
        
        loading_container = ModernCard(self.theme_manager)
        loading_container.setFixedHeight(300)
        loading_layout = QVBoxLayout()
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_layout.setSpacing(20)
        
        icon_label = QLabel("🏆")
        icon_label.setFont(QFont("Segoe UI", 48))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        loading_label = QLabel("Cargando Top Clientes...")
        loading_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setStyleSheet(f"color: {colors['BRIGHT_CYAN']};")
        
        sub_label = QLabel("Calculando gastos totales de todos los clientes\nEsto puede tomar unos segundos...")
        sub_label.setFont(QFont("Segoe UI", 12))
        sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_label.setStyleSheet(f"color: {colors['TEXT_SECONDARY']};")
        
        loading_layout.addWidget(icon_label)
        loading_layout.addWidget(loading_label)
        loading_layout.addWidget(sub_label)
        
        loading_container.setLayout(loading_layout)
        self.main_layout.addWidget(loading_container)

    def load_top_clients_data(self):
        """Cargar datos para top clientes"""
        if self.top_clients_data_loaded or self.top_clients_data_loading:
            return True
        
        try:
            self.top_clients_data_loading = True
            logging.info("Cargando datos de top clientes bajo demanda...")
            
            # Verificar si los datos básicos están cargados
            if not self.data_loaded:
                logging.warning("Datos básicos no cargados, cargando primero...")
                self.load_data()
            
            # Reutilizar datos si ya están cargados del sistema de créditos
            if not hasattr(self, 'all_clients_data') or not self.all_clients_data:
                from database import get_all_clients_data  # Asegúrate de importar
                self.all_clients_data = get_all_clients_data()
                
            if not hasattr(self, 'all_ventas_data') or not self.all_ventas_data:
                from database import get_all_ventas_data  # Asegúrate de importar
                self.all_ventas_data = get_all_ventas_data()
            
            # Calcular gastos totales por cliente
            self.all_clients_spending = self.calculate_all_clients_spending()
            
            logging.info(f"Datos de top clientes cargados: {len(self.all_clients_spending)} clientes analizados")
            
            self.top_clients_data_loaded = True
            self.top_clients_data_loading = False
            return True
            
        except Exception as e:
            logging.error(f"Error al cargar datos de top clientes: {e}")
            self.top_clients_data_loading = False
            self.top_clients_data_loaded = False
            
            # Mostrar error en lugar de cerrar la app
            QMessageBox.critical(self, "❌ Error", 
                            f"Error al cargar datos de top clientes:\n{str(e)}")
            return False

    def calculate_all_clients_spending(self):
        """Calcular el gasto total de todos los clientes"""
        clients_spending = {}
        
        try:
            for client_id, client_data in self.all_clients_data.items():
                total_spent = 0.0
                
                # Buscar todas las ventas del cliente
                for venta_id, venta_data in self.all_ventas_data.items():
                    if venta_data.get('cveCte') == client_id:
                        # Intentar extraer el monto del ticket
                        ticket_data = venta_data.get('datos', '')
                        
                        if ticket_data:
                            # Usar el mismo método que en CreditDetailWindow
                            monto = self.extract_amount_from_ticket_data(ticket_data)
                        else:
                            # Fallback a campos tradicionales
                            monto = venta_data.get('importe', 0) or venta_data.get('total', 0) or 0
                            if isinstance(monto, str):
                                try:
                                    monto = float(monto.replace(',', '').replace('$', ''))
                                except (ValueError, AttributeError):
                                    monto = 0
                        
                        total_spent += monto
                
                if total_spent > 0:
                    clients_spending[client_id] = {
                        'client_data': client_data,
                        'total_spent': total_spent
                    }
            
            return clients_spending
            
        except Exception as e:
            logging.error(f"Error calculando gastos de clientes: {e}")
            return {}

    def extract_amount_from_ticket_data(self, ticket_data):
        """Extraer el monto de los datos del ticket (reutilizado de CreditDetailWindow)"""
        if not ticket_data:
            return 0.0
        
        try:
            lines = ticket_data.split('\r\n')
            
            for line in lines:
                line = line.strip()
                
                if "IMPORTE:" in line:
                    try:
                        importe_part = line.split("IMPORTE:")[-1].strip()
                        importe_clean = importe_part.replace('$', '').replace(',', '').strip()
                        return float(importe_clean)
                    except (ValueError, IndexError):
                        continue
        except Exception:
            pass
        
        return 0.0

    def create_top_sub_navigation(self):
        """Crear sub-navegación para top clientes"""
        colors = self.get_current_colors()
        
        nav_frame = ModernCard(self.theme_manager)
        nav_frame.setFixedHeight(60)
        nav_frame.setContentsMargins(20, 10, 20, 10)
        
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(15)
        
        # Botón Top Clientes
        self.top_clientes_btn = ModernButton("🏆 TOP CLIENTES", self.theme_manager)
        self.top_clientes_btn.setCheckable(True)
        self.top_clientes_btn.setChecked(self.current_top_view == "clientes")
        self.top_clientes_btn.setFixedHeight(35)
        self.top_clientes_btn.setFixedWidth(180)
        self.top_clientes_btn.clicked.connect(lambda: self.switch_top_view("clientes"))
        
        # Botón Top Empresas
        self.top_empresas_btn = ModernButton("🏢 TOP EMPRESAS", self.theme_manager)
        self.top_empresas_btn.setCheckable(True)
        self.top_empresas_btn.setChecked(self.current_top_view == "empresas")
        self.top_empresas_btn.setFixedHeight(35)
        self.top_empresas_btn.setFixedWidth(180)
        self.top_empresas_btn.clicked.connect(lambda: self.switch_top_view("empresas"))
        
        nav_layout.addWidget(self.top_clientes_btn)
        nav_layout.addWidget(self.top_empresas_btn)
        nav_layout.addStretch()
        
        # Estadísticas
        stats_text = self.get_top_stats_text()
        stats_label = QLabel(stats_text)
        stats_label.setFont(QFont("Segoe UI", 10))
        stats_label.setStyleSheet(f"color: {colors['TEXT_SECONDARY']};")
        nav_layout.addWidget(stats_label)
        
        nav_frame.setLayout(nav_layout)
        self.main_layout.addWidget(nav_frame)

    def switch_top_view(self, view):
        """Cambiar vista de top clientes/empresas"""
        if self.current_top_view != view:
            self.current_top_view = view
            
            # Actualizar botones
            self.top_clientes_btn.setChecked(view == "clientes")
            self.top_empresas_btn.setChecked(view == "empresas")
            
            # Actualizar estadísticas
            stats_widgets = self.findChildren(QLabel)
            for widget in stats_widgets:
                if "Total gastado" in widget.text():
                    widget.setText(self.get_top_stats_text())
                    break
            
            # Recrear contenido
            self.recreate_only_top_content()

    def get_top_stats_text(self):
        """Obtener texto de estadísticas para vista actual"""
        filtered_data = self.filter_top_clients_by_type(self.current_top_view)
        
        if filtered_data:
            total_spending = sum(data['total_spent'] for data in filtered_data.values())
            count = len(filtered_data)
            type_name = "Clientes" if self.current_top_view == "clientes" else "Empresas"
            return f"{count} {type_name} • Total gastado: ${total_spending:,.0f}"
        else:
            type_name = "Clientes" if self.current_top_view == "clientes" else "Empresas"
            return f"0 {type_name} • Total gastado: $0"

    def filter_top_clients_by_type(self, client_type):
        """Filtrar clientes por tipo para top"""
        filtered = {}
        
        for client_id, spending_data in self.all_clients_spending.items():
            # Verificar tipo (cliente/empresa)
            client_state = self.client_states.get(client_id, {})
            is_company = client_state.get('company', False)
            
            if client_type == "clientes" and is_company:
                continue
            elif client_type == "empresas" and not is_company:
                continue
            
            filtered[client_id] = spending_data
        
        return filtered

    def create_top_content(self):
        """Crear contenido de top clientes"""
        # Filtrar datos por tipo actual
        filtered_data = self.filter_top_clients_by_type(self.current_top_view)
        
        # Ordenar por gasto total (top 10)
        sorted_clients = sorted(
            filtered_data.items(),
            key=lambda x: x[1]['total_spent'],
            reverse=True
        )[:10]  # Solo top 10
        
        # Crear tabla
        self.create_top_table(sorted_clients)

    def recreate_only_top_content(self):
        """Recrear solo el contenido de top clientes"""
        layout_count = self.main_layout.count()
        
        # Eliminar solo el último widget (el contenido)
        if layout_count > 1:
            last_item = self.main_layout.itemAt(layout_count - 1)
            if last_item and last_item.widget():
                last_item.widget().deleteLater()
                self.main_layout.removeWidget(last_item.widget())
        
        # Crear nuevo contenido
        self.create_top_content()

    def create_top_table(self, sorted_clients):
        """Crear tabla de top clientes"""
        colors = self.get_current_colors()
        theme = self.theme_manager.get_current_theme()
        
        # Card contenedor
        table_card = ModernCard(self.theme_manager)
        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(20, 20, 20, 20)
        table_layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Título con ícono
        title_section = QHBoxLayout()
        title_section.setSpacing(10)
        
        icon_label = QLabel("🏆")
        icon_label.setFont(QFont("Segoe UI", 24))
        
        type_name = "CLIENTES" if self.current_top_view == "clientes" else "EMPRESAS"
        title_label = QLabel(f"TOP 10 {type_name} QUE MÁS HAN GASTADO")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {colors['BRIGHT_CYAN']};")
        
        title_section.addWidget(icon_label)
        title_section.addWidget(title_label)
        
        header_layout.addLayout(title_section)
        header_layout.addStretch()
        
        # Total general del top 10
        if sorted_clients:
            total_top = sum(client[1]['total_spent'] for client in sorted_clients)
            total_label = QLabel(f"Total Top 10: ${total_top:,.0f}")
            total_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
            total_label.setStyleSheet(f"color: {colors['SUCCESS_GREEN']};")
            header_layout.addWidget(total_label)
        
        table_layout.addLayout(header_layout)
        
        # Tabla
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(['Posición', 'Cliente', 'Total Gastado', 'Última Compra', 'Promedio por Compra'])
        
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Configurar columnas
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        
        table.setColumnWidth(0, 80)
        table.setColumnWidth(2, 130)
        table.setColumnWidth(3, 120)
        table.setColumnWidth(4, 150)
        
        # Estilo de tabla premium
        table.setStyleSheet(f"""
            QTableWidget {{
                background: {theme['card_bg_alpha']};
                border: 1px solid rgba({self.hex_to_rgb(colors['BRIGHT_CYAN'])}, 0.3);
                font-size: 12px;
                border-radius: 8px;
            }}
            QTableWidget::item {{
                padding: 10px 8px;
            }}
            QTableWidget::item:selected {{
                background: rgba({self.hex_to_rgb(colors['BRIGHT_CYAN'])}, 0.3);
            }}
            QTableWidget QHeaderView::section {{
                border-bottom: 2px solid {colors['BRIGHT_CYAN']};
                padding: 10px 8px;
                font-size: 11px;
                font-weight: bold;
            }}
        """)
        
        # Poblar tabla
        self.populate_top_table(table, sorted_clients)
        
        table_layout.addWidget(table)
        table_card.setLayout(table_layout)
        self.main_layout.addWidget(table_card)

    def populate_top_table(self, table, sorted_clients):
        """Poblar tabla de top clientes"""
        from datetime import datetime
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont, QColor
        from PyQt6.QtWidgets import QTableWidgetItem
        
        table.setRowCount(len(sorted_clients))
        
        # Colores para posiciones
        position_colors = {
            1: '#FFD700',  # Oro
            2: '#C0C0C0',  # Plata
            3: '#CD7F32',  # Bronce
        }
        
        for row, (client_id, spending_data) in enumerate(sorted_clients):
            try:
                position = row + 1
                client_data = spending_data['client_data']
                total_spent = spending_data['total_spent']
                
                # Posición con medalla
                position_text = f"#{position}"
                if position <= 3:
                    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
                    position_text = f"{medals[position]} {position}"
                
                position_item = QTableWidgetItem(position_text)
                position_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                position_item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                if position in position_colors:
                    position_item.setForeground(QColor(position_colors[position]))
                table.setItem(row, 0, position_item)
                
                # Nombre del cliente
                nombre = client_data.get('nombre', 'Sin nombre')
                name_item = QTableWidgetItem(nombre)
                name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                name_item.setData(Qt.ItemDataRole.UserRole, client_id)
                name_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
                name_item.setToolTip(f"ID: {client_id}\nNombre completo: {nombre}")
                table.setItem(row, 1, name_item)
                
                # Total gastado
                spent_item = QTableWidgetItem(f"${total_spent:,.0f}")
                spent_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                spent_item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                spent_item.setForeground(QColor('#22C55E'))
                table.setItem(row, 2, spent_item)
                
                # Última compra (buscar la fecha más reciente)
                last_purchase = self.get_last_purchase_date(client_id)
                if last_purchase:
                    last_purchase_str = last_purchase.strftime("%d/%m/%Y")
                else:
                    last_purchase_str = "N/A"
                
                last_item = QTableWidgetItem(last_purchase_str)
                last_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                last_item.setFont(QFont("Segoe UI", 9))
                table.setItem(row, 3, last_item)
                
                # Promedio por compra
                purchase_count = self.count_client_purchases(client_id)
                if purchase_count > 0:
                    avg_per_purchase = total_spent / purchase_count
                    avg_text = f"${avg_per_purchase:,.0f}"
                    tooltip = f"{purchase_count} compras total"
                else:
                    avg_text = "N/A"
                    tooltip = "Sin compras registradas"
                
                avg_item = QTableWidgetItem(avg_text)
                avg_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                avg_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
                avg_item.setForeground(QColor('#6366F1'))
                avg_item.setToolTip(tooltip)
                table.setItem(row, 4, avg_item)
                
            except Exception as e:
                logging.error(f"Error poblando fila {row}: {e}")
                continue
        
        # Conectar doble clic
        table.cellDoubleClicked.connect(lambda row, col: self.on_top_client_double_click(table, row))

    def get_last_purchase_date(self, client_id):
        """Obtener la fecha de la última compra del cliente"""
        last_date = None
        
        for venta_id, venta_data in self.all_ventas_data.items():
            if venta_data.get('cveCte') == client_id:
                fecha_str = venta_data.get('fecha')
                if fecha_str:
                    try:
                        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                        if last_date is None or fecha > last_date:
                            last_date = fecha
                    except:
                        continue
        
        return last_date

    def count_client_purchases(self, client_id):
        """Contar el número de compras del cliente"""
        count = 0
        for venta_id, venta_data in self.all_ventas_data.items():
            if venta_data.get('cveCte') == client_id:
                count += 1
        return count

    def on_top_client_double_click(self, table, row):
        """Maneja el doble clic en un cliente del top"""
        try:
            name_item = table.item(row, 1)
            if name_item:
                client_id = name_item.data(Qt.ItemDataRole.UserRole)
                if client_id:
                    # Usar los datos apropiados según disponibilidad
                    if client_id in self.clientes_data:
                        client_data = self.clientes_data[client_id]
                    elif client_id in self.all_clients_data:
                        client_data = self.all_clients_data[client_id]
                    else:
                        QMessageBox.warning(self, "⚠️ Error", "No se pudo obtener la información del cliente")
                        return
                    
                    self.detail_window = ClienteDetalleWindow(self, client_data, client_id)
                    self.detail_window.show()
        except Exception as e:
            logging.error(f"Error al abrir detalles del top cliente: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al abrir detalles del cliente: {str(e)}")

    def retry_top_data_load(self):
        """Reintentar carga de datos de top clientes"""
        self.top_clients_data_loaded = False
        self.top_clients_data_loading = False
        self.create_top_clientes_view()
    
    
    
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
        """Cargar SOLO datos principales desde la base de datos"""
        try:
            logging.info("Cargando datos principales desde la base de datos...")
            colors = self.get_current_colors()
            
            # Mostrar estado de carga
            self.amount_label.setText("⏳ Cargando...")
            self.clientes_label.setText("--")
            self.empresas_label.setText("--")
            self.buro_label.setText("--")
            
            # Cargar SOLO datos principales (más rápido)
            self.clientes_data = get_clients_data()
            self.ventas_data = get_ventas_data()
            self.client_states = get_client_states()
            self.clients_buro = get_clients_without_credit()
            
            logging.info(f"Datos principales cargados: {len(self.clientes_data)} clientes con deuda, "
                        f"{len(self.ventas_data)} ventas pendientes")
            
            self.data_loaded = True
            self.update_debt_info()
            self.last_update_time = time.time()
            self.refresh_current_view()
                            
        except Exception as e:
            logging.error(f"Error al cargar datos principales: {e}")
            self.clientes_data = {}
            self.ventas_data = {}
            self.client_states = {}
            self.clients_buro = {}
            self.data_loaded = False
            
            self.amount_label.setText("❌ Error")
            self.clientes_label.setText("Error")
            self.empresas_label.setText("Error")
            self.buro_label.setText("Error")

    def load_credit_data(self):
        """Cargar datos del sistema de créditos SOLO cuando se necesite"""
        if self.credit_data_loaded or self.credit_data_loading:
            return True  # Ya están cargados o se están cargando
        
        try:
            self.credit_data_loading = True
            logging.info("Cargando datos del sistema de créditos bajo demanda...")
            
            # Mostrar indicador de carga específico para créditos
            self.show_credit_loading_indicator()
            
            # Procesar eventos para mostrar el indicador
            QApplication.processEvents()
            
            # CARGAR DATOS PARA SISTEMA DE CRÉDITOS
            self.all_clients_data = get_all_clients_data()
            self.all_ventas_data = get_all_ventas_data()
            self.clients_credit_scores = get_all_clients_credit_scores()
            self.credit_statistics = get_credit_statistics()
            
            logging.info(f"Datos de créditos cargados: {len(self.all_clients_data)} clientes totales, "
                        f"{len(self.all_ventas_data)} ventas totales, "
                        f"{len(self.clients_credit_scores)} puntajes crediticios calculados")
            
            self.credit_data_loaded = True
            self.credit_data_loading = False
            return True
            
        except Exception as e:
            logging.error(f"Error al cargar datos de créditos: {e}")
            self.credit_data_loading = False
            QMessageBox.critical(self, "❌ Error", 
                            f"Error al cargar datos del sistema de créditos:\n{str(e)}")
            return False
    
    def reload_data(self):
        """Recargar datos - con opción para créditos y top clientes"""
        try:
            logging.info("Recargando datos...")
            
            # Siempre recargar datos principales
            self.load_data()
            
            # Si estamos en vista de créditos, recargar también esos datos
            if self.current_view == "creditos" and self.credit_data_loaded:
                self.credit_data_loaded = False
                self.create_creditos_view()
            # Si estamos en vista de top clientes, recargar también esos datos
            elif self.current_view == "top" and self.top_clients_data_loaded:
                self.top_clients_data_loaded = False
                self.create_top_clientes_view()
            else:
                self.refresh_current_view()
            
            QMessageBox.information(self, "✅ Éxito", "Datos recargados correctamente")
            
        except Exception as e:
            logging.error(f"Error al recargar datos: {e}")
            QMessageBox.critical(self, "❌ Error", f"Error al recargar datos: {str(e)}")

    def clear_credit_data_if_not_needed(self):
        """Liberar memoria de datos de créditos si no se está usando esa vista"""
        if self.current_view != "creditos" and self.credit_data_loaded:
            logging.info("Liberando memoria de datos crediticios (no se están usando)")
            self.all_clients_data = {}
            self.all_ventas_data = {}
            self.clients_credit_scores = {}
            self.credit_statistics = {}
            self.credit_data_loaded = False
    
    def refresh_current_view(self):
        """Actualizar la vista actual después de cargar datos"""
        if self.current_view == "buro":
            self.create_buro_view()
        elif self.current_view == "creditos":
            self.create_creditos_view()
        elif self.current_view == "top":  # AGREGAR ESTA LÍNEA
            self.create_top_clientes_view()
        else:
            self.create_clientes_view()

    def show_credit_loading_indicator(self):
        """Mostrar indicador de carga específico para créditos"""
        self.clear_layout(self.main_layout)
        colors = self.get_current_colors()
        
        loading_container = ModernCard(self.theme_manager)
        loading_container.setFixedHeight(300)
        loading_layout = QVBoxLayout()
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_layout.setSpacing(20)
        
        # Ícono de carga más llamativo
        icon_label = QLabel("💳")
        icon_label.setFont(QFont("Segoe UI", 48))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Mensaje principal
        loading_label = QLabel("Cargando Sistema de Créditos...")
        loading_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setStyleSheet(f"color: {colors['BRIGHT_CYAN']};")
        
        # Mensaje secundario
        sub_label = QLabel("Analizando historial crediticio de todos los clientes\nEsto puede tomar unos segundos...")
        sub_label.setFont(QFont("Segoe UI", 12))
        sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_label.setStyleSheet(f"color: {colors['TEXT_SECONDARY']};")
        
        # Barra de progreso visual (solo decorativa)
        progress_container = QWidget()
        progress_container.setFixedHeight(4)
        progress_container.setStyleSheet(f"""
            QWidget {{
                background: {colors['CARD_BG']};
                border-radius: 2px;
            }}
        """)
        
        loading_layout.addWidget(icon_label)
        loading_layout.addWidget(loading_label)
        loading_layout.addWidget(sub_label)
        loading_layout.addWidget(progress_container)
        
        loading_container.setLayout(loading_layout)
        self.main_layout.addWidget(loading_container)
   
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