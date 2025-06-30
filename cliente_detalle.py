def show_note_dialog(self):
        """Muestra el diálogo para agregar una nota con manejo de errores"""
        try:
            dialog = NoteDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                note_text = dialog.get_note_text()
                if not note_text:
                    QMessageBox.warning(self, "Advertencia", "Por favor ingrese una nota")
                    return
                    
                if self.save_note_to_db(self.client_id, note_text):
                    # Recargar notas
                    self.load_client_notes()
                    QMessageBox.information(self, "Éxito", "Nota guardada correctamente")
                else:
                    QMessageBox.warning(self, "Error", "No se pudo guardar la nota")
        except Exception as e:
            logging.error(f"Error en diálogo de nota: {e}")
            QMessageBox.critical(self, "Error", f"Error inesperado: {str(e)}")# cliente_detalle.py
import sys
import logging
import webbrowser
import re
from datetime import datetime, date
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QFrame, QScrollArea, QTextEdit, QDialog, 
                            QFormLayout, QLineEdit, QComboBox, QCalendarWidget,
                            QMessageBox, QSplitter, QGridLayout)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor

# Importar funciones de database
from database import (get_db_connection, get_client_notes, update_promise_date, 
                     update_telefono3, format_phone_number, UserSession)

class ClienteDetalleWindow(QWidget):
    def __init__(self, parent, client_data, client_id):
        super().__init__()
        self.parent = parent
        self.client_data = client_data
        self.client_id = client_id
        
        # Colores corporativos
        self.COLOR_ROJO = "#E31837"
        self.COLOR_NEGRO = "#333333"
        self.COLOR_BLANCO = "#FFFFFF"
        self.COLOR_GRIS = "#F5F5F5"
        self.COLOR_GRIS_CLARO = "#EFEFEF"
        self.COLOR_ROJO_HOVER = "#C41230"
        self.COLOR_GRIS_HOVER = "#E8E8E8"
        
        self.initUI()
        self.load_client_notes()
        
    def initUI(self):
        """Inicializa la interfaz de usuario"""
        self.setWindowTitle(f"Detalle Cliente - {self.client_data.get('nombre', 'Sin nombre')}")
        
        # Centrar la ventana correctamente
        window_width = 1200
        window_height = 800
        screen = self.screen()
        screen_width = screen.availableGeometry().width()
        screen_height = screen.availableGeometry().height()
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.setGeometry(x, y, window_width, window_height)
        self.setFixedSize(window_width, window_height)  # Fijar el tamaño
        
        # Aplicar estilos CSS
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.COLOR_BLANCO};
                color: {self.COLOR_NEGRO};
                font-family: Arial;
            }}
            
            QFrame[frameShape="4"] {{
                background-color: {self.COLOR_GRIS};
                border: none;
                max-height: 1px;
            }}
            
            QPushButton {{
                background-color: {self.COLOR_BLANCO};
                color: {self.COLOR_NEGRO};
                border: 1px solid {self.COLOR_GRIS};
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {self.COLOR_GRIS_HOVER};
            }}
            
            QPushButton.danger {{
                background-color: {self.COLOR_ROJO};
                color: white;
                border: 1px solid {self.COLOR_ROJO};
            }}
            
            QPushButton.danger:hover {{
                background-color: {self.COLOR_ROJO_HOVER};
            }}
            
            QLabel.title {{
                font-size: 16px;
                font-weight: bold;
                color: {self.COLOR_NEGRO};
                padding: 10px;
            }}
            
            QLabel.field-label {{
                font-weight: bold;
                color: {self.COLOR_NEGRO};
            }}
            
            QFrame.section {{
                border: 2px solid {self.COLOR_GRIS};
                border-radius: 8px;
                background-color: {self.COLOR_BLANCO};
                margin: 5px;
            }}
            
            QFrame.note-frame {{
                background-color: {self.COLOR_GRIS_CLARO};
                border: 1px solid {self.COLOR_GRIS};
                border-radius: 4px;
                padding: 8px;
                margin: 5px;
            }}
        """)
        
        # Layout principal horizontal
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Splitter para dividir contenido principal y panel lateral
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Área de contenido principal (izquierda)
        self.create_main_content_area(splitter)
        
        # Panel de control lateral (derecha)
        self.create_control_panel(splitter)
        
        # Configurar proporciones del splitter
        splitter.setSizes([800, 300])
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        
    def create_main_content_area(self, parent):
        """Crea el área principal de contenido"""
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Frame de información del cliente
        self.create_cliente_frame(main_layout)
        
        # Frame de timeline con scroll
        self.create_timeline_frame(main_layout)
        
        # Frame de adeudos
        self.create_adeudo_frame(main_layout)
        
        main_widget.setLayout(main_layout)
        parent.addWidget(main_widget)
        
    def create_cliente_frame(self, layout):
        """Crea el frame con información del cliente"""
        cliente_frame = QFrame()
        cliente_frame.setProperty("class", "section")
        cliente_layout = QVBoxLayout()
        
        # Título
        title_label = QLabel("INFORMACIÓN DEL CLIENTE")
        title_label.setProperty("class", "title")
        cliente_layout.addWidget(title_label)
        
        # Grid para información del cliente
        info_widget = QWidget()
        info_layout = QGridLayout()
        
        # Crear campos de información
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
            value = QLabel(str(value_text))
            
            info_layout.addWidget(label, row, 0)
            info_layout.addWidget(value, row, 1)
            row += 1
        
        info_widget.setLayout(info_layout)
        cliente_layout.addWidget(info_widget)
        
        cliente_frame.setLayout(cliente_layout)
        layout.addWidget(cliente_frame)
        
    def create_timeline_frame(self, layout):
        """Crea el frame de timeline con scroll"""
        timeline_frame = QFrame()
        timeline_frame.setProperty("class", "section")
        timeline_layout = QVBoxLayout()
        
        # Título
        title_label = QLabel("LÍNEA DE TIEMPO")
        title_label.setProperty("class", "title")
        timeline_layout.addWidget(title_label)
        
        # Botón de recarga para debugging
        reload_btn = QPushButton("🔄 Recargar Notas")
        reload_btn.clicked.connect(self.load_client_notes)
        reload_btn.setMaximumWidth(150)
        timeline_layout.addWidget(reload_btn)
        
        # Área de scroll para las notas
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(300)
        scroll_area.setMaximumHeight(400)
        
        # Widget contenedor para las notas
        self.notes_widget = QWidget()
        self.notes_layout = QVBoxLayout()
        self.notes_widget.setLayout(self.notes_layout)
        
        scroll_area.setWidget(self.notes_widget)
        timeline_layout.addWidget(scroll_area)
        
        timeline_frame.setLayout(timeline_layout)
        layout.addWidget(timeline_frame)
        
    def create_adeudo_frame(self, layout):
        """Crea el frame de adeudos con altura fija y scroll"""
        adeudo_frame = QFrame()
        adeudo_frame.setProperty("class", "section")
        adeudo_layout = QVBoxLayout()
        
        # Título
        title_label = QLabel("ADEUDOS")
        title_label.setProperty("class", "title")
        adeudo_layout.addWidget(title_label)
        
        # Área de scroll con altura fija para adeudos
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedHeight(200)  # Altura fija
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Widget contenedor para los adeudos
        adeudos_widget = QWidget()
        adeudos_layout = QVBoxLayout()
        adeudos_widget.setLayout(adeudos_layout)
        
        # Obtener y mostrar adeudos
        adeudos = self.get_adeudos_from_db()
        
        if not adeudos:
            no_adeudos_label = QLabel("No hay adeudos registrados")
            no_adeudos_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            adeudos_layout.addWidget(no_adeudos_label)
        else:
            # Crear lista de adeudos
            total = 0
            for adeudo in adeudos:
                adeudo_row = QFrame()
                adeudo_row.setProperty("class", "note-frame")
                row_layout = QHBoxLayout()
                
                # Información del ticket
                ticket_info = QLabel(f"Ticket #{adeudo['ticket']} - {adeudo['fecha']}")
                ticket_info.setStyleSheet("color: blue; text-decoration: underline; cursor: pointer;")
                ticket_info.mousePressEvent = lambda event, data=adeudo: self.show_ticket_detail(data)
                
                monto_label = QLabel(f"${adeudo['monto']:,.2f}")
                monto_label.setAlignment(Qt.AlignmentFlag.AlignRight)
                
                row_layout.addWidget(ticket_info)
                row_layout.addWidget(monto_label)
                
                adeudo_row.setLayout(row_layout)
                adeudos_layout.addWidget(adeudo_row)
                
                total += adeudo['monto']
            
            # Espaciador para empujar el total hacia abajo
            adeudos_layout.addStretch()
            
            # Total al final
            total_frame = QFrame()
            total_layout = QHBoxLayout()
            
            total_label = QLabel("TOTAL:")
            total_label.setProperty("class", "field-label")
            
            total_amount = QLabel(f"${total:,.2f}")
            total_amount.setStyleSheet(f"color: {self.COLOR_ROJO}; font-weight: bold; font-size: 14px;")
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
        """Crea el panel de control lateral"""
        control_widget = QWidget()
        control_widget.setFixedWidth(280)
        control_layout = QVBoxLayout()
        control_layout.setContentsMargins(10, 10, 10, 10)
        
        # Título del panel
        title_label = QLabel("CONTROLES")
        title_label.setProperty("class", "title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        control_layout.addWidget(title_label)
        
        # Botón agregar nota
        add_note_btn = QPushButton("+ Agregar Nota")
        add_note_btn.clicked.connect(self.show_note_dialog)
        control_layout.addWidget(add_note_btn)
        
        # Botón agregar teléfono
        add_phone_btn = QPushButton("+ Teléfono")
        add_phone_btn.clicked.connect(self.show_telefono_dialog)
        control_layout.addWidget(add_phone_btn)
        
        # Botones de notas rápidas
        quick_notes = [
            ("Buzón", "Mandó a buzón de voz"),
            ("No disponible", "El número marcado no está disponible"),
            ("Notifico a WhatsApp", "Se le notificó vía WhatsApp")
        ]
        
        for btn_text, note_text in quick_notes:
            btn = QPushButton(btn_text)
            btn.clicked.connect(lambda checked, text=note_text: self.create_quick_note(text))
            control_layout.addWidget(btn)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        control_layout.addWidget(separator)
        
        # Botón fecha promesa
        calendar_btn = QPushButton("Fecha Promesa")
        calendar_btn.clicked.connect(self.show_calendar_dialog)
        control_layout.addWidget(calendar_btn)
        
        # Separador
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        control_layout.addWidget(separator2)
        
        # Botón empresa
        self.company_btn = QPushButton()
        self.update_company_button()
        self.company_btn.clicked.connect(self.toggle_company)
        control_layout.addWidget(self.company_btn)
        
        # Botón buró
        self.buro_btn = QPushButton()
        self.update_buro_button()
        self.buro_btn.clicked.connect(self.toggle_buro)
        control_layout.addWidget(self.buro_btn)
        
        # Separador
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.Shape.HLine)
        control_layout.addWidget(separator3)
        
        # Botón WhatsApp
        whatsapp_btn = QPushButton("Conversación WhatsApp")
        whatsapp_btn.clicked.connect(self.abrir_whatsapp)
        control_layout.addWidget(whatsapp_btn)
        
        # Botón llamada
        phone_btn = QPushButton("Llamar por teléfono")
        phone_btn.clicked.connect(self.realizar_llamada)
        control_layout.addWidget(phone_btn)
        
        # Espaciador
        control_layout.addStretch()
        
        control_widget.setLayout(control_layout)
        parent.addWidget(control_widget)
        
    def load_client_notes(self):
        """Carga las notas del cliente usando consulta directa a la base de datos"""
        try:
            logging.info(f"Cargando notas para cliente: {self.client_id}")
            
            # Hacer consulta directa a la base de datos
            conn = get_db_connection()
            if not conn:
                logging.error("No se pudo conectar a la base de datos")
                return
            
            cursor = conn.cursor()
            
            # Consulta directa
            query = """
                SELECT id, note_text, created_at, ISNULL(user_name, 'Sistema') as user_name
                FROM Notes
                WHERE client_id = ?
                ORDER BY created_at DESC
            """
            
            cursor.execute(query, (self.client_id,))
            rows = cursor.fetchall()
            
            logging.info(f"Filas obtenidas de la base de datos: {len(rows)}")
            
            notes = []
            for row in rows:
                try:
                    # Log de cada fila
                    logging.info(f"Procesando fila: {row}")
                    
                    note = {
                        'id': row[0] if row[0] else 0,
                        'text': row[1] if row[1] else 'Sin texto',
                        'timestamp': row[2] if row[2] else datetime.now(),
                        'user_name': row[3] if row[3] else 'Sistema'
                    }
                    notes.append(note)
                    logging.info(f"Nota procesada: {note}")
                    
                except Exception as e:
                    logging.error(f"Error procesando fila {row}: {e}")
                    continue
            
            conn.close()
            
            logging.info(f"Total de notas a mostrar: {len(notes)}")
            self.refresh_notes_display(notes)
            
        except Exception as e:
            logging.error(f"Error al cargar notas: {e}")
            import traceback
            logging.error(f"Traceback completo: {traceback.format_exc()}")
            # Mostrar lista vacía en caso de error
            self.refresh_notes_display([])
        
    def refresh_notes_display(self, notes):
        """Actualiza la visualización de las notas"""
        try:
            logging.info(f"refresh_notes_display llamada con {len(notes)} notas")
            
            # Verificar que notes_layout existe
            if not hasattr(self, 'notes_layout') or not self.notes_layout:
                logging.error("notes_layout no existe o es None")
                return
            
            # Limpiar notas existentes de forma segura
            for i in reversed(range(self.notes_layout.count())): 
                child = self.notes_layout.itemAt(i)
                if child and child.widget():
                    widget = child.widget()
                    widget.setParent(None)
                    widget.deleteLater()
            
            # Agregar nuevas notas
            for idx, note in enumerate(notes):
                logging.info(f"Agregando nota {idx}: {note}")
                
                note_frame = QFrame()
                note_frame.setProperty("class", "note-frame")
                note_layout = QVBoxLayout()
                
                # Header con fecha y usuario
                header_layout = QHBoxLayout()
                
                timestamp = note['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                date_label = QLabel(f"Nota del {timestamp}")
                date_label.setProperty("class", "field-label")
                
                user_label = QLabel(f"Por: {note['user_name']}")
                user_label.setStyleSheet("font-style: italic; color: gray;")
                
                header_layout.addWidget(date_label)
                header_layout.addWidget(user_label)
                header_layout.addStretch()
                
                # Texto de la nota
                text_label = QLabel(note['text'])
                text_label.setWordWrap(True)
                text_label.setStyleSheet("margin-top: 5px;")
                
                note_layout.addLayout(header_layout)
                note_layout.addWidget(text_label)
                
                note_frame.setLayout(note_layout)
                self.notes_layout.addWidget(note_frame)
                
                logging.info(f"Nota {idx} agregada correctamente")
            
            # Agregar espaciador al final
            self.notes_layout.addStretch()
            
            logging.info("refresh_notes_display completado exitosamente")
                
        except Exception as e:
            logging.error(f"Error en refresh_notes_display: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
        
    def show_note_dialog(self):
        """Muestra el diálogo para agregar una nota"""
        dialog = NoteDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            note_text = dialog.get_note_text()
            if note_text and self.save_note_to_db(self.client_id, note_text):
                self.load_client_notes()
            else:
                QMessageBox.warning(self, "Error", "No se pudo guardar la nota")
                
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
                
    def create_quick_note(self, note_text):
        """Crea una nota rápida"""
        if self.save_note_to_db(self.client_id, note_text):
            self.load_client_notes()
        else:
            QMessageBox.warning(self, "Error", "No se pudo guardar la nota")
            
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
        text = "No es empresa" if is_company else "Empresa"
        if is_company:
            self.company_btn.setProperty("class", "danger")
        else:
            self.company_btn.setProperty("class", "")
        self.company_btn.setText(text)
        self.company_btn.style().polish(self.company_btn)
        
    def update_buro_button(self):
        """Actualiza el botón de buró"""
        is_buro = self.get_buro_state(self.client_id)
        text = "En Buró" if is_buro else "Buró"
        if is_buro:
            self.buro_btn.setProperty("class", "danger")
        else:
            self.buro_btn.setProperty("class", "")
        self.buro_btn.setText(text)
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
    
    def show_note_dialog(self):
        """Muestra el diálogo para agregar una nota con manejo de errores"""
        try:
            dialog = NoteDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                note_text = dialog.get_note_text()
                if not note_text:
                    QMessageBox.warning(self, "Advertencia", "Por favor ingrese una nota")
                    return
                    
                if self.save_note_to_db(self.client_id, note_text):
                    # Recargar notas
                    self.load_client_notes()
                    QMessageBox.information(self, "Éxito", "Nota guardada correctamente")
                else:
                    QMessageBox.warning(self, "Error", "No se pudo guardar la nota")
        except Exception as e:
            logging.error(f"Error en diálogo de nota: {e}")
            QMessageBox.critical(self, "Error", f"Error inesperado: {str(e)}")
            
    def create_quick_note(self, note_text):
        """Crea una nota rápida"""
        try:
            if self.save_note_to_db(self.client_id, note_text):
                self.load_client_notes()
            else:
                QMessageBox.warning(self, "Error", "No se pudo guardar la nota")
        except Exception as e:
            logging.error(f"Error en nota rápida: {e}")
            QMessageBox.critical(self, "Error", f"Error inesperado: {str(e)}")
            
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


# Diálogos auxiliares
class NoteDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Agregar Nota")
        self.setFixedSize(450, 250)
        
        # Centrar respecto al padre
        if parent:
            parent_geo = parent.geometry()
            x = parent_geo.x() + (parent_geo.width() - 450) // 2
            y = parent_geo.y() + (parent_geo.height() - 250) // 2
            self.move(x, y)
        
        layout = QVBoxLayout()
        
        # Título
        title_label = QLabel("Agregar nueva nota")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Campo de texto
        layout.addWidget(QLabel("Nota:"))
        self.text_edit = QTextEdit()
        self.text_edit.setMaximumHeight(120)
        self.text_edit.setPlaceholderText("Escriba aquí los detalles de la nota...")
        layout.addWidget(self.text_edit)
        
        # Contador de caracteres
        self.char_count = QLabel("0 caracteres")
        self.char_count.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.char_count)
        
        # Conectar el contador
        self.text_edit.textChanged.connect(self.update_char_count)
        
        # Botones
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Guardar Nota")
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
        self.setWindowTitle("Agregar/Actualizar Teléfono")
        self.setFixedSize(400, 180)
        
        # Centrar respecto al padre
        if parent:
            parent_geo = parent.geometry()
            x = parent_geo.x() + (parent_geo.width() - 400) // 2
            y = parent_geo.y() + (parent_geo.height() - 180) // 2
            self.move(x, y)
        
        layout = QVBoxLayout()
        
        if current_phone and current_phone.strip():
            current_label = QLabel(f"Teléfono actual: {current_phone}")
            current_label.setStyleSheet("color: #E31837; font-weight: bold;")
            layout.addWidget(current_label)
        
        layout.addWidget(QLabel("Nuevo teléfono:"))
        self.phone_edit = QLineEdit(current_phone)
        self.phone_edit.setPlaceholderText("Ej: 7551234567")
        layout.addWidget(self.phone_edit)
        
        # Botones
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Guardar")
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


class CalendarDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Fecha de Promesa")
        self.setFixedSize(350, 400)
        
        layout = QVBoxLayout()
        
        # Título
        layout.addWidget(QLabel("Seleccione la fecha de promesa:"))
        
        # Calendario
        self.calendar = QCalendarWidget()
        self.calendar.setMinimumDate(QDate.currentDate())
        layout.addWidget(self.calendar)
        
        # Método de pago
        payment_layout = QHBoxLayout()
        payment_layout.addWidget(QLabel("Método de pago:"))
        
        self.payment_combo = QComboBox()
        self.payment_combo.addItems([
            "No especificado", "Efectivo", "Tarjeta", 
            "Transferencia", "Cheque"
        ])
        payment_layout.addWidget(self.payment_combo)
        
        layout.addLayout(payment_layout)
        
        # Botones
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Guardar")
        save_btn.clicked.connect(self.accept)
        save_btn.setProperty("class", "danger")
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def get_selection(self):
        qdate = self.calendar.selectedDate()
        python_date = date(qdate.year(), qdate.month(), qdate.day())
        payment_method = self.payment_combo.currentText()
        return python_date, payment_method


class TicketDetailDialog(QDialog):
    def __init__(self, parent, ticket_data):
        super().__init__(parent)
        self.setWindowTitle(f"Ticket #{ticket_data['ticket']}")
        self.setFixedSize(450, 600)
        
        layout = QVBoxLayout()
        
        # Área de scroll para el contenido del ticket
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Widget contenedor
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        
        # Procesar y mostrar el contenido del ticket
        lines = ticket_data['datos'].split('\r\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Crear etiqueta para cada línea
            line_label = QLabel(line)
            line_label.setFont(QFont("Courier", 9))
            line_label.setWordWrap(True)
            
            # Estilos especiales para diferentes tipos de líneas
            if "GARCIA RINES" in line:
                line_label.setFont(QFont("Courier", 11, QFont.Weight.Bold))
                line_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            elif line.startswith("TICKET:") or line.startswith("CLIENTE:"):
                line_label.setFont(QFont("Courier", 9, QFont.Weight.Bold))
            elif "CANT" in line and "DESCRIPCION" in line:
                line_label.setFont(QFont("Courier", 9, QFont.Weight.Bold))
            elif "ARTICULOS" in line or "IMPORTE:" in line or "ADEUDA:" in line:
                line_label.setAlignment(Qt.AlignmentFlag.AlignRight)
                line_label.setFont(QFont("Courier", 9, QFont.Weight.Bold))
            elif "DEBO Y PAGARE" in line or "ACEPTO" in line:
                line_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                line_label.setFont(QFont("Courier", 9, QFont.Weight.Bold))
            
            content_layout.addWidget(line_label)
        
        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        
        layout.addWidget(scroll_area)
        
        # Botón cerrar
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        close_btn.setProperty("class", "danger")
        layout.addWidget(close_btn)
        
        self.setLayout(layout)