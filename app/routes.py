# -*- coding: utf-8 -*-
from werkzeug.utils import secure_filename
from transliterate import translit
from app import app
from app import db
import time
from app.forms import LoginForm, RegisterForm, EditProfileForm, AddProductForm
from app.models import User, Product, Category, Type, Site, Items
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required, login_user, logout_user



def is_auth():
    if current_user.is_authenticated:
        return None
    else:
        return LoginForm()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@app.route("/")
@app.route("/index")
def index():
    login_form = is_auth()
    products = Product.query.all()
    categories = Category.query.all()
    return render_template("index.html", login_form=login_form, products=products, categories=categories)


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
    return render_template("index.html", login_form=login_form)

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

# @app.route("/<username>/settings", methods = ['GET', 'POST'])
# @login_required


# @app.route('/test')
# def test():
#     pr = Product.query.all()
#     manager = User.query.get(1)
#     for site in manager.sites:
#         products = site.products
#         for product in products:
#             return product.name
#     for p in pr:
#         manager = p.site.manager.login
#     return str(manager)


@app.route('/product/<int:id>')
def product(id):
    login_form = is_auth()

    post_product = Product.query.get(id)
    product_items = post_product.items.all()
    post_product.get_busy_items()
    post_product.get_percent_items_goal()
    categories = Category.query.all()

    return render_template("post.html",title = post_product.name, product_items=product_items, product=post_product, login_form=login_form,categories=categories)

@app.route('/categories')
def categories():
    login_form = is_auth()
    categories = Category.query.all()

    return render_template("categories.html", title = "Категории", categories = categories, login_form=login_form)

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
        site = request.form['site']
        file = request.files['main_img']
        now = str(int(time.time()))
        if file and allowed_file(file.filename):
            file.filename = translit(product_name, reversed=True)+ '_'+now
            main_img = app.config['UPLOAD_FOLDER'] + secure_filename(file.filename)
            file.save('app' + main_img)
        inputs = ['second_image_1','second_image_2','second_image_3','second_image_4']
        secondary_img = []
        for inp in inputs:
            s_file = request.files.get(inp, None)
            if s_file != None:
                img = request.files[inp]
                if img and allowed_file(img.filename):
                    img.filename = file.filename + '_'+str(inputs.index(inp))
                    s_path = app.config['UPLOAD_FOLDER'] + secure_filename(img.filename)
                    s_file.save('app' + s_path)
                    secondary_img.append(s_path)

        # s_file = request.files.get('second_image_1', None)
        # if s_file != None:
        #     img =  request.files['second_image_1']
        #     if img and allowed_file(img.filename):
        #         img.filename = file.filename + '_1'
        #         s_path = app.config['UPLOAD_FOLDER'] + secure_filename(img.filename)
        #         s_file.save('app' + s_path)
        #         secondary_img.append(s_path)
        #
        # s_file = request.files.get('second_image_2', None)
        # if s_file != None:
        #     img = request.files['second_image_2']
        #     if img and allowed_file(img.filename):
        #         img.filename = file.filename + '_2'
        #         s_path = app.config['UPLOAD_FOLDER'] + secure_filename(img.filename)
        #         s_file.save('app' + s_path)
        #         secondary_img.append(s_path)
        #
        # s_file = request.files.get('second_image_3', None)
        # if s_file != None:
        #     img = request.files['second_image_3']
        #     if img and allowed_file(img.filename):
        #         img.filename = file.filename + '_3'
        #         s_path = app.config['UPLOAD_FOLDER'] + secure_filename(img.filename)
        #         s_file.save('app' + s_path)
        #         secondary_img.append(s_path)
        #
        # s_file = request.files.get('second_image_4', None)
        # if s_file != None:
        #     img = request.files['second_image_4']
        #     if img and allowed_file(img.filename):
        #         img.filename = file.filename + '_4'
        #         s_path = app.config['UPLOAD_FOLDER'] + secure_filename(img.filename)
        #         s_file.save('app' + s_path)
        #         secondary_img.append(s_path)

        product = Product()
        product.name = product_name
        product.url=url
        product.goal = goal
        product.description = description
        product.price = price
        product.date_add = now
        product.category_id = category
        product.type_id = type
        product.site_id = site
        product.main_image = main_img
        product.second_image = secondary_img
        db.session.add(product)
        db.session.commit()
        if type == 1:
            pass
        elif type == 2:
            for i in goal:
                item = Items()
                item.id_product = product.id
                db.session.add(item)
            db.session.commit()
        # return render_template("post.html",title = product.name, product_items=product.items, product=product, login_form=True,categories=categories)
    return render_template("add_product.html", title="Добавить товар", categories=categories, types=types, sites=sites, add_form=add_form)


# @app.route('/add_product/upload')
# @login_required
# def upload():
#     file = request.files['upload']
#
#     path = app.config["UPLOAD_FOLDER"]+file.filename

