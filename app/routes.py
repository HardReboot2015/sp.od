# -*- coding: utf-8 -*-
from werkzeug.utils import secure_filename
from transliterate import translit
from app import app
from app import db
import time
from app.forms import LoginForm, RegisterForm, EditProfileForm, AddProductForm, OrderForm, ChangeProductForm, MakeOrderForm
from app.models import User, Product, Category, Type, Site, Items, ItemPack, Messages
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required, login_user, logout_user
import re

from json import dumps, loads


def is_auth():
    if current_user.is_authenticated:
        return None
    else:
        return LoginForm()

# file validation function
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@app.route("/")
@app.route("/index")
def index():
    login_form = is_auth()
    products = Product.query.order_by(Product.date_add.desc()).all()
    categories = Category.query.all()
    return render_template("index.html", login_form=login_form, products=products, categories=categories)

#авторизация
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = User.query.filter_by(login = login_form.username.data).first()
        if user is None or not user.check_password(login_form.password.data):
            # flash('Неверный логин или пароль')
            return redirect(url_for('login'))
        login_user(user, remember=login_form.remember_me.data)
        return redirect(url_for('index'))
    return redirect(url_for("index", login_form=login_form))

#регистрация
@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    register_form = RegisterForm()
    categories = Category.query.all()
    if register_form.validate_on_submit():
        user = User(first_name=register_form.first_name.data, last_name=register_form.last_name.data,
                    login=register_form.login.data, email=register_form.email.data)
        user.set_password(register_form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('index'))

    return render_template("register.html", no_sidebar = True, title = "Регистрация", register_form = register_form, categories=categories )

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# product page
@app.route('/product/<int:id>')
def product(id):
    login_form = is_auth()
    post_product = Product.query.get(id)
    item_packs = post_product.item_packs.order_by(ItemPack.status,ItemPack.id).all()

    items = []
    if post_product.type_id == 1: # товар типа ростовка
        order_form = None
        for item_pack in item_packs:    #Сортировка итемов по возрастанию id
            i = item_pack.items.order_by(Items.id).all()
            items.append(i)
    else:   #товар типа "минимальное количество"
        item_packs = ItemPack.query.filter_by(id_product = id).order_by(ItemPack.status).first()
        item_packs.get_product_busy_items()
        item_packs.get_percent_items_goal()
        order_form = OrderForm()
        if current_user.is_authenticated:
            current_user.ordered_items(id, current_user.id)

    categories = Category.query.all()

    return render_template("post.html",title = post_product.name, product=post_product,item_packs=item_packs,items=items,
                           login_form=login_form,order_form = order_form,categories=categories)

@app.route('/order_product', methods=["GET", "POST"])
@login_required
def order_product():
    morder_form = MakeOrderForm()
    sites = Site.query.all()
    categories = Category.query.all()

    if request.method == "POST":
        site = Site.query.get(int(request.form['site']))
        message = Messages()
        message.time = int(time.time())
        addition = {'name': request.form['name'],
                    'site':int(request.form['site']),
                    'link': request.form['url'],
                    'category':int(request.form['category'])
                    }
        message.addition = dumps(addition, ensure_ascii=False)
        message.from_user = current_user.id
        message.recepient_id = site.manager_id
        message.m_text = request.form['additional']
        message.type = 1
        db.session.add(message)
        db.session.commit()
        return redirect(url_for("index"))

    return render_template("order_product.html", title="Заказать товар", morder_form=morder_form, sites=sites, categories=categories)


#заказ размера товара типа ростовка
@app.route('/product/<int:product_id>/<int:id>/order')
@login_required
def order(product_id, id):
    id_user = current_user.id
    item = Items.query.get(id)
    product = Product.query.get(product_id)
    product.first_free()
    item = Items.query.get(product.free_items[item.size])

    item_pack = ItemPack.query.get(item.id_itemPack)
    item.id_user = id_user
    item_pack.change_status()

    if product.add_rows() :
        item_pack2 = ItemPack()
        item_pack2.goal = item_pack.goal
        item_pack2.id_product = product_id
        item_pack2.sizes = item_pack.sizes
        item_pack2.status = 4
        db.session.add(item_pack2)
        db.session.commit()
        for size in item_pack.sizes:
            items = Items()
            items.id_itemPack = item_pack2.id
            items.size = size
            db.session.add(items)
    # сделать бронирование первого свободного размера

    db.session.commit()
    return redirect(url_for("product",id=product_id))

#заказ итемов типа "минимальное количество" на странице товара
@app.route('/product/order_min/<int:product_id>', methods = ["POST"])
@login_required
def order_min(product_id):
    id_user = current_user.id
    order_form = OrderForm()
    item_pack = ItemPack.query.filter(ItemPack.id_product == product_id, ItemPack.status > 2).order_by(ItemPack.status, ItemPack.id).first_or_404()
    print(item_pack)
    item_pack.get_busy_items()
    count = int(request.form['count_order'])

    if count >= item_pack.goal - item_pack.count_busy: #если заказанное количество больше либо равно чем количество свободных итемов
        add_itempacks = (count - (item_pack.goal - item_pack.count_busy))//item_pack.goal + 1 # вычисляем сколько итемпаков должно быть добавлено
    else: add_itempacks = 0                             #иначе - переменная равна нулю

    if request.method == 'POST':
        if add_itempacks != 0: #если необходимо добавить итемпаки
            #
            while add_itempacks>0 or count>0: # цикл идет пока надо добавить итемпаки или поставить юзера
                item_pack_j = ItemPack.query.filter(ItemPack.id_product == product_id and ItemPack.status > 2).order_by(
                    ItemPack.status).first_or_404() #выборка итемпака доступного для изменения
                if item_pack_j.get_free_items() and count > 0:
                    #если в итепаке есть свободные итемы и все еще необходимо поставить итемы
                    for item in item_pack_j.items.filter_by(id_user=None).order_by(Items.id): # в цикле ставим юзера на итем
                        if count > 0:
                            item.id_user = current_user.id
                            count -=1   #минусуем количество которое надо поставить
                        else: break
                #
                else: #если в итемпаке нет свободных итемов
                    item_pack_j.status = 2 # меняем статус предыдущего итемпака
                    item_pack2 = ItemPack() #создаем новый итемпак
                    item_pack2.goal = item_pack_j.goal #даем ему параметры предыдущего итемпака
                    item_pack2.id_product = product_id
                    item_pack2.sizes = item_pack_j.sizes
                    item_pack2.status = 4
                    db.session.add(item_pack2) # добавляем в сессию информацию о итемпаке
                    db.session.commit()
                    for item in range(item_pack2.goal): #через цикл добавляем новые итемы
                        items = Items() #создаем новый итемпак
                        items.id_itemPack = item_pack2.id #даем параметры
                        if count > 0: #если еще надо поставить юзера на размер
                            items.id_user = current_user.id #ставим
                            count -= 1 #минусуем параметp
                            print(count)

                        db.session.add(items) #добавляем в сессию изменения
                    print(add_itempacks)
                    print(count)
                    add_itempacks -= 1 #минусуем количество добавления итемпаков
                db.session.commit() #коммитим изменения

        else: #если не надо добавлять итемпаки
            while count: #пока надо поставить на размер
                item = item_pack.items.filter_by(id_user = None).order_by(Items.id).first() #запрос на итемы
                item.id_user = id_user #ставим юзера
                count-=1 #минусуем параметр
            item_pack.change_status() #меняем статус итемпака если надо
        db.session.commit() #
    return redirect(url_for("product",id = product_id, order_form = order_form))

#отмена заказа товара, параметры: id_product, id - id итема или None, id типа товара
@app.route('/product/<int:product_id>/<id>/<int:type>/cancel')
@login_required
def cancel(product_id, id, type):
    if type == 1:
        item = Items.query.get(id)
        item.id_user = None
        db.session.commit()
        print("all good")
        product = Product.query.get(product_id)
        item.item_pack.change_status()
        product.delete_excess()
    elif type == 2:
        current_user.ordered_items(product_id, current_user.id)
        for id_item in current_user.all_ordered:
            item = Items.query.get(id_item)
            item.id_user = None
            item.item_pack.change_status()
        db.session.commit()
        product = Product.query.get(product_id)
        product.defragmentation()
        product.delete_excess()
    return redirect(url_for("product", id = product_id))

#отображение товаров организатора
@app.route('/manager_products/<int:id>')
def manager_products(id):
    categories = Category.query.all()
    if current_user.is_manage == True:
        sites = current_user.sites.all()
        products = []
        for site in sites:
            product = site.products.all()
            for p in product:
                products.append(p)

    return render_template("manager_products.html", products = products, categories=categories)

#страница категорий
@app.route('/categories')
def categories():
    login_form = is_auth()
    categories = Category.query.all()
    return render_template("categories.html", title = "Категории", categories = categories, login_form=login_form)

# товары категории
@app.route('/category/<int:id>')
def category(id):
    login_form = is_auth()
    category = Category.query.get(id)
    categories = Category.query.all()
    products = category.products.all()
    return render_template("category.html",title=category.name, products=products, login_form=login_form, categories = categories )

#настройки юзера
@app.route('/settings/<username>', methods = ['GET', 'POST'])
@login_required
def settings(username):
    if not current_user.is_authenticated:
        return redirect(url_for('index'))
    form = EditProfileForm(current_user.login)
    if form.validate_on_submit():
        current_user.login = form.login.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data

        current_user.password = form.password2.data
        current_user.email = form.email.data

    elif request.method == 'GET':
        form.login.data = current_user.login
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.phone.data = current_user.phone
        form.first_name.data = current_user.first_name

        form.password2.data = current_user.password
        form.email.data = current_user.email

    return render_template("settings.html", title = "Настройки")

#добавление товара
@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if not current_user.is_manage or not current_user.is_admin:
        return redirect(url_for('index'))
    add_form = AddProductForm()
    categories = Category.query.all()
    sites = Site.query.filter_by(manager_id=current_user.id)
    types = Type.query.all()

    if request.method == "POST":
        product_name = request.form['name']
        price = request.form['price']
        description = request.form['description']
        goal = request.form['goal']
        url = request.form['url']
        type = request.form['type']
        category = request.form['category']
        article = request.form['article']
        site = request.form['site']
        file = request.files['main_img']
        now = str(int(time.time()))
        if file and allowed_file(file.filename): #add main image
            file.filename = translit(product_name, reversed=True)+ '_'+now
            main_img = app.config['UPLOAD_FOLDER'] + secure_filename(file.filename)
            file.save('app' + main_img)
        inputs = ['second_image_1','second_image_2','second_image_3','second_image_4']
        secondary_img = []
        for inp in inputs: #add secondary_images
            s_file = request.files.get(inp, None)
            if s_file != None:
                img = request.files[inp]
                if img and allowed_file(img.filename):
                    img.filename = file.filename + '_'+str(inputs.index(inp))
                    s_path = app.config['UPLOAD_FOLDER'] + secure_filename(img.filename)
                    s_file.save('app' + s_path)
                    secondary_img.append(s_path)

        product = Product()
        item_pack = ItemPack()
        product.name = product_name
        product.url=url
        item_pack.goal = goal
        product.description = description
        product.price = price
        product.date_add = now
        product.category_id = category
        product.type_id = type
        product.site_id = site
        product.main_image = main_img
        product.article = article
        product.second_image = secondary_img
        db.session.add(product)
        db.session.commit()
        item_pack.id_product = product.id
        item_pack.status = 4
        db.session.add(item_pack)
        db.session.commit()
        if product.type_id == 1:
            sizes = re.findall(r'\b[-\w]+',request.form['sizes'])
            item_pack.sizes = sizes
            for i in sizes:
                items = Items()
                items.id_itemPack = item_pack.id
                items.size = i
                db.session.add(items)
        else:
            for i in range(item_pack.goal):
                items = Items()
                items.id_itemPack = item_pack.id
                db.session.add(items)
        db.session.commit()
        return redirect(url_for("product", id=product.id))


        # if type == 1:
        #     pass
        # elif type == 2:
        #     for i in goal:
        #         item = Items()
        #         item.id_product = product.id
        #         db.session.add(item)
        #     db.session.commit()
        # return render_template("post.html",title = product.name, product_items=product.items, product=product, login_form=True,categories=categories)
    return render_template("add_product.html", title="Добавить товар", categories=categories, types=types, sites=sites,
                           add_form=add_form)



#изменить товар
@app.route("/product/change/<int:id>", methods = ["GET", "POST"])
@login_required
def change_product(id):
    product = Product.query.get(id)
    categories = Category.query.all()
    types = Type.query.all()
    sites = Site.query.all()
    sizes = ""
    arr_sizes = []
    main_item_pack = product.item_packs.filter(ItemPack.status > 2).order_by(ItemPack.status).first()
    if product.type_id == 1:
        for size in main_item_pack.sizes:
            sizes += size + "; "
            arr_sizes.append(size)


    if not current_user.is_admin or current_user.id != product.site.manager_id:
        return url_for("product", id = id)
    cp_form = ChangeProductForm()
    if request.method == "POST":

        if request.form['name'] != product.name and request.form['name'] != "": product.name = request.form['name']
        if request.form['price'] != product.price and request.form['price'] != "": product.price = request.form['price']
        if request.form['description'] != product.description and request.form['description'] != "": product.description = request.form['description']
        if request.form['goal'] != main_item_pack.goal and request.form['goal'] != "": main_item_pack.goal = request.form['goal']
        if request.form['url'] != product.url and request.form['url'] != "":product.url = request.form['url']
        if request.form['article'] != product.article and request.form['article'] != "": product.article = request.form['article']
        if request.form['category'] != product.category_id: product.category_id = request.form['category']
        if request.form['site'] != product.site_id:product.site_id = request.form['site']
        if request.form['sizes'] != sizes:
            string_sizes = re.findall(r'\b[-\w]+',request.form['sizes'])
            print(len(string_sizes))
            print(request.form['goal'])
            if len(string_sizes) == int(request.form['goal']):
                for item_pack in product.item_packs.filter(ItemPack.status > 2).order_by(ItemPack.status).all():
                    item_pack.sizes = string_sizes
                    item_pack.items.delete()
                    for i in string_sizes:
                        items = Items()
                        items.id_itemPack = item_pack.id
                        items.size = i
                        db.session.add(items)

        db.session.commit()
        product.delete_excess()
        # работа с картинками

        # file = request.files['main_img']
        # now = str(int(time.time()))
        # if file and allowed_file(file.filename): #add main image
        #     file.filename = translit(product_name, reversed=True)+ '_'+now
        #     main_img = app.config['UPLOAD_FOLDER'] + secure_filename(file.filename)
        #     file.save('app' + main_img)
        # inputs = ['second_image_1','second_image_2','second_image_3','second_image_4']
        # secondary_img = []
        # for inp in inputs: #add secondary_images
        #     s_file = request.files.get(inp, None)
        #     if s_file != None:
        #         img = request.files[inp]
        #         if img and allowed_file(img.filename):
        #             img.filename = file.filename + '_'+str(inputs.index(inp))
        #             s_path = app.config['UPLOAD_FOLDER'] + secure_filename(img.filename)
        #             s_file.save('app' + s_path)
        #             secondary_img.append(s_path)

        # db.session.add(product)
        # db.session.commit()
        # item_pack.id_product = product.id
        # db.session.add(item_pack)
        # db.session.commit()
        # if product.type_id == 2:
        #     for i in range(item_pack.goal):
        #         items = Items()
        #         items.id_itemPack = item_pack.id
        #         db.session.add(items)
        # db.session.commit()
        return redirect(url_for("product", id=product.id))
    return render_template("change_product.html", title="Изменить товар", cp_form=cp_form, categories=categories,  types=types, sites=sites, product=product, sizes = sizes)

@app.route("/delete_product/<int:id>")
@login_required
def delete_product(id):
    if current_user.is_admin or current_user.is_manage:
        product = Product.query.get(id)
        categories = Category.query.all()
        item_packs = product.item_packs.filter(ItemPack.status > 1)
        for item_pack in item_packs:
            item_pack.items.delete()
            db.session.delete(item_pack)
            db.session.commit()
        db.session.delete(product)
        db.session.commit()
        return redirect(url_for("index", categories=categories))
    else:
        return redirect(url_for("product", id = id))