
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import random
from datetime import datetime, timedelta

from db import SessionLocal, init_db
from models import Product, Transaction, TransactionItem

from pydantic import BaseModel

# simple utility and config
ALLOW_DESTRUCTIVE = str(os.environ.get('ALLOW_DESTRUCTIVE', 'false')).lower() in ('1', 'true', 'yes')
ADMIN_KEY = os.environ.get('ADMIN_KEY')

app = FastAPI()

# Allow CORS from anywhere (match previous behavior)
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


class ProductCreate(BaseModel):
	name: str
	price: float
	cost: float
	stock: int = 0


class ProductUpdate(BaseModel):
	name: str | None = None
	price: float | None = None
	cost: float | None = None
	stock: int | None = None


class CartItem(BaseModel):
	product_id: int
	quantity: int


def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


@app.on_event('startup')
def on_startup():
	# ensure tables exist
	init_db()


@app.get('/')
def root():
	return {'message': 'POS API Server', 'status': 'running', 'docs': '/docs'}


@app.get('/health')
def health():
	return {'status': 'ok'}


@app.get('/api/products')
def get_products(db: Session = Depends(get_db)):
	products = db.query(Product).all()
	return [
		{'id': p.id, 'name': p.name, 'price': p.price, 'cost': p.cost, 'stock': p.stock}
		for p in products
	]


@app.post('/api/products', status_code=201)
def add_product(payload: ProductCreate, db: Session = Depends(get_db)):
	p = Product(name=payload.name, price=payload.price, cost=payload.cost, stock=payload.stock)
	db.add(p)
	db.commit()
	db.refresh(p)
	return {'message': 'Product added', 'id': p.id}


@app.get('/api/products/{product_id}')
def get_product(product_id: int, db: Session = Depends(get_db)):
	p = db.get(Product, product_id)
	if not p:
		raise HTTPException(status_code=404, detail='Product not found')
	return {'id': p.id, 'name': p.name, 'price': p.price, 'cost': p.cost, 'stock': p.stock}


@app.put('/api/products/{product_id}')
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
	p = db.get(Product, product_id)
	if not p:
		raise HTTPException(status_code=404, detail='Product not found')
	if payload.name is not None:
		p.name = payload.name
	if payload.price is not None:
		p.price = payload.price
	if payload.cost is not None:
		p.cost = payload.cost
	if payload.stock is not None:
		p.stock = payload.stock
	db.commit()
	return {'message': 'Product updated'}


@app.delete('/api/products/{product_id}')
def delete_product(product_id: int, db: Session = Depends(get_db)):
	p = db.get(Product, product_id)
	if not p:
		raise HTTPException(status_code=404, detail='Product not found')
	db.delete(p)
	db.commit()
	return {'message': 'Product deleted'}


@app.post('/api/checkout', status_code=201)
def checkout(cart: list[CartItem], db: Session = Depends(get_db)):
	if not isinstance(cart, list):
		raise HTTPException(status_code=400, detail='Invalid cart format')
	try:
		with db.begin():
			total = 0
			items = []
			for entry in cart:
				product = db.get(Product, entry.product_id)
				if not product or product.stock < entry.quantity:
					raise HTTPException(status_code=400, detail=f"Product {entry.product_id} 庫存不足或不存在")
				total += product.price * entry.quantity
				items.append((product, entry.quantity, product.price))
			tx = Transaction(total_amount=total, timestamp=datetime.utcnow())
			db.add(tx)
			db.flush()
			for product, qty, price in items:
				ti = TransactionItem(transaction_id=tx.id, product_id=product.id, quantity=qty, price_at_sale=price)
				db.add(ti)
				product.stock -= qty
		return {'message': 'Checkout success', 'transaction_id': tx.id}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/transactions')
def get_transactions(db: Session = Depends(get_db)):
	txs = db.query(Transaction).order_by(Transaction.timestamp.desc()).all()
	return [
		{'id': t.id, 'timestamp': t.timestamp.strftime('%Y-%m-%d %H:%M:%S'), 'total_amount': t.total_amount}
		for t in txs
	]


@app.get('/api/transactions/{transaction_id}')
def get_transaction_detail(transaction_id: int, db: Session = Depends(get_db)):
	t = db.get(Transaction, transaction_id)
	if not t:
		raise HTTPException(status_code=404, detail='Transaction not found')
	items = [
		{'id': i.id, 'product_id': i.product_id, 'quantity': i.quantity, 'price_at_sale': i.price_at_sale}
		for i in t.items
	]
	return {'id': t.id, 'timestamp': t.timestamp.strftime('%Y-%m-%d %H:%M:%S'), 'total_amount': t.total_amount, 'items': items}


def _check_destructive(request: Request):
	# allow if ALLOW_DESTRUCTIVE or correct ADMIN_KEY header
	if ALLOW_DESTRUCTIVE:
		return True
	if ADMIN_KEY:
		header = request.headers.get('X-ADMIN-KEY')
		return header == ADMIN_KEY
	return False


@app.post('/api/reset_seed')
def reset_seed(request: Request, db: Session = Depends(get_db)):
	# Public: allow frontend (or any caller) to recreate sample data
	try:
		with db.begin():
			db.query(TransactionItem).delete()
			db.query(Transaction).delete()
			db.query(Product).delete()

		PRODUCT_NAMES = [
			'Espresso', 'Latte', 'Cappuccino', 'Tea', 'Orange Juice', 'Muffin', 'Bagel', 'Sandwich',
			'Chocolate', 'Soda', 'Water', 'Cookie', 'Salad', 'Burger', 'Fries', 'Milk', 'Yogurt', 'Granola', 'Apple', 'Banana'
		]
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

		return {'message': 'reset complete', 'products_created': created, 'transactions_created': created_tx}
	except Exception as e:
		db.rollback()
		raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/init_db', status_code=201)
def init_db_endpoint(request: Request, db: Session = Depends(get_db)):
	# Public: allow frontend (or any caller) to initialize & seed the DB
	try:
		# ensure tables
		init_db()
		# clear & seed
		with db.begin():
			db.query(TransactionItem).delete()
			db.query(Transaction).delete()
			db.query(Product).delete()

		PRODUCT_NAMES = [
			'Espresso', 'Latte', 'Cappuccino', 'Tea', 'Orange Juice', 'Muffin', 'Bagel', 'Sandwich',
			'Chocolate', 'Soda', 'Water', 'Cookie', 'Salad', 'Burger', 'Fries', 'Milk', 'Yogurt', 'Granola', 'Apple', 'Banana'
		]
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

		return {'message': 'setup complete', 'products_created': created, 'transactions_created': created_tx}
	except Exception as e:
		db.rollback()
		raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
	import uvicorn
	port = int(os.environ.get('PORT', '5001'))
	uvicorn.run('app:app', host='127.0.0.1', port=port, reload=True)

