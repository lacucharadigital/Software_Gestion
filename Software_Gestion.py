import sqlite3

# Crear / abrir la base de datos
conn = sqlite3.connect("tienda.db")
cursor = conn.cursor()

# Ejecutar una consulta
cursor.execute("SELECT * FROM Productos")

# Obtener resultados
productos = cursor.fetchall()
for p in productos:
    print(p)

# Cerrar conexión
conn.close()