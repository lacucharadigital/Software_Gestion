import streamlit as st
import sqlite3
import os
from datetime import datetime

# ============================================
# CONFIGURACIÓN INICIAL
# ============================================

# Ruta absoluta a la base de datos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'tienda.db')

# Inicializar session_state
if 'carrito' not in st.session_state:
    st.session_state.carrito = []
if 'mostrar_confirmacion' not in st.session_state:
    st.session_state.mostrar_confirmacion = False

# ============================================
# CONEXIÓN A BASE DE DATOS
# ============================================

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ============================================
# CABECERA: Título + Botón Confirmar
# ============================================

col1, col2 = st.columns([3, 1])

with col1:
    st.title("Catálogo de Productos")

with col2:
    total_carrito = sum(item['subtotal'] for item in st.session_state.carrito)
    num_items = len(st.session_state.carrito)
    
    if st.button(f"🛒 Confirmar ({num_items} items - {total_carrito:.2f}€)"):
        if st.session_state.carrito:
            st.session_state.mostrar_confirmacion = True
        else:
            st.warning("El carrito está vacío")

# ============================================
# MOSTRAR CARRITO
# ============================================

if st.session_state.carrito:
    with st.expander(f"📋 Ver Carrito ({num_items} productos)"):
        for item in st.session_state.carrito:
            st.write(f"{item['cantidad']}x {item['nombre']} = {item['subtotal']:.2f}€")
        st.write(f"**Total: {total_carrito:.2f}€**")

# ============================================
# PAGINACIÓN
# ============================================

if 'pagina' not in st.session_state:
    st.session_state.pagina = 0

PRODUCTOS_POR_PAGINA = 30
offset = st.session_state.pagina * PRODUCTOS_POR_PAGINA

# ============================================
# LISTADO DE PRODUCTOS
# ============================================

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT p.id_producto, p.nombre, c.nombre as categoria, 
           p.precio, s.cantidad as stock
    FROM Productos p
    JOIN Categorias c ON p.id_categoria = c.id_categoria
    JOIN Stock s ON p.id_producto = s.id_producto
    WHERE p.activo = 1
    ORDER BY p.id_producto
    LIMIT ? OFFSET ?
""", (PRODUCTOS_POR_PAGINA, offset))

productos = cursor.fetchall()

# Mostrar cada producto con botón +
for prod in productos:
    id_prod, nombre, categoria, precio, stock = prod
    
    col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 1, 1, 1, 1])
    
    with col1:
        st.write(nombre)
    with col2:
        st.write(categoria)
    with col3:
        st.write(f"{precio:.2f}€")
    with col4:
        st.write(f"{stock} uds")
    with col5:
        cantidad = st.number_input(
            f"qty_{id_prod}", 
            min_value=1, 
            max_value=stock, 
            value=1, 
            label_visibility="collapsed"
        )
    with col6:
        if st.button(f"➕", key=f"add_{id_prod}"):
            if cantidad <= stock:
                st.session_state.carrito.append({
                    'id_producto': id_prod,
                    'nombre': nombre,
                    'precio': precio,
                    'cantidad': cantidad,
                    'subtotal': precio * cantidad
                })
                st.rerun()
            else:
                st.error("Stock insuficiente")

# ============================================
# CONTROLES DE PAGINACIÓN (abajo)
# ============================================

cursor.execute("SELECT COUNT(*) FROM Productos WHERE activo = 1")
total_productos = cursor.fetchone()[0]
total_paginas = (total_productos // PRODUCTOS_POR_PAGINA) + 1

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    if st.button("⬅️ Anterior") and st.session_state.pagina > 0:
        st.session_state.pagina -= 1
        st.rerun()

with col3:
    if st.button("Siguiente ➡️") and (st.session_state.pagina + 1) * PRODUCTOS_POR_PAGINA < total_productos:
        st.session_state.pagina += 1
        st.rerun()

with col2:
    st.write(f"Página {st.session_state.pagina + 1} de {total_paginas}")

conn.close()

# ============================================
# FORMULARIO DE CONFIRMACIÓN DE VENTA
# ============================================

if st.session_state.mostrar_confirmacion:
    
    st.divider()
    st.subheader("📝 Confirmar Venta")
    
    # Mostrar resumen
    st.write(f"**Total a pagar:** {total_carrito:.2f}€")
    st.write(f"**Número de items:** {num_items}")
    
    # Obtener clientes
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_cliente, nombre FROM Clientes ORDER BY nombre")
    clientes = cursor.fetchall()
    conn.close()
    
    # Formulario
    with st.form("form_confirmar"):
        
        # Desplegable de clientes
        id_cliente = st.selectbox(
            "Seleccionar cliente:",
            options=[c[0] for c in clientes],
            format_func=lambda x: next(c[1] for c in clientes if c[0] == x)
        )
        
        # Botones
        col1, col2 = st.columns(2)
        
        with col1:
            submit = st.form_submit_button("✅ Finalizar Venta")
        
        with col2:
            cancel = st.form_submit_button("❌ Cancelar")
    
    # Procesar resultado del formulario
    if submit:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # 1. Insertar venta
            fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("""
                INSERT INTO Ventas (fecha, id_cliente, total)
                VALUES (?, ?, ?)
            """, (fecha, id_cliente, total_carrito))
            
            id_venta = cursor.lastrowid
            
            # 2. Insertar líneas de venta
            for item in st.session_state.carrito:
                cursor.execute("""
                    INSERT INTO LineasVenta (id_venta, id_producto, cantidad, precio_unitario)
                    VALUES (?, ?, ?, ?)
                """, (id_venta, item['id_producto'], item['cantidad'], item['precio']))
            
            # 3. Guardar todo
            conn.commit()
            conn.close()
            
            # 4. Limpiar carrito
            st.session_state.carrito = []
            st.session_state.mostrar_confirmacion = False
            
            st.success(f"✅ ¡Venta #{id_venta} registrada correctamente!")
            st.balloons()
            
        except Exception as e:
            st.error(f"Error al guardar: {e}")
            conn.rollback()
            conn.close()
    
    if cancel:
        st.session_state.mostrar_confirmacion = False
        st.rerun()