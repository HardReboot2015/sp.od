from app import db, login
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    name = db.Column(db.String(128), nullable=False)
    price = db.Column(db.Float, nullable=False, default=0)
    description = db.Column(db.String(512), nullable=True, default="")
    main_image = db.Column(db.String(128), nullable=False, default="")
    second_image = db.Column(db.ARRAY(db.String), nullable=True, default=[])
    goal = db.Column(db.Integer, nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey("type.id"))
    site_id = db.Column(db.Integer, db.ForeignKey("site.id"))
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))

    items = db.relationship('Items', backref = 'product', lazy='dynamic')


    def __repr__(self):
        return "Product №{} | Name: {}".format(self.id, self.name)

    def get_busy_items(self):
        product = Product.query.get(self.id)
        self.count = len(product.items.filter(Items.id_user != None).all())

    def get_percent_items_goal(self):
        self.percent_items = self.count / self.goal * 100

    def get_percent_price_goal(self):
        self.price_sum = self.count * self.price
        self.percent_price = self.price_sum / self.goal * 100

class Items(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    size = db.Column(db.String(32), nullable=False)
    payed = db.Column(db.Boolean, default=False)
    id_color = db.Column(db.Integer, db.ForeignKey("color.id"))
    id_product = db.Column(db.Integer, db.ForeignKey("product.id"))
    id_user = db.Column(db.Integer, db.ForeignKey("user.id"))



class Color(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)

    items = db.relationship('Items', backref='color', lazy='dynamic')

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)

    products = db.relationship('Product', backref='category', lazy='dynamic')

class Type(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)

    products = db.relationship('Product', backref='type', lazy='dynamic')

class Site(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    url = db.Column(db.String(64), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    type = db.Column(db.Integer, nullable=False, default=0)

    products = db.relationship('Product', backref='site', lazy='dynamic')


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    login = db.Column(db.String(64), nullable=False, unique=True)
    email = db.Column(db.String(128), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    photo = db.Column(db.String(128), nullable=False, default="/static/images/site/default_photo.png")
    phone = db.Column(db.String(32), nullable=True, unique=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_manage = db.Column(db.Boolean, default=False)

    sites = db.relationship('Site', backref='manager', lazy='dynamic')
    items = db.relationship('Items', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
