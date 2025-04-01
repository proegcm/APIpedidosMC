#from flask import Flask, request, jsonify
#import pyodbc
from flask import Flask, jsonify, send_file, request, url_for
from fpdf import FPDF
import pyodbc
import io
import base64
import json


app = Flask(__name__) #Instancia de la aplicación Flask. host.docker.internal
                      #el argumento __name__ es una variable especial en phyton que representa el nombre del módulo actual, al ejecutarse se establece a "__main__" o sea, el script se ejecuta como el programa principal.

# Función para obtener conexión a SQL Server
def get_sql_server_connection():
    connection = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=localhost,1433;'
        'DATABASE=MaterialesCreativos;'
        'UID=MCEGCM;'
        'PWD=PG1MCre@tiv0s;'
        'Trusted_Connection=no;'
    )
    return connection

def quitaNulo(txt):
    if isinstance(txt, str):
        return txt.strip()  # Si es cadena, eliminar espacios
    return str(txt) if txt is not None else ""  # Convertir otros valores a string o devolver vacío

# Función para generar el PDF y retornar en base64 
def generar_pdf_base64(listadoPedidos):
    pdf = FPDF()
    pdf.add_page()

    # Título del documento
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(200, 10, 'Listado de Pedidos', ln=True, align='C')

    # Espaciado
    pdf.ln(10)

    # Detalles de los pedidos
    #pdf.set_font('Arial', '', 12)
    for pedido in listadoPedidos:
        # Título del documento
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(200, 10, f'Pedido Folio #{pedido["folio"]}', ln=True)
        #pdf.cell(200, 10, f'Folio: {pedido["folio"]}', ln=True)
        pdf.cell(200, 10, f'Cliente: {pedido["cliente"]}', ln=True)
        pdf.set_font('Arial', '', 12)
        pdf.cell(200, 10, f'Total: Q.{pedido["total"]} - Pago: Q.{pedido["pago"]} - Cambio: Q.{pedido["cambio"]}', ln=True)
        pdf.cell(200, 10, f'A cargo de: {pedido["usuario_registro"]} - Estado Actual: {pedido["estado_actual"]}', ln=True)
        pdf.ln(5)  # Espacio entre pedidos

        pdf.set_font('Arial', 'B', 14)
        pdf.cell(200, 10, f'Tracking:', ln=True)
        # Tracking del pedido
        for tracking in pedido["tracking"]:
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(200, 10, f'  - Estado: {tracking["estado"]}', ln=True)
            pdf.set_font('Arial', '', 12)
            pdf.cell(200, 10, f'      Fecha: {tracking["fecha_estado"]}', ln=True)
            if(tracking["mensajero"]):
                pdf.cell(200, 10, f'      Mensajero: {tracking["mensajero"]}', ln=True)
            if(tracking["paqueteria"]):
                pdf.cell(200, 10, f'      Paquetería: {tracking["paqueteria"]}', ln=True)
            if(tracking["observaciones"]):
                pdf.cell(200, 10, f'      Observaciones: {tracking["observaciones"]}', ln=True)
            pdf.ln(3)  # Espacio entre tracking items

        pdf.ln(10)  # Espacio después de cada pedido

    # Guardar el PDF en un archivo en memoria (BytesIO)
    pdf_output = io.BytesIO()

    # Usar `pdf.output` con el parámetro `dest='S'` para escribir en un buffer de salida
    pdf_output.write(pdf.output(dest='S').encode('latin1'))

    # Convertir el contenido del archivo PDF a base64
    pdf_output.seek(0)  # Mover el puntero al inicio del archivo en memoria
    pdf_base64 = base64.b64encode(pdf_output.read()).decode('utf-8')

    # Cerrar el archivo en memoria
    pdf_output.close()

    # Retornar el contenido del PDF en base64
    return pdf_base64

#------------------- INICIO DE SESIÓN -----------------------------
#Endpoint ingreso portal
@app.route('/LoginMC', methods=['POST'])
def LoginMC():
    # Obtiene los datos JSON de la solicitud
    data = request.get_json()
    print("LoginMC >>> ",data)

    connection = None
    cursor = None

    # Verifica si se recibieron los datos
    if not data:
        return jsonify({"error": "No se recibieron datos válidos."}), 400
    # Procesa los datos JSON
    try:
        credencialesMC = data.get('LOGIN')
        USR = credencialesMC.get('USR')
        PSSWRD = credencialesMC.get('PSSWRD')
        
        if not USR or not PSSWRD:
            return jsonify({"error": "Usuario y contraseña son obligatorios."}), 400

        
        try:
            connection = get_sql_server_connection()
            cursor = connection.cursor()
            cursor.execute("""
                            SELECT US.ID_Usuario, US.Nombre, US.Telefono, US.Activo, US.Username, Password , R.Nombre_Rol
                            FROM USUARIO US INNER JOIN ROL R ON US.ID_Rol = R.ID_Rol WHERE US.Username = ? ;               
            """, (USR,))

            # Obtener los resultados
            usuario = cursor.fetchone()

            if usuario:
                idUsuario = quitaNulo(usuario.ID_Usuario)
                nombre = quitaNulo(usuario.Nombre)
                telefono = quitaNulo(usuario.Telefono)
                activo = quitaNulo(usuario.Activo)
                username = quitaNulo(usuario.Username)
                password = quitaNulo(usuario.Password)
                rol = quitaNulo(usuario.Nombre_Rol) 
                if (activo == "S"):
                    if (password == quitaNulo(PSSWRD)):
                        return jsonify({"CODIGO": "200", "MENSAJE": "OK", "AUTORIZACION": True, "TIPO": rol, "ID": idUsuario, "NOMBRE": nombre}), 200
                    else:
                        return jsonify({"CODIGO": "401", "MENSAJE": "La contraseña es incorrecta, por favor inténtalo de nuevo.", "AUTORIZACION": False}), 401
                else:
                    return jsonify({"CODIGO": "403", "MENSAJE": "El usuario ingresado está inactivo. Contacte al administrador.", "AUTORIZACION": False}), 403
                
            else:
                 return jsonify({"CODIGO": "404", "MENSAJE": "No existe una cuenta con el nombre de usuario ingresado. Por favor, inténtalo de nuevo.", "AUTORIZACION": False}), 404
    
        except pyodbc.Error as e:
            return jsonify({"CODIGO": "500", "MENSAJE": "Error de comunicación a la base de datos. Contácte al administrador.", "AUTORIZACION": False}), 500
        finally:
            # Cerrar la conexión
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    except Exception as e:
        print("Error:::: ",str(e))
        return jsonify({"CODIGO": "500", "MENSAJE": "Ocurrió un error en el servidor. Inténtalo de nuevo, si el inconveniente persiste contacte al administrador.", "AUTORIZACION": False}), 500


#Endpoint insertar pedido - producción
@app.route('/ingresoPedidoMC', methods=['POST'])
def ingresoPedidoMC():
    # Obtiene los datos JSON de la solicitud
    data = request.get_json()
    print("ingresoPedidoMC >>> La data entrante es: ",data)

    connection = None
    cursor = None

    # Verifica si se recibieron los datos
    if not data:
        return jsonify({"error": "No se recibieron datos válidos."}), 400
    # Procesa los datos JSON
    try:
        infoPedido = data.get('infoPedido')
        FOLIO = infoPedido.get('folio')
        FECHA = infoPedido.get('fecha')
        CAJERO = infoPedido.get('cajero')
        CLIENTE = infoPedido.get('cliente')
        TOTAL = infoPedido.get('total')
        PAGO = infoPedido.get('pago')
        CAMBIO = infoPedido.get('cambio')
        ESTATUS = infoPedido.get('estatus')
        USUARIO = data.get('usuario')
        DETALLE = json.dumps(infoPedido.get('detallePedido', []))
        print("entra infoPedido: ",infoPedido)
        print("entra usuario: ",USUARIO)

        # Inserta los datos en la tabla USUARIO en SQL Server
        connection = get_sql_server_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""INSERT INTO PEDIDO (FOLIO, FECHA, CAJERO, CLIENTE, TOTAL, PAGO, CAMBIO, ID_USUARIOREGISTRO, DETALLE)
                VALUES (?, ?, ?, ?, ?, ?, ?, (SELECT ID_USUARIO FROM USUARIO WHERE USERNAME=?), ?)""", (FOLIO, FECHA, CAJERO, CLIENTE, TOTAL, PAGO, CAMBIO, USUARIO, DETALLE))
            connection.commit()

            return jsonify({"mensaje": f"El pedido con No. folio {FOLIO}  ha pasado a producción."}), 201
    
        except pyodbc.Error as e:
            # Rollback en caso de error
            connection.rollback()

            error_msg = str(e)
            error_code = e.args[0]

            # Manejar error de conversión de fecha
            if '22007' in error_code:
                return jsonify({"error": "Error en la conversión de la fecha. Verifica el formato de la fecha ingresada."}), 400

            # Manejar error de clave duplicada
            elif '23000' in error_code and 'duplicate key' in error_msg.lower():
                return jsonify({"error": f"El pedido con número de folio {FOLIO} ya se encuentra registrado."}), 409

            # Otros errores
            else:
                return jsonify({"error": f"Error inesperado al ejecutar la consulta. Intenta nuevamente, si el inconveniente persiste contacte al administrador."}), 500
        finally:
            # Cerrar la conexión
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    except Exception as e:
        print("Error:::: ",str(e))
        return jsonify({"error": "Excepción producida al ingresar el pedido. Intenta nuevamente."}), 500

#Endpoint consultar lista de pedidos Vendedor - Piloto - Administrador
@app.route('/obtengoPedidosDashboardMC', methods=['POST'])
def obtengoPedidosDashboardMC():
    # Obtiene los datos JSON de la solicitud
    data = request.get_json()
    print(">>> La data entrante es: ", data)
    
    connection = None
    cursor = None

    # Verifica si se recibieron los datos
    if not data:
        return jsonify({"error": "No se recibieron datos válidos."}), 400
    
    # Procesa los datos JSON
    try:
        infoUsuario = data.get('infoUsuario')
        USUARIO = infoUsuario.get('usuario')

        # Consultar pedidos a cargo del usuario CONVERT(VARCHAR(20), P.Fecha, 103) + ' ' + CONVERT(VARCHAR(8), P.Fecha, 108) AS FECHA, 
        connection = get_sql_server_connection()
        cursor = connection.cursor()
        cursor.execute("""
                    SELECT 
                        p.Folio AS FOLIO,
                        p.Fecha AS FECHA,
                        p.Cajero AS CAJERO,
                        p.Cliente AS CLIENTE,
                        p.Total AS TOTAL,
                        p.Pago AS PAGO,
                        p.Cambio AS CAMBIO,
                        ur.Username AS USUARIO_REGISTRO,
                        p.Estatus AS ESTADO_ACTUAL,
                        uc.Username AS USUARIO_CAMBIO,
                        um.Username AS MENSAJERO,
                        um.ID_Usuario AS IDMENSAJERO,
                        pa.Nombre AS PAQUETERIA,
                        pa.ID_Paqueteria AS IDPAQUETERIA,
                        CONVERT(VARCHAR(20), ep.FechaTransaccion, 103) + ' ' + CONVERT(VARCHAR(8), ep.FechaTransaccion, 108) AS FECHA_ESTADO, 
                        ep.Observaciones AS OBSERVACIONES
                    FROM 
                        USUARIO u
                    JOIN
                        ROL r ON u.ID_Rol = r.ID_Rol
                    LEFT JOIN
                        PEDIDO p ON
                        (R.Nombre_Rol = 'VENDEDOR' AND p.ID_UsuarioRegistro = u.ID_Usuario) OR
                        (R.Nombre_Rol = 'ADMINISTRADOR') OR
                        (R.Nombre_Rol = 'PILOTO' AND EXISTS (
                            SELECT 1 
                            FROM ESTADOS_PEDIDO EP 
                            WHERE EP.ID_Mensajero = U.ID_Usuario AND EP.Folio = P.Folio
                        ))
                    LEFT JOIN 
                        ESTADOS_PEDIDO ep ON p.Folio = ep.Folio
                    LEFT JOIN
                        USUARIO ur ON p.ID_UsuarioRegistro = ur.ID_Usuario
                    LEFT JOIN 
                        USUARIO um ON ep.ID_Mensajero = um.ID_Usuario 
                    LEFT JOIN
                        USUARIO uc ON ep.ID_Usuario = uc.ID_Usuario
                    LEFT JOIN
                        PAQUETERIA pa ON ep.ID_Paqueteria = pa.ID_Paqueteria
                    WHERE 
                        u.Username = ? -- Filtro usuario
                        AND (
                            (p.Estatus IN ('Anulado', 'Entregado') AND ep.EstadoNuevo IN ('Anulado', 'Entregado') AND CAST(ep.FechaTransaccion AS DATE) = CAST(GETDATE() AS DATE))
                            OR (p.Estatus NOT IN ('Anulado', 'Entregado'))
                        )
                        AND p.Estatus = ep.EstadoNuevo
                    ORDER BY 
                        p.Folio, ep.FechaTransaccion DESC; 
        """, (USUARIO))
        
        # Obtener los resultados
        rows = cursor.fetchall()
        
        # Convertir los resultados a un diccionario
        listadoPedidos = []
        for row in rows:
            pedido = {
                "folio": quitaNulo(row.FOLIO),
                "fecha": quitaNulo(row.FECHA),
                "cajero": quitaNulo(row.CAJERO),
                "cliente": quitaNulo(row.CLIENTE),
                "total": quitaNulo(row.TOTAL),
                "pago": quitaNulo(row.PAGO),
                "cambio": quitaNulo(row.CAMBIO),
                "mensajero": quitaNulo(row.MENSAJERO),
                "id_mens": quitaNulo(row.IDMENSAJERO),
                "paqueteria": quitaNulo(row.PAQUETERIA),
                "id_paq": quitaNulo(row.IDPAQUETERIA),
                "usuario_registro": quitaNulo(row.USUARIO_REGISTRO),
                "usuario_cambio" : quitaNulo(row.USUARIO_CAMBIO),
                "estado_actual": quitaNulo(row.ESTADO_ACTUAL),
                "fecha_estado": quitaNulo(row.FECHA_ESTADO),
                "observaciones": quitaNulo(row.OBSERVACIONES)
            }
            listadoPedidos.append(pedido)

        
        # Retornar los resultados en formato JSON
        return jsonify({"listadoPedidos": listadoPedidos}),201
    
    except Exception as e:
        print("Error: ", e)
        return jsonify({"error": "Ocurrió un error al procesar la solicitud"}), 500
    finally:
        # Cerrar la conexión
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    
#Endpoint consultar lista de pedidos Historial
@app.route('/obtengoHistorialPedidosMC', methods=['POST'])
def obtengoHistorialPedidosMC():
    # Obtiene los datos JSON de la solicitud
    data = request.get_json()
    print(" obtengoHistorialPedidosMC >>>", data)

    connection = None
    cursor = None
    
    # Verifica si se recibieron los datos
    if not data:
        return jsonify({"error": "No se recibieron datos válidos."}), 400
    
    # Procesa los datos JSON
    try:
        USUARIO_CONSULTA = data.get('usuarioConsulta')
        USUARIO = data.get('usuario')
        FECHA_INICIO = data.get('fechaInicio')
        FECHA_FIN = data.get('fechaFin')
        ESTADO = data.get('estado')
        PILOTO = data.get('piloto')

       
        connection = get_sql_server_connection()
        cursor = connection.cursor()
        query = """ 
            SELECT 
                p.Folio AS FOLIO,
                p.Fecha AS FECHA,
                p.Cajero AS CAJERO,
                p.Cliente AS CLIENTE,
                p.Total AS TOTAL,
                p.Pago AS PAGO,
                p.Cambio AS CAMBIO,
                ur.Username AS USUARIO_REGISTRO,
                p.Estatus AS ESTADO_ACTUAL,
                ep.EstadoNuevo AS ESTADO,
                uc.Username AS USUARIO_CAMBIO,
                um.Username AS MENSAJERO,
                um.ID_Usuario AS IDMENSAJERO,
                pa.Nombre AS PAQUETERIA,
                pa.ID_Paqueteria AS IDPAQUETERIA,
                CONVERT(VARCHAR(20), ep.FechaTransaccion, 103) + ' ' + CONVERT(VARCHAR(8), ep.FechaTransaccion, 108) AS FECHA_ESTADO, 
                ep.Observaciones AS OBSERVACIONES
            FROM 
                USUARIO u
            JOIN
                ROL r ON u.ID_Rol = r.ID_Rol
            LEFT JOIN
                PEDIDO p ON
                (R.Nombre_Rol = 'VENDEDOR' AND p.ID_UsuarioRegistro = u.ID_Usuario) OR
                (R.Nombre_Rol = 'ADMINISTRADOR') OR
                (R.Nombre_Rol = 'PILOTO' AND EXISTS (
                    SELECT 1 
                    FROM ESTADOS_PEDIDO EP 
                    WHERE EP.ID_Mensajero = U.ID_Usuario AND EP.Folio = P.Folio
                ))
            LEFT JOIN 
                ESTADOS_PEDIDO ep ON p.Folio = ep.Folio
            LEFT JOIN
                USUARIO ur ON p.ID_UsuarioRegistro = ur.ID_Usuario
            LEFT JOIN 
                USUARIO um ON ep.ID_Mensajero = um.ID_Usuario 
            LEFT JOIN
                USUARIO uc ON ep.ID_Usuario = uc.ID_Usuario
            LEFT JOIN
                PAQUETERIA pa ON ep.ID_Paqueteria = pa.ID_Paqueteria
            WHERE 
                u.Username = ?
        """
        # Lista de parámetros para la consulta, siempre incluirá USUARIO_CONSULTA
        params = [USUARIO_CONSULTA]

        # Agregar condición para USUARIO si está presente
        if USUARIO:
            query += " AND ur.ID_Usuario = ?"
            params.append(USUARIO)

        # Agregar condición para FECHA_INICIO y FECHA_FIN
        if FECHA_INICIO and not FECHA_FIN:
            # Solo se proporciona FECHA_INICIO, usarla en ambas posiciones
            query += " AND (CAST(p.Fecha AS DATE) BETWEEN ? AND ?)"
            params.append(FECHA_INICIO)
            params.append(FECHA_INICIO)  # Usar la misma fecha para ambos

        elif FECHA_INICIO and FECHA_FIN:
            # Ambas fechas se proporcionan, usar FECHA_INICIO primero y FECHA_FIN después
            query += " AND (CAST(p.Fecha AS DATE) BETWEEN ? AND ?)"
            params.append(FECHA_INICIO)
            params.append(FECHA_FIN)

        # Agregar condición para ESTADO si es diferente de "Todos"
        if ESTADO and ESTADO != "Todos":
            query += " AND p.Estatus = ?"
            params.append(ESTADO)

        print("Query : : ", query)
        # Ejecutar la consulta con los parámetros
        cursor.execute(query, params)
        
        # Obtener los resultados
        resultados = cursor.fetchall()

        # Convertir los resultados a un diccionario agrupado por folio
        listadoPedidos = []
        pedidos_dict = {}

        for row in resultados:
            folio = quitaNulo(row.FOLIO)

            # Si el pedido ya existe en el diccionario, solo agregamos el tracking
            if folio in pedidos_dict:
                tracking = {
                    "estado": quitaNulo(row.ESTADO),
                    "usuario_cambio": quitaNulo(row.USUARIO_CAMBIO),
                    "mensajero": quitaNulo(row.MENSAJERO),
                    "id_mensajero": quitaNulo(row.IDMENSAJERO),
                    "paqueteria": quitaNulo(row.PAQUETERIA),
                    "fecha_estado": quitaNulo(row.FECHA_ESTADO),
                    "observaciones": quitaNulo(row.OBSERVACIONES)
                }
                pedidos_dict[folio]["tracking"].append(tracking)
            else:
                # Si es la primera vez que encontramos este folio, creamos el pedido
                pedido = {
                    "folio": folio,
                    "fecha": quitaNulo(row.FECHA),
                    "cajero": quitaNulo(row.CAJERO),
                    "cliente": quitaNulo(row.CLIENTE),
                    "total": quitaNulo(row.TOTAL),
                    "pago": quitaNulo(row.PAGO),
                    "cambio": quitaNulo(row.CAMBIO),
                    "usuario_registro": quitaNulo(row.USUARIO_REGISTRO),
                    "estado_actual": quitaNulo(row.ESTADO_ACTUAL),
                    "tracking": [{
                        "estado": quitaNulo(row.ESTADO),
                        "usuario_cambio": quitaNulo(row.USUARIO_CAMBIO),
                        "mensajero": quitaNulo(row.MENSAJERO),
                        "id_mensajero": quitaNulo(row.IDMENSAJERO),
                        "paqueteria": quitaNulo(row.PAQUETERIA),
                        "fecha_estado": quitaNulo(row.FECHA_ESTADO),
                        "observaciones": quitaNulo(row.OBSERVACIONES)
                    }]
                }
                pedidos_dict[folio] = pedido

        # Convertir el diccionario a una lista
        listadoPedidos = list(pedidos_dict.values())

        # Generar el PDF en base64
        pdf_base64 = generar_pdf_base64(listadoPedidos)

        
        # Retornar los resultados en formato JSON
        return jsonify({"listadoPedidos": listadoPedidos, "pdf_base64": pdf_base64}),201
    
    except Exception as e:
        print("Error: ", e)
        return jsonify({"error": "Ocurrió un error al procesar la solicitud"}), 500
    finally:
        # Cerrar la conexión
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    
#Endpoint consultar listado de Pilotos ACTIVOS = S
@app.route('/obtengoPilotosMC', methods=['POST'])
def obtengoPilotosMC():

    print(">>> obtengoPilotosMC")

    connection = None
    cursor = None
    
    try:
        # Consultar pedidos a cargo del usuario
        connection = get_sql_server_connection()
        cursor = connection.cursor()
        cursor.execute("""
        SELECT 
            U.ID_Usuario AS ID_USUARIO, 
            U.Nombre AS NOMBRE, 
            U.Telefono AS TELEFONO, 
            U.Activo AS ACTIVO, 
            U.Username AS USRNOMBRE
        FROM 
            USUARIO U
        JOIN 
            ROL R ON U.ID_Rol = R.ID_Rol
        WHERE 
            R.Nombre_Rol = 'PILOTO' AND U.Activo = 'S';
        """)
        
        # Obtener los resultados
        rows = cursor.fetchall()
        
        # Convertir los resultados a un diccionario
        listadoPilotos = []
        for row in rows:
            piloto = {
                'id_usuario': row.ID_USUARIO,
                'nombre': row.NOMBRE,
                'telefono': row.TELEFONO,
                'activo': row.ACTIVO,
                'username': row.USRNOMBRE
            }
            listadoPilotos.append(piloto)
    
        # Retornar los resultados en formato JSON
        return jsonify({"listadoPilotos": listadoPilotos}),201
    except Exception as e:
        print("Error: ", e)
        return jsonify({"error": "Ocurrió un error al procesar la solicitud"}), 500
    finally:
        # Cerrar la conexión
        if cursor:
            cursor.close()
        if connection:
            connection.close()

#Endpoint consultar listado de Pilotos - TODOS
@app.route('/consultaPilotosMC', methods=['POST'])
def consultaPilotosMC():

    print(">>> consultaPilotosMC")

    connection = None
    cursor = None
    
    try:
        # Consultar usuarios pilotos
        connection = get_sql_server_connection()
        cursor = connection.cursor()
        cursor.execute("""
        SELECT 
        U.ID_Usuario AS ID_USUARIO, 
        U.Nombre AS NOMBRE, 
        U.Telefono AS TELEFONO, 
        U.Activo AS ACTIVO, 
        U.Username AS USRNOMBRE,
        U.Password AS PASSWD
            FROM 
                USUARIO U
            JOIN 
                ROL R ON U.ID_Rol = R.ID_Rol
            WHERE 
                R.Nombre_Rol = 'PILOTO';
        """)
        
        # Obtener los resultados
        rows = cursor.fetchall()
        
        # Convertir los resultados a un diccionario
        listadoPilotos = []
        for row in rows:
            piloto = {
                'id_usuario': row.ID_USUARIO,
                'nombre': row.NOMBRE,
                'telefono': row.TELEFONO,
                'activo': row.ACTIVO,
                'username': row.USRNOMBRE,
                'password': row.PASSWD
            }
            listadoPilotos.append(piloto)
    
        # Retornar los resultados en formato JSON
        return jsonify({"listadoPilotos": listadoPilotos}),201
    except Exception as e:
        print("Error: ", e)
        return jsonify({"error": "Ocurrió un error al procesar la solicitud"}), 500
    finally:
        # Cerrar la conexión
        if cursor:
            cursor.close()
        if connection:
            connection.close()

#Endpoint consultar listado de Paqueterías - TODOS
@app.route('/consultaPaqueteriasMC', methods=['POST'])
def consultaPaqueteriasMC():

    print(">>> consultaPaqueteriasMC ")

    connection = None
    cursor = None
    
    try:
        # Consultar todos los transportes de paquetería
        connection = get_sql_server_connection()
        cursor = connection.cursor()
        cursor.execute("""
        SELECT 
            ID_Paqueteria AS ID_PAQUETERIA, 
            Nombre AS TRANSPORTE
        FROM 
            PAQUETERIA;
        """)
        
        # Obtener los resultados
        rows = cursor.fetchall()
        
        # Convertir los resultados a un diccionario
        listadoPaqueterias = []
        for row in rows:
            paqueteria = {
                'id_paqueteria': row.ID_PAQUETERIA,
                'nombre': row.TRANSPORTE,
            }
            listadoPaqueterias.append(paqueteria)
    
        # Retornar los resultados en formato JSON
        return jsonify({"listadoPaqueterias": listadoPaqueterias}),201
    except Exception as e:
        print("Error: ", e)
        return jsonify({"error": "Ocurrió un error al procesar la solicitud"}), 500
    finally:
        # Cerrar la conexión
        if cursor:
            cursor.close()
        if connection:
            connection.close()

#Endpoint insertar cambio de estado
@app.route('/cambioEstadoPedidoMC', methods=['POST'])
def cambioEstadoPedidoMC():
    # Obtiene los datos JSON de la solicitud
    data = request.get_json()
    print(">>> cambioEstadoPedidoMC: ",data)

    connection = None
    cursor = None

    # Verifica si se recibieron los datos
    if not data:
        return jsonify({"error": "No se recibieron datos válidos."}), 400
    # Procesa los datos JSON
    try:
        FOLIO = data.get('folio')
        ESTADO_ANTERIOR = data.get('estadoAnterior')
        ESTADO_NUEVO = data.get('estadoNuevo')
        USUARIO_CAMBIO = data.get('usuario')
        MENSAJERO = data.get('idMensajero')
        PAQUETERIA = data.get('idPaqueteria')
        OBSERVACIONES = data.get('observaciones')


        # Inserta los datos en la tabla ESTADOS_PEDIDOS en SQL Server
        connection = get_sql_server_connection()
        cursor = connection.cursor()
        try:
            #Llamado a procedimieto almacenado
            cursor.execute("""EXEC ActualizarEstadoPedido @Folio=?, @EstadoAnterior=?, @EstadoNuevo=?, @Username=?, @ID_Mensajero=?, @ID_Paqueteria=?, @Observaciones=?""", 
                           (FOLIO, ESTADO_ANTERIOR, ESTADO_NUEVO, USUARIO_CAMBIO, MENSAJERO, PAQUETERIA, OBSERVACIONES))
            connection.commit()

            return jsonify({"mensaje": "Pedido No. "+FOLIO+" trasladado al estado "+ESTADO_NUEVO+"."}), 201
    
        except pyodbc.Error as e:
            # Si ocurre un error, deshace los cambios
            connection.rollback()
            error_msg = str(e)
            
            # Error por violación de integridad referencial (por ejemplo, si el Folio no existe en la tabla PEDIDO)
            if 'FOREIGN KEY' in error_msg:
                return jsonify({"error": "Error de integridad referencial: Asegúrate de que los IDs de Folio, Usuario, Mensajero, o Paquetería existan en sus respectivas tablas."}), 400
            
            # Error general de la base de datos
            return jsonify({"error": f"Error al ejecutar la consulta: {error_msg}"}), 500
        
        finally:
            # Cerrar la conexión
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    except Exception as e:
        print("Error:::: ",str(e))
        return jsonify({"error": "Excepción producida al cambiar de estado el pedido actual. Intenta nuevamente."}), 500


#Endpoint consultar listado de Usuarios (TODOS)
@app.route('/consultaUsuariosMC', methods=['POST'])
def consultaUsuariosMC():

    print(">>> consultaUsuariosMC")

    connection = None
    cursor = None
    
    try:
        # Consultar usuarios
        connection = get_sql_server_connection()
        cursor = connection.cursor()
        cursor.execute("""
                       SELECT U.ID_Usuario AS ID, U.Nombre AS NOMBRE, U.Telefono AS TELEFONO, U.Activo AS ACTIVO, U.Username AS USRNOMBRE, R.Nombre_Rol AS ROL, 
                       U.Password AS CONTRA, CONVERT(VARCHAR(20), U.FechaCreacion, 103) + ' ' + CONVERT(VARCHAR(8), U.FechaCreacion, 108) AS FECHA_CREADO 
                       FROM USUARIO U LEFT JOIN ROL R ON U.ID_Rol = R.ID_Rol;
        """)
        
        # Obtener los resultados
        rows = cursor.fetchall()
        
        # Convertir los resultados a un diccionario
        listadoUsuarios = []
        for row in rows:
            user = {
                'id_usuario': row.ID,
                'nombre': row.NOMBRE,
                'telefono': row.TELEFONO,
                'activo': row.ACTIVO,
                'username': row.USRNOMBRE,
                'rol': row.ROL,
                'password' : row.CONTRA,
                'fecha_creado' : row.FECHA_CREADO
            }
            listadoUsuarios.append(user)
    
        # Retornar los resultados en formato JSON
        return jsonify({"listadoUsuarios": listadoUsuarios}),201
    except Exception as e:
        print("Error: ", e)
        return jsonify({"error": "Ocurrió un error al procesar la solicitud"}), 500
    finally:
        # Cerrar la conexión
        if cursor:
            cursor.close()
        if connection:
            connection.close()

#Endpoint consultar lista de roles
@app.route('/consultaRolesMC', methods=['POST'])
def consultaRolesMC():

    print("consultaRolesMC >>>")

    connection = None
    cursor = None
    
    try:
        # Consultar roles
        connection = get_sql_server_connection()
        cursor = connection.cursor()
        cursor.execute("""
                       SELECT ID_Rol, Nombre_Rol FROM ROL;
        """)
        
        # Obtener los resultados
        rows = cursor.fetchall()
        
        # Convertir los resultados a un diccionario
        listadoRoles = []
        for row in rows:
            rol = {
                'id_rol': row.ID_Rol,
                'nombrerol': row.Nombre_Rol
            }
            listadoRoles.append(rol)
    
        # Retornar los resultados en formato JSON
        return jsonify({"listadoRoles": listadoRoles}),201
    except Exception as e:
        print("Error: ", e)
        return jsonify({"error": "Ocurrió un error al procesar la solicitud"}), 500
    finally:
        # Cerrar la conexión
        if cursor:
            cursor.close()
        if connection:
            connection.close()



#------------------ USUARIOS ---------------------------
#Endpoint insertar usuarios
@app.route('/ingresoUsuarioMC', methods=['POST'])
def ingresoUsuarioMC():
    # Obtiene los datos JSON de la solicitud
    data = request.get_json()
    print("ingresoUsuarioMC >>> La data entrante es: ",data)

    connection = None
    cursor = None

    # Verifica si se recibieron los datos
    if not data:
        return jsonify({"error": "No se recibieron datos válidos."}), 400
    # Procesa los datos JSON
    try:
        NOMBRE = data.get('nombre')
        TELEFONO = data.get('telefono')
        ACTIVO = data.get('activo')
        USERNAME = data.get('username')
        PASSWORD = data.get('password')
        IDROL = data.get('idrol')

        # Inserta los datos en la tabla USUARIO en SQL Server
        connection = get_sql_server_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""INSERT INTO USUARIO (Nombre, Telefono, Activo, Username, Password, ID_Rol, FechaCreacion)
                              VALUES (?, ?, ?, ?, ?, ?, GETDATE()); """, (NOMBRE, TELEFONO, ACTIVO, USERNAME, PASSWORD, IDROL))
            connection.commit()

            return jsonify({"mensaje": f"El usuario '{USERNAME}' ha sido agregado."}), 201
    
        except pyodbc.Error as e:
            # Rollback en caso de error
            connection.rollback()

            error_msg = str(e)
            error_code = e.args[0]

            # Manejar error de restricción UNIQUE (clave duplicada)
            if '23000' in error_code and 'duplicate' in error_msg.lower():
                return jsonify({"error": f"El nombre de usuario '{USERNAME}' ya está en uso. Por favor, elige otro."}), 409

            # Otros errores de base de datos
            else:
                return jsonify({"error": f"Error inesperado en la base de datos: {error_msg}"}), 500

        finally:
            # Cerrar la conexión
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    except Exception as e:
        print("Error::: ", str(e))
        return jsonify({"error": "Ocurrió un error al procesar la solicitud. Intenta nuevamente."}), 500

@app.route('/editarUsuarioMC', methods=['PUT'])
def editarUsuarioMC():
    # Obtiene los datos JSON de la solicitud
    data = request.get_json()
    cambios = []
    print("editarUsuarioMC >>>", data)

    connection = None
    cursor = None

    # Verifica si se recibieron los datos
    if not data:
        return jsonify({"error": "No se recibieron datos válidos."}), 400

    # Procesa los datos JSON
    try:
        ID = data.get('id')
        NOMBRE = data.get('nombre')
        TELEFONO = data.get('telefono')
        ACTIVO = data.get('activo')
        USERNAME = data.get('username')
        PASSWORD = data.get('password')
        IDROL = data.get('idrol')
        USRCAMBIO = data.get('usrcambio')

        connection = get_sql_server_connection()
        
        with connection:
            cursor = connection.cursor()
            try:
                # Recuperar el usuario actual
                cursor.execute("SELECT * FROM USUARIO WHERE ID_Usuario = ?;", ID)
                usuario_actual = cursor.fetchone()

                # Verificar que el usuario existe
                if not usuario_actual:
                    return jsonify({"error": "Usuario no encontrado"}), 404
                print("usuario encontrado: ",usuario_actual)
                # Comprobar cambios y registrar
                if usuario_actual.Nombre != NOMBRE:
                    cambios.append(('Nombre', usuario_actual.Nombre, NOMBRE))
                    cursor.execute("UPDATE USUARIO SET Nombre = ? WHERE ID_Usuario = ?", NOMBRE, ID)

                if usuario_actual.Telefono != TELEFONO:
                    cambios.append(('Telefono', usuario_actual.Telefono, TELEFONO))
                    cursor.execute("UPDATE USUARIO SET Telefono = ? WHERE ID_Usuario = ?", TELEFONO, ID)

                if usuario_actual.Activo != ACTIVO:
                    cambios.append(('Activo', usuario_actual.Activo, ACTIVO))
                    cursor.execute("UPDATE USUARIO SET Activo = ? WHERE ID_Usuario = ?", ACTIVO, ID)

                if usuario_actual.Username != USERNAME:
                    # Verificar si el nuevo Username ya está en uso
                    cursor.execute("SELECT * FROM USUARIO WHERE Username = ? AND ID_Usuario != ?", USERNAME, ID)
                    if cursor.fetchone():
                        return jsonify({"error": "El Username ya está en uso"}), 400

                    cambios.append(('Username', usuario_actual.Username, USERNAME))
                    cursor.execute("UPDATE USUARIO SET Username = ? WHERE ID_Usuario = ?", USERNAME, ID)

                if usuario_actual.Password != PASSWORD:
                    cambios.append(('Password', usuario_actual.Password, PASSWORD))
                    cursor.execute("UPDATE USUARIO SET Password = ? WHERE ID_Usuario = ?", PASSWORD, ID)

                if int(usuario_actual.ID_Rol) != int(IDROL):
                    cambios.append(('ID_Rol', usuario_actual.ID_Rol, IDROL))
                    cursor.execute("UPDATE USUARIO SET ID_Rol = ? WHERE ID_Usuario = ?", IDROL, ID)

                # Registrar cambios en la tabla CAMBIOS_USUARIO
                if cambios:
                    for campo, valor_anterior, valor_nuevo in cambios:
                        cursor.execute("""
                            INSERT INTO CAMBIOS_USUARIO (ID_Usuario, ID_UsuarioCambio, FechaCambio, CampoModificado, ValorAnterior, ValorNuevo, Operacion)
                            VALUES (?, ?, GETDATE(), ?, ?, ?, ?)
                        """, (ID, USRCAMBIO, campo, valor_anterior, valor_nuevo, 'Modificación'))

                # Guardar cambios en la base de datos
                connection.commit()
                return jsonify({"mensaje": "Usuario modificado con éxito"}), 200

            except pyodbc.Error as db_error:
                # Rollback en caso de error en la base de datos
                connection.rollback()
                print(f"Error de base de datos: {db_error}")
                return jsonify({"error": "Error en la base de datos."}), 500

            finally:
                # Cerrar la conexión
                if cursor:
                    cursor.close()
    except Exception as e:
        print("Error::: ", str(e))
        return jsonify({"error": "Ocurrió un error al procesar la solicitud. Intenta nuevamente."}), 500

    finally:
        if connection:
            connection.close()

@app.route('/eliminarUsuarioMC/<int:id_usuario>', methods=['DELETE'])
def eliminarUsuarioMC(id_usuario):
    print(f">>> Eliminando usuario con ID: {id_usuario}")

    connection = None
    cursor = None
    
    try:
       
        connection = get_sql_server_connection()
        with connection:
            cursor = connection.cursor()
            
            # Verificar si el usuario existe
            cursor.execute("SELECT * FROM USUARIO WHERE ID_Usuario = ?;", (id_usuario,))
            usuario = cursor.fetchone()
            
            if not usuario:
                return jsonify({"error": "Usuario no encontrado"}), 404
            
            # Eliminar el usuario
            cursor.execute("DELETE FROM USUARIO WHERE ID_Usuario = ?;", (id_usuario,))
            
            # Confirmar la eliminación
            connection.commit()
            return jsonify({"mensaje": "Usuario eliminado con éxito"}), 200

    except Exception as e:
        error_message = str(e)
        print(f"Error::: {error_message}")
        
        # Verifica si el error es un conflicto de clave foránea
        if "conflicted with the REFERENCE constraint" in error_message:
            return jsonify({"error": "No se ha podido eliminar el usuario. Intente editarlo y colóquelo como inactivo si desea revocar permisos de acceso al sistema."}), 400
        
        # Para otros errores, puedes retornar un mensaje genérico
        return jsonify({"error": "Error al eliminar el usuario"}), 500

    finally:
        # Cerrar la conexión
        if cursor:
           cursor.close()
        if connection:
           connection.close()


#------------------- ROLES -----------------------------
#Endpoint insertar roles
@app.route('/ingresoRolMC', methods=['POST'])
def ingresoRolMC():
    # Obtiene los datos JSON de la solicitud
    data = request.get_json()
    print("ingresoRolMC >>> La data entrante es: ",data)

    connection = None
    cursor = None

    # Verifica si se recibieron los datos
    if not data:
        return jsonify({"error": "No se recibieron datos válidos."}), 400
    # Procesa los datos JSON
    try:
        NOMBRE = data.get('nombrerol')

        # Inserta los datos en la tabla USUARIO en SQL Server
        connection = get_sql_server_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""INSERT INTO ROL (Nombre_Rol)
                              VALUES (?); """, (NOMBRE))
            connection.commit()

            return jsonify({"mensaje": f"El rol '{NOMBRE}' ha sido agregado."}), 201
    
        except pyodbc.Error as e:
            # Rollback en caso de error
            connection.rollback()

            error_msg = str(e)
            error_code = e.args[0]

            # Manejar error de restricción UNIQUE (clave duplicada)
            if '23000' in error_code and 'duplicate' in error_msg.lower():
                return jsonify({"error": f"El rol de usuario '{NOMBRE}' ya está registrado. Por favor, intenta nuevamente."}), 409

            # Otros errores de base de datos
            else:
                return jsonify({"error": f"Error inesperado en la base de datos: {error_msg}"}), 500

        finally:
            # Cerrar la conexión
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    except Exception as e:
        print("Error::: ", str(e))
        return jsonify({"error": "Ocurrió un error al procesar la solicitud. Intenta nuevamente."}), 500

@app.route('/editarRolMC', methods=['PUT'])
def editarRolMC():
    # Obtiene los datos JSON de la solicitud
    data = request.get_json()
    
    print("editarRolMC >>>", data)

    connection = None
    cursor = None

    # Verifica si se recibieron los datos
    if not data:
        return jsonify({"error": "No se recibieron datos válidos."}), 400

    # Procesa los datos JSON
    try:
        # Extrae los valores de la solicitud
        IDROL = data.get('id_rol')
        NOMBRE_ROL = data.get('nombrerol')

        # Verifica que se envió el ID y el nombre del rol
        if not IDROL or not NOMBRE_ROL:
            return jsonify({"error": "Faltan datos necesarios (id_rol, nombre_rol)."}), 400

        connection = get_sql_server_connection()
        
        with connection:
            cursor = connection.cursor()

            # Verificar si el rol existe
            cursor.execute("SELECT * FROM ROL WHERE ID_Rol = ?;", IDROL)
            rol_actual = cursor.fetchone()

            if not rol_actual:
                return jsonify({"error": "Rol no encontrado"}), 404

            # Actualizar el nombre del rol
            cursor.execute("UPDATE ROL SET Nombre_Rol = ? WHERE ID_Rol = ?", NOMBRE_ROL, IDROL)

            # Guardar cambios en la base de datos
            connection.commit()

            return jsonify({"mensaje": "Rol modificado con éxito"}), 200

    except pyodbc.Error as db_error:
        # Rollback en caso de error en la base de datos
        connection.rollback()
        print(f"Error de base de datos: {db_error}")
        return jsonify({"error": "Error en la base de datos."}), 500

    except Exception as e:
        print(f"Error::: {str(e)}")
        return jsonify({"error": "Ocurrió un error al procesar la solicitud. Intenta nuevamente."}), 500

    finally:
        # Cerrar la conexión
        if cursor:
           cursor.close()
        if connection:
           connection.close()

@app.route('/eliminarRolMC/<int:id_rol>', methods=['DELETE'])
def eliminarRol(id_rol):
    print(f">>> Eliminando rol con ID: {id_rol}")

    connection = None
    cursor = None
    
    try:
        connection = get_sql_server_connection()
        with connection:
            cursor = connection.cursor()
            
            # Verificar si el rol existe
            cursor.execute("SELECT Nombre_Rol FROM ROL WHERE ID_Rol = ?;", (id_rol))
            rol = cursor.fetchone()
            
            if not rol:
                return jsonify({"error": "Rol no encontrado"}), 404
            
            # Accede al segundo valor de la tupla (Nombre_Rol)
            nombre_rol = rol[0]  

            # Eliminar el rol
            cursor.execute("DELETE FROM ROL WHERE ID_Rol = ?;", (id_rol,))
            
            # Confirmar la eliminación
            connection.commit()
            return jsonify({"mensaje": f"El rol '{nombre_rol}' se ha eliminado con éxito."}), 200

    except Exception as e:
        error_message = str(e)
        print(f"Error::: {error_message}")
        
        # Verifica si el error es un conflicto de clave foránea
        if "conflicted with the REFERENCE constraint" in error_message:
            return jsonify({"error": f"No se ha podido eliminar el rol '{nombre_rol}'. Puede estar siendo usado por usuarios del sistema."}), 400
        
        # Para otros errores, puedes retornar un mensaje genérico
        return jsonify({"error": "Error al eliminar el rol"}), 500

    finally:
        # Cerrar la conexión
        if cursor:
           cursor.close()
        if connection:
           connection.close()


#------------------- PAQUETERÍAS -----------------------------
#Endpoint insertar roles
@app.route('/ingresoPaqueteriaMC', methods=['POST'])
def ingresoPaqueteriaMC():
    # Obtiene los datos JSON de la solicitud
    data = request.get_json()
    print("ingresoPaqueteriaMC >>> ",data)

    connection = None
    cursor = None

    # Verifica si se recibieron los datos
    if not data:
        return jsonify({"error": "No se recibieron datos válidos."}), 400
    # Procesa los datos JSON
    try:
        NOMBRE = data.get('nombre_paqueteria')

        # Inserta los datos en la tabla PAQUETERIA en SQL Server
        connection = get_sql_server_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""INSERT INTO PAQUETERIA (Nombre)
                              VALUES (?); """, (NOMBRE))
            connection.commit()

            return jsonify({"mensaje": f"La empresa de paquetería '{NOMBRE}' ha sido agregada."}), 201
    
        except pyodbc.Error as e:
            # Rollback en caso de error
            connection.rollback()

            error_msg = str(e)
            error_code = e.args[0]

            # Manejar error de restricción UNIQUE (clave duplicada)
            if '23000' in error_code and 'duplicate' in error_msg.lower():
                return jsonify({"error": f"La empresa de paquetería '{NOMBRE}' ya está registrada. Por favor, intenta nuevamente."}), 409

            # Otros errores de base de datos
            else:
                print(error_msg)
                return jsonify({"error": f"Error inesperado en la base de datos."}), 500

        finally:
            # Cerrar la conexión
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    except Exception as e:
        print("Error::: ", str(e))
        return jsonify({"error": "Ocurrió un error al procesar la solicitud. Intenta nuevamente."}), 500

@app.route('/editarPaqueteriaMC', methods=['PUT'])
def editarPaqueteriaMC():
    # Obtiene los datos JSON de la solicitud
    data = request.get_json()
    print("editarPaqueteriaMC >>>", data)

    connection = None
    cursor = None

    # Verifica si se recibieron los datos
    if not data:
        return jsonify({"error": "No se recibieron datos válidos."}), 400

    # Procesa los datos JSON
    try:
        id_paqueteria = data.get('id_paqueteria')
        nombre_nuevo = data.get('nombre')

        connection = get_sql_server_connection()
        with connection:
            cursor = connection.cursor()
            
            # Verificar si la paquetería existe
            cursor.execute("SELECT * FROM PAQUETERIA WHERE ID_Paqueteria = ?;", (id_paqueteria,))
            paqueteria_actual = cursor.fetchone()

            if not paqueteria_actual:
                return jsonify({"error": "Paquetería no encontrada"}), 404
            
            # Comprobar si el nuevo nombre ya existe
            cursor.execute("SELECT * FROM PAQUETERIA WHERE Nombre = ? AND ID_Paqueteria != ?;", (nombre_nuevo, id_paqueteria))
            if cursor.fetchone():
                return jsonify({"error": "El nombre de la paquetería ya está en uso"}), 400

            # Actualizar el nombre de la paquetería
            cursor.execute("UPDATE PAQUETERIA SET Nombre = ? WHERE ID_Paqueteria = ?", (nombre_nuevo, id_paqueteria))
            
            # Confirmar la actualización
            connection.commit()
            return jsonify({"mensaje": "Paquetería editada con éxito"}), 200

    except Exception as e:
        print(f"Error::: {str(e)}")
        return jsonify({"error": "Error al editar la paquetería"}), 500

    finally:
        # Cerrar la conexión
        if cursor:
           cursor.close()
        if connection:
           connection.close()

@app.route('/eliminarPaqueteriaMC/<int:id_paqueteria>', methods=['DELETE'])
def eliminarPaqueteriaMC(id_paqueteria):
    print(f">>> Eliminando paquetería con ID: {id_paqueteria}")

    connection = None
    cursor = None

    try:
        connection = get_sql_server_connection()
        with connection:
            cursor = connection.cursor()

            # Verificar si la paquetería existe
            cursor.execute("SELECT Nombre FROM PAQUETERIA WHERE ID_Paqueteria = ?;", (id_paqueteria,))
            paqueteria = cursor.fetchone()

            if not paqueteria:
                return jsonify({"error": "Paquetería no encontrada"}), 404
            
            nombre_paq = paqueteria[0]  

            # Eliminar la paquetería
            cursor.execute("DELETE FROM PAQUETERIA WHERE ID_Paqueteria = ?;", (id_paqueteria,))

            # Confirmar la eliminación
            connection.commit()
            return jsonify({"mensaje": f"Paquetería '{nombre_paq}' eliminada con éxito."}), 200

    except Exception as e:
        error_message = str(e)
        print(f"Error::: {error_message}")

        # Verifica si el error es un conflicto de clave foránea
        if "conflicted with the REFERENCE constraint" in error_message:
            return jsonify({"error": f"No se ha podido eliminar la paquetería '{nombre_paq}'. Puede estar siendo utilizada en otras tablas."}), 400

        # Para otros errores, puedes retornar un mensaje genérico
        return jsonify({"error": "Error al eliminar la paquetería"}), 500

    finally:
        # Cerrar la conexión
        if cursor:
           cursor.close()
        if connection:
           connection.close()


#-------------------- ESTADOS --------------------------------
#Endpoint para consultar estados de pedidos
@app.route('/consultaCatalogoEstadosMC', methods=['POST'])
def consultaCatalogoEstadosMC():

    print(">>> consultaCatalogoEstadosMC")

    connection = None
    cursor = None
    
    try:
        # Consultar pedidos a cargo del usuario
        connection = get_sql_server_connection()
        cursor = connection.cursor()
        cursor.execute(""" SELECT IDestado, NombreEstado, CodigoEstado FROM CATALOGO_ESTADOS """)
        
        # Obtener los resultados
        rows = cursor.fetchall()
        
        # Convertir los resultados a un diccionario
        listaEstados = []
        listaCodigos = []
        for row in rows:
            piloto = {
                'id_usuario': row.ID_USUARIO,
                'nombre': row.NOMBRE,
                'telefono': row.TELEFONO,
                'activo': row.ACTIVO,
                'username': row.USRNOMBRE
            }
            listaEstados.append(piloto)
    
        # Retornar los resultados en formato JSON
        return jsonify({"listadoPilotos": listaEstados}),201
    except Exception as e:
        print("Error: ", e)
        return jsonify({"error": "Ocurrió un error al procesar la solicitud"}), 500
    finally:
        # Cerrar la conexión
        if cursor:
            cursor.close()
        if connection:
            connection.close()


if __name__ == '__main__':
    #app.run(debug=True)
    app.run(host='0.0.0.0', port=5000)
