from app import create_app, db, Product

app = create_app()

with app.app_context():
    db.create_all()
    count = Product.query.count()
    if count == 0:
        p1 = Product(name='Apple', price=0.5, cost=0.3, stock=100)
        p2 = Product(name='Banana', price=0.3, cost=0.1, stock=150)
        p3 = Product(name='Coffee', price=2.5, cost=1.0, stock=50)
        db.session.add_all([p1, p2, p3])
        db.session.commit()
        print('Seeded 3 products')
    else:
        print(f'Products already exist: {count}')
