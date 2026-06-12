import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import shutil
from fpdf import FPDF
import sys # Asegúrate de tener import sys arriba

# --- PALETA DE COLORES POIO ---
COLOR_NARANJA = "#FF6600"
COLOR_AMARILLO = "#FFCC00"
COLOR_FONDO = "#FFF8E1"  # Un crema suave
COLOR_TEXTO = "#333333"

class PoioSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("POIO - Gestión Integral de Local")
        self.root.geometry("1200x850")
        self.root.configure(bg=COLOR_FONDO)
        
        # --- MEJORA: Cierre seguro de BD ---
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # ... dentro del __init__ ...
        if getattr(sys, 'frozen', False):
            # Si la app está empaquetada (.exe)
            self.BASE_DIR = os.path.dirname(sys.executable)
        else:
            # Si la app corre normal (.py)
            self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        self.db_path = os.path.join(self.BASE_DIR, "poio_business.db")

        self.conn = sqlite3.connect(self.db_path)
        self.create_db()
        
        self.carrito = []
        self.subtotal_actual = 0.0

        # --- ESTILOS MODERNOS ---
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Estilo de Pestañas
        self.style.configure("TNotebook", background=COLOR_FONDO, borderwidth=0)
        self.style.configure("TNotebook.Tab", font=("Arial", 11, "bold"), padding=[15, 5], background=COLOR_AMARILLO)
        self.style.map("TNotebook.Tab", background=[("selected", COLOR_NARANJA)], foreground=[("selected", "white")])
        
        # Header de la App
        self.header = tk.Frame(root, bg=COLOR_NARANJA, height=70)
        self.header.pack(fill="x")
        tk.Label(self.header, text="POIO 🍗", font=("Impact", 28), fg="white", bg=COLOR_NARANJA).pack(side="left", padx=20)
        tk.Label(self.header, text="FRITURA DE LA BUENA", font=("Arial", 10, "bold"), fg=COLOR_AMARILLO, bg=COLOR_NARANJA).pack(side="left", pady=(10,0))

        self.tabs = ttk.Notebook(root)
        self.tab_ventas = tk.Frame(self.tabs, bg=COLOR_FONDO)
        self.tab_bodega = tk.Frame(self.tabs, bg=COLOR_FONDO)
        self.tab_compras = tk.Frame(self.tabs, bg=COLOR_FONDO)
        
        self.tabs.add(self.tab_ventas, text="🍗 VENTAS (CAJA)")
        self.tabs.add(self.tab_bodega, text="📦 BODEGA (INSUMOS)")
        self.tabs.add(self.tab_compras, text="➕ REGISTROS")
        self.tabs.pack(expand=1, fill="both", padx=5, pady=5)

        self.setup_ventas()
        self.setup_bodega()
        self.setup_compras()

    # --- TUS FUNCIONES ORIGINALES ---
    def create_db(self):
        cursor = self.conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS inventario (item TEXT PRIMARY KEY, cantidad REAL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS bodega (item TEXT PRIMARY KEY, cantidad REAL, unidad TEXT, categoria TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS ventas (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, total REAL, pago REAL, vuelto REAL)')
        cursor.execute('''CREATE TABLE IF NOT EXISTS detalle_ventas (id INTEGER PRIMARY KEY AUTOINCREMENT, venta_id INTEGER, producto TEXT, precio_u REAL, FOREIGN KEY(venta_id) REFERENCES ventas(id))''')
        cursor.execute('CREATE TABLE IF NOT EXISTS compras (id INTEGER PRIMARY KEY, fecha TEXT, item TEXT, cantidad REAL, costo REAL)')
        
        items_v = [('Pollo (Pz)', 0), ('Gaseosa Personal', 0), ('Gaseosa Grande', 0), ('Carton Papas', 0)]
        cursor.executemany("INSERT OR IGNORE INTO inventario VALUES (?, ?)", items_v)
        
        items_b = [
            ('Harina', 0, 'Costal 25lb', 'BASE'), ('Maicena', 0, 'Costal 55lb', 'BASE'), ('Aceite', 0, 'Galón', 'BASE'),
            ('Polvo para hornear', 0, 'Envase 100g', 'ESPECIAS'), ('Sal', 0, 'Bolsa 1lb', 'ESPECIAS'), 
            ('MSG', 0, 'Bolsa 1lb', 'ESPECIAS'), ('Ajo en Polvo', 0, 'Envase 737g', 'ESPECIAS'), 
            ('Cebolla en Polvo', 0, 'Envase 270g', 'ESPECIAS'), ('Curry', 0, 'Envase 56g', 'ESPECIAS'), 
            ('Paprika', 0, 'Envase 420g', 'ESPECIAS'), ('Chiele Cobanero', 0, 'Envase 45g', 'ESPECIAS'), 
            ('Pimienta Negra', 0, 'Envase 240g', 'ESPECIAS'),
            ('Bolsas Kraft 5lb', 0, 'Fardo 500u', 'EMPAQUES'), ('Bolsas Kraft 10lb', 0, 'Fardo 500u', 'EMPAQUES'), 
            ('Bolsas Plast. Peque', 0, 'Fardo 500u', 'EMPAQUES'), ('Bolsas Plast. Grande', 0, 'Fardo 500u', 'EMPAQUES'), 
            ('Servilletas', 0, 'Bolsa 500u', 'EMPAQUES')
        ]
        for item, cant, uni, cat in items_b:
            cursor.execute("INSERT OR IGNORE INTO bodega (item, cantidad, unidad, categoria) VALUES (?, ?, ?, ?)", (item, cant, uni, cat))
        self.conn.commit()

    # --- MEJORA: Cierre de conexión ---
    def on_closing(self):
        self.conn.close()
        self.root.destroy()

    def hacer_backup_manual(self):
        try:
            backup_dir = os.path.join(self.BASE_DIR, "backups")
            if not os.path.exists(backup_dir): os.makedirs(backup_dir)
            nombre = f"backup_poio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            destino = os.path.join(backup_dir, nombre)
            shutil.copy2(self.db_path, destino)
            messagebox.showinfo("Backup Exitoso", f"Copia guardada en:\n{destino}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el respaldo: {e}")

    def setup_bodega(self):
        main_frame = tk.Frame(self.tab_bodega, bg=COLOR_FONDO)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Título en Rojo Oscuro
        tk.Label(main_frame, text="📦 CONTROL DE EXISTENCIAS EN BODEGA", 
                 font=("Segoe UI", 16, "bold"), bg=COLOR_FONDO, fg="#8B0000").pack(pady=15)
        
        # Contenedor para los labels
        self.info_container = tk.Frame(main_frame, bg=COLOR_FONDO)
        self.info_container.pack(pady=10)
        
        # Configuramos las columnas para que tengan peso y se distribuyan
        for i in range(4):
            self.info_container.grid_columnconfigure(i, weight=1)

        tk.Label(main_frame, text="<- CLIC PARA SACAR DE BODEGA A COCINA ->", 
                 font=("Segoe UI", 9, "bold"), fg= COLOR_NARANJA, bg=COLOR_FONDO).pack(pady=(10, 5))
        
        self.buttons_container = tk.Frame(main_frame, bg=COLOR_FONDO)
        self.buttons_container.pack(pady=10)
        
        self.actualizar_labels_bodega()

    def actualizar_labels_bodega(self):
        for widget in self.info_container.winfo_children(): widget.destroy()
        for widget in self.buttons_container.winfo_children(): widget.destroy()
        
        cursor = self.conn.cursor()
        categorias = ["TIENDA", "BASE", "ESPECIAS", "EMPAQUES"]
        
        # 1. Dibujar las tarjetas con ALTURA UNIFORME
        for idx, cat in enumerate(categorias):
            card = tk.LabelFrame(self.info_container, text=f" {cat} ", font=("Segoe UI", 10, "bold"), 
                                 padx=15, pady=15, bg="white", fg="#8B0000",
                                 bd=0, highlightthickness=1, highlightbackground="#D1D1D1")
            
            card.grid(row=0, column=idx, padx=10, sticky="nsew")
            card.grid_columnconfigure(0, weight=1)
            card.grid_columnconfigure(1, weight=1)

            if cat == "TIENDA":
                cursor.execute("SELECT item, cantidad, 'unid' FROM inventario")
            else:
                cursor.execute("SELECT item, cantidad, unidad FROM bodega WHERE categoria=?", (cat,))
            
            items = cursor.fetchall()
            for i, (nombre, cant, uni) in enumerate(items):
                tk.Label(card, text=f"{nombre}:", font=("Segoe UI", 10, "bold"), 
                         fg="#8B0000", bg="white").grid(row=i, column=0, sticky="e", pady=2)
                tk.Label(card, text=f"{int(cant)} {uni}", font=("Segoe UI", 10, "bold"), 
                         fg=COLOR_NARANJA, bg="white").grid(row=i, column=1, sticky="w", padx=5, pady=2)

        # 2. Botones de acción centrados
        cursor.execute("SELECT item, unidad FROM bodega")
        for i, (nombre, unidad) in enumerate(cursor.fetchall()):
            btn_frame = tk.Frame(self.buttons_container, bg="white", 
                                 highlightbackground="#D1D1D1", highlightthickness=1)
            btn_frame.grid(row=i//5, column=i%5, padx=6, pady=3)
            
            btn = tk.Button(btn_frame, text=f"{nombre}\n(-1 {unidad})", 
                            width=16, height=3, bg="white", fg="#8B0000",
                            relief="flat", font=("Segoe UI", 10, "bold"),
                            activebackground=COLOR_FONDO, cursor="hand2",
                            command=lambda n=nombre: self.usar_insumo_bodega(n))
            btn.pack()

    # --- MEJORA: Implementación de salida de bodega ---
    def usar_insumo_bodega(self, nombre):
        if messagebox.askyesno("POIO - Bodega", f"¿Confirmas el uso de 1 unidad de {nombre}?"):
            cursor = self.conn.cursor()
            cursor.execute("UPDATE bodega SET cantidad = cantidad - 1 WHERE item=?", (nombre,))
            self.conn.commit()
            self.actualizar_labels_bodega()

    def setup_ventas(self):
        # Colores específicos
        ROJO_POLLO = "#8B0000"
        
        frame_productos = tk.Frame(self.tab_ventas, bg=COLOR_FONDO)
        frame_productos.pack(side="left", fill="both", expand=True, padx=20, pady=10)
        
        # Stock centrado
        self.lbl_stock = tk.Label(frame_productos, text="", font=("Segoe UI", 10, "bold"), 
                                  fg=COLOR_NARANJA, bg=COLOR_FONDO)
        self.lbl_stock.pack(pady=(0, 15))
        self.actualizar_labels_stock()
        
        # Contenedor PRINCIPAL sin scrollbar
        container = tk.Frame(frame_productos, bg=COLOR_FONDO)
        container.pack(expand=True)

        # Configuración para CENTRAR las 2 columnas
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        prods = [
            ("COMBOS PERSONALES", [("Combo 2 Pzs", 31, 2, 1, 0, 1), ("Combo 3 Pzs", 38, 3, 1, 0, 1)]),
            ("PA' COMPARTIR", [("Familiar 8 Pzs", 100, 8, 0, 1, 4), ("Familiar 6 Pzs", 85, 6, 0, 1, 3)]),
            ("PIEZAS INDIVIDUALES", [("Pierna", 12, 1, 0, 0, 0), ("Cuadril", 12, 1, 0, 0, 0), 
                                     ("Pechuga", 13, 1, 0, 0, 0), ("Ala", 11, 1, 0, 0, 0)]),
            ("EXTRAS Y BEBIDAS", [("Porción Papas", 8, 0, 0, 0, 1), ("Gaseosa Personal", 8, 0, 1, 0, 0), ("Gaseosa Grande", 12, 0, 0, 1, 0), ("Agua Pura", 5, 0, 0, 1, 0)])
        ]
        
        row_idx = 0
        for cat, items in prods:
            tk.Label(container, text=cat, font=("Segoe UI", 15, "bold"), 
                     bg=COLOR_FONDO, fg=ROJO_POLLO).grid(row=row_idx, column=0, columnspan=2, pady=(5, 5))
            row_idx += 1
            col_idx = 0
            for name, price, pz, gp, gg, papas in items:
                card_frame = tk.Frame(container, bg="white", highlightbackground="#D1D1D1", highlightthickness=1)
                card_frame.grid(row=row_idx, column=col_idx, padx=15, pady=4)
                
                btn = tk.Button(card_frame, 
                               text=f"{name.upper()}\nQ{price}.00", 
                               width=22, height=3, 
                               font=("Segoe UI", 11, "bold"),
                               bg="white", 
                               fg=COLOR_NARANJA,
                               activebackground=COLOR_AMARILLO,
                               relief="flat",
                               cursor="hand2",
                               command=lambda n=name, p=price, z=pz, p1=gp, p2=gg, pa=papas: self.agregar_al_carrito(n, p, z, p1, p2, pa))
                btn.pack()
                
                col_idx += 1
                if col_idx > 1: 
                    col_idx = 0
                    row_idx += 1
            row_idx += 1

        # PANEL DERECHO (CARRITO)
        frame_carrito = tk.Frame(self.tab_ventas, width=350, bg="white", relief="flat")
        frame_carrito.pack(side="right", fill="both", padx=15, pady=15)
        frame_carrito.pack_propagate(False)
        
        tk.Label(frame_carrito, text="ORDEN ACTUAL", font=("Segoe UI", 14, "bold"), 
                 bg=ROJO_POLLO, fg="white", pady=12).pack(fill="x")
        
        self.lista_carrito = tk.Listbox(frame_carrito, width=40, height=15, 
                                        font=("Consolas", 11), borderwidth=0, 
                                        fg=COLOR_TEXTO, selectbackground=COLOR_AMARILLO)
        self.lista_carrito.pack(padx=10, pady=10)
        
        self.lbl_total_orden = tk.Label(frame_carrito, text="TOTAL: Q0.00", 
                                        font=("Impact", 26), bg="white", fg=ROJO_POLLO)
        self.lbl_total_orden.pack(pady=10)
        
        tk.Button(frame_carrito, text="💰 COBRAR ORDEN", bg="#28a745", fg="white", 
                  font=("Segoe UI", 14, "bold"), height=2, relief="flat",
                  command=self.cobrar_orden).pack(fill="x", padx=20, pady=5)
        
        tk.Button(frame_carrito, text="🗑️ LIMPIAR CARRITO", bg="#E74C3C", fg="white", 
                  font=("Segoe UI", 10, "bold"), relief="flat",
                  command=self.limpiar_carrito).pack(fill="x", padx=20, pady=5)

        tk.Frame(frame_carrito, bg="#D1D1D1", height=2).pack(fill="x", padx=20, pady=20)

        tk.Button(frame_carrito, text="📊 CIERRE DE CAJA", bg=COLOR_AMARILLO, fg=COLOR_TEXTO,
                  font=("Segoe UI", 10, "bold"), relief="flat",
                  command=self.mostrar_cierre_caja).pack(fill="x", padx=40, pady=5)
        
        tk.Button(frame_carrito, text="💾 RESPALDO DB", bg="#3498DB", fg="white", 
                  font=("Segoe UI", 10, "bold"), relief="flat",
                  command=self.hacer_backup_manual).pack(fill="x", padx=40, pady=5)
        
    def agregar_al_carrito(self, nombre, precio, pz, gp, gg, papas):
        self.carrito.append({'nombre': nombre, 'precio': precio, 'pz': pz, 'gp': gp, 'gg': gg, 'papas': papas})
        self.lista_carrito.insert(tk.END, f"{nombre:15} Q{precio:>6.2f}")
        self.subtotal_actual += precio
        self.lbl_total_orden.config(text=f"TOTAL: Q{self.subtotal_actual:.2f}")

    def limpiar_carrito(self):
        self.carrito = []
        self.subtotal_actual = 0.0
        self.lista_carrito.delete(0, tk.END)
        self.lbl_total_orden.config(text="TOTAL: Q0.00")

    def cobrar_orden(self):
        if not self.carrito: 
            messagebox.showwarning("Atención", "Carrito vacío.", parent=self.root)
            return
        totales = {'Pollo (Pz)': 0, 'Gaseosa Personal': 0, 'Gaseosa Grande': 0, 'Carton Papas': 0}
        for item in self.carrito:
            totales['Pollo (Pz)'] += item['pz']; totales['Gaseosa Personal'] += item['gp']
            totales['Gaseosa Grande'] += item['gg']; totales['Carton Papas'] += item['papas']
        cursor = self.conn.cursor()
        for k, v in totales.items():
            if v > 0:
                cursor.execute("SELECT cantidad FROM inventario WHERE item=?", (k,))
                if cursor.fetchone()[0] < v:
                    messagebox.showerror("Error", f"Sin stock de {k}", parent=self.root); return
        pago = simpledialog.askfloat("Cobro", f"Total: Q{self.subtotal_actual:.2f}\n¿Con cuánto pagan?", parent=self.root)
        if pago is None or pago < self.subtotal_actual: return
        vuelto = pago - self.subtotal_actual
        messagebox.showinfo("Vuelto", f"Vuelto: Q{vuelto:.2f}", parent=self.root)
        
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO ventas (fecha, total, pago, vuelto) VALUES (?,?,?,?)", (fecha, self.subtotal_actual, pago, vuelto))
        venta_id = cursor.lastrowid
        for item in self.carrito:
            cursor.execute("INSERT INTO detalle_ventas (venta_id, producto, precio_u) VALUES (?,?,?)", (venta_id, item['nombre'], item['precio']))
        for k, v in totales.items():
            if v > 0: cursor.execute("UPDATE inventario SET cantidad = cantidad - ? WHERE item=?", (v, k))
        self.conn.commit(); self.limpiar_carrito(); self.actualizar_labels_stock(); self.actualizar_labels_bodega()

    def generar_pdf_cierre(self, fecha, detalles, total_v, fondo_hoy, fondo_man, a_dep):
        try:
            report_dir = os.path.join(self.BASE_DIR, "reportes_pdf")
            if not os.path.exists(report_dir): os.makedirs(report_dir)
            nombre_pdf = f"cierre_{fecha}_{datetime.now().strftime('%H%M%S')}.pdf"
            ruta_pdf = os.path.join(report_dir, nombre_pdf)
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 18)
            pdf.set_text_color(200, 0, 0)
            pdf.cell(200, 10, txt="POIO - REPORTE DE CIERRE DIARIO", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(200, 10, txt=f"Fecha de Operación: {fecha}", ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", 'B', 11)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(20, 10, "Cant", 1, 0, 'C', True)
            pdf.cell(110, 10, "Producto", 1, 0, 'L', True)
            pdf.cell(40, 10, "Total", 1, 1, 'R', True)
            pdf.set_font("Arial", size=11)
            for prod, cant, sub in detalles:
                pdf.cell(20, 10, str(cant), 1, 0, 'C')
                pdf.cell(110, 10, str(prod), 1, 0, 'L')
                pdf.cell(40, 10, f"Q{sub:.2f}", 1, 1, 'R')
            pdf.ln(10)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(130, 8, "VENTAS NETAS DEL DÍA:", 0); pdf.cell(40, 8, f"Q{total_v:.2f}", 0, 1, 'R')
            pdf.cell(130, 8, "FONDO INICIAL:", 0); pdf.cell(40, 8, f"Q{fondo_hoy:.2f}", 0, 1, 'R')
            pdf.set_font("Arial", 'B', 13)
            pdf.cell(130, 10, "TOTAL FÍSICO EN CAJA:", 'T'); pdf.cell(40, 10, f"Q{total_v + fondo_hoy:.2f}", 'T', 1, 'R')
            pdf.ln(5)
            pdf.set_font("Arial", 'I', 12)
            pdf.cell(130, 8, "RESERVA PARA SENCILLO (MAÑANA):", 0); pdf.cell(40, 8, f"Q{fondo_man:.2f}", 0, 1, 'R')
            pdf.set_font("Arial", 'B', 14)
            pdf.set_fill_color(255, 255, 0)
            pdf.cell(130, 12, "TOTAL A DEPOSITAR / ENTREGAR:", 1, 0, 'L', True); pdf.cell(40, 12, f"Q{a_dep:.2f}", 1, 1, 'R', True)
            pdf.output(ruta_pdf)
            messagebox.showinfo("PDF Creado", f"Reporte guardado como: {nombre_pdf}")
        except Exception as e:
            messagebox.showerror("Error PDF", f"Error: {e}")

    def mostrar_cierre_caja(self):
        hoy = datetime.now().strftime("%Y-%m-%d")
        cursor = self.conn.cursor()
        query = "SELECT producto, COUNT(*), SUM(precio_u) FROM detalle_ventas d JOIN ventas v ON d.venta_id = v.id WHERE v.fecha LIKE ? GROUP BY producto"
        cursor.execute(query, (f"{hoy}%",))
        detalles = cursor.fetchall()
        if not detalles:
            messagebox.showinfo("Cierre", "No hay ventas hoy.", parent=self.root); return
        total_v = sum(d[2] for d in detalles)
        fondo_hoy = simpledialog.askfloat("Cierre", "Fondo con el que abriste HOY:", initialvalue=100.0, parent=self.root)
        if fondo_hoy is None: return
        fondo_maniana = simpledialog.askfloat("Cierre", "¿Cuánto dejarás para MAÑANA?", initialvalue=100.0, parent=self.root)
        if fondo_maniana is None: return
        total_fisico = total_v + fondo_hoy
        a_depositar = total_fisico - fondo_maniana
        resumen_pantalla = (f"--- RESUMEN POIO ---\nVentas Netas: Q{total_v:.2f}\nEfectivo Total en Caja: Q{total_fisico:.2f}\n\nDEJAR EN CAJA: Q{fondo_maniana:.2f}\nDEPOSITAR/LLEVAR: Q{a_depositar:.2f}")
        messagebox.showinfo("Reporte de Cierre", resumen_pantalla, parent=self.root)
        if messagebox.askyesno("PDF", "¿Generar reporte PDF para aliados?", parent=self.root):
            self.generar_pdf_cierre(hoy, detalles, total_v, fondo_hoy, fondo_maniana, a_depositar)
        self.root.focus_force()

    def registrar_merma(self):
        try:
            item, cant = self.combo_item.get(), float(self.ent_cant.get())
            if not item or cant <= 0: raise ValueError
            if messagebox.askyesno("Confirmar", f"¿Merma de {cant} de {item}?"):
                # MEJORA: Limpiar nombre para merma igual que en compra
                item_db = item.split(" - ")[0] if " - " in item else item
                item_db = item_db.replace(" (unid)", "")
                
                table = "inventario" if self.tipo_inv.get().startswith("Rotación") else "bodega"
                cursor = self.conn.cursor()
                cursor.execute(f"UPDATE {table} SET cantidad = cantidad - ? WHERE item=?", (cant, item_db))
                self.conn.commit(); self.actualizar_labels_stock(); self.actualizar_labels_bodega()
        except: messagebox.showerror("Error", "Datos inválidos", parent=self.root)

    def setup_compras(self):
        # Colores de marca
        ROJO_OSCURO = "#8B0000"
        
        container = tk.Frame(self.tab_compras, bg="white", padx=50, pady=40, highlightthickness=1, highlightbackground="#D1D1D1")
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(container, text="REGISTRO DE COMPRAS E INVENTARIO", font=("Segoe UI", 18, "bold"), bg="white", fg=ROJO_OSCURO).pack(pady=(0, 25))
        
        font_labels = ("Segoe UI", 11, "bold")
        font_inputs = ("Segoe UI", 12)

        # 1. CATEGORÍA
        tk.Label(container, text="1. Seleccione Categoría:", bg="white", fg=COLOR_NARANJA, font=font_labels).pack(anchor="w", padx=5)
        self.tipo_inv = ttk.Combobox(container, 
                                     values=["Rotación Diaria (1:1 Venta)", "Abastecimiento por Mayor (Fardos/Costales)"], 
                                     state="readonly", width=45, font=font_inputs)
        self.tipo_inv.pack(pady=(5, 15))
        self.tipo_inv.bind("<<ComboboxSelected>>", self.update_combo_items)
        
        # 2. PRODUCTO
        tk.Label(container, text="2. Escriba para filtrar productos:", bg="white", fg=COLOR_NARANJA, font=font_labels).pack(anchor="w", padx=5)
        self.combo_item = ttk.Combobox(container, state="normal", width=45, font=font_inputs)
        self.combo_item.pack(pady=(5, 15))
        self.combo_item.bind("<KeyRelease>", self.filtrar_sin_trabas)
        
        # 3. CANTIDAD
        tk.Label(container, text="3. Cantidad (según unidad indicada):", bg="white", fg=COLOR_NARANJA, font=font_labels).pack(anchor="w", padx=5)
        self.ent_cant = tk.Entry(container, width=46, font=font_inputs, bd=1, relief="solid")
        self.ent_cant.pack(pady=(5, 15))
        
        # 4. COSTO
        tk.Label(container, text="4. Costo Total de la Compra (Q):", bg="white", fg=COLOR_NARANJA, font=font_labels).pack(anchor="w", padx=5)
        self.ent_costo = tk.Entry(container, width=46, font=font_inputs, bd=1, relief="solid")
        self.ent_costo.pack(pady=(5, 15))
        
        # BOTONES
        tk.Button(container, text="➕ REGISTRAR ENTRADA", bg="#28a745", fg="white", 
                  font=("Segoe UI", 12, "bold"), width=38, height=2, bd=0, cursor="hand2",
                  command=self.comprar).pack(pady=(15, 8))
        
        tk.Button(container, text="🗑️ REGISTRAR MERMA", bg=COLOR_AMARILLO, fg="white", 
                  font=("Segoe UI", 11, "bold"), width=38, height=1, bd=0, cursor="hand2",
                  command=self.registrar_merma).pack(pady=5)

    def filtrar_sin_trabas(self, event):
        if event.keysym == "Return":
            self.ent_cant.focus_set()
            return
        if event.keysym in ("Down", "Up", "Left", "Right", "Escape"):
            return
        texto = event.widget.get().lower()
        if texto == '':
            event.widget['values'] = self.lista_completa_productos
        else:
            filtrados = [item for item in self.lista_completa_productos if texto in item.lower()]
            event.widget['values'] = filtrados

    def update_combo_items(self, event):
        cursor = self.conn.cursor()
        if "Rotación" in self.tipo_inv.get():
            self.lista_completa_productos = ["Pollo (Pz)", "Gaseosa Personal (unid)", "Gaseosa Grande (unid)", "Carton Papas (unid)"]
        else:
            cursor.execute("SELECT item, unidad FROM bodega")
            self.lista_completa_productos = [f"{r[0]} - {r[1]}" for r in cursor.fetchall()]
        self.combo_item['values'] = self.lista_completa_productos
        self.combo_item.set('') 
        self.combo_item.focus_set()

    # --- TUS FUNCIONES CON EL ARREGLO DE NOMBRES ---
    def comprar(self):
        try:
            seleccion = self.combo_item.get()
            if not seleccion: return
            
            # --- SOLUCIÓN PARA GASEOSAS Y PAPAS ---
            item_db = seleccion.split(" - ")[0] if " - " in seleccion else seleccion
            item_db = item_db.replace(" (unid)", "") # Esto limpia el nombre para la DB
            
            cant, costo = float(self.ent_cant.get()), float(self.ent_costo.get())
            table = "inventario" if "Rotación" in self.tipo_inv.get() else "bodega"
            
            cursor = self.conn.cursor()
            cursor.execute(f"UPDATE {table} SET cantidad = cantidad + ? WHERE item=?", (cant, item_db))
            cursor.execute("INSERT INTO compras (fecha, item, cantidad, costo) VALUES (?,?,?,?)", 
                           (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), seleccion, cant, costo))
            
            self.conn.commit()
            self.actualizar_labels_stock()
            self.actualizar_labels_bodega()
            
            messagebox.showinfo("Éxito", f"Se han sumado {cant} unidades a {item_db}.", parent=self.root)
            self.ent_cant.delete(0, tk.END)
            self.ent_costo.delete(0, tk.END)
            
        except ValueError:
            messagebox.showerror("Error", "Ingresa números válidos en Cantidad y Costo.", parent=self.root)

    def actualizar_labels_stock(self):
        cursor = self.conn.cursor(); cursor.execute("SELECT * FROM inventario")
        items = cursor.fetchall(); self.lbl_stock.config(text=f"STOCK TIENDA: {' | '.join([f'{i[0]}: {int(i[1])}' for i in items])}")

if __name__ == "__main__":
    root = tk.Tk(); app = PoioSystem(root); root.mainloop()