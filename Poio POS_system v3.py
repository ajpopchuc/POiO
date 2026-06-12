import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import shutil
from fpdf import FPDF

# --- PALETA DE COLORES POIO (REFINADA PARA UI) ---
COLOR_NARANJA = "#FF6600"
COLOR_AMARILLO = "#FFCC00"
COLOR_FONDO = "#F5F6F7"  # Gris ultra claro para descansar la vista
COLOR_CARD = "#FFFFFF"   # Blanco para las tarjetas
COLOR_TEXTO = "#2D3436"
COLOR_ROJO = "#FF7675"

class PoioSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("POIO - Gestión de Negocio")
        self.root.geometry("1280x800")
        self.root.configure(bg=COLOR_FONDO)
        
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.BASE_DIR, "poio_business.db")

        self.conn = sqlite3.connect(self.db_path)
        self.create_db()
        
        self.carrito = []
        self.subtotal_actual = 0.0

        # --- ESTILOS MODERNOS ---
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Notebook Minimalista
        self.style.configure("TNotebook", background=COLOR_FONDO, borderwidth=0)
        self.style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[20, 10], background="#E0E0E0")
        self.style.map("TNotebook.Tab", background=[("selected", COLOR_NARANJA)], foreground=[("selected", "white")])
        
        # Header Superior
        self.header = tk.Frame(root, bg=COLOR_CARD, height=70, relief="flat", bd=0)
        self.header.pack(fill="x", side="top")
        
        # Logo Texto (Simulando el estilo de tu logo)
        tk.Label(self.header, text="POIO", font=("Impact", 32), fg=COLOR_NARANJA, bg=COLOR_CARD).pack(side="left", padx=(30, 5))
        tk.Label(self.header, text="FRITURA DE LA BUENA", font=("Segoe UI", 9, "bold"), fg=COLOR_AMARILLO, bg=COLOR_CARD).pack(side="left", pady=(15,0))

        self.tabs = ttk.Notebook(root)
        self.tab_ventas = tk.Frame(self.tabs, bg=COLOR_FONDO)
        self.tab_bodega = tk.Frame(self.tabs, bg=COLOR_FONDO)
        self.tab_compras = tk.Frame(self.tabs, bg=COLOR_FONDO)
        
        self.tabs.add(self.tab_ventas, text="  VENTAS  ")
        self.tabs.add(self.tab_bodega, text="  BODEGA  ")
        self.tabs.add(self.tab_compras, text="  REGISTROS  ")
        self.tabs.pack(expand=1, fill="both", padx=20, pady=10)

        self.setup_ventas()
        self.setup_bodega()
        self.setup_compras()

    # --- LÓGICA DE BASE DE DATOS (SIN CAMBIOS) ---
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

    # --- UI DE BODEGA ---
    def setup_bodega(self):
        main_frame = tk.Frame(self.tab_bodega, bg=COLOR_FONDO)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.info_container = tk.Frame(main_frame, bg=COLOR_FONDO)
        self.info_container.pack(fill="x", pady=10)
        
        tk.Label(main_frame, text="SACAR DE BODEGA A COCINA", font=("Segoe UI", 10, "bold"), fg="#636E72", bg=COLOR_FONDO).pack(pady=10)
        
        self.buttons_container = tk.Frame(main_frame, bg=COLOR_FONDO)
        self.buttons_container.pack(pady=10)
        self.actualizar_labels_bodega()

    def actualizar_labels_bodega(self):
        for widget in self.info_container.winfo_children(): widget.destroy()
        for widget in self.buttons_container.winfo_children(): widget.destroy()
        cursor = self.conn.cursor()
        categorias = ["TIENDA", "BASE", "ESPECIAS", "EMPAQUES"]
        for idx, cat in enumerate(categorias):
            card = tk.LabelFrame(self.info_container, text=f" {cat} ", font=("Segoe UI", 9, "bold"), padx=15, pady=15, bg=COLOR_CARD, fg=COLOR_NARANJA, bd=0, highlightthickness=1, highlightbackground="#E0E0E0")
            card.grid(row=0, column=idx, padx=10, sticky="nw")
            if cat == "TIENDA":
                cursor.execute("SELECT item, cantidad, 'unid' FROM inventario")
            else:
                cursor.execute("SELECT item, cantidad, unidad FROM bodega WHERE categoria=?", (cat,))
            items = cursor.fetchall()
            for i, (nombre, cant, uni) in enumerate(items):
                color = COLOR_TEXTO if cant > 5 else COLOR_ROJO
                tk.Label(card, text=f"{nombre}:", font=("Segoe UI", 9), fg=color, bg=COLOR_CARD).grid(row=i, column=0, sticky="w")
                tk.Label(card, text=f"{int(cant)} {uni}", font=("Segoe UI", 9, "bold"), fg=color, bg=COLOR_CARD).grid(row=i, column=1, sticky="w", padx=10)

        cursor.execute("SELECT item, unidad FROM bodega")
        for i, (nombre, unidad) in enumerate(cursor.fetchall()):
            btn = tk.Button(self.buttons_container, text=f"{nombre}\n-1 {unidad}", width=16, height=3, bg=COLOR_CARD, 
                            relief="flat", font=("Segoe UI", 9, "bold"), fg=COLOR_TEXTO, bd=0, highlightthickness=1, highlightbackground="#E0E0E0",
                            cursor="hand2", command=lambda n=nombre: self.usar_insumo_bodega(n))
            btn.grid(row=i//6, column=i%6, padx=8, pady=8)

    def usar_insumo_bodega(self, nombre):
        cursor = self.conn.cursor()
        cursor.execute("SELECT cantidad FROM bodega WHERE item=?", (nombre,))
        cant_actual = cursor.fetchone()[0]
        if cant_actual <= 0:
            messagebox.showerror("Error", "¡Stock en bodega es 0!")
            return
        if messagebox.askyesno("Confirmar", f"¿Sacar 1 unidad de {nombre}?"):
            cursor.execute("UPDATE bodega SET cantidad = cantidad - 1 WHERE item=?", (nombre,))
            self.conn.commit()
            self.actualizar_labels_bodega()

    # --- UI DE VENTAS (MODERNA) ---
    def setup_ventas(self):
        # Panel Izquierdo (Productos)
        frame_productos = tk.Frame(self.tab_ventas, bg=COLOR_FONDO)
        frame_productos.pack(side="left", fill="both", expand=True, padx=(0, 20))
        
        self.lbl_stock = tk.Label(frame_productos, text="", font=("Segoe UI", 10, "bold"), fg=COLOR_NARANJA, bg=COLOR_FONDO)
        self.lbl_stock.pack(pady=10, anchor="w")
        self.actualizar_labels_stock()
        
        canvas = tk.Canvas(frame_productos, bg=COLOR_FONDO, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame_productos, orient="vertical", command=canvas.yview)
        container = tk.Frame(canvas, bg=COLOR_FONDO)

        container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        prods = [
            ("COMBOS", [("Combo 2 Pzs", 35, 2, 1, 0, 1), ("Combo 3 Pzs", 45, 3, 1, 0, 1)]),
            ("COMPARTIR", [("Familiar 8 Pzs", 120, 8, 0, 1, 4), ("Familiar 6 Pzs", 95, 6, 0, 1, 3)]),
            ("PIEZAS", [("Pierna", 12, 1, 0, 0, 0), ("Cuadril", 12, 1, 0, 0, 0), 
                             ("Pechuga", 15, 1, 0, 0, 0), ("Ala", 12, 1, 0, 0, 0)]),
            ("EXTRAS", [("Porción Papas", 10, 0, 0, 0, 1), ("Gaseosa Personal", 7, 0, 1, 0, 0), ("Gaseosa Grande", 15, 0, 0, 1, 0)])
        ]
        
        row_idx = 0
        for cat, items in prods:
            tk.Label(container, text=cat, font=("Segoe UI", 10, "bold"), bg=COLOR_FONDO, fg="#636E72").grid(row=row_idx, column=0, columnspan=3, sticky="w", pady=(15, 5), padx=10)
            row_idx += 1
            col_idx = 0
            for name, price, pz, gp, gg, papas in items:
                card_frame = tk.Frame(container, bg=COLOR_CARD, highlightthickness=1, highlightbackground="#E0E0E0")
                card_frame.grid(row=row_idx, column=col_idx, padx=8, pady=8)
                
                btn = tk.Button(card_frame, text=f"{name}\n\nQ{price}.00", width=18, height=5, 
                               font=("Segoe UI", 10, "bold"), bg=COLOR_CARD, fg=COLOR_TEXTO, 
                               activebackground=COLOR_FONDO, relief="flat", bd=0, cursor="hand2",
                               command=lambda n=name, p=price, z=pz, p1=gp, p2=gg, pa=papas: self.agregar_al_carrito(n, p, z, p1, p2, pa))
                btn.pack()
                
                col_idx += 1
                if col_idx > 2: col_idx = 0; row_idx += 1
            row_idx += 1

        # Panel Derecho (Carrito / Ticket)
        frame_carrito = tk.Frame(self.tab_ventas, width=380, bg=COLOR_CARD, relief="flat", highlightthickness=1, highlightbackground="#E0E0E0")
        frame_carrito.pack(side="right", fill="both")
        frame_carrito.pack_propagate(False)
        
        tk.Label(frame_carrito, text="ORDEN ACTUAL", font=("Segoe UI", 12, "bold"), bg=COLOR_CARD, fg=COLOR_TEXTO).pack(pady=20)
        
        self.lista_carrito = tk.Listbox(frame_carrito, width=40, height=18, font=("Consolas", 10), borderwidth=0, 
                                        fg=COLOR_TEXTO, bg=COLOR_CARD, selectbackground=COLOR_AMARILLO, highlightthickness=0)
        self.lista_carrito.pack(padx=20)
        
        tk.Frame(frame_carrito, bg="#E0E0E0", height=1).pack(fill="x", padx=20, pady=20)

        self.lbl_total_orden = tk.Label(frame_carrito, text="Q0.00", font=("Segoe UI", 32, "bold"), bg=COLOR_CARD, fg=COLOR_NARANJA)
        self.lbl_total_orden.pack()
        tk.Label(frame_carrito, text="TOTAL A PAGAR", font=("Segoe UI", 8, "bold"), bg=COLOR_CARD, fg="#B2BEC3").pack()
        
        tk.Button(frame_carrito, text="COBRAR ORDEN", bg="#2ECC71", fg="white", font=("Segoe UI", 14, "bold"), 
                  height=2, relief="flat", bd=0, cursor="hand2", command=self.cobrar_orden).pack(fill="x", padx=30, pady=(30, 5))
        
        tk.Button(frame_carrito, text="Limpiar Carrito", bg=COLOR_CARD, fg=COLOR_ROJO, font=("Segoe UI", 9, "bold"), 
                  relief="flat", bd=0, cursor="hand2", command=self.limpiar_carrito).pack(pady=5)

        # Botones de gestión al fondo
        footer_btns = tk.Frame(frame_carrito, bg=COLOR_CARD)
        footer_btns.pack(side="bottom", fill="x", pady=20)
        
        tk.Button(footer_btns, text="Cierre", bg=COLOR_AMARILLO, fg=COLOR_TEXTO, font=("Segoe UI", 8, "bold"), 
                  width=12, relief="flat", command=self.mostrar_cierre_caja).pack(side="left", padx=(30, 5))
        
        tk.Button(footer_btns, text="Backup", bg="#3498DB", fg="white", font=("Segoe UI", 8, "bold"), 
                  width=12, relief="flat", command=self.hacer_backup_manual).pack(side="left")

    # --- LÓGICA DE CARRITO (SIN CAMBIOS) ---
    def agregar_al_carrito(self, nombre, precio, pz, gp, gg, papas):
        self.carrito.append({'nombre': nombre, 'precio': precio, 'pz': pz, 'gp': gp, 'gg': gg, 'papas': papas})
        self.lista_carrito.insert(tk.END, f" {nombre:18} Q{precio:>6.2f}")
        self.subtotal_actual += precio
        self.lbl_total_orden.config(text=f"Q{self.subtotal_actual:.2f}")

    def limpiar_carrito(self):
        self.carrito = []
        self.subtotal_actual = 0.0
        self.lista_carrito.delete(0, tk.END)
        self.lbl_total_orden.config(text="Q0.00")

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

    # --- LÓGICA DE CIERRE Y PDF (SIN CAMBIOS) ---
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

    # --- REGISTROS Y COMPRAS ---
    def registrar_merma(self):
        try:
            item, cant = self.combo_item.get(), float(self.ent_cant.get())
            if not item or cant <= 0: raise ValueError
            if messagebox.askyesno("Confirmar", f"¿Merma de {cant} de {item}?"):
                table = "inventario" if self.tipo_inv.get().startswith("Venta") else "bodega"
                cursor = self.conn.cursor()
                cursor.execute(f"UPDATE {table} SET cantidad = cantidad - ? WHERE item=?", (cant, item))
                self.conn.commit(); self.actualizar_labels_stock(); self.actualizar_labels_bodega()
        except: messagebox.showerror("Error", "Datos inválidos", parent=self.root)

    def setup_compras(self):
        container = tk.Frame(self.tab_compras, bg=COLOR_CARD, padx=40, pady=40, highlightthickness=1, highlightbackground="#E0E0E0")
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(container, text="REGISTRO DE INVENTARIO", font=("Segoe UI", 14, "bold"), bg=COLOR_CARD, fg=COLOR_NARANJA).pack(pady=(0, 20))
        
        self.tipo_inv = ttk.Combobox(container, values=["Venta Rápida (Tienda)", "Bodega (Fardos/Costales)"], state="readonly", width=35)
        self.tipo_inv.pack(pady=5); self.tipo_inv.bind("<<ComboboxSelected>>", self.update_combo_items)
        
        self.combo_item = ttk.Combobox(container, state="readonly", width=35); self.combo_item.pack(pady=5)
        
        tk.Label(container, text="Cantidad:", bg=COLOR_CARD, font=("Segoe UI", 9)).pack(anchor="w", padx=2); self.ent_cant = tk.Entry(container, width=37, bd=1, relief="solid"); self.ent_cant.pack(pady=5)
        tk.Label(container, text="Costo Total (Q):", bg=COLOR_CARD, font=("Segoe UI", 9)).pack(anchor="w", padx=2); self.ent_costo = tk.Entry(container, width=37, bd=1, relief="solid"); self.ent_costo.pack(pady=5)
        
        tk.Button(container, text="GUARDAR COMPRA", bg="#2ECC71", fg="white", font=("Segoe UI", 10, "bold"), width=30, height=2, bd=0, command=self.comprar).pack(pady=(20, 5))
        tk.Button(container, text="REGISTRAR MERMA", bg=COLOR_ROJO, fg="white", width=30, bd=0, command=self.registrar_merma).pack(pady=5)

    def update_combo_items(self, event):
        if "Venta" in self.tipo_inv.get():
            self.combo_item['values'] = ["Pollo (Pz)", "Gaseosa Personal", "Gaseosa Grande", "Carton Papas"]
        else:
            cursor = self.conn.cursor(); cursor.execute("SELECT item FROM bodega"); self.combo_item['values'] = [r[0] for r in cursor.fetchall()]

    def comprar(self):
        try:
            item, cant, costo = self.combo_item.get(), float(self.ent_cant.get()), float(self.ent_costo.get())
            table = "inventario" if "Venta" in self.tipo_inv.get() else "bodega"
            cursor = self.conn.cursor()
            cursor.execute(f"UPDATE {table} SET cantidad = cantidad + ? WHERE item=?", (cant, item))
            cursor.execute("INSERT INTO compras (fecha, item, cantidad, costo) VALUES (?,?,?,?)", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), item, cant, costo))
            self.conn.commit(); self.actualizar_labels_stock(); self.actualizar_labels_bodega()
            messagebox.showinfo("Éxito", "Registrado correctamente.", parent=self.root)
        except: messagebox.showerror("Error", "Datos inválidos.", parent=self.root)

    def actualizar_labels_stock(self):
        cursor = self.conn.cursor(); cursor.execute("SELECT * FROM inventario")
        items = cursor.fetchall(); self.lbl_stock.config(text=f"STOCK EN TIENDA:  {'  |  '.join([f'{i[0]}: {int(i[1])}' for i in items])}")

if __name__ == "__main__":
    root = tk.Tk()
    root.option_add("*Font", "SegoeUI 10")
    app = PoioSystem(root)
    root.mainloop()