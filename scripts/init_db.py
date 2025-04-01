from src.db.database import engine, Base
from src.db.models import Novel, Episode, Evaluation

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database tables created successfully")
