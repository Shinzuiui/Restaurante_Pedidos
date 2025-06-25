from fpdf import FPDF
from datetime import datetime
from tkinter import messagebox

def generar_boleta(pedido_id, cliente_nombre, fecha_pedido, pedido_items):
    if not pedido_items:
        messagebox.showwarning("Boleta vacía", "No hay ítems en el pedido para generar la boleta.")
        return False

    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_margins(left=15, top=15, right=15)
        pdf.set_auto_page_break(auto=True, margin=15)

        # Encabezado
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Restaurante Sabor", ln=True, align="C")
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 8, "RUT: 12.345.678-9", ln=True, align="C")
        pdf.cell(0, 8, "Dirección: Calle Falsa 123, Santiago, Chile", ln=True, align="C")
        pdf.cell(0, 8, "Teléfono: +56 9 1234 5678", ln=True, align="C")
        pdf.ln(10)

        # Información del pedido
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 8, f"Boleta N°: {pedido_id}", ln=True, align="L")
        pdf.cell(0, 8, f"Cliente: {cliente_nombre}", ln=True, align="L")
        pdf.cell(0, 8, f"Fecha: {fecha_pedido.strftime('%d/%m/%Y %H:%M:%S')}", ln=True, align="L")
        pdf.ln(10)

        # Tabla de ítems
        pdf.set_font("Arial", "B", 12)
        pdf.cell(80, 10, "Nombre", border=1, align="C")
        pdf.cell(30, 10, "Cantidad", border=1, align="C")
        pdf.cell(40, 10, "Precio Unit.", border=1, align="C")
        pdf.cell(40, 10, "Subtotal", border=1, align="C")
        pdf.ln()

        pdf.set_font("Arial", size=11)
        subtotal = 0
        for item in pedido_items.values():
            menu = item["menu"]  # Cambiado de "producto" a "menu"
            cantidad = item["cantidad"]
            precio_unitario = menu.precio
            nombre = menu.nombre
            sub = cantidad * precio_unitario
            subtotal += sub
            pdf.cell(80, 10, nombre, border=1)
            pdf.cell(30, 10, str(cantidad), border=1, align="C")
            pdf.cell(40, 10, f"${precio_unitario:.2f}", border=1, align="C")
            pdf.cell(40, 10, f"${sub:.2f}", border=1, align="C")
            pdf.ln()

        # Totales
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        iva = subtotal * 0.19
        total = subtotal + iva
        pdf.cell(0, 8, f"Subtotal: ${subtotal:.2f}", ln=True, align="R")
        pdf.cell(0, 8, f"IVA (19%): ${iva:.2f}", ln=True, align="R")
        pdf.cell(0, 8, f"Total: ${total:.2f}", ln=True, align="R")

        # Pie de página
        pdf.ln(10)
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 8, "Gracias por su compra. Para consultas, contáctenos al +56 9 1234 5678.", ln=True, align="C")
        pdf.cell(0, 8, "Los productos adquiridos no tienen garantía.", ln=True, align="C")

        # Guardar el PDF
        nombre_archivo = f"boleta_{pedido_id}.pdf"
        pdf.output(f"boletas/{nombre_archivo}", "F")
        messagebox.showinfo("Boleta generada", f"La boleta fue guardada como '{nombre_archivo}'")

        return True
    except Exception as e:
        print(f"Error al generar la boleta: {e}")
        messagebox.showerror("Error", f"No se pudo generar la boleta: {str(e)}")
        return False