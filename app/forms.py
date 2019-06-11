from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, FileField, MultipleFileField, \
    SelectField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign in')

class RegisterForm(FlaskForm):
    last_name = StringField('LastName', validators=[DataRequired()])
    first_name = StringField('FirstName', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email(message="Некорректный адрес эл.почты")])
    login = StringField('Login', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat password', validators=[DataRequired(), EqualTo('password', message="Введенные пароли не совпадают")])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError("Такая почта уже используется")
    def validate_login(self, login):
        user = User.query.filter_by(login = login.data).first()
        if user is not None:
            raise ValidationError("Такой логин уже используется")

class EditProfileForm(FlaskForm):
    # Общая информация
    login = StringField('Login', validators=[DataRequired()])
    last_name = StringField('LastName', validators=[DataRequired()])
    first_name = StringField('FirstName', validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired()])
    # image = StringField('Image', validators=[DataRequired()])
    # Защита
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat password',
                              validators=[DataRequired(), EqualTo('password', message="Введенные пароли не совпадают")])
    # Cмена емаила после отправления сбщ на почту
    email = StringField('Email', validators=[DataRequired()])
    submit = SubmitField('Edit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, login):
        if login.data != self.original_username:
            user = User.query.filter_by(username=self.login.data).first()
            if user is not None:
                raise ValidationError('Please use a different username')

class AddProductForm(FlaskForm):
    name = StringField("Product_name", validators=[DataRequired()])
    price = StringField("Price", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    main_img = FileField("MainImage", validators=[FileRequired()])
    second_image_1 = FileField("SecondaryImage1", validators=[FileRequired()])
    second_image_2 = FileField("SecondaryImage2", validators=[FileRequired()])
    second_image_3 = FileField("SecondaryImage3", validators=[FileRequired()])
    second_image_4 = FileField("SecondaryImage4", validators=[FileRequired()])
    url = StringField("Url", validators=[DataRequired()])
    article = StringField("Article", validators=[DataRequired()])
    goal = StringField("Goal", validators=[DataRequired()])
    type = SelectField("Type", validators=[DataRequired()])
    site =SelectField("Site", validators=[DataRequired()])
    category = SelectField("Category", validators=[DataRequired()])
    sizes = StringField("Sizes", validators=[DataRequired()])

    submit = SubmitField("Save")

class ChangeProductForm(FlaskForm):
    name = StringField("Product_name", validators=[DataRequired()])
    price = StringField("Price", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    # main_img = FileField("MainImage", validators=[FileRequired()])
    # second_image_1 = FileField("SecondaryImage1", validators=[FileRequired()])
    # second_image_2 = FileField("SecondaryImage2", validators=[FileRequired()])
    # second_image_3 = FileField("SecondaryImage3", validators=[FileRequired()])
    # second_image_4 = FileField("SecondaryImage4", validators=[FileRequired()])
    url = StringField("Url", validators=[DataRequired()])
    article = StringField("Article", validators=[DataRequired()])
    goal = StringField("Goal", validators=[DataRequired()])
    type = SelectField("Type", validators=[DataRequired()])
    site = SelectField("Site", validators=[DataRequired()])
    category = SelectField("Category", validators=[DataRequired()])
    sizes = StringField("Sizes", validators=[DataRequired()])
    submit = SubmitField("Save")

class OrderForm(FlaskForm):
    count_order = StringField("CountField")
    submit = SubmitField("Order")

class MakeOrderForm(FlaskForm):
    name = StringField("Product_name", validators=[DataRequired()])
    site = SelectField("Site", validators=[DataRequired()])
    category = SelectField("Category", validators=[DataRequired()])
    url = StringField("Url", validators=[DataRequired()])
    additional = TextAreaField("Additional")
    send_mail = BooleanField('SendMail')
    submit = SubmitField("Order")