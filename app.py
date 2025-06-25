import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import re
from database import SessionLocal
from crud.cliente_crud import crear_cliente, listar_clientes, actualizar_cliente, eliminar_cliente
from crud.ingrediente_crud import crear_ingrediente, obtener_ingredientes, actualizar_ingrediente, eliminar_ingrediente
from crud.menu_crud import crear_menu, listar_menus, actualizar_menu, eliminar_menu
from crud.pedido_crud import crear_pedido
from graficos import grafico_ventas_por_fecha, grafico_menus_mas_vendidos, grafico_ingredientes_mas_utilizados
from models import Cliente, Ingrediente, Menu, Pedido, ingrediente_menu, menu_pedido
from sqlalchemy.orm import joinedload
from datetime import datetime
from Boleta import generar_boleta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Restaurante - Gestión")
        self.geometry("1000x700")
        self.resizable(True, True)

        self.pedido_actual = {}  # Almacena menús seleccionados temporalmente
        self.canvas = None  # Para el lienzo de gráficos

        # Crear tabview
        self.tabview = ctk.CTkTabview(self, width=1000, height=700)
        self.tabview.pack(pady=10, padx=10, fill="both", expand=True)

        # Crear pestañas
        self.tab_ingredientes = self.tabview.add("Ingredientes")
        self.tab_menus = self.tabview.add("Menús")
        self.tab_clientes = self.tabview.add("Clientes")
        self.tab_compra = self.tabview.add("Panel de Compra")
        self.tab_pedidos = self.tabview.add("Pedidos")
        self.tab_graficos = self.tabview.add("Gráficos")

        self.crear_tab_ingredientes()
        self.crear_tab_menus()
        self.crear_tab_clientes()
        self.crear_tab_compra()
        self.crear_tab_pedidos()
        self.crear_tab_graficos()

    def crear_tab_clientes(self):
        frame = ctk.CTkFrame(self.tab_clientes)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("ID", "Nombre", "Correo")
        self.tree_clientes = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            self.tree_clientes.heading(col, text=col)
            self.tree_clientes.column(col, anchor="center", width=150)
        self.tree_clientes.pack(fill="both", expand=True)
        self.tree_clientes.bind('<<TreeviewSelect>>', self.cargar_cliente)

        form_frame = ctk.CTkFrame(frame)
        form_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(form_frame, text="Nombre:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_nombre_cliente = ctk.CTkEntry(form_frame, placeholder_text="Ej: Juan Pérez")
        self.entry_nombre_cliente.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(form_frame, text="Correo:").grid(row=1, column=0, padx=5, pady=5)
        self.entry_correo_cliente = ctk.CTkEntry(form_frame, placeholder_text="Ej: juan@correo.com")
        self.entry_correo_cliente.grid(row=1, column=1, padx=5, pady=5)

        self.cliente_id = None  # Para rastrear cliente seleccionado

        ctk.CTkButton(form_frame, text="Agregar Cliente", command=self.agregar_cliente).grid(row=2, column=0, padx=5, pady=5)
        ctk.CTkButton(form_frame, text="Actualizar Cliente", command=self.actualizar_cliente).grid(row=2, column=1, padx=5, pady=5)
        ctk.CTkButton(form_frame, text="Eliminar Cliente", command=self.eliminar_cliente).grid(row=3, column=0, columnspan=2, pady=5)

        self.actualizar_treeview_clientes()

    def cargar_cliente(self, event):
        selected_item = self.tree_clientes.selection()
        if selected_item:
            cliente_id = int(self.tree_clientes.item(selected_item, "values")[0])
            with SessionLocal() as db:
                cliente = db.query(Cliente).filter_by(id=cliente_id).first()
                self.entry_nombre_cliente.delete(0, tk.END)
                self.entry_correo_cliente.delete(0, tk.END)
                self.entry_nombre_cliente.insert(0, cliente.nombre)
                self.entry_correo_cliente.insert(0, cliente.correo)
                self.cliente_id = cliente_id

    def actualizar_treeview_clientes(self):
        with SessionLocal() as db:
            self.tree_clientes.delete(*self.tree_clientes.get_children())
            for cliente in listar_clientes(db):
                self.tree_clientes.insert("", "end", values=(cliente.id, cliente.nombre, cliente.correo))

    def agregar_cliente(self):
        nombre = self.entry_nombre_cliente.get().strip()
        correo = self.entry_correo_cliente.get().strip()
        
        if not nombre or not correo:
            messagebox.showerror("Error", "Complete todos los campos (nombre y correo)")
            return
        if not re.match(r"[^@]+@[^@]+\.[^@]+", correo):
            messagebox.showerror("Error", "Formato de correo inválido (ej: usuario@dominio.com)")
            return
        
        with SessionLocal() as db:
            try:
                cliente = crear_cliente(db, nombre, correo)
                if cliente:
                    print(f"Cliente agregado: {nombre}, {correo}")  # Depuración
                    self.actualizar_treeview_clientes()
                    self.actualizar_combo_clientes_y_menus()
                    self.entry_nombre_cliente.delete(0, tk.END)
                    self.entry_correo_cliente.delete(0, tk.END)
                    self.cliente_id = None
                    messagebox.showinfo("Éxito", f"Cliente '{nombre}' agregado correctamente")
                else:
                    print(f"Error: Correo {correo} ya registrado")  # Depuración
                    messagebox.showerror("Error", f"El correo '{correo}' ya está registrado. Por favor, use un correo diferente.")
            except Exception as e:
                print(f"Error inesperado al agregar cliente: {e}")  # Depuración
                messagebox.showerror("Error", f"No se pudo agregar el cliente: {str(e)}")

    def actualizar_cliente(self):
        if not self.cliente_id:
            messagebox.showerror("Error", "Seleccione un cliente para actualizar")
            return
        nombre = self.entry_nombre_cliente.get().strip()
        correo = self.entry_correo_cliente.get().strip()
        
        if not nombre or not correo:
            messagebox.showerror("Error", "Complete todos los campos (nombre y correo)")
            return
        if not re.match(r"[^@]+@[^@]+\.[^@]+", correo):
            messagebox.showerror("Error", "Formato de correo inválido (ej: usuario@dominio.com)")
            return
        
        with SessionLocal() as db:
            try:
                cliente = actualizar_cliente(db, self.cliente_id, nombre, correo)
                if cliente:
                    print(f"Cliente actualizado: ID {self.cliente_id}, {nombre}, {correo}")  # Depuración
                    self.actualizar_treeview_clientes()
                    self.actualizar_combo_clientes_y_menus()
                    self.entry_nombre_cliente.delete(0, tk.END)
                    self.entry_correo_cliente.delete(0, tk.END)
                    self.cliente_id = None
                    messagebox.showinfo("Éxito", f"Cliente '{nombre}' actualizado correctamente")
                else:
                    print(f"Error: Correo {correo} ya registrado por otro cliente o cliente no encontrado")  # Depuración
                    messagebox.showerror("Error", f"El correo '{correo}' ya está registrado por otro cliente. Por favor, use un correo diferente.")
            except Exception as e:
                print(f"Error inesperado al actualizar cliente: {e}")  # Depuración
                messagebox.showerror("Error", f"No se pudo actualizar el cliente: {str(e)}")

    def eliminar_cliente(self):
        selected_item = self.tree_clientes.selection()
        if selected_item:
            cliente_id = int(self.tree_clientes.item(selected_item, "values")[0])
            with SessionLocal() as db:
                if eliminar_cliente(db, cliente_id):
                    self.actualizar_treeview_clientes()
                    self.actualizar_combo_clientes_y_menus()
                    self.entry_nombre_cliente.delete(0, tk.END)
                    self.entry_correo_cliente.delete(0, tk.END)
                    self.cliente_id = None
                    messagebox.showinfo("Éxito", "Cliente eliminado")
                else:
                    messagebox.showerror("Error", "No se pudo eliminar el cliente")
        else:
            messagebox.showerror("Error", "Seleccione un cliente")

    def crear_tab_ingredientes(self):
        frame_principal = ctk.CTkFrame(self.tab_ingredientes)
        frame_principal.pack(fill="both", expand=True, padx=10, pady=10)

        frame_derecha = ctk.CTkFrame(frame_principal)
        frame_derecha.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        frame_izquierda = ctk.CTkFrame(frame_principal)
        frame_izquierda.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        subtitulo = ctk.CTkLabel(frame_izquierda, text="Seleccione un ingrediente:", font=("Arial", 15))
        subtitulo.pack(pady=(20, 5), padx=10, anchor="center")

        opciones = ["Papas", "Bebida", "Vienesa", "Pan de Completo", "Tomate", "Palta", "Pan de Hamburguesa", "Lamina de queso", "Churrasco de carne"]
        self.combobox_ingredientes = ctk.CTkComboBox(frame_izquierda, values=opciones, width=150)
        self.combobox_ingredientes.pack(padx=20, anchor="center")

        subtitulo_cantidad = ctk.CTkLabel(frame_izquierda, text="Ingrese la cantidad:", font=("Arial", 15))
        subtitulo_cantidad.pack(pady=(20, 5), padx=10, anchor="center")

        self.entrada_cantidad_ingrediente = ctk.CTkEntry(frame_izquierda, placeholder_text="Ej: 10", width=150)
        self.entrada_cantidad_ingrediente.pack(padx=20, anchor="center")

        ctk.CTkLabel(frame_izquierda, text="Tipo:").pack(pady=(10, 5))
        self.entry_tipo_ingrediente = ctk.CTkEntry(frame_izquierda, placeholder_text="Ej: Vegetal, Proteína", width=150)
        self.entry_tipo_ingrediente.pack(padx=20, anchor="center")

        ctk.CTkLabel(frame_izquierda, text="Unidad:").pack(pady=(10, 5))
        self.entry_unidad_ingrediente = ctk.CTkEntry(frame_izquierda, placeholder_text="Ej: Unidades, Litros", width=150)
        self.entry_unidad_ingrediente.pack(padx=20, anchor="center")

        self.tree_ingredientes = ttk.Treeview(frame_derecha, columns=("ID", "Nombre", "Tipo", "Cantidad", "Unidad"), show="headings", height=10)
        for col in ("ID", "Nombre", "Tipo", "Cantidad", "Unidad"):
            self.tree_ingredientes.heading(col, text=col)
            self.tree_ingredientes.column(col, anchor="center", width=120)
        self.tree_ingredientes.pack(fill="both", expand=True, pady=20, padx=20)
        self.tree_ingredientes.bind('<<TreeviewSelect>>', self.cargar_ingrediente)

        self.ingrediente_id = None

        button_frame = ctk.CTkFrame(frame_izquierda)
        button_frame.pack(pady=20, padx=25, anchor="center")
        ctk.CTkButton(button_frame, text="Agregar Ingrediente", command=self.agregar_ingrediente).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Actualizar Ingrediente", command=self.actualizar_ingrediente).pack(side="left", padx=5)
        ctk.CTkButton(frame_derecha, text="Eliminar Ingrediente", command=self.eliminar_ingrediente).pack(pady=10, anchor="center")

        self.actualizar_treeview_ingredientes()

    def cargar_ingrediente(self, event):
        selected_item = self.tree_ingredientes.selection()
        if selected_item:
            ingrediente_id = int(self.tree_ingredientes.item(selected_item, "values")[0])
            with SessionLocal() as db:
                ingrediente = db.query(Ingrediente).filter_by(id=ingrediente_id).first()
                self.combobox_ingredientes.set(ingrediente.nombre)
                self.entrada_cantidad_ingrediente.delete(0, tk.END)
                self.entrada_cantidad_ingrediente.insert(0, str(ingrediente.cantidad))
                self.entry_tipo_ingrediente.delete(0, tk.END)
                self.entry_tipo_ingrediente.insert(0, ingrediente.tipo)
                self.entry_unidad_ingrediente.delete(0, tk.END)
                self.entry_unidad_ingrediente.insert(0, ingrediente.unidad)
                self.ingrediente_id = ingrediente_id

    def actualizar_treeview_ingredientes(self):
        with SessionLocal() as db:
            self.tree_ingredientes.delete(*self.tree_ingredientes.get_children())
            for ingrediente in obtener_ingredientes(db):
                self.tree_ingredientes.insert("", "end", values=(ingrediente.id, ingrediente.nombre, ingrediente.tipo, ingrediente.cantidad, ingrediente.unidad))

    def agregar_ingrediente(self):
        nombre = self.combobox_ingredientes.get()
        tipo = self.entry_tipo_ingrediente.get()
        unidad = self.entry_unidad_ingrediente.get()
        cantidad = self.entrada_cantidad_ingrediente.get()

        if not (nombre and tipo and unidad and cantidad):
            messagebox.showerror("Error", "Complete todos los campos")
            return
        try:
            cantidad = float(cantidad)
            if cantidad <= 0:
                messagebox.showerror("Error", "La cantidad debe ser mayor que cero")
                return
        except ValueError:
            messagebox.showerror("Error", "Ingrese una cantidad numérica válida")
            return

        with SessionLocal() as db:
            nuevo = crear_ingrediente(db, nombre, tipo, cantidad, unidad)
            if nuevo:
                self.actualizar_treeview_ingredientes()
                self.combobox_ingredientes.set("")
                self.entrada_cantidad_ingrediente.delete(0, tk.END)
                self.entry_tipo_ingrediente.delete(0, tk.END)
                self.entry_unidad_ingrediente.delete(0, tk.END)
                self.ingrediente_id = None
                messagebox.showinfo("Éxito", f"Ingrediente '{nombre}' agregado")
            else:
                messagebox.showerror("Error", "El ingrediente ya existe con ese nombre y tipo")

    def actualizar_ingrediente(self):
        if not self.ingrediente_id:
            messagebox.showerror("Error", "Seleccione un ingrediente para actualizar")
            return
        nombre = self.combobox_ingredientes.get()
        tipo = self.entry_tipo_ingrediente.get()
        unidad = self.entry_unidad_ingrediente.get()
        cantidad = self.entrada_cantidad_ingrediente.get()

        if not (nombre and tipo and unidad and cantidad):
            messagebox.showerror("Error", "Complete todos los campos")
            return
        try:
            cantidad = float(cantidad)
            if cantidad <= 0:
                messagebox.showerror("Error", "La cantidad debe ser mayor que cero")
                return
        except ValueError:
            messagebox.showerror("Error", "Ingrese una cantidad numérica válida")
            return

        with SessionLocal() as db:
            ingrediente = actualizar_ingrediente(db, self.ingrediente_id, nombre=nombre, tipo=tipo, cantidad=cantidad, unidad=unidad)
            if ingrediente:
                self.actualizar_treeview_ingredientes()
                self.combobox_ingredientes.set("")
                self.entrada_cantidad_ingrediente.delete(0, tk.END)
                self.entry_tipo_ingrediente.delete(0, tk.END)
                self.entry_unidad_ingrediente.delete(0, tk.END)
                self.ingrediente_id = None
                messagebox.showinfo("Éxito", f"Ingrediente actualizado")
            else:
                messagebox.showerror("Error", "No se pudo actualizar el ingrediente")

    def eliminar_ingrediente(self):
        selected_item = self.tree_ingredientes.selection()
        if selected_item:
            ingrediente_id = int(self.tree_ingredientes.item(selected_item, "values")[0])
            with SessionLocal() as db:
                if eliminar_ingrediente(db, ingrediente_id):
                    self.actualizar_treeview_ingredientes()
                    self.combobox_ingredientes.set("")
                    self.entrada_cantidad_ingrediente.delete(0, tk.END)
                    self.entry_tipo_ingrediente.delete(0, tk.END)
                    self.entry_unidad_ingrediente.delete(0, tk.END)
                    self.ingrediente_id = None
                    messagebox.showinfo("Éxito", "Ingrediente eliminado")
                else:
                    messagebox.showerror("Error", "No se pudo eliminar el ingrediente")
        else:
            messagebox.showerror("Error", "Seleccione un ingrediente")

    def crear_tab_menus(self):
        frame = ctk.CTkFrame(self.tab_menus)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        left_frame = ctk.CTkFrame(frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=10)

        columns = ("ID", "Nombre", "Precio")
        self.tree_menus = ttk.Treeview(left_frame, columns=columns, show="headings", height=15)
        for col in columns:
            self.tree_menus.heading(col, text=col)
            self.tree_menus.column(col, anchor="center", width=100)
        self.tree_menus.pack(fill="both", expand=True)
        self.tree_menus.bind("<<TreeviewSelect>>", self.mostrar_descripcion_menu)

        btn_crear_menu = ctk.CTkButton(left_frame, text="Crear Menú", command=self.abrir_ventana_crear_menu)
        btn_crear_menu.pack(pady=10)

        btn_actualizar_menu = ctk.CTkButton(left_frame, text="Actualizar Menú", command=self.abrir_ventana_actualizar_menu)
        btn_actualizar_menu.pack(pady=10)

        btn_eliminar_menu = ctk.CTkButton(left_frame, text="Eliminar Menú", command=self.eliminar_menu)
        btn_eliminar_menu.pack(pady=10)

        right_frame = ctk.CTkFrame(frame)
        right_frame.pack(side="left", fill="both", expand=True, padx=10)

        self.label_desc_menu = ctk.CTkLabel(right_frame, text="Descripción del menú seleccionado:", font=("Arial", 15))
        self.label_desc_menu.pack(pady=10)

        self.texto_descripcion = ctk.CTkTextbox(right_frame, width=300, height=300, font=("Arial", 13))
        self.texto_descripcion.pack(padx=10, pady=10)
        self.texto_descripcion.configure(state="disabled")

        self.cargar_menus()

    def cargar_menus(self):
        with SessionLocal() as db:
            self.tree_menus.delete(*self.tree_menus.get_children())
            menus = listar_menus(db)
            for menu in menus:
                self.tree_menus.insert("", "end", values=(menu.id, menu.nombre, f"${menu.precio:.2f}"))

    def mostrar_descripcion_menu(self, event):
        selected = self.tree_menus.selection()
        self.texto_descripcion.configure(state="normal")
        self.texto_descripcion.delete("1.0", "end")
        if not selected:
            self.texto_descripcion.configure(state="disabled")
            return

        menu_id = int(self.tree_menus.item(selected[0], "values")[0])
        with SessionLocal() as db:
            menu = db.query(Menu).filter_by(id=menu_id).first()
            if menu:
                self.texto_descripcion.insert("1.0", menu.descripcion)
            self.texto_descripcion.configure(state="disabled")

    def abrir_ventana_crear_menu(self):
        ventana = ctk.CTkToplevel(self)
        ventana.title("Crear Nuevo Menú")
        ventana.geometry("500x600")
        ventana.transient(self)
        ventana.grab_set()

        ctk.CTkLabel(ventana, text="Nombre del Menú:").pack(pady=5)
        entry_nombre = ctk.CTkEntry(ventana, placeholder_text="Ej: Completo")
        entry_nombre.pack(pady=5)

        ctk.CTkLabel(ventana, text="Descripción:").pack(pady=5)
        entry_descripcion = ctk.CTkTextbox(ventana, height=100, width=300)
        entry_descripcion.pack(pady=5)

        ctk.CTkLabel(ventana, text="Precio:").pack(pady=5)
        entry_precio = ctk.CTkEntry(ventana, placeholder_text="Ej: 3500")
        entry_precio.pack(pady=5)

        ctk.CTkLabel(ventana, text="Selecciona Ingredientes:").pack(pady=5)
        listbox_ingredientes = tk.Listbox(ventana, selectmode=tk.MULTIPLE, height=8, width=40)
        listbox_ingredientes.pack(pady=5)

        cantidades_frame = ctk.CTkFrame(ventana)
        cantidades_frame.pack(pady=5, fill="x")
        cantidades_vars = {}

        with SessionLocal() as db:
            ingredientes = obtener_ingredientes(db)
            print("Ingredientes cargados:", [(i.id, i.nombre) for i in ingredientes])
            if not ingredientes:
                messagebox.showwarning("Advertencia", "No hay ingredientes disponibles. Agregue ingredientes primero.")
                ventana.destroy()
                return
            for ing in ingredientes:
                listbox_ingredientes.insert(tk.END, f"{ing.id}: {ing.nombre} ({ing.tipo})")

        def actualizar_cantidades(event):
            for widget in cantidades_frame.winfo_children():
                widget.destroy()
            cantidades_vars.clear()
            selected_indices = listbox_ingredientes.curselection()
            for idx, index in enumerate(selected_indices):
                ing_id = int(listbox_ingredientes.get(index).split(":")[0])
                ing_nombre = listbox_ingredientes.get(index).split(": ")[1].split(" (")[0]
                cantidades_vars[ing_id] = ctk.StringVar(value="0")
                ctk.CTkLabel(cantidades_frame, text=f"Cant. {ing_nombre}:").grid(row=idx, column=0, padx=5, pady=2, sticky="w")
                ctk.CTkEntry(cantidades_frame, textvariable=cantidades_vars[ing_id], width=100).grid(row=idx, column=1, padx=5, pady=2)

        listbox_ingredientes.bind("<<ListboxSelect>>", actualizar_cantidades)

        def guardar_menu():
            nombre = entry_nombre.get().strip()
            descripcion = entry_descripcion.get("1.0", "end").strip()
            precio_str = entry_precio.get().strip()
            ingredientes_info = []

            if not nombre or not descripcion or not precio_str:
                messagebox.showerror("Error", "Complete todos los campos")
                return
            try:
                precio = float(precio_str)
                if precio <= 0:
                    messagebox.showerror("Error", "El precio debe ser mayor que cero")
                    return
            except ValueError:
                messagebox.showerror("Error", "Ingrese un precio numérico válido")
                return

            for ing_id in cantidades_vars:
                cantidad = cantidades_vars[ing_id].get().strip()
                try:
                    cantidad_float = float(cantidad)
                    if cantidad_float > 0:
                        ingredientes_info.append({"ingrediente_id": ing_id, "cantidad": cantidad_float})
                except ValueError:
                    continue

            print("Ingredientes seleccionados:", ingredientes_info)
            if not ingredientes_info:
                messagebox.showerror("Error", "Seleccione al menos un ingrediente con cantidad mayor que cero")
                return

            with SessionLocal() as db:
                if db.query(Menu).filter_by(nombre=nombre).first():
                    messagebox.showerror("Error", "El nombre del menú ya existe")
                    return
                nuevo_menu = crear_menu(db, nombre, descripcion, ingredientes_info, precio)
                if nuevo_menu:
                    self.cargar_menus()
                    self.actualizar_combo_clientes_y_menus()
                    ventana.destroy()
                    messagebox.showinfo("Éxito", f"Menú '{nombre}' creado")
                else:
                    messagebox.showerror("Error", "No se pudo crear el menú")

        ctk.CTkButton(ventana, text="Guardar Menú", command=guardar_menu).pack(pady=10)

    def abrir_ventana_actualizar_menu(self):
        selected = self.tree_menus.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Selecciona un menú para actualizar")
            return

        menu_id = int(self.tree_menus.item(selected[0], "values")[0])
        with SessionLocal() as db:
            menu = db.query(Menu).filter_by(id=menu_id).first()
            if not menu:
                messagebox.showerror("Error", "Menú no encontrado")
                return

            ventana = ctk.CTkToplevel(self)
            ventana.title("Actualizar Menú")
            ventana.geometry("500x600")
            ventana.transient(self)
            ventana.grab_set()

            ctk.CTkLabel(ventana, text="Nombre del Menú:").pack(pady=5)
            entry_nombre = ctk.CTkEntry(ventana)
            entry_nombre.insert(0, menu.nombre)
            entry_nombre.pack(pady=5)

            ctk.CTkLabel(ventana, text="Descripción:").pack(pady=5)
            entry_descripcion = ctk.CTkTextbox(ventana, height=100, width=300)
            entry_descripcion.insert("1.0", menu.descripcion)
            entry_descripcion.pack(pady=5)

            ctk.CTkLabel(ventana, text="Precio:").pack(pady=5)
            entry_precio = ctk.CTkEntry(ventana)
            entry_precio.insert(0, str(menu.precio))
            entry_precio.pack(pady=5)

            ctk.CTkLabel(ventana, text="Selecciona Ingredientes:").pack(pady=5)
            listbox_ingredientes = tk.Listbox(ventana, selectmode=tk.MULTIPLE, height=8, width=40)
            listbox_ingredientes.pack(pady=5)

            cantidades_frame = ctk.CTkFrame(ventana)
            cantidades_frame.pack(pady=5, fill="x")
            cantidades_vars = {}

            ingredientes = obtener_ingredientes(db)
            print("Ingredientes cargados:", [(i.id, i.nombre) for i in ingredientes])
            if not ingredientes:
                messagebox.showwarning("Advertencia", "No hay ingredientes disponibles")
                ventana.destroy()
                return
            for ing in ingredientes:
                listbox_ingredientes.insert(tk.END, f"{ing.id}: {ing.nombre} ({ing.tipo})")

            for ing in menu.ingredientes:
                cantidad = db.query(ingrediente_menu.c.cantidad).filter_by(menu_id=menu_id, ingrediente_id=ing.id).scalar()
                idx = next((i for i in range(listbox_ingredientes.size()) if f"{ing.id}:" in listbox_ingredientes.get(i)), None)
                if idx is not None:
                    listbox_ingredientes.selection_set(idx)

            def actualizar_cantidades(event):
                for widget in cantidades_frame.winfo_children():
                    widget.destroy()
                cantidades_vars.clear()
                selected_indices = listbox_ingredientes.curselection()
                for idx, index in enumerate(selected_indices):
                    ing_id = int(listbox_ingredientes.get(index).split(":")[0])
                    ing_nombre = listbox_ingredientes.get(index).split(": ")[1].split(" (")[0]
                    cantidad = db.query(ingrediente_menu.c.cantidad).filter_by(menu_id=menu_id, ingrediente_id=ing_id).scalar() or 0
                    cantidades_vars[ing_id] = ctk.StringVar(value=str(cantidad))
                    ctk.CTkLabel(cantidades_frame, text=f"Cant. {ing_nombre}:").grid(row=idx, column=0, padx=5, pady=2, sticky="w")
                    ctk.CTkEntry(cantidades_frame, textvariable=cantidades_vars[ing_id], width=100).grid(row=idx, column=1, padx=5, pady=2)

            listbox_ingredientes.bind("<<ListboxSelect>>", actualizar_cantidades)
            actualizar_cantidades(None)

            def guardar_actualizacion():
                nombre = entry_nombre.get().strip()
                descripcion = entry_descripcion.get("1.0", "end").strip()
                precio_str = entry_precio.get().strip()
                ingredientes_info = []

                if not nombre or not descripcion or not precio_str:
                    messagebox.showerror("Error", "Complete todos los campos")
                    return
                try:
                    precio = float(precio_str)
                    if precio <= 0:
                        messagebox.showerror("Error", "El precio debe ser mayor que cero")
                        return
                except ValueError:
                    messagebox.showerror("Error", "Ingrese un precio numérico válido")
                    return

                for ing_id in cantidades_vars:
                    cantidad = cantidades_vars[ing_id].get().strip()
                    try:
                        cantidad_float = float(cantidad)
                        if cantidad_float > 0:
                            ingredientes_info.append({"ingrediente_id": ing_id, "cantidad": cantidad_float})
                    except ValueError:
                        continue

                print("Ingredientes seleccionados para actualizar:", ingredientes_info)
                if not ingredientes_info:
                    messagebox.showerror("Error", "Seleccione al menos un ingrediente con cantidad mayor que cero")
                    return

                with SessionLocal() as db:
                    if db.query(Menu).filter(Menu.nombre == nombre, Menu.id != menu_id).first():
                        messagebox.showerror("Error", "El nombre del menú ya existe")
                        return
                    nuevo_menu = actualizar_menu(db, menu_id, nombre, descripcion, ingredientes_info, precio)
                    if nuevo_menu:
                        self.cargar_menus()
                        self.actualizar_combo_clientes_y_menus()
                        self.texto_descripcion.configure(state="normal")
                        self.texto_descripcion.delete("1.0", "end")
                        self.texto_descripcion.configure(state="disabled")
                        ventana.destroy()
                        messagebox.showinfo("Éxito", f"Menú '{nombre}' actualizado")
                    else:
                        messagebox.showerror("Error", "No se pudo actualizar el menú")

            ctk.CTkButton(ventana, text="Guardar Menú", command=guardar_actualizacion).pack(pady=10)

    def eliminar_menu(self):
        selected = self.tree_menus.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Selecciona un menú para eliminar")
            return

        menu_id = int(self.tree_menus.item(selected[0], "values")[0])
        if messagebox.askyesno("Confirmación", "¿Estás seguro de eliminar este menú?"):
            with SessionLocal() as db:
                if eliminar_menu(db, menu_id):
                    self.cargar_menus()
                    self.actualizar_combo_clientes_y_menus()
                    self.texto_descripcion.configure(state="normal")
                    self.texto_descripcion.delete("1.0", "end")
                    self.texto_descripcion.configure(state="disabled")
                    messagebox.showinfo("Éxito", "Menú eliminado")
                else:
                    messagebox.showerror("Error", "No se pudo eliminar el menú")

    def crear_tab_pedidos(self):
        frame_filtros = ctk.CTkFrame(self.tab_pedidos)
        frame_filtros.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(frame_filtros, text="Filtrar por cliente:").pack(side="left", padx=10)

        self.tree_pedidos = ttk.Treeview(self.tab_pedidos, columns=("ID", "Cliente", "Fecha", "Total"), show="headings", height=10)
        self.tree_pedidos.heading("ID", text="ID")
        self.tree_pedidos.heading("Cliente", text="Cliente")
        self.tree_pedidos.heading("Fecha", text="Fecha")
        self.tree_pedidos.heading("Total", text="Total")
        self.tree_pedidos.pack(fill="both", expand=True, padx=10, pady=(5, 0))
        self.tree_pedidos.bind("<<TreeviewSelect>>", self.mostrar_detalles_pedido)

        frame_detalles = ctk.CTkFrame(self.tab_pedidos)
        frame_detalles.pack(fill="both", expand=False, padx=10, pady=10)

        self.label_fecha = ctk.CTkLabel(frame_detalles, text="Fecha: ")
        self.label_fecha.pack(anchor="w")

        self.label_total = ctk.CTkLabel(frame_detalles, text="Total: ")
        self.label_total.pack(anchor="w")

        self.label_menus = ctk.CTkLabel(frame_detalles, text="Menús:")
        self.label_menus.pack(anchor="w")

        self.listbox_menus = tk.Listbox(frame_detalles, height=5)
        self.listbox_menus.pack(fill="both", expand=True)

        def filtrar_por_cliente(event=None):
            seleccion = self.combo_clientes_pedidos.get()
            if not seleccion or seleccion == "Todos":
                cargar_pedidos()
                return
            cliente_id = int(seleccion.split(" - ")[0])
            self.tree_pedidos.delete(*self.tree_pedidos.get_children())
            with SessionLocal() as db:
                pedidos = db.query(Pedido).options(joinedload(Pedido.cliente)).filter(Pedido.cliente_id == cliente_id).all()
                for pedido in pedidos:
                    self.tree_pedidos.insert("", "end", values=(
                        pedido.id,
                        pedido.cliente.nombre,
                        str(pedido.fecha),
                        f"${pedido.total:.2f}"
                    ))

        def cargar_pedidos():
            self.tree_pedidos.delete(*self.tree_pedidos.get_children())
            self.listbox_menus.delete(0, tk.END)
            self.label_fecha.configure(text="Fecha: ")
            self.label_total.configure(text="Total: ")
            with SessionLocal() as db:
                pedidos = db.query(Pedido).options(joinedload(Pedido.cliente)).all()
                for pedido in pedidos:
                    self.tree_pedidos.insert("", "end", values=(
                        pedido.id,
                        pedido.cliente.nombre,
                        str(pedido.fecha),
                        f"${pedido.total:.2f}"
                    ))
                clientes = listar_clientes(db)
                self.combo_clientes_pedidos.configure(values=["Todos"] + [f"{c.id} - {c.nombre}" for c in clientes])
                if clientes:
                    self.combo_clientes_pedidos.set("Todos")

        self.combo_clientes_pedidos = ctk.CTkComboBox(frame_filtros, values=["Todos"], command=filtrar_por_cliente)
        self.combo_clientes_pedidos.pack(side="left", padx=10)

        btn_mostrar_todos = ctk.CTkButton(frame_filtros, text="Mostrar Todos", command=cargar_pedidos)
        btn_mostrar_todos.pack(side="left", padx=10)

        cargar_pedidos()

    def mostrar_detalles_pedido(self, event):
        selected = self.tree_pedidos.selection()
        if not selected:
            return
        pedido_id = int(self.tree_pedidos.item(selected[0], "values")[0])
        with SessionLocal() as db:
            pedido = db.query(Pedido).options(joinedload(Pedido.menus)).filter_by(id=pedido_id).first()
            if pedido:
                self.label_fecha.configure(text=f"Fecha: {pedido.fecha.strftime('%Y-%m-%d %H:%M:%S')}")
                self.label_total.configure(text=f"Total: ${pedido.total:.2f}")
                self.listbox_menus.delete(0, tk.END)
                with SessionLocal() as db:
                    cantidades = db.query(menu_pedido.c.cantidad, Menu.nombre).join(Menu, menu_pedido.c.menu_id == Menu.id).filter(menu_pedido.c.pedido_id == pedido_id).all()
                    for cantidad, nombre in cantidades:
                        self.listbox_menus.insert(tk.END, f"{cantidad}x {nombre}")

    def crear_tab_compra(self):
            frame = ctk.CTkFrame(self.tab_compra)
            frame.pack(fill="x", padx=10, pady=5)

            ctk.CTkLabel(frame, text="Seleccionar Cliente:").pack(pady=2)
            with SessionLocal() as db:
                clientes = listar_clientes(db)
                self.combo_clientes = ctk.CTkComboBox(frame, values=["Sin clientes"] if not clientes else [c.nombre for c in clientes], state="disabled" if not clientes else "normal")
                if clientes:
                    self.combo_clientes.set(clientes[0].nombre)
            self.combo_clientes.pack(pady=2)
            self.combo_clientes.bind("<<ComboboxSelected>>", self.on_cliente_cambio)

            ctk.CTkLabel(frame, text="Seleccionar Menú:").pack(pady=2)
            with SessionLocal() as db:
                menus = listar_menus(db)
                self.combo_menus = ctk.CTkComboBox(frame, values=["Sin menús"] if not menus else [m.nombre for m in menus], state="disabled" if not menus else "normal")
                if menus:
                    self.combo_menus.set(menus[0].nombre)
            self.combo_menus.pack(pady=2)

            # Botones para agregar y eliminar
            botones_frame = ctk.CTkFrame(frame)
            botones_frame.pack(pady=5)
            ctk.CTkButton(botones_frame, text="Agregar al Pedido", command=self.agregar_a_pedido).pack(side="left", padx=5)
            ctk.CTkButton(botones_frame, text="Eliminar Menú", command=self.eliminar_menu_pedido).pack(side="left", padx=5)

            self.tree_compra = ttk.Treeview(frame, columns=("Nombre", "Cantidad", "Precio"), show="headings")
            self.tree_compra.heading("Nombre", text="Nombre del Menú")
            self.tree_compra.heading("Cantidad", text="Cantidad")
            self.tree_compra.heading("Precio", text="Precio Unitario")
            self.tree_compra.column("Nombre", anchor="w", width=200)
            self.tree_compra.column("Cantidad", anchor="center", width=100)
            self.tree_compra.column("Precio", anchor="center", width=120)
            self.tree_compra.pack(fill="x", pady=5)

            self.total_label = ctk.CTkLabel(frame, text="Total: $0.00", font=("Arial", 16))
            self.total_label.pack(pady=5)

            ctk.CTkButton(frame, text="Confirmar Pedido", command=self.confirmar_pedido).pack(pady=5)

            self.actualizar_treeview_compra()

    def on_cliente_cambio(self, event):
        self.pedido_actual = {}
        self.actualizar_treeview_compra()
        print(f"Cliente cambiado a: {self.combo_clientes.get()}, Pedido reiniciado")

    def actualizar_combo_clientes_y_menus(self):
        with SessionLocal() as db:
            clientes = listar_clientes(db)
            if not clientes:
                self.combo_clientes.configure(values=["Sin clientes"], state="disabled")
            else:
                self.combo_clientes.configure(values=[c.nombre for c in clientes], state="normal")
                if not self.combo_clientes.get() or self.combo_clientes.get() == "Sin clientes":
                    self.combo_clientes.set(clientes[0].nombre)
            
            menus = listar_menus(db)
            if not menus:
                self.combo_menus.configure(values=["Sin menús"], state="disabled")
            else:
                self.combo_menus.configure(values=[m.nombre for m in menus], state="normal")
                if not self.combo_menus.get() or self.combo_menus.get() == "Sin menús":
                    self.combo_menus.set(menus[0].nombre)
        print("ComboBox actualizados: Clientes:", self.combo_clientes.cget("values"), "Menús:", self.combo_menus.cget("values"))

    def actualizar_treeview_compra(self):
        total = 0
        self.tree_compra.delete(*self.tree_compra.get_children())
        for nombre, item in self.pedido_actual.items():
            cantidad = item["cantidad"]
            precio = item["menu"].precio
            self.tree_compra.insert("", "end", values=(nombre, cantidad, f"${precio:.2f}"))
            total += cantidad * precio
        self.total_label.configure(text=f"Total: ${total:.2f}")

    def actualizar_treeview_pedidos(self):
        self.tree_pedidos.delete(*self.tree_pedidos.get_children())
        with SessionLocal() as db:
            pedidos = db.query(Pedido).options(joinedload(Pedido.cliente)).all()
            for pedido in pedidos:
                self.tree_pedidos.insert("", "end", values=(
                    pedido.id,
                    pedido.cliente.nombre,
                    str(pedido.fecha),
                    f"${pedido.total:.2f}"))
            
    def eliminar_menu_pedido(self):
        selected_item = self.tree_compra.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Seleccione un menú para eliminar")
            return
        if not self.pedido_actual:
            messagebox.showwarning("Advertencia", "No hay menús en el pedido")
            return

        # Obtener el nombre del menú seleccionado
        menu_nombre = self.tree_compra.item(selected_item, "values")[0]
        
        if menu_nombre in self.pedido_actual:
            # Reducir la cantidad o eliminar el menú
            self.pedido_actual[menu_nombre]["cantidad"] -= 1
            if self.pedido_actual[menu_nombre]["cantidad"] == 0:
                del self.pedido_actual[menu_nombre]
            print(f"Menú {menu_nombre} eliminado/reducido del pedido. Pedido actual: {self.pedido_actual}")
            self.actualizar_treeview_compra()
            messagebox.showinfo("Éxito", f"Menú '{menu_nombre}' eliminado/reducido del pedido")
        else:
            messagebox.showerror("Error", f"El menú '{menu_nombre}' no está en el pedido")

    def agregar_menu_pedido(self, menu):
            with SessionLocal() as db:
                ingredientes = db.query(ingrediente_menu).filter_by(menu_id=menu.id).all()
                for ing in ingredientes:
                    ingrediente = db.query(Ingrediente).filter_by(id=ing.ingrediente_id).first()
                    if not ingrediente:
                        messagebox.showerror("Error", f"Ingrediente ID {ing.ingrediente_id} no encontrado para el menú {menu.nombre}")
                        return False
                    # Calcular la cantidad total requerida del ingrediente en el pedido actual
                    cantidad_actual = sum(
                        item["cantidad"] * db.query(ingrediente_menu.c.cantidad)
                        .filter_by(menu_id=item["menu"].id, ingrediente_id=ing.ingrediente_id)
                        .scalar() or 0
                        for item in self.pedido_actual.values()
                    )
                    cantidad_nueva = ing.cantidad  # Cantidad requerida por una unidad del menú
                    if ingrediente.cantidad < cantidad_actual + cantidad_nueva:
                        messagebox.showwarning(
                            "Sin stock",
                            f"No hay más stock de {ingrediente.nombre} para el menú {menu.nombre}. "
                            f"Stock disponible: {ingrediente.cantidad}, requerido: {cantidad_actual + cantidad_nueva}"
                        )
                        return False
            # Si el stock es suficiente, agregar el menú
            if menu.nombre in self.pedido_actual:
                self.pedido_actual[menu.nombre]["cantidad"] += 1
            else:
                self.pedido_actual[menu.nombre] = {"menu": menu, "cantidad": 1}
            print(f"Menú {menu.nombre} añadido al pedido, Cantidad: {self.pedido_actual[menu.nombre]['cantidad']}")
            return True

    def agregar_a_pedido(self):
        menu_nombre = self.combo_menus.get()
        cliente_nombre = self.combo_clientes.get()
        if not menu_nombre or menu_nombre == "Sin menús":
            messagebox.showerror("Error", "Seleccione un menú válido")
            return
        if not cliente_nombre or cliente_nombre == "Sin clientes":
            messagebox.showerror("Error", "Seleccione un cliente válido")
            return
        with SessionLocal() as db:
            menu = db.query(Menu).filter_by(nombre=menu_nombre).first()
            if not menu:
                messagebox.showerror("Error", "Menú no encontrado")
                return
            try:
                if self.agregar_menu_pedido(menu):
                    self.actualizar_treeview_compra()
                # No es necesario un else, ya que agregar_menu_pedido muestra la advertencia
            except Exception as e:
                print(f"Error inesperado al agregar menú: {e}")
                messagebox.showerror("Error", f"No se pudo agregar el menú: {str(e)}")

    def confirmar_pedido(self):
        cliente_nombre = self.combo_clientes.get()
        if not cliente_nombre or cliente_nombre == "Sin clientes":
            messagebox.showerror("Error", "Seleccione un cliente válido")
            return
        if not self.pedido_actual:
            messagebox.showerror("Error", "No hay menús en el pedido")
            return

        with SessionLocal() as db:
            cliente = db.query(Cliente).filter_by(nombre=cliente_nombre).first()
            if not cliente:
                messagebox.showerror("Error", "Cliente no encontrado")
                return
            try:
                total = sum(item["cantidad"] * item["menu"].precio for item in self.pedido_actual.values())
                menu_cantidades = {item["menu"].id: item["cantidad"] for item in self.pedido_actual.values()}
                descripcion = "Pedido desde Panel de Compra: " + ", ".join([f"{item['cantidad']}x {nombre}" for nombre, item in self.pedido_actual.items()])
                pedido = crear_pedido(db, descripcion=descripcion, total=total, cliente_id=cliente.id, menu_cantidades=menu_cantidades)
                if pedido:
                    print(f"Pedido confirmado: Cliente {cliente_nombre}, Total ${total:.2f}, Menús: {menu_cantidades}")
                    # Generar boleta
                    generar_boleta(pedido.id, cliente_nombre, pedido.fecha, self.pedido_actual)
                    self.pedido_actual = {}
                    self.actualizar_treeview_compra()
                    self.actualizar_treeview_pedidos()
                    self.actualizar_treeview_ingredientes()
                    messagebox.showinfo("Éxito", f"Pedido confirmado para {cliente_nombre} por ${total:.2f}")
                else:
                    print("Error: No se pudo crear el pedido en la base de datos")
                    messagebox.showerror("Error", "No se pudo confirmar el pedido: Error en la base de datos")
            except ValueError as e:
                print(f"Error al confirmar pedido: {e}")
                messagebox.showerror("Error", f"No se pudo confirmar el pedido: {str(e)}")
            except Exception as e:
                print(f"Error inesperado al confirmar pedido: {e}")
                messagebox.showerror("Error", f"No se pudo confirmar el pedido: {str(e)}")

    def crear_tab_graficos(self):
        frame = ctk.CTkFrame(self.tab_graficos)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Filtros
        filtros_frame = ctk.CTkFrame(frame)
        filtros_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(filtros_frame, text="Seleccionar Gráfico:").pack(side="left", padx=5)
        opciones_graficos = ["Ventas por Fecha", "Menús Más Vendidos", "Ingredientes Más Utilizados"]
        self.combo_graficos = ctk.CTkComboBox(filtros_frame, values=opciones_graficos)
        self.combo_graficos.pack(side="left", padx=5)

        ctk.CTkLabel(filtros_frame, text="Fecha Inicio (YYYY-MM-DD):").pack(side="left", padx=5)
        self.entry_fecha_inicio = ctk.CTkEntry(filtros_frame, placeholder_text="Ej: 2023-01-01")
        self.entry_fecha_inicio.pack(side="left", padx=5)

        ctk.CTkLabel(filtros_frame, text="Fecha Fin (YYYY-MM-DD):").pack(side="left", padx=5)
        self.entry_fecha_fin = ctk.CTkEntry(filtros_frame, placeholder_text="Ej: 2023-12-31")
        self.entry_fecha_fin.pack(side="left", padx=5)

        ctk.CTkButton(filtros_frame, text="Generar Gráfico", command=self.generar_grafico).pack(side="left", padx=5)

        # Área para el gráfico
        self.grafico_frame = ctk.CTkFrame(frame)
        self.grafico_frame.pack(fill="both", expand=True, pady=10)

    def generar_grafico(self):
        # Limpiar gráfico anterior
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            plt.close(self.canvas.figure)

        tipo_grafico = self.combo_graficos.get()
        if not tipo_grafico:
            messagebox.showerror("Error", "Seleccione un tipo de gráfico")
            return

        fecha_inicio = None
        fecha_fin = None
        if tipo_grafico == "Ventas por Fecha":
            try:
                fecha_inicio_str = self.entry_fecha_inicio.get().strip()
                fecha_fin_str = self.entry_fecha_fin.get().strip()
                if fecha_inicio_str:
                    fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
                if fecha_fin_str:
                    fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d")
                if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
                    messagebox.showerror("Error", "La fecha de inicio debe ser menor o igual a la fecha de fin")
                    return
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD")
                return

        with SessionLocal() as db:
            fig = None
            if tipo_grafico == "Ventas por Fecha":
                fig = grafico_ventas_por_fecha(db, fecha_inicio, fecha_fin)
            elif tipo_grafico == "Menús Más Vendidos":
                fig = grafico_menus_mas_vendidos(db)
            elif tipo_grafico == "Ingredientes Más Utilizados":
                fig = grafico_ingredientes_mas_utilizados(db)
            else:
                messagebox.showerror("Error", "Seleccione un tipo de gráfico válido")
                return

            # Mostrar el gráfico en la interfaz
            self.canvas = FigureCanvasTkAgg(fig, master=self.grafico_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill="both", expand=True)


app = App()
app.mainloop()