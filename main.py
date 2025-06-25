from database import Base, engine
import models

# Crea todas las tablas en la base de datos
print("Creando tablas...")
Base.metadata.create_all(bind=engine)
print("¡Listo! Tablas creadas.")
