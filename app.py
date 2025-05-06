from flask import Flask, render_template, request, redirect, url_for, send_file, send_from_directory
from flask_migrate import Migrate
from extensions import db
from models import Offer, OfferItem, Customer, Product
from datetime import datetime
from io import BytesIO

app = Flask(__name__, static_folder='static')
app.secret_key = 'maliyet-super-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maliyet.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Veritabanı ve migrate bağlanıyor
db.init_app(app)
migrate = Migrate(app, db)

# Teklif numarası otomatik üretici
def generate_offer_number():
    last = Offer.query.order_by(Offer.id.desc()).first()
    number = last.id + 1 if last else 1
    return f"TEK-{datetime.now().year}-{str(number).zfill(4)}"

try:
    from utils import generate_pdf
except ImportError:
    generate_pdf = None

@app.route('/offer/new', methods=['GET', 'POST'])
def new_offer():
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        customer = Customer.query.filter_by(name=customer_name).first()

        if not customer:
            customer = Customer(
                name=customer_name,
                address=request.form.get('customer_address'),
                phone=request.form.get('customer_phone'),
                email=request.form.get('customer_email')  # <<-- yeni alan
            )
            db.session.add(customer)
            db.session.commit()

        offer = Offer(
            offer_number=generate_offer_number(),
            customer_id=customer.id,
            created_by="admin",
            created_at=datetime.now(),
            valid_until=datetime.strptime(request.form['valid_until'], '%Y-%m-%d'),
            currency=request.form.get('currency')  # <<-- yeni alan
        )
        db.session.add(offer)
        db.session.commit()
        return redirect(url_for('add_items', offer_id=offer.id))
    return render_template('offer_form.html')

@app.route('/offer/<int:offer_id>/items', methods=['GET'])
def add_items(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    offer_items = OfferItem.query.filter_by(offer_id=offer_id).all()

    # OfferItem'ları JSON'a uygun hale getir
    items = [{
        'product': i.product,
        'size': i.size,
        'quantity': i.quantity,
        'unit_cost': i.unit_cost,
        'assembly_cost': i.assembly_cost,
        'profit_rate': i.profit_rate,
        'total_cost': i.total_cost,
        'sale_price': i.sale_price
    } for i in offer_items]

    return render_template('offer_items.html', offer=offer, items=items, currency=offer.currency)

@app.route('/offer/<int:offer_id>/save_items', methods=['POST'])
def save_items(offer_id):
    data = request.get_json()

    # 1. Önce mevcut kayıtları sil
    OfferItem.query.filter_by(offer_id=offer_id).delete()
    db.session.commit()

    # 2. Yeni gelenleri ekle
    for item in data:
        db.session.add(OfferItem(
            offer_id=offer_id,
            product=item['product'],
            size=item['size'],
            quantity=item['quantity'],
            unit_cost=item['unit_cost'],
            assembly_cost=item['assembly_cost'],
            profit_rate=item['profit_rate'],
            total_cost=item['total_cost'],
            sale_price=item['sale_price']
        ))
    db.session.commit()
    return {'status': 'success'}

@app.route('/offer/<int:offer_id>/pdf')
def offer_pdf(offer_id):
    if not generate_pdf:
        return "PDF özelliği devre dışı.", 501
    offer = Offer.query.get_or_404(offer_id)
    pdf = generate_pdf(offer)
    return send_file(BytesIO(pdf), download_name=f"{offer.offer_number}.pdf", as_attachment=True)

@app.route('/offers')
def list_offers():
    offers = Offer.query.order_by(Offer.created_at.desc()).all()
    return render_template('offer_list.html', offers=offers)

@app.route('/api/customers')
def search_customers():
    q = request.args.get('q', '')
    results = Customer.query.filter(Customer.name.ilike(f"%{q}%")).all()
    return [{
        'id': c.id,
        'name': c.name,
        'address': c.address,
        'phone': c.phone
    } for c in results]


@app.route('/products')
def list_products():
    products = Product.query.all()
    return render_template('product_list.html', products=products)

@app.route('/product/new', methods=['GET', 'POST'])
def new_product():
    if request.method == 'POST':
        product = Product(
            name=request.form['name'],
            size=request.form['size'],
            unit_cost=float(request.form['unit_cost']),
            assembly_cost=float(request.form['assembly_cost']),
            default_profit_rate=float(request.form['default_profit_rate'])
        )
        db.session.add(product)
        db.session.commit()
        return redirect(url_for('list_products'))
    return render_template('product_form.html')

@app.route('/api/products')
def api_products():
    q = request.args.get('q', '')
    results = Product.query.filter(Product.name.ilike(f"%{q}%")).all()
    return [{
        'id': p.id,
        'name': p.name,
        'size': p.size,
        'unit_cost': p.unit_cost,
        'assembly_cost': p.assembly_cost,
        'default_profit_rate': p.default_profit_rate
    } for p in results]


@app.route('/')
def home():
    # İstatistikleri hesapla
    offers_count = Offer.query.count()
    customers_count = Customer.query.count()
    products_count = Product.query.count()

    # Bu ayki teklifleri hesapla
    from datetime import datetime, date
    today = date.today()
    first_day = date(today.year, today.month, 1)
    this_month_offers = Offer.query.filter(
        Offer.created_at >= first_day,
        Offer.created_at <= today
    ).count()

    # Son 5 teklifi getir
    recent_offers = Offer.query.order_by(Offer.created_at.desc()).limit(5).all()

    # Son 5 müşteriyi getir
    recent_customers = Customer.query.order_by(Customer.id.desc()).limit(5).all()

    return render_template('index.html',
                           offers_count=offers_count,
                           customers_count=customers_count,
                           products_count=products_count,
                           this_month_offers=this_month_offers,
                           recent_offers=recent_offers,
                           recent_customers=recent_customers)

@app.context_processor
def inject_now():
    from datetime import datetime
    return {'datetime': datetime}


@app.route('/static/<path:filename>')
def staticfiles(filename):
    return send_from_directory(app.static_folder, filename)


# Bu kısım sadece doğrudan python ile çalıştırıldığında çalışır
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4444)