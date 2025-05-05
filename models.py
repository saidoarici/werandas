from extensions import db

class CostItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(100))
    size = db.Column(db.String(50))
    quantity = db.Column(db.Integer)
    unit_cost = db.Column(db.Float)
    assembly_cost = db.Column(db.Float)
    profit_rate = db.Column(db.Float)
    total_cost = db.Column(db.Float)
    sale_price = db.Column(db.Float)
    created_at = db.Column(db.DateTime)


class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    offer_number = db.Column(db.String(50), unique=True)

    # İşte eksik olan foreign key burası:
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))

    created_by = db.Column(db.String(50))
    created_at = db.Column(db.DateTime)
    valid_until = db.Column(db.DateTime)
    currency = db.Column(db.String(10))

    items = db.relationship('OfferItem', backref='offer', cascade="all, delete-orphan")

    @property
    def total_cost(self):
        return sum(item.total_cost for item in self.items)


class OfferItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    offer_id = db.Column(db.Integer, db.ForeignKey('offer.id'))
    product = db.Column(db.String(100))
    size = db.Column(db.String(50))
    quantity = db.Column(db.Integer)
    unit_cost = db.Column(db.Float)
    assembly_cost = db.Column(db.Float)
    profit_rate = db.Column(db.Float)
    total_cost = db.Column(db.Float)
    sale_price = db.Column(db.Float)


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(30))
    email = db.Column(db.String(100))

    # Bu ilişkiyi ancak Offer.customer_id foreign key olursa kurabiliriz
    offers = db.relationship("Offer", backref="customer", lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    size = db.Column(db.String(50))
    unit_cost = db.Column(db.Float, default=0)
    assembly_cost = db.Column(db.Float, default=0)
    default_profit_rate = db.Column(db.Float, default=20.0)

    def __repr__(self):
        return f"<Product {self.name}>"