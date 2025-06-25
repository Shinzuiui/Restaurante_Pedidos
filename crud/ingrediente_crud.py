from sqlalchemy.orm import Session
from models import Ingrediente

# Crear ingrediente (solo si no existe con el mismo nombre y tipo)
def crear_ingrediente(db: Session, nombre: str, tipo: str, cantidad: float, unidad: str):
    existe = db.query(Ingrediente).filter_by(nombre=nombre, tipo=tipo).first()
    if existe:
        return None  # Ya existe
    nuevo = Ingrediente(nombre=nombre, tipo=tipo, cantidad=cantidad, unidad=unidad)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

# Leer todos los ingredientes
def obtener_ingredientes(db: Session):
    return db.query(Ingrediente).all()

# Leer uno por ID
def obtener_ingrediente_por_id(db: Session, ingrediente_id: int):
    return db.query(Ingrediente).filter(Ingrediente.id == ingrediente_id).first()

# Actualizar ingrediente
def actualizar_ingrediente(db: Session, ingrediente_id: int, **kwargs):
    ingrediente = obtener_ingrediente_por_id(db, ingrediente_id)
    if ingrediente:
        for key, value in kwargs.items():
            setattr(ingrediente, key, value)
        db.commit()
        db.refresh(ingrediente)
    return ingrediente

# Eliminar ingrediente
def eliminar_ingrediente(db: Session, ingrediente_id: int):
    ingrediente = obtener_ingrediente_por_id(db, ingrediente_id)
    if ingrediente:
        db.delete(ingrediente)
        db.commit()
        return True
    return False
