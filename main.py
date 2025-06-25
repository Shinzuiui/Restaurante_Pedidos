from database import Base, engine

# Crea todas las tablas en la base de datos
print("Creando tablas...")
Base.metadata.create_all(bind=engine)
print("¡Listo! Tablas creadas.")
