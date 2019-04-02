# -*- coding: utf-8 -*-
from app import app
from app import db
from app.forms import LoginForm, RegisterForm, EditProfileForm
from app.models import User, Product, Category, Type, Site
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required, login_user, logout_user



def is_auth():
    if current_user.is_authenticated:
        return None
    else:
        return LoginForm()

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
    categories = Category.query.all()
    sites = Site.query.filter_by(manager_id=current_user.id)
    types = Type.query.all()
    return render_template("add_product.html", title="Добавить товар", categories=categories, types=types, sites=sites)
