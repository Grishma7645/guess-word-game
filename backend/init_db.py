from backend.database import Base, engine
from backend import models

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully.")
