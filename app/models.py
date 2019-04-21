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
    url = db.Column(db.String(1024), nullable=False)
    # goal = db.Column(db.Integer, nullable=False)
    date_add = db.Column(db.Integer, nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey("type.id"))
    site_id = db.Column(db.Integer, db.ForeignKey("site.id"))
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))

    item_packs = db.relationship('ItemPack', backref = 'product', lazy ='dynamic')

    def first_free(self): #первый свободный итем каждого размера
        all_itemPacks = self.item_packs
        if all_itemPacks is not None:
            sizes = set(all_itemPacks[0].sizes)
            self.free_items = dict.fromkeys(sizes, 0)
            for itemPack in all_itemPacks:
                if itemPack.status == 3 or itemPack.status == 4:
                    items = itemPack.items.order_by(Items.id).all()
                    if items is not None:
                        for item in items:
                            if item.id_user is None:
                                if self.free_items[item.size] == 0 or item.id < self.free_items[item.size]:

                                    self.free_items[item.size] = item.id
        return self.free_items

    def add_rows(self):
        self.first_free()
        for k in self.free_items.keys():
            if self.free_items[k] == 0:
                return True
        return False

    def delete_excess(self):# удалить лишний пустой итемпак
        count_excess = len(self.item_packs.filter_by(status=4).all())
        if count_excess > 1:
           for item_pack in self.item_packs:
                if count_excess == 1: break
                Items.query.filter_by(id_itemPack = item_pack.id).delete()
                ItemPack.query.filter_by(id=item_pack.id).delete()
                count_excess -= 1
                db.session.commit()



class ItemPack(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    id_product = db.Column(db.Integer,db.ForeignKey("product.id"),nullable=False)
    goal = db.Column(db.Integer, nullable=False)
    sizes = db.Column(db.ARRAY(db.String), nullable=True, default=[])
    status = db.Column(db.Integer, db.ForeignKey("status.id"))
    date_collect = db.Column(db.Integer, nullable=True)

    items = db.relationship('Items', backref = 'item_pack', lazy='dynamic')


    def get_free_items(self):
        itemPack = ItemPack.query.get(self.id)
        items = itemPack.items.all()
        for item in items:
            if item.id_user is None:    #eсли есть хоть один свободный элемент данной ростовки
                return True             #возвращаем True, то есть есть свободные итемы
        return False                    #иначе - False(ростовка собрана)

    def get_busy_items(self):           #количество занятых элементов ростовки
        itemPack = ItemPack.query.get(self.id)
        self.count = len(itemPack.items.filter(Items.id_user != None).all())

    def get_percent_items_goal(self):   #процент количества итемов от цели
        self.percent_items = self.count / self.goal * 100

    def get_percent_price_goal(self):   #процент собранного количества денег от цели(денежной)
        self.price_sum = self.count * self.price
        self.percent_price = self.price_sum / self.goal * 100

    def change_status(self):
        self.get_busy_items()
        if self.count == 0:
            self.status = 4
        elif self.count != len(self.items.all()):
            self.status = 3
        else:
            for item in self.items:
                if item.confirmed == False:
                    self.status = 2
                elif item.payed == False:
                    self.status = 1
                else:
                    self.status = None
        db.session.commit()







class Status(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    name = db.Column(db.String(128), nullable=False)

class Items(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    size = db.Column(db.String(32), nullable=True)
    payed = db.Column(db.Boolean, default=False)
    confirmed = db.Column(db.Boolean, default=False)
    id_color = db.Column(db.Integer, db.ForeignKey("color.id"))
    id_itemPack = db.Column(db.Integer, db.ForeignKey("item_pack.id"))
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
    password = db.Column(db.String(256), nullable=False)
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

