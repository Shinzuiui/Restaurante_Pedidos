from sqlalchemy.orm import Session
from sqlalchemy import Table, Column, Integer, Float, ForeignKey
from models import Pedido, Ingrediente, Menu, menu_pedido, ingrediente_menu
from datetime import datetime   
from database import Base


def crear_pedido(db: Session, descripcion: str, total: float, cliente_id: int, menu_cantidades: dict):
    try:
        # Verificar inventario para todos los menús
        for menu_id, cantidad in menu_cantidades.items():
            menu = db.query(Menu).filter_by(id=menu_id).first()
            if not menu:
                raise ValueError(f"Menú con ID {menu_id} no encontrado")
            ingredientes = db.query(ingrediente_menu).filter_by(menu_id=menu_id).all()
            for ing in ingredientes:
                ingrediente = db.query(Ingrediente).filter_by(id=ing.ingrediente_id).first()
                if not ingrediente or ingrediente.cantidad < ing.cantidad * cantidad:
                    raise ValueError(f"No hay suficiente stock de {ingrediente.nombre} para {cantidad}x {menu.nombre}")
        
        # Crear el pedido
        pedido = Pedido(
            descripcion=descripcion,
            total=total,
            cliente_id=cliente_id,
            fecha=datetime.now()
        )
        db.add(pedido)
        db.commit()
        db.refresh(pedido)
        
        # Asociar menús al pedido con cantidades
        for menu_id, cantidad in menu_cantidades.items():
            print(f"Insertando en pedido_menu: pedido_id={pedido.id}, menu_id={menu_id}, cantidad={cantidad}")  # Depuración
            db.execute(
                menu_pedido.insert().values(
                    pedido_id=pedido.id,
                    menu_id=menu_id,
                    cantidad=cantidad
                )
            )
        
        # Actualizar inventario
        for menu_id, cantidad in menu_cantidades.items():
            ingredientes = db.query(ingrediente_menu).filter_by(menu_id=menu_id).all()
            for ing in ingredientes:
                ingrediente = db.query(Ingrediente).filter_by(id=ing.ingrediente_id).first()
                ingrediente.cantidad -= ing.cantidad * cantidad
                db.add(ingrediente)
        
        db.commit()
        print(f"Pedido creado: ID {pedido.id}, Cliente ID {cliente_id}, Menús: {menu_cantidades}")  # Depuración
        return pedido
    except Exception as e:
        db.rollback()
        print(f"Error al crear pedido: {e}")  # Depuración
        raise

def obtener_pedido(db: Session, pedido_id: int):
    return db.query(Pedido).filter(Pedido.id == pedido_id).first()

def listar_pedidos(db: Session):
    return db.query(Pedido).all()

def actualizar_pedido(db: Session, pedido_id: int, descripcion: str = None, total: float = None, cliente_id: int = None, menu_ids: list = None):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        return None
    if descripcion:
        pedido.descripcion = descripcion
    if total is not None:
        pedido.total = total
    if cliente_id:
        pedido.cliente_id = cliente_id
    db.commit()

    if menu_ids is not None:
        # Eliminar las relaciones previas de menús
        db.execute(
            menu_pedido.delete().where(menu_pedido.c.pedido_id == pedido_id)
        )
        db.commit()
        # Insertar las nuevas relaciones
        for menu_id in menu_ids:
            menu = db.query(Menu).filter(Menu.id == menu_id).first()
            if menu:
                db.execute(
                    menu_pedido.insert().values(
                        menu_id=menu.id,
                        pedido_id=pedido.id
                    )
                )
        db.commit()
    db.refresh(pedido)
    return pedido

def eliminar_pedido(db: Session, pedido_id: int):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        return False
    db.delete(pedido)
    db.commit()
    return True
