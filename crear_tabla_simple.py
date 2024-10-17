import sqlite3

# Conexión a la base de datos SQLite
conn = sqlite3.connect('usuarios.db')
c = conn.cursor()

# Crear la tabla
c.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        nombre TEXT,
        apellido TEXT,
        cedula TEXT,
        direccion TEXT,
        telefono TEXT,
        ticket INTEGER,
        pago BOOLEAN
    )
''')

# Guardar los cambios y cerrar la conexión
conn.commit()
conn.close()

print("Tabla creada exitosamente.")
