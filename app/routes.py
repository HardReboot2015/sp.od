# -*- coding: utf-8 -*-
from app import app
from app import db
from app.forms import LoginForm, RegisterForm
from app.models import User, Product
from flask import render_template, flash, redirect, url_for
from flask_login import current_user, login_required, login_user, logout_user

@app.route("/")
@app.route("/index")
def index():
    if current_user.is_authenticated:
        login_form = None
    else:
        login_form = LoginForm()
    products = Product.query.all()
    return render_template("index.html", login_form=login_form, products=products)


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
    if register_form.validate_on_submit():
        user = User(first_name=register_form.first_name.data, last_name=register_form.last_name.data,
                    login=register_form.login.data, email=register_form.email.data)
        user.set_password(register_form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('index'))
    return render_template("register.html", no_sidebar = True, title = "Регистрация", register_form = register_form )

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# @app.route("/<username>/settings", methods = ['GET', 'POST'])
# @login_required

@app.route('/test')
def test():
    pr = Product.query.all()
    manager = User.query.get(1)
    for site in manager.sites:
        products = site.products
        for product in products:
            return product.name
    for p in pr:
        manager = p.site.manager.login
    return str(manager)

@app.route('/product/<int:id>')
def product(id):
    if current_user.is_authenticated:
        login_form = None
    else:
        login_form = LoginForm()

    post_product = Product.query.get(id)
    product_items = post_product.items.all()
    post_product.get_busy_items()
    post_product.get_percent_items_goal()
    return render_template("post.html",title = post_product.name, product_items=product_items, product=post_product, login_form=login_form)