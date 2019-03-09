from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
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



