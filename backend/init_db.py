from db import init_db, SessionLocal
from models import Product

def seed_minimal():
    init_db()
    db = SessionLocal()
    try:
        count = db.query(Product).count()
        if count == 0:
            p1 = Product(name='Apple', price=0.5, cost=0.3, stock=100)
            p2 = Product(name='Banana', price=0.3, cost=0.1, stock=150)
            p3 = Product(name='Coffee', price=2.5, cost=1.0, stock=50)
            db.add_all([p1, p2, p3])
            db.commit()
            print('Seeded 3 products')
        else:
            print(f'Products already exist: {count}')
    finally:
        db.close()

if __name__ == '__main__':
    seed_minimal()
