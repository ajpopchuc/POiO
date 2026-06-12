import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import shutil
from fpdf import FPDF

class PoioSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("POIO - Gestión Integral de Local")
        self.root.geometry("1200x850")
        
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.BASE_DIR, "poio_business.db")

        self.conn = sqlite3.connect(self.db_path)
        self.create_db()
        
        self.carrito = []
        self.subtotal_actual = 0.0

        self.tabs = ttk.Notebook(root)
        self.tab_ventas = ttk.Frame(self.tabs)
        self.tab_bodega = ttk.Frame(self.tabs)
        self.tab_compras = ttk.Frame(self.tabs)
        
        self.tabs.add(self.tab_ventas, text="🍗 VENTAS (CAJA)")
        self.tabs.add(self.tab_bodega, text="📦 BODEGA (INSUMOS)")
        self.tabs.add(self.tab_compras, text="➕ REGISTRAR COMPRAS / MERMAS")
        self.tabs.pack(expand=1, fill="both")

        self.setup_ventas()
        self.setup_bodega()
        self.setup_compras()

    def create_db(self):
        cursor = self.conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS inventario (item TEXT PRIMARY KEY, cantidad REAL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS bodega (item TEXT PRIMARY KEY, cantidad REAL, unidad TEXT, categoria TEXT)')
        
        # TABLAS NORMALIZADAS
        cursor.execute('''CREATE TABLE IF NOT EXISTS ventas 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, total REAL, pago REAL, vuelto REAL)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS detalle_ventas 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, venta_id INTEGER, 
                           producto TEXT, precio_u REAL, 
                           FOREIGN KEY(venta_id) REFERENCES ventas(id))''')
        
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

    def setup_bodega(self):
        main_frame = tk.Frame(self.tab_bodega)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        tk.Label(main_frame, text="📦 CONTROL DE EXISTENCIAS EN BODEGA", font=("Arial", 16, "bold")).pack(pady=10)
        self.info_container = tk.Frame(main_frame)
        self.info_container.pack(fill="x", pady=10)
        tk.Label(main_frame, text="⬇️ CLIC PARA SACAR DE BODEGA A COCINA ⬇️", font=("Arial", 10, "italic"), fg="gray").pack()
        self.buttons_container = tk.Frame(main_frame)
        self.buttons_container.pack(pady=10)
        self.actualizar_labels_bodega()

    def actualizar_labels_bodega(self):
        for widget in self.info_container.winfo_children(): widget.destroy()
        for widget in self.buttons_container.winfo_children(): widget.destroy()
        cursor = self.conn.cursor()
        categorias = ["TIENDA", "BASE", "ESPECIAS", "EMPAQUES"]
        for idx, cat in enumerate(categorias):
            card = tk.LabelFrame(self.info_container, text=f" {cat} ", font=("Arial", 10, "bold"), padx=10, pady=10)
            card.grid(row=0, column=idx, padx=10, sticky="nw")
            if cat == "TIENDA":
                cursor.execute("SELECT item, cantidad, 'unid' FROM inventario")
            else:
                cursor.execute("SELECT item, cantidad, unidad FROM bodega WHERE categoria=?", (cat,))
            items = cursor.fetchall()
            for i, (nombre, cant, uni) in enumerate(items):
                color = "black" if cant > 5 else "red"
                tk.Label(card, text=f"{nombre}:", font=("Arial", 9, "bold"), fg=color).grid(row=i, column=0, sticky="w")
                tk.Label(card, text=f"{int(cant)} {uni}", font=("Arial", 9), fg=color).grid(row=i, column=1, sticky="w", padx=5)

        cursor.execute("SELECT item, unidad FROM bodega")
        for i, (nombre, unidad) in enumerate(cursor.fetchall()):
            btn = tk.Button(self.buttons_container, text=f"{nombre}\n(-1 {unidad})", width=18, height=3, bg="#f8f9fa",
                            command=lambda n=nombre: self.usar_insumo_bodega(n))
            btn.grid(row=i//5, column=i%5, padx=5, pady=5)

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

    def setup_ventas(self):
        frame_productos = tk.Frame(self.tab_ventas)
        frame_productos.pack(side="left", fill="both", expand=True, padx=10)
        self.lbl_stock = tk.Label(frame_productos, text="", font=("Arial", 10, "bold"), fg="blue")
        self.lbl_stock.pack(pady=5)
        self.actualizar_labels_stock()
        
        container = tk.Frame(frame_productos)
        container.pack()
        prods = [
            ("Combos", [("Combo 2 Pzs", 35, 2, 1, 0, 1), ("Combo 3 Pzs", 45, 3, 1, 0, 1)]),
            ("Familiares", [("Familiar 8 Pzs", 120, 8, 0, 1, 4), ("Familiar 6 Pzs", 95, 6, 0, 1, 3)]),
            ("Individuales", [("Pierna", 12, 1, 0, 0, 0), ("Cuadril", 12, 1, 0, 0, 0), 
                             ("Pechuga", 15, 1, 0, 0, 0), ("Ala", 12, 1, 0, 0, 0)]),
            ("Extras", [("Porción Papas", 10, 0, 0, 0, 1), ("Gaseosa Personal", 7, 0, 1, 0, 0), ("Gaseosa Grande", 15, 0, 0, 1, 0)])
        ]
        row_idx = 0
        for cat, items in prods:
            tk.Label(container, text=f"--- {cat} ---", font=("Arial", 10, "bold")).grid(row=row_idx, column=0, columnspan=2, pady=5)
            row_idx += 1
            col_idx = 0
            for name, price, pz, gp, gg, papas in items:
                btn = tk.Button(container, text=f"{name}\nQ{price}", width=20, height=3,
                                command=lambda n=name, p=price, z=pz, p1=gp, p2=gg, pa=papas: self.agregar_al_carrito(n, p, z, p1, p2, pa))
                btn.grid(row=row_idx, column=col_idx, padx=3, pady=3)
                col_idx += 1
                if col_idx > 1: col_idx = 0; row_idx += 1
            row_idx += 1

        frame_carrito = tk.Frame(self.tab_ventas, width=300, bg="#f8f9fa", relief="sunken", bd=2)
        frame_carrito.pack(side="right", fill="both", padx=10, pady=10)
        tk.Label(frame_carrito, text="ORDEN ACTUAL", font=("Arial", 12, "bold"), bg="#f8f9fa").pack(pady=10)
        self.lista_carrito = tk.Listbox(frame_carrito, width=40, height=15, font=("Courier", 10))
        self.lista_carrito.pack(padx=10, pady=5)
        self.lbl_total_orden = tk.Label(frame_carrito, text="TOTAL: Q0.00", font=("Arial", 16, "bold"), bg="#f8f9fa", fg="red")
        self.lbl_total_orden.pack(pady=10)
        tk.Button(frame_carrito, text="🗑️ Limpiar", command=self.limpiar_carrito).pack(fill="x", padx=20, pady=2)
        tk.Button(frame_carrito, text="💰 COBRAR", bg="#28a745", fg="white", font=("Arial", 14, "bold"), height=2, command=self.cobrar_orden).pack(fill="x", padx=20, pady=10)
        tk.Button(frame_carrito, text="📊 Cierre del día", bg="#ffc107", command=self.mostrar_cierre_caja).pack(fill="x", padx=20, pady=5)
        tk.Button(frame_carrito, text="💾 RESPALDO (BACKUP)", bg="#17a2b8", fg="white", command=self.hacer_backup_manual).pack(fill="x", padx=20, pady=5)

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
        
        # INSERT NORMALIZADO
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO ventas (fecha, total, pago, vuelto) VALUES (?,?,?,?)", 
                       (fecha, self.subtotal_actual, pago, vuelto))
        venta_id = cursor.lastrowid
        for item in self.carrito:
            cursor.execute("INSERT INTO detalle_ventas (venta_id, producto, precio_u) VALUES (?,?,?)",
                           (venta_id, item['nombre'], item['precio']))
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
            
            # Encabezado POIO
            pdf.set_font("Arial", 'B', 18)
            pdf.set_text_color(200, 0, 0)
            pdf.cell(200, 10, txt="POIO - REPORTE DE CIERRE DIARIO", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(200, 10, txt=f"Fecha de Operación: {fecha}", ln=True, align='C')
            pdf.ln(10)
            
            # Detalle de Ventas
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
            
            # --- SECCIÓN DE CAJA (Lo que tus aliados verán) ---
            pdf.ln(10)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(130, 8, "VENTAS NETAS DEL DÍA:", 0)
            pdf.cell(40, 8, f"Q{total_v:.2f}", 0, 1, 'R')
            
            pdf.cell(130, 8, "FONDO INICIAL (CON EL QUE SE ABRIÓ):", 0)
            pdf.cell(40, 8, f"Q{fondo_hoy:.2f}", 0, 1, 'R')
            
            pdf.set_font("Arial", 'B', 13)
            pdf.cell(130, 10, "TOTAL FÍSICO EN CAJA:", 'T')
            pdf.cell(40, 10, f"Q{total_v + fondo_hoy:.2f}", 'T', 1, 'R')
            
            pdf.ln(5)
            pdf.set_font("Arial", 'I', 12)
            pdf.cell(130, 8, "RESERVA PARA SENCILLO (MAÑANA):", 0)
            pdf.cell(40, 8, f"Q{fondo_man:.2f}", 0, 1, 'R')
            
            pdf.set_font("Arial", 'B', 14)
            pdf.set_fill_color(255, 255, 0) # Resaltado en amarillo
            pdf.cell(130, 12, "TOTAL A DEPOSITAR / ENTREGAR:", 1, 0, 'L', True)
            pdf.cell(40, 12, f"Q{a_dep:.2f}", 1, 1, 'R', True)
            
            pdf.output(ruta_pdf)
            messagebox.showinfo("PDF Creado", f"Reporte guardado como: {nombre_pdf}")
            
        except Exception as e:
            messagebox.showerror("Error PDF", f"Error: {e}")

    def mostrar_cierre_caja(self):
        hoy = datetime.now().strftime("%Y-%m-%d")
        cursor = self.conn.cursor()
        query = """
            SELECT producto, COUNT(*), SUM(precio_u) 
            FROM detalle_ventas d
            JOIN ventas v ON d.venta_id = v.id
            WHERE v.fecha LIKE ? 
            GROUP BY producto
        """
        cursor.execute(query, (f"{hoy}%",))
        detalles = cursor.fetchall()
        
        if not detalles:
            messagebox.showinfo("Cierre", "No hay ventas hoy.", parent=self.root)
            return

        total_v = sum(d[2] for d in detalles)
        
        # Agregamos parent=self.root para que NO se vayan al fondo
        fondo_hoy = simpledialog.askfloat("Cierre", "Fondo con el que abriste HOY:", 
                                          initialvalue=100.0, parent=self.root)
        if fondo_hoy is None: return
        
        fondo_maniana = simpledialog.askfloat("Cierre", "¿Cuánto dejarás para MAÑANA?", 
                                              initialvalue=100.0, parent=self.root)
        if fondo_maniana is None: return

        total_fisico = total_v + fondo_hoy
        a_depositar = total_fisico - fondo_maniana

        resumen_pantalla = (
            f"--- RESUMEN POIO ---\n"
            f"Ventas Netas: Q{total_v:.2f}\n"
            f"Efectivo Total en Caja: Q{total_fisico:.2f}\n\n"
            f"DEJAR EN CAJA: Q{fondo_maniana:.2f}\n"
            f"DEPOSITAR/LLEVAR: Q{a_depositar:.2f}"
        )
        
        messagebox.showinfo("Reporte de Cierre", resumen_pantalla, parent=self.root)
        
        if messagebox.askyesno("PDF", "¿Generar reporte PDF para aliados?", parent=self.root):
            self.generar_pdf_cierre(hoy, detalles, total_v, fondo_hoy, fondo_maniana, a_depositar)
        
        # Forzar el foco de vuelta a la app principal
        self.root.focus_force()

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
        tk.Label(self.tab_compras, text="COMPRAS / INVENTARIO", font=("Arial", 14, "bold")).pack(pady=10)
        self.tipo_inv = ttk.Combobox(self.tab_compras, values=["Venta Rápida (Tienda)", "Bodega (Fardos/Costales)"], state="readonly")
        self.tipo_inv.pack(); self.tipo_inv.bind("<<ComboboxSelected>>", self.update_combo_items)
        self.combo_item = ttk.Combobox(self.tab_compras, state="readonly"); self.combo_item.pack()
        tk.Label(self.tab_compras, text="Cantidad:").pack(); self.ent_cant = tk.Entry(self.tab_compras); self.ent_cant.pack()
        tk.Label(self.tab_compras, text="Costo Total:").pack(); self.ent_costo = tk.Entry(self.tab_compras); self.ent_costo.pack()
        tk.Button(self.tab_compras, text="➕ Guardar Compra", bg="green", fg="white", command=self.comprar).pack(pady=10)
        tk.Button(self.tab_compras, text="🗑️ Registrar Merma", bg="orange", command=self.registrar_merma).pack(pady=5)

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
            messagebox.showinfo("Éxito", "Registrado.", parent=self.root)
        except: messagebox.showerror("Error", "Datos inválidos.", parent=self.root)

    def actualizar_labels_stock(self):
        cursor = self.conn.cursor(); cursor.execute("SELECT * FROM inventario")
        items = cursor.fetchall(); self.lbl_stock.config(text=f"STOCK TIENDA: {' | '.join([f'{i[0]}: {int(i[1])}' for i in items])}")

if __name__ == "__main__":
    root = tk.Tk(); app = PoioSystem(root); root.mainloop()