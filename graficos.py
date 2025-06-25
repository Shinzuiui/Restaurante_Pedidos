from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Pedido, Menu, Ingrediente, ingrediente_menu, menu_pedido
import matplotlib.pyplot as plt

def grafico_ventas_por_fecha(db: Session, fecha_inicio=None, fecha_fin=None):
    fig, ax = plt.subplots(figsize=(8, 5))
    query = db.query(func.date(Pedido.fecha).label("fecha"), func.sum(Pedido.total).label("total"))
    if fecha_inicio and fecha_fin:
        query = query.filter(Pedido.fecha.between(fecha_inicio, fecha_fin))
    query = query.group_by(func.date(Pedido.fecha)).order_by(func.date(Pedido.fecha))
    resultados = query.all()

    if not resultados:
        ax.text(0.5, 0.5, "No hay datos para el rango seleccionado", ha="center", va="center")
        return fig

    fechas = [r.fecha for r in resultados]
    totales = [r.total for r in resultados]
    ax.bar(fechas, totales, color="skyblue")
    ax.set_title("Ventas por Fecha")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Total ($)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig

def grafico_menus_mas_vendidos(db: Session):
    fig, ax = plt.subplots(figsize=(8, 5))
    resultados = (
        db.query(Menu.nombre, func.sum(menu_pedido.c.cantidad).label("total_vendido"))
        .join(menu_pedido, Menu.id == menu_pedido.c.menu_id)
        .group_by(Menu.nombre)
        .order_by(func.sum(menu_pedido.c.cantidad).desc())
        .all()
    )

    if not resultados:
        ax.text(0.5, 0.5, "No hay datos de menús vendidos", ha="center", va="center")
        return fig

    menus = [r.nombre for r in resultados]
    cantidades = [r.total_vendido for r in resultados]
    ax.bar(menus, cantidades, color="lightgreen")
    ax.set_title("Menús Más Vendidos")
    ax.set_xlabel("Menú")
    ax.set_ylabel("Cantidad Vendida")
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig

def grafico_ingredientes_mas_utilizados(db: Session):
    fig, ax = plt.subplots(figsize=(8, 5))
    resultados = (
        db.query(Ingrediente.nombre, func.sum(ingrediente_menu.c.cantidad * menu_pedido.c.cantidad).label("total_usado"))
        .join(ingrediente_menu, Ingrediente.id == ingrediente_menu.c.ingrediente_id)
        .join(menu_pedido, ingrediente_menu.c.menu_id == menu_pedido.c.menu_id)
        .group_by(Ingrediente.nombre)
        .order_by(func.sum(ingrediente_menu.c.cantidad * menu_pedido.c.cantidad).desc())
        .all()
    )

    if not resultados:
        ax.text(0.5, 0.5, "No hay datos de ingredientes utilizados", ha="center", va="center")
        return fig

    ingredientes = [r.nombre for r in resultados]
    cantidades = [r.total_usado for r in resultados]
    ax.bar(ingredientes, cantidades, color="salmon")
    ax.set_title("Ingredientes Más Utilizados")
    ax.set_xlabel("Ingrediente")
    ax.set_ylabel("Cantidad Utilizada")
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig