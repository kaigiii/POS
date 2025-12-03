
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from config import Config
from datetime import datetime, timedelta
import random

db = SQLAlchemy()

class Product(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(128), unique=True, nullable=False)
	price = db.Column(db.Float, nullable=False)
	cost = db.Column(db.Float, nullable=False)
	stock = db.Column(db.Integer, default=0, nullable=False)

class Transaction(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	timestamp = db.Column(db.DateTime, default=datetime.utcnow)
	total_amount = db.Column(db.Float, nullable=False)
	items = db.relationship('TransactionItem', backref='transaction', lazy=True)

class TransactionItem(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)
	product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
	quantity = db.Column(db.Integer, nullable=False)
	price_at_sale = db.Column(db.Float, nullable=False)

def create_app():
	app = Flask(__name__)
	app.config.from_object(Config)
	db.init_app(app)
	# Configure CORS; by default allow all (adjust in production if needed)
	CORS(app)

	# destructive actions (reset/init) should be explicitly enabled in production
	# set ALLOW_DESTRUCTIVE=1 or 'true' in environment to allow these endpoints
	# For developer convenience: also allow when Flask is running in debug mode
	allow_destructive_env = str(os.environ.get('ALLOW_DESTRUCTIVE', 'false')).lower() in ('1', 'true', 'yes')
	allow_destructive = allow_destructive_env or app.debug
	# optional admin key: if set, endpoints require header X-ADMIN-KEY to match
	admin_key = os.environ.get('ADMIN_KEY')
	@app.route('/api/products', methods=['GET'])
	def get_products():
		products = Product.query.all()
		result = [
			{
				'id': p.id,
				'name': p.name,
				'price': p.price,
				'cost': p.cost,
				'stock': p.stock
			} for p in products
		]
		return jsonify(result)

	@app.route('/health', methods=['GET'])
	def health():
		return jsonify({'status': 'ok'}), 200

	@app.route('/api/products', methods=['POST'])
	def add_product():
		data = request.get_json()
		product = Product(
			name=data['name'],
			price=data['price'],
			cost=data['cost'],
			stock=data.get('stock', 0)
		)
		db.session.add(product)
		db.session.commit()
		return jsonify({'message': 'Product added', 'id': product.id}), 201

	@app.route('/api/products/<int:product_id>', methods=['GET'])
	def get_product(product_id):
		product = Product.query.get(product_id)
		if not product:
			return jsonify({'error': 'Product not found'}), 404
		return jsonify({
			'id': product.id,
			'name': product.name,
			'price': product.price,
			'cost': product.cost,
			'stock': product.stock
		})

	@app.route('/api/products/<int:product_id>', methods=['PUT'])
	def update_product(product_id):
		product = Product.query.get(product_id)
		if not product:
			return jsonify({'error': 'Product not found'}), 404
		data = request.get_json()
		product.name = data.get('name', product.name)
		product.price = data.get('price', product.price)
		product.cost = data.get('cost', product.cost)
		product.stock = data.get('stock', product.stock)
		db.session.commit()
		return jsonify({'message': 'Product updated'})

	@app.route('/api/products/<int:product_id>', methods=['DELETE'])
	def delete_product(product_id):
		product = Product.query.get(product_id)
		if not product:
			return jsonify({'error': 'Product not found'}), 404
		db.session.delete(product)
		db.session.commit()
		return jsonify({'message': 'Product deleted'})
	@app.route('/api/checkout', methods=['POST'])
	def checkout():
		cart = request.get_json()
		if not isinstance(cart, list):
			return jsonify({'error': 'Invalid cart format'}), 400
		try:
			with db.session.begin():
				total = 0
				items = []
				for entry in cart:
					product = Product.query.get(entry['product_id'])
					if not product or product.stock < entry['quantity']:
						db.session.rollback()
						return jsonify({'error': f"Product {entry['product_id']} 庫存不足或不存在"}), 400
					total += product.price * entry['quantity']
					items.append((product, entry['quantity'], product.price))
				transaction = Transaction(total_amount=total)
				db.session.add(transaction)
				db.session.flush()  # 取得 transaction.id
				for product, qty, price in items:
					ti = TransactionItem(
						transaction_id=transaction.id,
						product_id=product.id,
						quantity=qty,
						price_at_sale=price
					)
					db.session.add(ti)
					product.stock -= qty
				db.session.commit()
			return jsonify({'message': 'Checkout success', 'transaction_id': transaction.id}), 201
		except Exception as e:
			db.session.rollback()
			return jsonify({'error': str(e)}), 500
	@app.route('/api/transactions', methods=['GET'])
	def get_transactions():
		transactions = Transaction.query.order_by(Transaction.timestamp.desc()).all()
		result = [
			{
				'id': t.id,
				'timestamp': t.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
				'total_amount': t.total_amount
			} for t in transactions
		]
		return jsonify(result)

	@app.route('/api/transactions/<int:transaction_id>', methods=['GET'])
	def get_transaction_detail(transaction_id):
		t = Transaction.query.get(transaction_id)
		if not t:
			return jsonify({'error': 'Transaction not found'}), 404
		items = [
			{
				'id': i.id,
				'product_id': i.product_id,
				'quantity': i.quantity,
				'price_at_sale': i.price_at_sale
			} for i in t.items
		]
		return jsonify({
			'id': t.id,
			'timestamp': t.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
			'total_amount': t.total_amount,
			'items': items
		})

	# 管理: 重設範例資料（清除並重新建立 products + transactions）
	@app.route('/api/reset_seed', methods=['POST'])
	def reset_seed():
		# NOTE: this endpoint is destructive; protected by ADMIN_KEY if present, otherwise by ALLOW_DESTRUCTIVE
		if admin_key:
			provided = request.headers.get('X-ADMIN-KEY')
			if not provided or provided != admin_key:
				return jsonify({'error': 'forbidden (invalid admin key)'}), 403
		else:
			if not allow_destructive and os.environ.get('FLASK_ENV') != 'development':
				return jsonify({'error': 'destructive endpoints are disabled'}), 403
		try:
			# remove children first
			TransactionItem.query.delete()
			Transaction.query.delete()
			Product.query.delete()
			db.session.commit()
		except Exception:
			db.session.rollback()

		# sample product names
		PRODUCT_NAMES = [
			'Espresso', 'Latte', 'Cappuccino', 'Tea', 'Orange Juice', 'Muffin', 'Bagel', 'Sandwich',
			'Chocolate', 'Soda', 'Water', 'Cookie', 'Salad', 'Burger', 'Fries', 'Milk', 'Yogurt', 'Granola', 'Apple', 'Banana'
		]
		# create products
		created = 0
		for name in PRODUCT_NAMES:
			p = Product(name=name,
					price=round(random.uniform(0.5, 10.0), 2),
					cost=round(random.uniform(0.2, 5.0), 2),
					stock=random.randint(10, 200))
			db.session.add(p)
			created += 1
		db.session.commit()

		# create random transactions
		tx_count = 50
		created_tx = 0
		products = Product.query.all()
		if products:
			for i in range(tx_count):
				items = []
				for _ in range(random.randint(1, 4)):
					p = random.choice(products)
					qty = random.randint(1, 5)
					items.append((p, qty))
				total = sum(p.price * q for p, q in items)
				t = Transaction(timestamp=datetime.utcnow() - timedelta(days=random.randint(0, 30)), total_amount=round(total, 2))
				db.session.add(t)
				db.session.flush()
				for p, q in items:
					ti = TransactionItem(transaction_id=t.id, product_id=p.id, quantity=q, price_at_sale=p.price)
					db.session.add(ti)
					p.stock = max(0, p.stock - q)
				created_tx += 1
			db.session.commit()

		return jsonify({'message': 'reset complete', 'products_created': created, 'transactions_created': created_tx})

	@app.route('/api/init_db', methods=['POST'])
	def init_db_endpoint():
		# Create tables and optionally seed minimal products (for first-time setup)
		if admin_key:
			provided = request.headers.get('X-ADMIN-KEY')
			if not provided or provided != admin_key:
				return jsonify({'error': 'forbidden (invalid admin key)'}), 403
		else:
			if not allow_destructive and os.environ.get('FLASK_ENV') != 'development':
				return jsonify({'error': 'destructive endpoints are disabled'}), 403
		# Combined behavior: ensure tables exist, then remove existing data and seed sample products + transactions
		try:
			with app.app_context():
				# ensure tables
				db.create_all()
				# destructive: clear existing data
				try:
					TransactionItem.query.delete()
					Transaction.query.delete()
					Product.query.delete()
					db.session.commit()
				except Exception:
					db.session.rollback()

				# sample product names
				PRODUCT_NAMES = [
					'Espresso', 'Latte', 'Cappuccino', 'Tea', 'Orange Juice', 'Muffin', 'Bagel', 'Sandwich',
					'Chocolate', 'Soda', 'Water', 'Cookie', 'Salad', 'Burger', 'Fries', 'Milk', 'Yogurt', 'Granola', 'Apple', 'Banana'
				]

				created = 0
				products = []
				for name in PRODUCT_NAMES:
					p = Product(name=name,
							price=round(random.uniform(0.5, 10.0), 2),
							cost=round(random.uniform(0.2, 5.0), 2),
							stock=random.randint(10, 200))
					db.session.add(p)
					products.append(p)
					created += 1
				db.session.commit()

				# create random transactions
				tx_count = 50
				created_tx = 0
				if products:
					products = Product.query.all()
					for i in range(tx_count):
						items = []
						for _ in range(random.randint(1, 4)):
							p = random.choice(products)
							qty = random.randint(1, 5)
							items.append((p, qty))
						total = sum(p.price * q for p, q in items)
						t = Transaction(timestamp=datetime.utcnow() - timedelta(days=random.randint(0, 30)), total_amount=round(total, 2))
						db.session.add(t)
						db.session.flush()
						for p, q in items:
							ti = TransactionItem(transaction_id=t.id, product_id=p.id, quantity=q, price_at_sale=p.price)
							db.session.add(ti)
							p.stock = max(0, p.stock - q)
						created_tx += 1
					db.session.commit()

				return jsonify({'message': 'setup complete', 'products_created': created, 'transactions_created': created_tx}), 201
		except Exception as e:
			db.session.rollback()
			return jsonify({'error': str(e)}), 500
	return app

# 初始化資料庫
if __name__ == '__main__':
	app = create_app()
	if not os.path.exists('pos.db'):
		with app.app_context():
			db.create_all()
	# Allow overriding port and debug via environment for flexible local testing
	port = int(os.environ.get('PORT', '5001'))
	debug_env = str(os.environ.get('FLASK_DEBUG', 'true')).lower()
	debug_mode = debug_env in ('1', 'true', 'yes')
	app.run(host='127.0.0.1', port=port, debug=debug_mode)
