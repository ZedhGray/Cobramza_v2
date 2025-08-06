# database.py
import pyodbc
import logging
from datetime import datetime, date, time
from config import SQL_SERVER, DATABASE, USERNAME, PASSWORD

def get_db_connection():
    try:
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}'
        logging.info(f"Intentando conectar a la base de datos: {SQL_SERVER}/{DATABASE}")
        connection = pyodbc.connect(conn_str)
        logging.info("Conexión exitosa a la base de datos")
        return connection
    except pyodbc.Error as e:
        logging.error(f"Error al conectar a la base de datos: {e}")
        return None


def get_clients_data():
    conn = get_db_connection()
    if not conn:
        logging.error("No se pudo establecer conexión con la base de datos")
        return {}
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                Clave,
                ISNULL(Estado, '') as Estado,
                ISNULL(Fecha, '') as Fecha,
                ISNULL(Nombre, '') as Nombre,
                ISNULL(Direccion, '') as Direccion,
                ISNULL(Telefono1, '') as Telefono1,
                ISNULL(Telefono2, '') as Telefono2,
                ISNULL(Telefono3, '') as Telefono3,  -- NUEVA LÍNEA
                ISNULL(Descripcion, '') as Descripcion,
                ISNULL(Email, '') as Email,
                ISNULL(Referencia, '') as Referencia,
                ISNULL(Obs, '') as Obs,
                ISNULL(Credito, 0) as Credito,
                ISNULL(MontoCredito, 0) as MontoCredito,
                ISNULL(DiasCredito, 0) as DiasCredito,
                ISNULL(InteresCredito, '') as InteresCredito,
                ISNULL(Saldo, 0) as Saldo,
                ISNULL(NL, 0) as NL,
                ISNULL(NC, '') as NC,
                ISNULL(Membresia, '') as Membresia,
                ISNULL(Nivel, 0) as Nivel,
                ISNULL(Modificado, '') as Modificado,
                ISNULL(Et1, '') as Et1,
                ISNULL(LineaDeCredito, '') as LineaDeCredito
            FROM Clientes4
            WHERE Saldo > 0
        """
        
        logging.info(f"Ejecutando consulta SQL: {query}")
        cursor.execute(query)
        results = cursor.fetchall()
        
        logging.info(f"Registros encontrados: {len(results)}")
        
        def format_date(date_value):
            if date_value:
                if isinstance(date_value, (datetime, date)):
                    return date_value.strftime('%Y-%m-%d')
                try:
                    return datetime.strptime(str(date_value), '%Y-%m-%d').strftime('%Y-%m-%d')
                except (ValueError, TypeError):
                    logging.warning(f"Valor de fecha no válido: {date_value}")
                    return ""
            return ""
        
        clients_data = {
            str(row.Clave): {
                "estado": row.Estado.strip() if row.Estado else "",
                "fecha": format_date(row.Fecha),
                "nombre": row.Nombre.strip() if row.Nombre else "",
                "direccion": row.Direccion.strip() if row.Direccion else "",
                "telefono1": row.Telefono1.strip() if row.Telefono1 else "",
                "telefono2": row.Telefono2.strip() if row.Telefono2 else "",
                "telefono3": format_phone_number(row.Telefono3.strip() if row.Telefono3 else ""),
                "descripcion": row.Descripcion.strip() if row.Descripcion else "",
                "email": row.Email.strip() if row.Email else "",
                "referencia": row.Referencia.strip() if row.Referencia else "",
                "obs": row.Obs.strip() if row.Obs else "",
                "credito": bool(row.Credito),
                "montoCredito": float(row.MontoCredito) if row.MontoCredito else 0.0,
                "diasCredito": int(row.DiasCredito) if row.DiasCredito else 0,
                "interesCredito": row.InteresCredito.strip() if row.InteresCredito else "",
                "saldo": float(row.Saldo) if row.Saldo else 0.0,
                "nl": int(row.NL) if row.NL else 0,
                "nc": row.NC.strip() if row.NC else "",
                "membresia": format_date(row.Membresia),
                "nivel": int(row.Nivel) if row.Nivel else 0,
                "modificado": format_date(row.Modificado),
                "et1": row.Et1.strip() if row.Et1 else "",
                "lineaDeCredito": row.LineaDeCredito.strip() if row.LineaDeCredito else ""
            } for row in results
        }
        
        logging.info(f"Datos procesados exitosamente. Total de registros: {len(clients_data)}")
        return clients_data
        
    except pyodbc.Error as e:
        logging.error(f"Error al obtener datos de clientes: {e}")
        return {}
    except Exception as e:
        logging.error(f"Error inesperado al procesar datos: {e}")
        return {}
    finally:
        logging.info("Cerrando conexión a la base de datos")
        conn.close()

   
def get_ventas_data():
    conn = get_db_connection()
    if not conn:
        logging.error("No se pudo establecer conexión con la base de datos")
        return {}
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                Folio,
                ISNULL(Estado, '') as Estado,
                ISNULL(CveCte, '') as CveCte,
                ISNULL(Cliente, '') as Cliente,
                ISNULL(Fecha, '') as Fecha,
                ISNULL(Hora, '') as Hora,
                ISNULL(Total, 0) as Total,
                ISNULL(Restante, 0) as Restante,
                ISNULL(FechaPago, '') as FechaPago,
                ISNULL(Paga, 0) as Paga,
                ISNULL(Cambio, '') as Cambio,
                ISNULL(Ticket, '') as Ticket,
                ISNULL(Condiciones, '') as Condiciones,
                ISNULL(FechaProg, '') as FechaProg,
                ISNULL(Corte, 0) as Corte,
                ISNULL(Vendedor, '') as Vendedor,
                ISNULL(ComoPago, '') as ComoPago,
                ISNULL(DiasCred, 0) as DiasCred,
                ISNULL(IntCred, '') as IntCred,
                ISNULL(Articulos, '') as Articulos,
                ISNULL(BarCuenta, '') as BarCuenta,
                ISNULL(BarMesero, '') as BarMesero,
                ISNULL(NotasAdicionales, '') as NotasAdicionales,
                ISNULL(IdBarCuenta, '') as IdBarCuenta,
                ISNULL(Bitacora, '') as Bitacora,
                ISNULL(Anticipo, 0) as Anticipo,
                ISNULL(FolioPago, '') as FolioPago,
                ISNULL(SaldoCliente, 0) as SaldoCliente,
                ISNULL(Caja, 0) as Caja
            FROM Ventas
            WHERE Estado != 'PAGADA'
            AND Estado != 'CANCELADA'
            AND Estado IS NOT NULL
            AND Restante > 0
        """
        
        logging.info(f"Ejecutando consulta SQL para Ventas: {query}")
        cursor.execute(query)
        results = cursor.fetchall()
        
        logging.info(f"Registros de Ventas encontrados: {len(results)}")
        
        def format_date(date_value):
            if date_value:
                if isinstance(date_value, (datetime, date)):
                    return date_value.strftime('%Y-%m-%d')
                try:
                    return datetime.strptime(str(date_value), '%Y-%m-%d').strftime('%Y-%m-%d')
                except (ValueError, TypeError):
                    logging.warning(f"Valor de fecha no válido: {date_value}")
                    return ""
            return ""

        def format_time(time_value):
            if time_value:
                if isinstance(time_value, time):
                    return time_value.strftime('%H:%M:%S')
                try:
                    if isinstance(time_value, str):
                        return time_value
                    return datetime.strptime(str(time_value), '%H:%M:%S').strftime('%H:%M:%S')
                except (ValueError, TypeError):
                    logging.warning(f"Valor de hora no válido: {time_value}")
                    return ""
            return ""
        
        ventas_data = {
            str(row.Folio): {
                "estado": row.Estado.strip() if row.Estado else "",
                "cveCte": row.CveCte.strip() if row.CveCte else "",
                "cliente": row.Cliente.strip() if row.Cliente else "",
                "fecha": format_date(row.Fecha),
                "hora": format_time(row.Hora),
                "total": float(row.Total) if row.Total else 0.0,
                "restante": float(row.Restante) if row.Restante else 0.0,
                "fechaPago": format_date(row.FechaPago),
                "paga": float(row.Paga) if row.Paga else 0.0,
                "cambio": row.Cambio.strip() if row.Cambio else "",
                "ticket": row.Ticket.strip() if row.Ticket else "",
                "condiciones": row.Condiciones.strip() if row.Condiciones else "",
                "fechaProg": format_date(row.FechaProg),
                "corte": int(row.Corte) if row.Corte else 0,
                "vendedor": row.Vendedor.strip() if row.Vendedor else "",
                "comoPago": row.ComoPago.strip() if row.ComoPago else "",
                "diasCorte": int(row.DiasCred) if row.DiasCred else 0,
                "intCred": row.IntCred.strip() if row.IntCred else "",
                "articulos": row.Articulos.strip() if row.Articulos else "",
                "barCuenta": row.BarCuenta.strip() if row.BarCuenta else "",
                "barMesero": row.BarMesero.strip() if row.BarMesero else "",
                "notasAdicionales": row.NotasAdicionales.strip() if row.NotasAdicionales else "",
                "idBarCuenta": row.IdBarCuenta.strip() if row.IdBarCuenta else "",
                "bitacora": row.Bitacora.strip() if row.Bitacora else "",
                "anticipo": float(row.Anticipo) if row.Anticipo else 0.0,
                "folioPago": row.FolioPago.strip() if row.FolioPago else "",
                "saldoCliente": float(row.SaldoCliente) if row.SaldoCliente else 0.0,
                "caja": int(row.Caja) if row.Caja else 0
            } for row in results
        }
        
        logging.info(f"Datos de Ventas procesados exitosamente. Total de registros: {len(ventas_data)}")
        return ventas_data
        
    except pyodbc.Error as e:
        logging.error(f"Error al obtener datos de Ventas: {e}")
        return {}
    except Exception as e:
        logging.error(f"Error inesperado al procesar datos de Ventas: {e}")
        return {}
    finally:
        logging.info("Cerrando conexión a la base de datos")
        conn.close()


#States     

def update_client_states(client_id: str, states: dict = None) -> bool:
    """
    Actualiza o crea un registro en la tabla ClientsStates para un cliente específico.
    Si states es None, crea un registro con valores predeterminados False.
    """
    conn = get_db_connection()
    if not conn:
        logging.error("No se pudo establecer conexión con la base de datos")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar si el cliente ya existe
        check_query = """
            SELECT client_id
            FROM dbo.ClientsStates 
            WHERE client_id = ?
        """
        cursor.execute(check_query, (client_id,))
        exists = cursor.fetchone() is not None
        
        if states is None:
            states = {
                "day1": False,
                "day2": False,
                "day3": False,
                "dueday": False,
                "promisePage": False
            }
        
        if exists:
            # Actualizar registro existente
            update_query = """
                UPDATE dbo.ClientsStates 
                SET day1 = ?, 
                    day2 = ?, 
                    day3 = ?, 
                    dueday = ?, 
                    promisePage = ?
                WHERE client_id = ?
            """
            cursor.execute(update_query, 
                         (states["day1"], states["day2"], states["day3"], 
                          states["dueday"], states["promisePage"], client_id))
        else:
            # Insertar nuevo registro
            insert_query = """
                INSERT INTO dbo.ClientsStates 
                (client_id, day1, day2, day3, dueday, promisePage)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.execute(insert_query, 
                         (client_id, states["day1"], states["day2"], states["day3"], 
                          states["dueday"], states["promisePage"]))
        
        conn.commit()
        logging.info(f"Estados del cliente {client_id} actualizados exitosamente")
        return True
        
    except pyodbc.Error as e:
        logging.error(f"Error al actualizar estados del cliente {client_id}: {e}")
        return False
    finally:
        conn.close()

def delete_client_states(client_id: str) -> bool:
    """
    Elimina el registro de un cliente de la tabla ClientsStates.
    """
    conn = get_db_connection()
    if not conn:
        logging.error("No se pudo establecer conexión con la base de datos")
        return False
    
    try:
        cursor = conn.cursor()
        delete_query = """
            DELETE FROM dbo.ClientsStates 
            WHERE client_id = ?
        """
        cursor.execute(delete_query, (client_id,))
        conn.commit()
        logging.info(f"Estados del cliente {client_id} eliminados exitosamente")
        return True
        
    except pyodbc.Error as e:
        logging.error(f"Error al eliminar estados del cliente {client_id}: {e}")
        return False
    finally:
        conn.close()

def get_client_states() -> dict:
    """
    Obtiene todos los registros de la tabla ClientsStates.
    """
    conn = get_db_connection()
    if not conn:
        logging.error("No se pudo establecer conexión con la base de datos")
        return {}
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT client_id, day1, day2, day3, dueday, promisePage, company, promiseDate
            FROM dbo.ClientsStates
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        return {
            str(row.client_id): {
                "day1": bool(row.day1),
                "day2": bool(row.day2),
                "day3": bool(row.day3),
                "dueday": bool(row.dueday),
                "promisePage": bool(row.promisePage),
                "company": bool(row.company),
                "promiseDate": row.promiseDate
            } for row in results
        }
        
    except pyodbc.Error as e:
        logging.error(f"Error al obtener estados de los clientes: {e}")
        return {}
    finally:
        conn.close()
# database.py
def get_client_notes(client_id: str) -> list:
    """
    Obtiene las notas de un cliente específico.
    Retorna una lista de diccionarios con las notas.
    """
    conn = get_db_connection()
    if not conn:
        logging.error("No se pudo establecer conexión con la base de datos")
        return []
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT id, note_text, created_at, ISNULL(user_name, 'Sistema') as user_name
            FROM Notes
            WHERE client_id = ?
            ORDER BY created_at DESC
        """
        cursor.execute(query, (client_id,))
        results = cursor.fetchall()
        
        notes = []
        for row in results:
            note = {
                'id': row.id if hasattr(row, 'id') else 0,
                'text': row.note_text if hasattr(row, 'note_text') else 'Sin texto',
                'created_at': row.created_at.isoformat() if hasattr(row, 'created_at') and row.created_at else datetime.now().isoformat(),
                'user_name': row.user_name if hasattr(row, 'user_name') else 'Sistema'
            }
            notes.append(note)
        
        logging.info(f"Se obtuvieron {len(notes)} notas para el cliente {client_id}")
        return notes
        
    except pyodbc.Error as e:
        logging.error(f"Error al obtener notas del cliente {client_id}: {e}")
        return []
    except Exception as e:
        logging.error(f"Error inesperado al obtener notas del cliente {client_id}: {e}")
        return []
    finally:
        conn.close()

def get_client_data(self, clave_id):
        """Obtiene los datos específicos de un cliente"""
        conn = get_db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            query = """
                SELECT client_id, day1, day2, day3, dueday, promisePage
                FROM dbo.ClientsStates
                WHERE client_id = ?
            """
            cursor.execute(query, (clave_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    "ID Cliente": row.client_id,
                    "Día 1": "Sí" if row.day1 else "No",
                    "Día 2": "Sí" if row.day2 else "No",
                    "Día 3": "Sí" if row.day3 else "No",
                    "Día Vencimiento": "Sí" if row.dueday else "No",
                    "Promesa de Pago": "Activa" if row.promisePage else "Inactiva"
                }
            return None
            
        except pyodbc.Error as e:
            logging.error(f"Error al obtener datos del cliente {clave_id}: {e}")
            return None
        finally:
            conn.close()
            

#wsp
def update_client_states_wsp(client_id: str, states: dict = None) -> bool:
    """
    Actualiza o crea un registro en la tabla ClientsStates para un cliente específico.
    Si states es None, crea un registro con valores predeterminados False.
    
    Parameters:
    client_id (str): ID del cliente a actualizar.
    states (dict): Diccionario con los nuevos estados del cliente.
    
    Returns:
    bool: True si la actualización fue exitosa, False en caso contrario.
    """
    conn = get_db_connection()
    if not conn:
        logging.error("No se pudo establecer conexión con la base de datos")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar si el cliente ya existe
        check_query = """
            SELECT client_id
            FROM dbo.ClientsStates 
            WHERE client_id = ?
        """
        cursor.execute(check_query, (client_id,))
        exists = cursor.fetchone() is not None
        
        if states is None:
            states = {
                "day1": False,
                "day2": False,
                "day3": False,
                "dueday": False,
                "promisePage": False
            }
        
        if exists:
            # Actualizar registro existente
            update_query = """
                UPDATE dbo.ClientsStates 
                SET day1 = ?, 
                    day2 = ?, 
                    day3 = ?, 
                    dueday = ?, 
                    promisePage = ?
                WHERE client_id = ?
            """
            cursor.execute(update_query, 
                         (states["day1"], states["day2"], states["day3"], 
                          states["dueday"], states["promisePage"], client_id))
        else:
            # Insertar nuevo registro
            insert_query = """
                INSERT INTO dbo.ClientsStates 
                (client_id, day1, day2, day3, dueday, promisePage)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.execute(insert_query, 
                         (client_id, states["day1"], states["day2"], states["day3"], 
                          states["dueday"], states["promisePage"]))
        
        conn.commit()
        logging.info(f"Estados del cliente {client_id} actualizados exitosamente")
        return True
        
    except pyodbc.Error as e:
        logging.error(f"Error al actualizar estados del cliente {client_id}: {e}")
        return False
    finally:
        conn.close()
        

def update_promise_date(client_id: str, promise_date: datetime.date) -> bool:
    """
    Actualiza o inserta la fecha de promesa de pago para un cliente específico.
    Implementa lógica UPSERT: UPDATE si existe, INSERT si no existe.
    
    Args:
        client_id (str): ID del cliente
        promise_date (datetime.date): Nueva fecha de promesa
        
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    conn = get_db_connection()
    if not conn:
        logging.error("No se pudo establecer conexión con la base de datos")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Primero intentamos UPDATE
        update_query = """
            UPDATE dbo.ClientsStates 
            SET promiseDate = ?
            WHERE client_id = ?
        """
        
        logging.info(f"Intentando UPDATE para cliente {client_id} con fecha {promise_date}")
        cursor.execute(update_query, (promise_date, client_id))
        rows_affected = cursor.rowcount
        
        logging.info(f"UPDATE afectó {rows_affected} filas para cliente {client_id}")
        
        # Si no se actualizó ninguna fila, el cliente no existe → INSERT
        if rows_affected == 0:
            insert_query = """
                INSERT INTO dbo.ClientsStates (client_id, day1, day2, day3, dueday, promisePage, promiseDate)
                VALUES (?, 0, 0, 0, 0, 0, ?)
            """
            
            logging.info(f"Cliente {client_id} no existe, ejecutando INSERT con fecha {promise_date}")
            cursor.execute(insert_query, (client_id, promise_date))
            rows_inserted = cursor.rowcount
            
            logging.info(f"INSERT creó {rows_inserted} fila(s) para cliente {client_id}")
            
            if rows_inserted == 0:
                logging.error(f"Error: INSERT no creó ninguna fila para cliente {client_id}")
                return False
            else:
                logging.info(f"Éxito: Cliente {client_id} creado con promesa {promise_date}")
        else:
            logging.info(f"Éxito: Cliente {client_id} actualizado con promesa {promise_date}")
        
        # Confirmar transacción
        conn.commit()
        logging.info(f"Transacción confirmada para cliente {client_id}")
        
        # Verificación adicional: confirmar que el dato se guardó
        verify_query = "SELECT promiseDate FROM dbo.ClientsStates WHERE client_id = ?"
        cursor.execute(verify_query, (client_id,))
        result = cursor.fetchone()
        
        if result and result[0]:
            logging.info(f"Verificación exitosa: Cliente {client_id} tiene promesa {result[0]}")
            return True
        else:
            logging.error(f"Verificación falló: No se encontró promesa para cliente {client_id}")
            return False
        
    except pyodbc.Error as e:
        logging.error(f"Error SQL al procesar promesa para cliente {client_id}: {e}")
        try:
            conn.rollback()
            logging.info(f"Rollback ejecutado para cliente {client_id}")
        except:
            pass
        return False
    except Exception as e:
        logging.error(f"Error inesperado al procesar promesa para cliente {client_id}: {e}")
        try:
            conn.rollback()
            logging.info(f"Rollback ejecutado para cliente {client_id}")
        except:
            pass
        return False
    finally:
        try:
            conn.close()
            logging.info(f"Conexión cerrada para cliente {client_id}")
        except:
            pass
     

def sync_clients_to_buro():
    """
    Synchronize clients from Clientes4 to ClientsBuro database.
    Only adds missing clients, does not modify existing ones.
    """
    conn = get_db_connection()
    if not conn:
        logging.error("No se pudo establecer conexión con la base de datos")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Fetch all client IDs from Clientes4
        cursor.execute("SELECT Clave FROM Clientes4")
        clientes_clave = [str(row.Clave) for row in cursor.fetchall()]
        
        # Check which clients already exist in ClientsBuro
        placeholders = ','.join(['?'] * len(clientes_clave))
        cursor.execute(f"""
            SELECT client_id FROM dbo.ClientsBuro 
            WHERE client_id IN ({placeholders})
        """, clientes_clave)
        existing_clients = [str(row.client_id) for row in cursor.fetchall()]
        
        # Identify and insert missing clients
        missing_clients = set(clientes_clave) - set(existing_clients)
        
        if missing_clients:
            insert_query = """
                INSERT INTO dbo.ClientsBuro (client_id, credit)
                VALUES (?, 0)
            """
            for client_id in missing_clients:
                cursor.execute(insert_query, (client_id,))
            
            conn.commit()
            logging.info(f"Added {len(missing_clients)} new clients to ClientsBuro")
        else:
            logging.info("No new clients to add to ClientsBuro")
        
        return True
        
    except pyodbc.Error as e:
        logging.error(f"Error al sincronizar clientes: {e}")
        return False
    finally:
        conn.close()


def get_clients_without_credit():
    """
    Retrieve clients from ClientsBuro with credit set to True (1)
    """
    conn = get_db_connection()
    if not conn:
        logging.error("No se pudo establecer conexión con la base de datos")
        return {}
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT cb.client_id, c.Nombre, c.Saldo
            FROM dbo.ClientsBuro cb
            JOIN Clientes4 c ON cb.client_id = c.Clave
            WHERE cb.credit = 1
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        clients_with_credit = {
            str(row.client_id): {
                'nombre': row.Nombre,
                'saldo': row.Saldo  # Add saldo to the dictionary
            } for row in results
        }
        
        return clients_with_credit
        
    except pyodbc.Error as e:
        logging.error(f"Error al obtener clientes con crédito: {e}")
        return {}
    finally:
        conn.close()
        

def update_telefono3(client_id: str, telefono3: str) -> bool:
    """
    Actualiza el campo Telefono3 para un cliente específico con formato.
    
    Args:
        client_id (str): ID del cliente
        telefono3 (str): Nuevo número de teléfono
        
    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario
    """
    conn = get_db_connection()
    if not conn:
        logging.error("No se pudo establecer conexión con la base de datos")
        return False
    
    try:
        # Formatear el teléfono antes de guardarlo
        telefono_formateado = format_phone_number(telefono3)
        
        cursor = conn.cursor()
        query = """
            UPDATE Clientes4 
            SET Telefono3 = ?
            WHERE Clave = ?
        """
        cursor.execute(query, (telefono_formateado, client_id))
        conn.commit()
        
        if cursor.rowcount > 0:
            logging.info(f"Teléfono3 actualizado para cliente {client_id}: {telefono_formateado}")
            return True
        else:
            logging.warning(f"No se encontró el cliente {client_id}")
            return False
        
    except pyodbc.Error as e:
        logging.error(f"Error al actualizar teléfono3: {e}")
        return False
    finally:
        conn.close()

def format_phone_number(phone):
    """
    Formatea un número de teléfono al estilo (755) 128-5755
    
    Args:
        phone (str): Número de teléfono sin formato
        
    Returns:
        str: Número formateado o el original si no se puede formatear
    """
    if not phone or not phone.strip():
        return ""
    
    # Limpiar el número - solo dígitos
    digits = ''.join(filter(str.isdigit, phone))
    
    # Si ya está formateado correctamente, devolverlo tal como está
    if '(' in phone and ')' in phone and '-' in phone:
        return phone
    
    # Formatear según la longitud
    if len(digits) == 10:
        # Formato: (755) 128-5755
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits.startswith('1'):
        # Si empieza con 1, quitar el 1 y formatear
        digits = digits[1:]
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 12 and digits.startswith('52'):
        # Si empieza con 52 (México), quitar el 52 y formatear
        digits = digits[2:]
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    else:
        # Si no se puede formatear, devolver tal como está
        return phone


# User and password validation
def validate_user(credentials):
    """
    Validate user credentials from the Usuarios table
    credentials format: "USERNAME PASSWORD"
    """
    conn = get_db_connection()
    if not conn:
        logging.error("No se pudo establecer conexión con la base de datos")
        return False
    
    try:
        cursor = conn.cursor()
        # Split credentials into username and password
        parts = credentials.strip().split(' ', 1)
        if len(parts) != 2:
            return False
            
        username, password = parts
        
        query = """
            SELECT COUNT(*)
            FROM Usuarios
            WHERE Usuario = ? AND Password = ?
        """
        
        cursor.execute(query, (username.upper(), password.upper()))
        count = cursor.fetchone()[0]
        
        return count > 0
        
    except pyodbc.Error as e:
        logging.error(f"Error al validar usuario: {e}")
        return False
    finally:
        conn.close()


import re

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


class UserSession:
    """Clase singleton para manejar la sesión del usuario"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserSession, cls).__new__(cls)
            cls._instance.username = None
            cls._instance.login_time = None
        return cls._instance
    
    @classmethod
    def set_user(cls, username):
        instance = cls()
        instance.username = username
        instance.login_time = datetime.now()
    
    @classmethod
    def get_user(cls):
        instance = cls()
        return instance.username
    
    @classmethod
    def is_logged_in(cls):
        instance = cls()
        return instance.username is not None
    


# =====================================
# SISTEMA DE PUNTAJE CREDITICIO
# =====================================

def get_all_clients_data():
    """
    Obtener TODOS los clientes (no solo los que tienen saldo > 0)
    Para el sistema de créditos
    """
    conn = get_db_connection()
    if not conn:
        logging.error("No se pudo establecer conexión con la base de datos")
        return {}
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                Clave,
                ISNULL(Estado, '') as Estado,
                ISNULL(Fecha, '') as Fecha,
                ISNULL(Nombre, '') as Nombre,
                ISNULL(Direccion, '') as Direccion,
                ISNULL(Telefono1, '') as Telefono1,
                ISNULL(Telefono2, '') as Telefono2,
                ISNULL(Telefono3, '') as Telefono3,
                ISNULL(Descripcion, '') as Descripcion,
                ISNULL(Email, '') as Email,
                ISNULL(Referencia, '') as Referencia,
                ISNULL(Obs, '') as Obs,
                ISNULL(Credito, 0) as Credito,
                ISNULL(MontoCredito, 0) as MontoCredito,
                ISNULL(DiasCredito, 0) as DiasCredito,
                ISNULL(InteresCredito, '') as InteresCredito,
                ISNULL(Saldo, 0) as Saldo,
                ISNULL(NL, 0) as NL,
                ISNULL(NC, '') as NC,
                ISNULL(Membresia, '') as Membresia,
                ISNULL(Nivel, 0) as Nivel,
                ISNULL(Modificado, '') as Modificado,
                ISNULL(Et1, '') as Et1,
                ISNULL(LineaDeCredito, '') as LineaDeCredito
            FROM Clientes4
        """
        
        logging.info(f"Ejecutando consulta SQL para TODOS los clientes: {query}")
        cursor.execute(query)
        results = cursor.fetchall()
        
        logging.info(f"Registros encontrados (todos los clientes): {len(results)}")
        
        def format_date(date_value):
            if date_value:
                if isinstance(date_value, (datetime, date)):
                    return date_value.strftime('%Y-%m-%d')
                try:
                    return datetime.strptime(str(date_value), '%Y-%m-%d').strftime('%Y-%m-%d')
                except (ValueError, TypeError):
                    logging.warning(f"Valor de fecha no válido: {date_value}")
                    return ""
            return ""
        
        clients_data = {
            str(row.Clave): {
                "estado": row.Estado.strip() if row.Estado else "",
                "fecha": format_date(row.Fecha),
                "nombre": row.Nombre.strip() if row.Nombre else "",
                "direccion": row.Direccion.strip() if row.Direccion else "",
                "telefono1": row.Telefono1.strip() if row.Telefono1 else "",
                "telefono2": row.Telefono2.strip() if row.Telefono2 else "",
                "telefono3": format_phone_number(row.Telefono3.strip() if row.Telefono3 else ""),
                "descripcion": row.Descripcion.strip() if row.Descripcion else "",
                "email": row.Email.strip() if row.Email else "",
                "referencia": row.Referencia.strip() if row.Referencia else "",
                "obs": row.Obs.strip() if row.Obs else "",
                "credito": bool(row.Credito),
                "montoCredito": float(row.MontoCredito) if row.MontoCredito else 0.0,
                "diasCredito": int(row.DiasCredito) if row.DiasCredito else 0,
                "interesCredito": row.InteresCredito.strip() if row.InteresCredito else "",
                "saldo": float(row.Saldo) if row.Saldo else 0.0,
                "nl": int(row.NL) if row.NL else 0,
                "nc": row.NC.strip() if row.NC else "",
                "membresia": format_date(row.Membresia),
                "nivel": int(row.Nivel) if row.Nivel else 0,
                "modificado": format_date(row.Modificado),
                "et1": row.Et1.strip() if row.Et1 else "",
                "lineaDeCredito": row.LineaDeCredito.strip() if row.LineaDeCredito else ""
            } for row in results
        }
        
        logging.info(f"Datos procesados exitosamente. Total de clientes: {len(clients_data)}")
        return clients_data
        
    except pyodbc.Error as e:
        logging.error(f"Error al obtener datos de todos los clientes: {e}")
        return {}
    except Exception as e:
        logging.error(f"Error inesperado al procesar datos: {e}")
        return {}
    finally:
        logging.info("Cerrando conexión a la base de datos")
        conn.close()


def get_all_ventas_data():
    """
    Obtener TODAS las ventas (incluyendo pagadas y canceladas)
    Para calcular el historial completo de pagos
    """
    conn = get_db_connection()
    if not conn:
        logging.error("No se pudo establecer conexión con la base de datos")
        return {}
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                Folio,
                ISNULL(Estado, '') as Estado,
                ISNULL(CveCte, '') as CveCte,
                ISNULL(Cliente, '') as Cliente,
                ISNULL(Fecha, '') as Fecha,
                ISNULL(Hora, '') as Hora,
                ISNULL(Total, 0) as Total,
                ISNULL(Restante, 0) as Restante,
                ISNULL(FechaPago, '') as FechaPago,
                ISNULL(Paga, 0) as Paga,
                ISNULL(Cambio, '') as Cambio,
                ISNULL(Ticket, '') as Ticket,
                ISNULL(Condiciones, '') as Condiciones,
                ISNULL(FechaProg, '') as FechaProg,
                ISNULL(Corte, 0) as Corte,
                ISNULL(Vendedor, '') as Vendedor,
                ISNULL(ComoPago, '') as ComoPago,
                ISNULL(DiasCred, 0) as DiasCred,
                ISNULL(IntCred, '') as IntCred,
                ISNULL(Articulos, '') as Articulos,
                ISNULL(BarCuenta, '') as BarCuenta,
                ISNULL(BarMesero, '') as BarMesero,
                ISNULL(NotasAdicionales, '') as NotasAdicionales,
                ISNULL(IdBarCuenta, '') as IdBarCuenta,
                ISNULL(Bitacora, '') as Bitacora,
                ISNULL(Anticipo, 0) as Anticipo,
                ISNULL(FolioPago, '') as FolioPago,
                ISNULL(SaldoCliente, 0) as SaldoCliente,
                ISNULL(Caja, 0) as Caja
            FROM Ventas
            WHERE CveCte IS NOT NULL 
            AND CveCte != ''
        """
        
        logging.info(f"Ejecutando consulta SQL para TODAS las ventas: {query}")
        cursor.execute(query)
        results = cursor.fetchall()
        
        logging.info(f"Registros de todas las ventas encontrados: {len(results)}")
        
        def format_date(date_value):
            if date_value:
                if isinstance(date_value, (datetime, date)):
                    return date_value.strftime('%Y-%m-%d')
                try:
                    return datetime.strptime(str(date_value), '%Y-%m-%d').strftime('%Y-%m-%d')
                except (ValueError, TypeError):
                    logging.warning(f"Valor de fecha no válido: {date_value}")
                    return ""
            return ""

        def format_time(time_value):
            if time_value:
                if isinstance(time_value, time):
                    return time_value.strftime('%H:%M:%S')
                try:
                    if isinstance(time_value, str):
                        return time_value
                    return datetime.strptime(str(time_value), '%H:%M:%S').strftime('%H:%M:%S')
                except (ValueError, TypeError):
                    logging.warning(f"Valor de hora no válido: {time_value}")
                    return ""
            return ""
        
        ventas_data = {
            str(row.Folio): {
                "estado": row.Estado.strip() if row.Estado else "",
                "cveCte": row.CveCte.strip() if row.CveCte else "",
                "cliente": row.Cliente.strip() if row.Cliente else "",
                "fecha": format_date(row.Fecha),
                "hora": format_time(row.Hora),
                "total": float(row.Total) if row.Total else 0.0,
                "restante": float(row.Restante) if row.Restante else 0.0,
                "fechaPago": format_date(row.FechaPago),
                "paga": float(row.Paga) if row.Paga else 0.0,
                "cambio": row.Cambio.strip() if row.Cambio else "",
                "ticket": row.Ticket.strip() if row.Ticket else "",
                "condiciones": row.Condiciones.strip() if row.Condiciones else "",
                "fechaProg": format_date(row.FechaProg),
                "corte": int(row.Corte) if row.Corte else 0,
                "vendedor": row.Vendedor.strip() if row.Vendedor else "",
                "comoPago": row.ComoPago.strip() if row.ComoPago else "",
                "diasCorte": int(row.DiasCred) if row.DiasCred else 0,
                "intCred": row.IntCred.strip() if row.IntCred else "",
                "articulos": row.Articulos.strip() if row.Articulos else "",
                "barCuenta": row.BarCuenta.strip() if row.BarCuenta else "",
                "barMesero": row.BarMesero.strip() if row.BarMesero else "",
                "notasAdicionales": row.NotasAdicionales.strip() if row.NotasAdicionales else "",
                "idBarCuenta": row.IdBarCuenta.strip() if row.IdBarCuenta else "",
                "bitacora": row.Bitacora.strip() if row.Bitacora else "",
                "anticipo": float(row.Anticipo) if row.Anticipo else 0.0,
                "folioPago": row.FolioPago.strip() if row.FolioPago else "",
                "saldoCliente": float(row.SaldoCliente) if row.SaldoCliente else 0.0,
                "caja": int(row.Caja) if row.Caja else 0
            } for row in results
        }
        
        logging.info(f"Datos de todas las ventas procesados exitosamente. Total de registros: {len(ventas_data)}")
        return ventas_data
        
    except pyodbc.Error as e:
        logging.error(f"Error al obtener datos de todas las ventas: {e}")
        return {}
    except Exception as e:
        logging.error(f"Error inesperado al procesar datos de todas las ventas: {e}")
        return {}
    finally:
        logging.info("Cerrando conexión a la base de datos")
        conn.close()


def calculate_client_credit_score(client_id, all_ventas_data):
    """
    Calcular el puntaje crediticio de un cliente basado en su historial de pagos
    
    Sistema de puntos:
    - Cliente inicia con 400 puntos
    - Pago < 30 días: +100 puntos
    - Pago 31-60 días: +50 puntos  
    - Pago 61-90 días: +10 puntos
    - Pago 91-120 días: -10 puntos
    - Más de 120 días sin pagar: -10 puntos por día
    """
    try:
        base_score = 400
        total_score = base_score
        
        client_ventas = [
            venta for venta in all_ventas_data.values() 
            if venta.get('cveCte') == client_id
        ]
        
        if not client_ventas:
            return {
                'score': base_score,
                'level': get_credit_level(base_score),
                'transactions': 0,
                'avg_days': 0,
                'details': []
            }
        
        transaction_details = []
        total_days = 0
        valid_transactions = 0
        
        for venta in client_ventas:
            try:
                fecha_venta = venta.get('fecha')
                fecha_pago = venta.get('fechaPago')
                estado = venta.get('estado', '').upper()
                folio = venta.get('ticket', 'N/A')
                
                if not fecha_venta:
                    continue
                
                # Convertir fecha de venta
                fecha_venta_dt = datetime.strptime(fecha_venta, '%Y-%m-%d').date()
                
                # Determinar fecha de referencia para el cálculo
                if estado == 'PAGADA' and fecha_pago:
                    # Ticket pagado - usar fecha de pago
                    try:
                        fecha_pago_dt = datetime.strptime(fecha_pago, '%Y-%m-%d').date()
                        days_diff = (fecha_pago_dt - fecha_venta_dt).days
                    except:
                        continue
                else:
                    # Ticket no pagado - usar fecha actual
                    fecha_pago_dt = datetime.now().date()
                    days_diff = (fecha_pago_dt - fecha_venta_dt).days
                
                # Calcular puntos según los días
                points = 0
                if days_diff <= 30:
                    points = 100
                elif days_diff <= 60:
                    points = 50
                elif days_diff <= 90:
                    points = 10
                elif days_diff <= 120:
                    points = -10
                else:
                    # Más de 120 días: -10 puntos por día desde el día 120
                    extra_days = days_diff - 120
                    points = -10 - (extra_days * 10)
                
                total_score += points
                total_days += days_diff
                valid_transactions += 1
                
                transaction_details.append({
                    'folio': folio,
                    'fecha_venta': fecha_venta,
                    'fecha_pago': fecha_pago if fecha_pago else 'Pendiente',
                    'days': days_diff,
                    'points': points,
                    'estado': estado
                })
                
            except Exception as e:
                logging.warning(f"Error procesando venta para cliente {client_id}: {e}")
                continue
        
        # No permitir que el score baje de 0
        total_score = max(0, total_score)
        
        avg_days = total_days / valid_transactions if valid_transactions > 0 else 0
        
        return {
            'score': total_score,
            'level': get_credit_level(total_score),
            'transactions': valid_transactions,
            'avg_days': round(avg_days, 1),
            'details': sorted(transaction_details, key=lambda x: x['fecha_venta'], reverse=True)
        }
        
    except Exception as e:
        logging.error(f"Error calculando puntaje para cliente {client_id}: {e}")
        return {
            'score': base_score,
            'level': get_credit_level(base_score),
            'transactions': 0,
            'avg_days': 0,
            'details': []
        }


def get_credit_level(score):
    """
    Determinar el nivel de crédito basado en el puntaje
    
    Niveles:
    - Dorado: 1000+ puntos (Crédito Alto)
    - Verde: 600-999 puntos (Crédito Normal) 
    - Amarillo: 400-599 puntos (Crédito a Revisión)
    - Naranja: 200-399 puntos (Crédito de Riesgo)
    - Rojo: 0-199 puntos (Sin Crédito - Buró)
    """
    if score >= 1000:
        return {
            'name': 'DORADO',
            'color': '#FFD700',
            'icon': '🥇',
            'description': 'Crédito Alto'
        }
    elif score >= 600:
        return {
            'name': 'VERDE', 
            'color': '#22C55E',
            'icon': '✅',
            'description': 'Crédito Normal'
        }
    elif score >= 400:
        return {
            'name': 'AMARILLO',
            'color': '#EAB308', 
            'icon': '⚠️',
            'description': 'Crédito a Revisión'
        }
    elif score >= 200:
        return {
            'name': 'NARANJA',
            'color': '#F97316',
            'icon': '🔶',
            'description': 'Crédito de Riesgo'
        }
    else:
        return {
            'name': 'ROJO',
            'color': '#EF4444',
            'icon': '🚫', 
            'description': 'Sin Crédito - Buró'
        }


def get_all_clients_credit_scores():
    """
    Calcular el puntaje crediticio para todos los clientes
    """
    try:
        logging.info("Iniciando cálculo de puntajes crediticios para todos los clientes...")
        
        # Obtener todos los datos
        all_clients = get_all_clients_data()
        all_ventas = get_all_ventas_data()
        
        if not all_clients:
            logging.warning("No se pudieron obtener datos de clientes")
            return {}
        
        credit_scores = {}
        
        for client_id, client_data in all_clients.items():
            try:
                score_data = calculate_client_credit_score(client_id, all_ventas)
                
                credit_scores[client_id] = {
                    'client_data': client_data,
                    'credit_score': score_data['score'],
                    'credit_level': score_data['level'],
                    'transactions': score_data['transactions'],
                    'avg_payment_days': score_data['avg_days'],
                    'transaction_details': score_data['details']
                }
                
            except Exception as e:
                logging.error(f"Error calculando score para cliente {client_id}: {e}")
                continue
        
        logging.info(f"Puntajes crediticios calculados para {len(credit_scores)} clientes")
        return credit_scores
        
    except Exception as e:
        logging.error(f"Error general en cálculo de puntajes crediticios: {e}")
        return {}


def get_clients_by_credit_level(level_name):
    """
    Obtener clientes filtrados por nivel de crédito
    """
    try:
        all_scores = get_all_clients_credit_scores()
        
        filtered_clients = {
            client_id: data for client_id, data in all_scores.items()
            if data['credit_level']['name'] == level_name.upper()
        }
        
        return filtered_clients
        
    except Exception as e:
        logging.error(f"Error filtrando clientes por nivel {level_name}: {e}")
        return {}


def get_credit_statistics():
    """
    Obtener estadísticas generales del sistema de créditos
    """
    try:
        all_scores = get_all_clients_credit_scores()
        
        if not all_scores:
            return {
                'total_clients': 0,
                'by_level': {},
                'avg_score': 0,
                'total_transactions': 0
            }
        
        stats = {
            'total_clients': len(all_scores),
            'by_level': {
                'DORADO': 0,
                'VERDE': 0, 
                'AMARILLO': 0,
                'NARANJA': 0,
                'ROJO': 0
            },
            'avg_score': 0,
            'total_transactions': 0
        }
        
        total_score = 0
        for client_data in all_scores.values():
            level = client_data['credit_level']['name']
            stats['by_level'][level] += 1
            total_score += client_data['credit_score']
            stats['total_transactions'] += client_data['transactions']
        
        stats['avg_score'] = round(total_score / len(all_scores), 1) if all_scores else 0
        
        return stats
        
    except Exception as e:
        logging.error(f"Error calculando estadísticas de crédito: {e}")
        return {
            'total_clients': 0,
            'by_level': {},
            'avg_score': 0,
            'total_transactions': 0
        }