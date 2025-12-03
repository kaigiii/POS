import random
from datetime import datetime, timedelta
from db import init_db, SessionLocal
from models import Product, Transaction, TransactionItem


PRODUCT_NAMES = [
    'Espresso', 'Latte', 'Cappuccino', 'Tea', 'Orange Juice', 'Muffin', 'Bagel', 'Sandwich',
    'Chocolate', 'Soda', 'Water', 'Cookie', 'Salad', 'Burger', 'Fries', 'Milk', 'Yogurt', 'Granola', 'Apple', 'Banana'
]


def reset_data():
    """Clear all tables and recreate sample products + random transactions."""
    init_db()
    db = SessionLocal()
    try:
        # delete existing data
        try:
            db.query(TransactionItem).delete()
            db.query(Transaction).delete()
            db.query(Product).delete()
            db.commit()
        except Exception:
            db.rollback()

        created = 0
        for name in PRODUCT_NAMES:
            p = Product(name=name, price=round(random.uniform(0.5, 10.0), 2), cost=round(random.uniform(0.2, 5.0), 2), stock=random.randint(10, 200))
            db.add(p)
            created += 1
        db.commit()

        tx_count = 50
        created_tx = 0
        products = db.query(Product).all()
        if products:
            for _ in range(tx_count):
                items = []
                for __ in range(random.randint(1, 4)):
                    p = random.choice(products)
                    qty = random.randint(1, 5)
                    items.append((p, qty))
                total = sum(p.price * q for p, q in items)
                t = Transaction(timestamp=datetime.utcnow() - timedelta(days=random.randint(0, 30)), total_amount=round(total, 2))
                db.add(t)
                db.flush()
                for p, q in items:
                    ti = TransactionItem(transaction_id=t.id, product_id=p.id, quantity=q, price_at_sale=p.price)
                    db.add(ti)
                    p.stock = max(0, p.stock - q)
                created_tx += 1
            db.commit()

        return {'products_created': created, 'transactions_created': created_tx}
    finally:
        db.close()


if __name__ == '__main__':
    res = reset_data()
    print(f"Products created: {res.get('products_created', 0)}, transactions: {res.get('transactions_created', 0)}")
