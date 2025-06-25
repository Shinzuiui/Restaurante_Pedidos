from sqlalchemy.orm import Session
from models import Menu, Ingrediente, ingrediente_menu

def crear_menu(db: Session, nombre: str, descripcion: str, ingredientes_info: list, precio: float):
    """
    ingredientes_info: lista de dicts con 'ingrediente_id' y 'cantidad'
    """
    nuevo_menu = Menu(nombre=nombre, descripcion=descripcion, precio=precio)
    db.add(nuevo_menu)
    db.commit()
    db.refresh(nuevo_menu)

    for item in ingredientes_info:
        ingrediente = db.query(Ingrediente).filter_by(id=item['ingrediente_id']).first()
        if ingrediente:
            db.execute(
                ingrediente_menu.insert().values(
                    ingrediente_id=ingrediente.id,
                    menu_id=nuevo_menu.id,
                    cantidad=item['cantidad']
                )
            )
    db.commit()
    db.refresh(nuevo_menu)
    return nuevo_menu

def obtener_menu(db: Session, menu_id: int):
    return db.query(Menu).filter(Menu.id == menu_id).first()

def listar_menus(db: Session):
    return db.query(Menu).all()

def actualizar_menu(db: Session, menu_id: int, nombre: str = None, descripcion: str = None, ingredientes_info: list = None, precio: float = None):
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        return None
    if nombre:
        menu.nombre = nombre
    if descripcion:
        menu.descripcion = descripcion
    if precio is not None:
        menu.precio = precio
    db.commit()

    if ingredientes_info is not None:
        # Primero eliminar relaciones actuales
        db.execute(
            ingrediente_menu.delete().where(ingrediente_menu.c.menu_id == menu_id)
        )
        db.commit()
        # Agregar las nuevas relaciones
        for item in ingredientes_info:
            ingrediente = db.query(Ingrediente).filter_by(id=item['ingrediente_id']).first()
            if ingrediente:
                db.execute(
                    ingrediente_menu.insert().values(
                        ingrediente_id=ingrediente.id,
                        menu_id=menu.id,
                        cantidad=item['cantidad']
                    )
                )
        db.commit()
    db.refresh(menu)
    return menu

def eliminar_menu(db: Session, menu_id: int):
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        return False
    db.delete(menu)
    db.commit()
    return True
