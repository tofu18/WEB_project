from flask import Flask, render_template, url_for, redirect
from data.db_session import create_session, global_init
from flask_wtf import FlaskForm
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from data.tables import User, Question, Message
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FileField, TextAreaField
from wtforms.validators import DataRequired
from flask_ngrok import run_with_ngrok

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    repeat_password = PasswordField('Повторите пароль', validators=[DataRequired()])
    profile_image = FileField('Картинка профиля')
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    username = StringField('Имя пользователя или email', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class QuestionForm(FlaskForm):
    topic = TextAreaField('Ваш вопрос', validators=[DataRequired()])
    submit = SubmitField('Создать')


class MessageForm(FlaskForm):
    message_text = TextAreaField('Введите текст сообщения', validators=[DataRequired()])
    submit = SubmitField('Отправить')


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
        elif session.query(User).filter(User.email == form.email.data).first():
            error_message = 'Пользователь с таким email уже существует'
        elif form.password.data != form.repeat_password.data:
            error_message = 'Пароли не совпадают'
        else:
            new_user = User(username=form.username.data, email=form.email.data)
            new_user.set_password(form.password.data)
            session.add(new_user)
            session.commit()
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
def create_question():
    form = QuestionForm()
    if form.validate_on_submit():
        question = Question(creator_id=current_user.id, topic=form.topic.data)
        session = create_session()
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


@app.route('/profile/<user_id>')
def profile(user_id):
    session = create_session()
    user = session.query(User).filter(User.id == user_id).first()
    return render_template('profile.html', user=user)


@app.route('/question/<question_id>', methods=['GET', 'POST'])
def question(question_id):
    form = MessageForm()
    session = create_session()
    question = session.query(Question).filter(Question.id == question_id).first()
    if form.validate_on_submit():
        message = Message(creator_id=current_user.id, response_to_question=question_id, text=form.message_text.data)
        session.add(message)
        session.commit()
    print(url_for('static', filename='css/question.css'))
    return render_template('question.html', question=question, form=form, cssfile=url_for('static', filename='css/question.css'))


def main():
    global_init('db/forum.db')
    app.run()


if __name__ == '__main__':
    main()
