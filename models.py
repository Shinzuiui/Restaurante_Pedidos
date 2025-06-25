from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Table, PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# Tabla intermedia para Menús y Pedidos
menu_pedido = Table(
    "menu_pedido",
    Base.metadata,
    Column("menu_id", Integer, ForeignKey("menus.id")),
    Column("pedido_id", Integer, ForeignKey("pedidos.id")),
    Column("cantidad", Integer, nullable=False, default=1),
    PrimaryKeyConstraint("menu_id", "pedido_id")
)

# Tabla intermedia para Ingredientes y Menús
ingrediente_menu = Table(
    "ingrediente_menu",
    Base.metadata,
    Column("ingrediente_id", Integer, ForeignKey("ingredientes.id")),
    Column("menu_id", Integer, ForeignKey("menus.id")),
    Column("cantidad", Float, nullable=False),
    PrimaryKeyConstraint("ingrediente_id", "menu_id")
)

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    correo = Column(String, unique=True, nullable=False)

    pedidos = relationship("Pedido", back_populates="cliente")

class Ingrediente(Base):
    __tablename__ = "ingredientes"
    __table_args__ = (UniqueConstraint('nombre', 'tipo', name='unique_nombre_tipo'),)

    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    tipo = Column(String, nullable=False)
    cantidad = Column(Float, nullable=False)
    unidad = Column(String, nullable=False)

    menus = relationship("Menu", secondary=ingrediente_menu, back_populates="ingredientes")

class Menu(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(80), nullable=False, unique=True)
    descripcion = Column(String, nullable=False)
    precio = Column(Float, nullable=False)  # Nuevo campo

    ingredientes = relationship("Ingrediente", secondary=ingrediente_menu, back_populates="menus")
    pedidos = relationship("Pedido", secondary=menu_pedido, back_populates="menus")

class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True)
    descripcion = Column(String)
    total = Column(Float)
    fecha = Column(DateTime, default=datetime.utcnow)

    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    cliente = relationship("Cliente", back_populates="pedidos")
    
    menus = relationship("Menu", secondary=menu_pedido, back_populates="pedidos")