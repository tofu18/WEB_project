from flask import Flask, render_template, url_for, redirect
from data.db_session import create_session, global_init
from flask_wtf import FlaskForm
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from data.tables import User, Question, Message
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FileField, TextAreaField
from wtforms.validators import DataRequired
from flask_ngrok import run_with_ngrok
import os
import random
from requests import get
import json

app = Flask(__name__)
run_with_ngrok(app)
app.config['SECRET_KEY'] = 'super_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    repeat_password = PasswordField('Повторите пароль', validators=[DataRequired()])
    profile_image = FileField()
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    username = StringField('Имя пользователя или', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class QuestionForm(FlaskForm):
    text = TextAreaField('Ваш вопрос', validators=[DataRequired()])
    image = FileField('Загрузить файл')
    submit = SubmitField('Создать')


class MessageForm(FlaskForm):
    message_text = TextAreaField('Введите текст сообщения', validators=[DataRequired()])
    reply_to = StringField('Ответ на')
    submit = SubmitField('Отправить')


class EditProfileForm(FlaskForm):
    username = StringField('Имя пользователя')
    about = TextAreaField('О себе')
    location = StringField('Ваше местоположение')
    image = FileField()
    submit = SubmitField('Изменить')


@login_manager.user_loader
def load_user(user_id):
    session = create_session()
    return session.query(User).get(user_id)


@app.route('/register', methods=['GET', 'POST'])
def registration():
    form = RegistrationForm()
    error_message = ''
    if form.validate_on_submit():
        session = create_session()
        if session.query(User).filter(User.username == form.username.data).first():
            error_message = 'Пользователь с таким именем уже существует\n'
        elif form.password.data != form.repeat_password.data:
            error_message = 'Пароли не совпадают'
        else:
            new_user = User(username=form.username.data)
            new_user.set_password(form.password.data)
            file = form.profile_image.data.read()
            if file != b'':
                image_name = f'static/img/{random.randrange(1, 2 ** 20)}.jpg'
                with open(image_name, mode='wb') as f:
                    f.write(file)
                new_user.profile_image = image_name
            session.add(new_user)
            session.commit()
            login_user(new_user)
            return redirect('/')
    return render_template('register.html', form=form, error_message=error_message)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    errormessage = ''
    if form.validate_on_submit():
        session = create_session()
        user = session.query(User).filter(User.username == form.username.data).first()
        if not user:
            errormessage = 'Пользователя с таким именем не существует'
        elif user.check_password(form.password.data):
            login_user(user)
            return redirect('/')

    return render_template('login.html', form=form, errormessage=errormessage)


@app.route('/create_question', methods=['GET', 'POST'])
@login_required
def create_question():
    form = QuestionForm()
    if form.validate_on_submit():
        question = Question(creator_id=current_user.id, text=form.text.data)
        session = create_session()
        image = form.image.data.read()
        if image != b'':
            image_name = f'static/img/{random.randrange(1, 2 ** 20)}.jpg'
            with open(image_name, mode='wb') as f:
                f.write(image)
            question.pinned_image = image_name
        session.add(question)
        session.commit()
        return redirect('/')
    return render_template('create_question.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/')
@login_required
def index():
    session = create_session()
    questions = session.query(Question).all()
    return render_template('index.html', questions=questions, user=current_user)


@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    session = create_session()
    user = session.query(User).filter(User.id == user_id).first()
    return render_template('profile.html', user=user)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        session = create_session()
        current_user.username = form.username.data
        current_user.about = form.about.data
        location = form.location.data
        current_user.location = location
        image = form.image.data
        f = image.read()
        if image != current_user.profile_image and f != b'':
            filename = f'static/img/{random.randrange(1, 2 ** 20)}.jpg'
            with open(filename, mode='wb') as file:
                file.write(f)
            os.remove(current_user.profile_image)
            current_user.profile_image = filename
        if location != None:
            response = get(
                f'https://geocode-maps.yandex.ru/1.x?geocode={location}&apikey=40d1649f-0493-4b70-98ba-98533de7710b&format=json')
            if response:
                response = json.loads(response.content)
                coords = response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject'][
                    'Point']['pos'].split()
                bbox = \
                    response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject'][
                        'boundedBy']['Envelope']
                bbox = ','.join(bbox['lowerCorner'].split()) + '~' + ','.join(bbox['upperCorner'].split())
                location_map = get(f'https://static-maps.yandex.ru/1.x?l=map&ll={coords[0]},{coords[1]}&bbox={bbox}')
                if location_map.content:
                    if current_user.location_image is None:
                        filename = f'static/img/{random.randrange(1, 2 ** 20)}.jpg'
                        with open(filename, mode='wb') as f:
                            f.write(location_map.content)
                        current_user.location_image = filename
                    else:
                        with open(current_user.location_image, mode='wb') as f:
                            f.write(location_map.content)
        session.merge(current_user)
        session.commit()
        return redirect(f'/profile/{current_user.id}')

    return render_template('edit_profile.html', form=form, current_user=current_user)


@app.route('/question/<question_id>', methods=['GET', 'POST'])
@login_required
def question(question_id):
    form = MessageForm()
    session = create_session()
    question = session.query(Question).filter(Question.id == question_id).first()
    if form.validate_on_submit():
        message = session.query(Message).filter(Message.id == form.reply_to.data).first()
        if (message and message in question.messages) or form.reply_to.data == '':
            message = Message(creator_id=current_user.id, reply_to_question=question_id, text=form.message_text.data,
                              reply_to=form.reply_to.data)
            session.add(message)
            session.commit()
            return redirect(f'/question/{question_id}')
    return render_template('question.html', question=question, form=form,
                           cssfile=url_for('static', filename='css/question.css'), current_user=current_user)


@app.route('/give_mod_rights/<id>')
@login_required
def give_mod_rights(id):
    if current_user.id == 1:
        session = create_session()
        user = session.query(User).filter(User.id == id).first()
        user.admin = True
        session.merge(user)
        session.commit()
    return redirect(f'/profile/{id}')


@app.route('/delete_question/<id>')
@login_required
def delete_question(id):
    if current_user.admin == 1:
        session = create_session()
        question = session.query(Question).filter(Question.id == id).first()
        if question.pinned_image != None:
            os.remove(question.pinned_image)
        session.delete(question)
        session.commit()
    return redirect('/')


@app.route('/delete_message/<id>')
@login_required
def delete_message(id):
    if current_user.admin == 1:
        session = create_session()
        message = session.query(Message).filter(Message.id == id).first()
        question_id = message.question.id
        session.delete(message)
        session.commit()
    return redirect(f'/question/{question_id}')


@app.route('/delete_user/<int:id>')
@login_required
def delete_user(id):
    if current_user.admin == 1 or current_user.id == id:
        session = create_session()
        user = session.query(User).filter(User.id == id).first()
        if user.admin != 1:
            if user.profile_image != None:
                os.remove(user.profile_image)
            session.delete(user)
            session.commit()

    if current_user.id == id:
        return redirect('/register')
    return redirect('/')


def main():
    global_init('db/forum.db')
    app.run()


if __name__ == '__main__':
    main()
