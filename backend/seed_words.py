from .database import SessionLocal
from .models import Word

words = ["AUDIO","HOMER","JOKER","TONER","TOWER",
         "CRANE","PLANT","BRICK","SHINE","FLAME",
         "TRACE","BRAVE","CLAMP","SHORE","LIGHT",
         "SWEET","GHOST","PRIDE","CYCLE","BLAZE"]

db = SessionLocal()
for w in words:
    if not db.query(Word).filter(Word.text==w).first():
        db.add(Word(text=w))
db.commit()
db.close()
print("Seeded 20 words ✅")
