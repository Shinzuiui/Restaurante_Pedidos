from sqlalchemy.orm import Session
from models import Cliente

def crear_cliente(db: Session, nombre: str, correo: str):
    # Verificar si el correo ya existe
    if db.query(Cliente).filter_by(correo=correo).first():
        return None
    try:
        cliente = Cliente(nombre=nombre, correo=correo)
        db.add(cliente)
        db.commit()
        db.refresh(cliente)
        return cliente
    except Exception as e:
        db.rollback()
        print(f"Error al crear cliente: {e}")  # Depuración
        return None

def obtener_cliente(db: Session, cliente_id: int):
    return db.query(Cliente).filter(Cliente.id == cliente_id).first()

def listar_clientes(db: Session):
    return db.query(Cliente).all()

def actualizar_cliente(db: Session, cliente_id: int, nombre: str, correo: str):
    # Verificar si el correo ya existe en otro cliente (excluyendo el cliente actual)
    existing_cliente = db.query(Cliente).filter(Cliente.correo == correo, Cliente.id != cliente_id).first()
    if existing_cliente:
        print(f"Error: Correo {correo} ya registrado por otro cliente (ID: {existing_cliente.id})")  # Depuración
        return None
    try:
        cliente = db.query(Cliente).filter_by(id=cliente_id).first()
        if not cliente:
            print(f"Error: Cliente con ID {cliente_id} no encontrado")  # Depuración
            return None
        cliente.nombre = nombre
        cliente.correo = correo
        db.commit()
        db.refresh(cliente)
        return cliente
    except Exception as e:
        db.rollback()
        print(f"Error al actualizar cliente: {e}")  # Depuración
        return None

def eliminar_cliente(db: Session, cliente_id: int):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        return False
    try:
        db.delete(cliente)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e
