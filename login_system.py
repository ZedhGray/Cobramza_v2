import tkinter as tk
from tkinter import ttk
import re
from datetime import datetime
from database import validate_user, UserSession

def extract_ticket_number(ticket_text):
    """Extract ticket number from ticket text using regex"""
    if not ticket_text:
        return "N/A"
    ticket_text = str(ticket_text)
    match = re.search(r'TICKET:(\d+)', ticket_text)
    if match:
        return match.group(1)
    # If it's just a number, return it directly
    return ticket_text if ticket_text.isdigit() else "N/A"

class LoadingSplash:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Cobranza v1.2")
        self.user_session = UserSession()
        
        # Configuración de la ventana
        window_width = 350
        window_height = 450
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # Colores y estilos
        self.COLORS = {
            'primary': '#e31837',      # Rojo Empresa color
            'secondary': '#f8f9fa',    # Gris muy claro
            'text': '#202124',         # Casi negro
            'error': '#d93025',        # Rojo error
            'white': '#ffffff',        # Blanco
            'border': '#dadce0'        # Gris borde
        }
        
        # Configuración de la ventana
        self.root.overrideredirect(True)
        self.root.configure(bg=self.COLORS['white'])
        
        # Crear borde personalizado
        self.create_window_border()
        
        # Frame principal con sombra
        self.main_frame = tk.Frame(
            self.root,
            bg=self.COLORS['white'],
            highlightbackground=self.COLORS['border'],
            highlightthickness=1
        )
        self.main_frame.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Logo o título
        self.create_header()
        
        # Frame de carga
        self.loading_frame = tk.Frame(self.main_frame, bg=self.COLORS['white'])
        self.loading_frame.pack(expand=True, fill='both', padx=20, pady=10)
        
        # Status y progreso
        self.create_loading_widgets()
        
        # Frame de login
        self.create_login_frame()
        
        # Ocultar login inicialmente
        self.login_frame.pack_forget()

    def create_window_border(self):
        """Crea una barra de título personalizada"""
        title_bar = tk.Frame(
            self.root,
            bg=self.COLORS['primary'],
            height=30
        )
        title_bar.pack(fill='x')
        
        # Título
        title_label = tk.Label(
            title_bar,
            text="Sistema de Cobranza",
            bg=self.COLORS['primary'],
            fg=self.COLORS['white'],
            font=('Segoe UI', 10)
        )
        title_label.pack(side='left', padx=10)
        
        
        # Botón cerrar
        close_button = tk.Label(
            title_bar,
            text="×",
            bg=self.COLORS['primary'],
            fg=self.COLORS['white'],
            font=('Segoe UI', 13, 'bold'),
            cursor='hand2'
        )
        close_button.pack(side='right', padx=10)
        close_button.bind('<Button-1>', lambda e: self.root.destroy())
        
        # Hacer la ventana arrastrable
        title_bar.bind('<Button-1>', self.start_move)
        title_bar.bind('<B1-Motion>', self.on_move)

    def create_header(self):
            """Crea el encabezado con logo"""
            header_frame = tk.Frame(self.main_frame, bg=self.COLORS['white'])
            header_frame.pack(fill='x', pady=20)
            
            # Aquí podrías agregar un logo real
            logo_label = tk.Label(
                header_frame,
                text="📊",  # Emoji como placeholder del logo
                font=('Segoe UI', 36),
                bg=self.COLORS['white'],
                fg=self.COLORS['primary']
            )
            logo_label.pack()
            
            company_label = tk.Label(
                header_frame,
                text="Sistema de Cobranza",
                font=('Segoe UI', 14, 'bold'),
                bg=self.COLORS['white'],
                fg=self.COLORS['text']
            )
            company_label.pack(pady=(5,0))
            
            # Añadimos el subtítulo
            subtitle_label = tk.Label(
                header_frame,
                text="Garcia Automotriz",
                font=('Segoe UI', 12),  # Fuente un poco más pequeña que el título
                bg=self.COLORS['white'],
                fg=self.COLORS['text']
            )
            subtitle_label.pack(pady=(2,0))

    def create_loading_widgets(self):
        """Crea los widgets de carga con estilo moderno"""
        self.status_label = tk.Label(
            self.loading_frame,
            text="Actualizando datos...",
            font=('Segoe UI', 10),
            bg=self.COLORS['white'],
            fg=self.COLORS['text']
        )
        self.status_label.pack(pady=10)
        
        # Frame para la barra de progreso con fondo gris
        progress_frame = tk.Frame(
            self.loading_frame,
            bg=self.COLORS['secondary'],
            height=6,
            width=200
        )
        progress_frame.pack(pady=10)
        progress_frame.pack_propagate(False)
        
        # Barra de progreso moderna
        self.progress = ttk.Progressbar(
            progress_frame,
            mode='indeterminate',
            length=200,
            style='Modern.Horizontal.TProgressbar'
        )
        self.progress.pack(expand=True, fill='both')
        
        # Configurar estilo de la barra de progreso
        style = ttk.Style()
        style.configure(
            'Modern.Horizontal.TProgressbar',
            troughcolor=self.COLORS['secondary'],
            background=self.COLORS['primary'],
            thickness=6
        )
        
        self.message = tk.Label(
            self.loading_frame,
            text="Por favor espere mientras se actualizan los datos",
            font=('Segoe UI', 9),
            fg=self.COLORS['text'],
            bg=self.COLORS['white'],
            wraplength=250,
            justify='center'
        )
        self.message.pack(pady=10)

    def create_login_frame(self):
        """Crea el frame de login con diseño moderno"""
        self.login_frame = tk.Frame(self.main_frame, bg=self.COLORS['white'])
        self.login_frame.pack(fill='x', pady=10, padx=20)
        
        # Frame para el campo de entrada
        entry_frame = tk.Frame(
            self.login_frame,
            bg=self.COLORS['white'],
            highlightbackground=self.COLORS['border'],
            highlightthickness=1
        )
        entry_frame.pack(fill='x', pady=5)
        
        # Icono de usuario
        user_icon = tk.Label(
            entry_frame,
            text="👤",  # Emoji como placeholder
            font=('Segoe UI', 12),
            bg=self.COLORS['white']
        )
        user_icon.pack(side='left', padx=5)
        
        # Campo de entrada
        self.login_var = tk.StringVar()
        self.login_entry = tk.Entry(
            entry_frame,
            textvariable=self.login_var,
            font=('Segoe UI', 10),
            show="●",
            bd=0,
            bg=self.COLORS['white']
        )
        self.login_entry.pack(side='left', fill='x', expand=True, padx=5, pady=8)
        
        # Mensaje de error
        self.error_label = tk.Label(
            self.login_frame,
            text="",
            font=('Segoe UI', 8),
            fg=self.COLORS['error'],
            bg=self.COLORS['white']
        )
        self.error_label.pack(pady=5)
        
        # Bind eventos
        self.login_entry.bind('<Return>', self.attempt_login)
        
        # Hover effects para el entry frame
        entry_frame.bind('<Enter>', lambda e: entry_frame.configure(highlightbackground=self.COLORS['primary']))
        entry_frame.bind('<Leave>', lambda e: entry_frame.configure(highlightbackground=self.COLORS['border']))

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def show_login(self):
        self.message.config(text="Ingrese Usuario y Contraseña")
        self.login_frame.pack(fill='x', pady=10)
        self.login_entry.focus()
        
    def attempt_login(self, event=None):
        credentials = self.login_var.get().strip().upper()
        if validate_user(credentials):
            username = credentials.split()[0]
            UserSession.set_user(username)
            self.root.quit()
        else:
            self.error_label.config(text="Credenciales inválidas")
            self.login_var.set("")
            
    def start_progress(self):
        self.progress.start(10)
    
    def stop_progress(self):
        self.progress.stop()
        
    def update_status(self, text):
        self.status_label.config(text=text)
        
    def destroy(self):
        if hasattr(self.root, 'splash_references'):
            del self.root.splash_references
        self.root.destroy()