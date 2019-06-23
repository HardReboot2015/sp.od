from app import db, login
from flask_login import UserMixin

from werkzeug.security import check_password_hash, generate_password_hash
import datetime
import itertools

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    name = db.Column(db.String(128), nullable=False)
    price = db.Column(db.Float, nullable=False, default=0)
    description = db.Column(db.String(512), nullable=True, default="")
    main_image = db.Column(db.String(128), nullable=False, default="")
    second_image = db.Column(db.ARRAY(db.String), nullable=True, default=[])
    url = db.Column(db.String(1024), nullable=False)
    # goal = db.Column(db.Integer, nullable=False)
    article = db.Column(db.String(64), nullable=True)
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
        item_packs = self.item_packs.filter_by(status=4).all()
        count_excess = len(item_packs)
        if count_excess > 1:
           for item_pack in item_packs:
                if count_excess == 1: break
                Items.query.filter_by(id_itemPack = item_pack.id).delete()
                ItemPack.query.filter_by(id=item_pack.id).delete()
                count_excess -= 1
        db.session.commit()


    def defragmentation(self):#дефрагментация итемпаков товара
        item_p = self.item_packs.filter(ItemPack.status>=2).order_by(ItemPack.id).all()
        busy_items = []
        all_items = []
        for item_pack in item_p:
            busy_items.extend(item_pack.items.filter(Items.id_user != None).all())
            all_items.extend(item_pack.items.order_by(Items.id).all())
        print("1. busy_items:" + str(busy_items) + "\n all_items:" + str(all_items))

        for it,it2 in itertools.zip_longest(busy_items, all_items):
            if it == None: break
            print(it,it2)
            if it.id == it2.id: continue
            else:
                it2.id_user = it.id_user
                print(it2)
                print("busy_items:"+str(busy_items) + "\n all_items:" + str(all_items))
                print()
                # all_items[][it.id].id_user = None

            print("busy_items:"+str(busy_items) + "\n all_items:" + str(all_items))

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
        self.count_busy = len(itemPack.items.filter(Items.id_user != None).all())

    def get_product_busy_items(self):
        itemPacks = ItemPack.query.filter_by(id_product=self.id_product)
        self.counts = 0
        for itemPack in itemPacks:
            itemPack.get_busy_items()
            self.counts += itemPack.count_busy

    def get_percent_items_goal(self):   #процент количества итемов от цели
        if self.counts < self.goal:
            self.percent_items = self.counts / self.goal * 100
        else:
            self.percent_items = 100

    def get_percent_price_goal(self):   #процент собранного количества денег от цели(денежной)
        self.price_sum = self.count_busy * self.price
        self.percent_price = self.price_sum / self.goal * 100

    def change_status(self):
        self.get_busy_items()
        if self.count_busy == 0:
            self.status = 4
        elif self.count_busy != len(self.items.all()):
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
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), nullable=False)
    url = db.Column(db.String(64), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    type = db.Column(db.Integer, nullable=False, default=0)

    products = db.relationship('Product', backref='site', lazy='dynamic')


class Messages(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    from_user = db.Column(db.Integer, db.ForeignKey('user.id'))
    recepient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # to_users = db.Column(db.ARRAY(db.Integer), nullable=True)
    m_text = db.Column(db.String(1024), nullable=False)
    addition = db.Column(db.Text, nullable=True)
    time = db.Column(db.Integer, nullable=False)
    type = db.Column(db.Integer, nullable=False)

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

    messages_sent = db.relationship('Messages', foreign_keys = 'Messages.from_user', backref='author', lazy = 'dynamic')
    messages_reseived = db.relationship('Messages', foreign_keys = 'Messages.recepient_id', backref = 'recepient', lazy='dynamic')

    last_message_read_time = db.Column(db.Integer)


    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def ordered_items(self, product_id, user_id):
        sql= 'SELECT COUNT(items.id) FROM items, item_pack WHERE item_pack.id_product = %s AND items."id_itemPack" = item_pack.id AND items.id_user = %s'
        res = db.engine.execute(sql, product_id,user_id).fetchone()[0]
        sql2 = 'SELECT items.id FROM items, item_pack WHERE item_pack.id_product = %s AND items."id_itemPack" = item_pack.id AND items.id_user = %s'
        res2 = db.engine.execute(sql2, product_id, user_id).fetchall()
        items_id = []
        for item in res2:
            items_id.append(item[0])
            self.count_ordered = res
        self.all_ordered = items_id

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime.date(1970, 1,1)
        return Messages.query.filter(self.id in Messages.to_user and Messages.time > last_read_time).count()


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

