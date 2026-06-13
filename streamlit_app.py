import streamlit as st
import sqlite3

st.title("Catálogo de Productos")

# Conexión
conn = sqlite3.connect('tienda.db')
conn.execute("PRAGMA foreign_keys = ON")

# Tamaño de página
PRODUCTOS_POR_PAGINA = 30

# Inicializar página en session_state (Streamlit recarga todo al interactuar)
if 'pagina' not in st.session_state:
    st.session_state.pagina = 0

# Calcular offset
offset = st.session_state.pagina * PRODUCTOS_POR_PAGINA

# Consulta paginada
cursor = conn.cursor()
cursor.execute("""
    SELECT p.id_producto, p.nombre, c.nombre as categoria, p.precio, s.cantidad
    FROM Productos p
    JOIN Categorias c ON p.id_categoria = c.id_categoria
    JOIN Stock s ON p.id_producto = s.id_producto
    WHERE p.activo = 1
    ORDER BY p.id_producto
    LIMIT ? OFFSET ?
""", (PRODUCTOS_POR_PAGINA, offset))

productos = cursor.fetchall()

# Mostrar en tabla
if productos:
    st.dataframe(productos, 
                 column_config={
                     0: "ID",
                     1: "Producto", 
                     2: "Categoría",
                     3: st.column_config.NumberColumn("Precio", format="%.2f €"),
                     4: "Stock"
                 })
else:
    st.info("No hay más productos")

# Controles de paginación
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    if st.button("⬅️ Anterior") and st.session_state.pagina > 0:
        st.session_state.pagina -= 1
        st.rerun()

with col3:
    # Comprobamos si hay más páginas
    cursor.execute("SELECT COUNT(*) FROM Productos WHERE activo = 1")
    total = cursor.fetchone()[0]
    if st.button("Siguiente ➡️") and (st.session_state.pagina + 1) * PRODUCTOS_POR_PAGINA < total:
        st.session_state.pagina += 1
        st.rerun()

with col2:
    st.write(f"Página {st.session_state.pagina + 1} de {(total // PRODUCTOS_POR_PAGINA) + 1}")

conn.close()