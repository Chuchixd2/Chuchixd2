from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import sqlite3
import logging

app = Flask(__name__)

# Configuración de Twilio
account_sid = 'ACceedb04d3e4527bb49587b19c860b610'
auth_token = '8dbec76cc569872f10e39f3daccbb69d'
client = Client(account_sid, auth_token)

# Crear y conectar a la base de datos SQLite
def init_db():
    conn = sqlite3.connect('usuarios.db', check_same_thread=False)
    c = conn.cursor()
    # Eliminar la tabla existente si es necesario
    c.execute('DROP TABLE IF EXISTS usuarios')
    # Crear la tabla con las columnas correctas
    c.execute('''
        CREATE TABLE usuarios (
            nombre TEXT,
            apellido TEXT,
            cedula TEXT,
            direccion TEXT,
            telefono TEXT,
            ticket INTEGER,
            pago BOOLEAN
        )
    ''')
    conn.commit()
    return conn, c

conn, c = init_db()

# Usuarios y contraseñas
usuarios = {'Jesusxd': 'Jesusbb2612'}

# Estado de autenticación de los usuarios
estado_autenticacion = {}

@app.route("/whatsapp", methods=['POST'])
def whatsapp():
    numero = request.form.get('From')
    mensaje = request.form.get('Body').strip()
    logging.info(f"Mensaje recibido de {numero}: {mensaje}")
    respuesta = MessagingResponse()
    msj_respuesta = respuesta.message()

    # Comprobar si el usuario está autenticado
    if numero not in estado_autenticacion:
        estado_autenticacion[numero] = {'autenticado': False, 'intentos': 0, 'proceso': None, 'datos': {}}

    estado = estado_autenticacion[numero]

    if not estado['autenticado']:
        if estado['intentos'] == 0:
            msj_respuesta.body("Bienvenido. Por favor, ingresa tu nombre de usuario:")
        elif estado['intentos'] == 1:
            estado['usuario'] = mensaje
            msj_respuesta.body("Ahora, por favor ingresa tu contraseña:")
        elif estado['intentos'] == 2:
            usuario = estado['usuario']
            if usuario in usuarios and usuarios[usuario] == mensaje:
                estado['autenticado'] = True
                estado['proceso'] = 'nombre_apellido'
                msj_respuesta.body("Autenticación exitosa. ¡Hola, {}! Por favor, ingresa tu nombre y apellido:".format(usuario))
            else:
                estado['intentos'] = 0
                msj_respuesta.body("Usuario o contraseña incorrectos. Por favor, intenta de nuevo. Ingresa tu nombre de usuario:")
        estado['intentos'] += 1
    else:
        # Proceso de recolección de datos
        if estado['proceso'] == 'nombre_apellido':
            estado['datos']['nombre_apellido'] = mensaje
            estado['proceso'] = 'cedula'
            msj_respuesta.body("Ingresa tu número de cédula:")
        elif estado['proceso'] == 'cedula':
            estado['datos']['cedula'] = mensaje
            estado['proceso'] = 'direccion'
            msj_respuesta.body("Ingresa tu dirección:")
        elif estado['proceso'] == 'direccion':
            estado['datos']['direccion'] = mensaje
            estado['proceso'] = 'telefono'
            msj_respuesta.body("Ingresa tu número de teléfono:")
        elif estado['proceso'] == 'telefono':
            estado['datos']['telefono'] = mensaje
            estado['proceso'] = 'ticket'
            msj_respuesta.body("Ingresa tu número de ticket (00 al 1000):")
        elif estado['proceso'] == 'ticket':
            ticket_num = int(mensaje)
            if ticket_num < 0 or ticket_num > 1000:
                msj_respuesta.body("Número de ticket inválido. Por favor, ingresa un número entre 00 y 1000:")
            else:
                c.execute("SELECT * FROM usuarios WHERE ticket = ?", (ticket_num,))
                if c.fetchone():
                    msj_respuesta.body("Ese número de ticket ya está ocupado. Por favor, ingresa un número diferente:")
                else:
                    estado['datos']['ticket'] = ticket_num
                    estado['proceso'] = 'pago'
                    msj_respuesta.body("¿Pagaste el ticket? Responde con 'sí' o 'no':")
        elif estado['proceso'] == 'pago':
            estado['datos']['pago'] = mensaje.lower() == 'sí'
            # Guardar datos en la base de datos
            c.execute("INSERT INTO usuarios (nombre, apellido, cedula, direccion, telefono, ticket, pago) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                      (estado['datos']['nombre_apellido'], estado['datos']['cedula'], estado['datos']['direccion'], 
                       estado['datos']['telefono'], estado['datos']['ticket'], estado['datos']['pago']))
            conn.commit()
            msj_respuesta.body("¡Datos guardados exitosamente!")
            estado['proceso'] = None
        else:
            msj_respuesta.body("¡Mensaje recibido! ¿Cómo puedo ayudarte?")

    return str(respuesta)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True, port=5000)
