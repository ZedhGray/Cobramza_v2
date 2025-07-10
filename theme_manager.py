# theme_manager.py
import json
import os
import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QRadioButton, QButtonGroup, QFrame, 
                            QGraphicsDropShadowEffect, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QIcon, QPainter, QPainterPath, QLinearGradient

class ThemeManager:
    """Administrador de temas para la aplicación"""
    
    # Tema Oscuro (actual)
    DARK_THEME = {
        'name': 'dark',
        'DARK_BG': "#0a0a0a",
        'CARD_BG': "#16213e", 
        'ACCENT_BLUE': "#0f3460",
        'BRIGHT_CYAN': "#00b4d8",
        'LOGO_FILE': "Logo-Blanco.png",
        'TITLE_TEXT': "#ffffff",
        'TEXT_PRIMARY': "#ffffff",
        'TEXT_SECONDARY': "#a0a0a0",
        'SUCCESS_GREEN': "#4ade80",
        'WARNING_ORANGE': "#fb923c",
        'DANGER_RED': "#ef4444",
        'PROMISE_PURPLE': "#a855f7",
        'gradient_start': "#0a0a0a",
        'gradient_mid1': "#1a1a2e",
        'gradient_mid2': "#16213e",
        'gradient_end': "#0a0a0a",
        'card_bg_alpha': "rgba(255, 255, 255, 0.08)",
        'border_alpha': "rgba(255, 255, 255, 0.2)",
        'hover_alpha': "rgba(255, 255, 255, 0.15)"
    }
    
    # Tema Claro (nuevo)
    LIGHT_THEME = {
        'name': 'light',
        'DARK_BG': "#f8f9fa",
        'CARD_BG': "#ffffff",
        'LOGO_FILE': "Logo.png",
        'ACCENT_BLUE': "#1976d2",
        'BRIGHT_CYAN': "#0288d1",
        'TITLE_TEXT': "#000000",
        'TEXT_PRIMARY': "#212529",
        'TEXT_SECONDARY': "#6c757d",
        'SUCCESS_GREEN': "#28a745",
        'WARNING_ORANGE': "#fd7e14",
        'DANGER_RED': "#dc3545",
        'PROMISE_PURPLE': "#6f42c1",
        'gradient_start': "#f8f9fa",
        'gradient_mid1': "#e9ecef",
        'gradient_mid2': "#dee2e6",
        'gradient_end': "#f8f9fa",
        'card_bg_alpha': "rgba(0, 0, 0, 0.05)",
        'border_alpha': "rgba(0, 0, 0, 0.1)",
        'hover_alpha': "rgba(0, 0, 0, 0.08)"
    }
    
    def __init__(self):
        self.config_file = "theme_config.json"
        self.current_theme = self.load_theme_preference()
    
    def load_theme_preference(self):
        """Carga la preferencia de tema guardada"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    theme_name = config.get('theme', 'dark')
                    return self.LIGHT_THEME if theme_name == 'light' else self.DARK_THEME
            return self.DARK_THEME
        except Exception as e:
            logging.error(f"Error cargando preferencia de tema: {e}")
            return self.DARK_THEME
    
    def save_theme_preference(self, theme_name):
        """Guarda la preferencia de tema"""
        try:
            config = {'theme': theme_name}
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
            logging.info(f"Tema guardado: {theme_name}")
        except Exception as e:
            logging.error(f"Error guardando preferencia de tema: {e}")
    
    def set_theme(self, theme_name):
        """Establece el tema actual"""
        if theme_name == 'light':
            self.current_theme = self.LIGHT_THEME
        else:
            self.current_theme = self.DARK_THEME
        
        self.save_theme_preference(theme_name)
    
    def get_current_theme(self):
        """Obtiene el tema actual"""
        return self.current_theme
    
    def is_dark_theme(self):
        """Verifica si el tema actual es oscuro"""
        return self.current_theme['name'] == 'dark'

class ModernCard(QFrame):
    """Tarjeta moderna que adapta su estilo según el tema"""
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

class ModernButton(QPushButton):
    """Botón moderno que adapta su estilo según el tema"""
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

class SettingsDialog(QDialog):
    """Diálogo de configuración con opciones de tema"""
    theme_changed = pyqtSignal(str)  # Señal emitida cuando cambia el tema
    
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setWindowTitle("⚙️ Configuración")
        self.setFixedSize(400, 300)
        
        # ESTABLECER ÍCONO
        try:
            icon_files = ['lga2.ico', 'lga.ico', 'logo.ico', 'icon.ico']
            for icon_file in icon_files:
                if os.path.exists(icon_file):
                    self.setWindowIcon(QIcon(icon_file))
                    break
        except Exception as e:
            logging.error(f"Error al establecer ícono de configuración: {e}")
        
        # Centrar respecto al padre
        if parent:
            parent_geo = parent.geometry()
            x = parent_geo.x() + (parent_geo.width() - 400) // 2
            y = parent_geo.y() + (parent_geo.height() - 300) // 2
            self.move(x, y)
        
        self.initUI()
        
    def initUI(self):
        """Inicializa la interfaz de usuario"""
        theme = self.theme_manager.get_current_theme()
        
        # Aplicar estilo según el tema actual
        if self.theme_manager.is_dark_theme():
            bg_color = theme['DARK_BG']
            text_color = theme['TEXT_PRIMARY']
            secondary_text = theme['TEXT_SECONDARY']
            accent_color = theme['BRIGHT_CYAN']
            card_bg = "rgba(255, 255, 255, 0.08)"
            border_color = "rgba(255, 255, 255, 0.2)"
        else:
            bg_color = theme['DARK_BG']
            text_color = theme['TEXT_PRIMARY']
            secondary_text = theme['TEXT_SECONDARY']
            accent_color = theme['BRIGHT_CYAN']
            card_bg = "rgba(255, 255, 255, 0.9)"
            border_color = "rgba(0, 0, 0, 0.1)"
        
        self.setStyleSheet(f"""
            QDialog {{
                background: {bg_color};
                color: {text_color};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            
            QLabel {{
                background: transparent;
                color: {text_color};
            }}
            
            QLabel.title {{
                font-size: 16px;
                font-weight: bold;
                color: {accent_color};
                padding: 10px;
            }}
            
            QLabel.section {{
                font-size: 12px;
                font-weight: bold;
                color: {secondary_text};
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-top: 10px;
            }}
            
            QRadioButton {{
                background: transparent;
                color: {text_color};
                font-size: 11px;
                padding: 8px;
                spacing: 10px;
            }}
            
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 2px solid {border_color.replace('rgba', '').replace(')', '').replace('(', '').split(',')[0]};
            }}
            
            QRadioButton::indicator:checked {{
                background: {accent_color};
                border: 2px solid {accent_color};
            }}
            
            QRadioButton::indicator:hover {{
                border: 2px solid {accent_color};
            }}
            
            QPushButton {{
                background: {card_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 11px;
            }}
            
            QPushButton:hover {{
                background: rgba({self.hex_to_rgb(accent_color)}, 0.2);
                border-color: {accent_color};
            }}
            
            QPushButton[class="primary"] {{
                background: {accent_color};
                color: white;
                border-color: {accent_color};
            }}
            
            QPushButton[class="primary"]:hover {{
                background: rgba({self.hex_to_rgb(accent_color)}, 0.8);
            }}
            
            QFrame[frameShape="4"] {{
                background: {border_color};
                max-height: 1px;
                margin: 10px 0;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("⚙️ CONFIGURACIÓN")
        title_label.setProperty("class", "title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(separator)
        
        # Sección de apariencia
        appearance_label = QLabel("🎨 APARIENCIA")
        appearance_label.setProperty("class", "section")
        layout.addWidget(appearance_label)
        
        # Opciones de tema
        theme_frame = QFrame()
        theme_frame.setStyleSheet(f"""
            QFrame {{
                background: {card_bg};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        theme_layout = QVBoxLayout()
        theme_layout.setSpacing(8)
        
        # Grupo de botones de radio
        self.theme_group = QButtonGroup()
        
        # Opción tema oscuro
        self.dark_radio = QRadioButton("🌙 Modo Oscuro")
        self.dark_radio.setToolTip("Tema oscuro para uso en ambientes con poca luz")
        self.theme_group.addButton(self.dark_radio)
        theme_layout.addWidget(self.dark_radio)
        
        # Opción tema claro
        self.light_radio = QRadioButton("☀️ Modo Claro")
        self.light_radio.setToolTip("Tema claro para uso en ambientes con buena iluminación")
        self.theme_group.addButton(self.light_radio)
        theme_layout.addWidget(self.light_radio)
        
        # Establecer selección actual
        if self.theme_manager.is_dark_theme():
            self.dark_radio.setChecked(True)
        else:
            self.light_radio.setChecked(True)
        
        theme_frame.setLayout(theme_layout)
        layout.addWidget(theme_frame)
        
        # Espaciador
        layout.addStretch()
        
        # Botones de acción
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.clicked.connect(self.reject)
        
        apply_btn = QPushButton("✅ Aplicar")
        apply_btn.setProperty("class", "primary")
        apply_btn.clicked.connect(self.apply_changes)
        apply_btn.setDefault(True)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(apply_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def hex_to_rgb(self, hex_color):
        """Convertir color hex a RGB"""
        hex_color = hex_color.lstrip('#')
        return ', '.join(str(int(hex_color[i:i+2], 16)) for i in (0, 2, 4))
    
    def apply_changes(self):
        """Aplica los cambios de configuración"""
        try:
            # Determinar tema seleccionado
            if self.light_radio.isChecked():
                new_theme = 'light'
            else:
                new_theme = 'dark'
            
            # Solo cambiar si es diferente al actual
            current_theme_name = self.theme_manager.get_current_theme()['name']
            if new_theme != current_theme_name:
                self.theme_manager.set_theme(new_theme)
                self.theme_changed.emit(new_theme)
                
                QMessageBox.information(
                    self, 
                    "✅ Configuración Aplicada", 
                    "Los cambios se han aplicado correctamente.\n"
                    "Algunas partes de la interfaz pueden requerir reiniciar la aplicación."
                )
            
            self.accept()
            
        except Exception as e:
            logging.error(f"Error aplicando configuración: {e}")
            QMessageBox.critical(
                self, 
                "❌ Error", 
                f"Error al aplicar la configuración: {str(e)}"
            )