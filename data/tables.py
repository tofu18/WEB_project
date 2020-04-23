import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String)
    about = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String,
                              index=True, unique=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)
    profile_image = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    questions = orm.relation('Question', back_populates='user')
    messages = orm.relation('Message', back_populates='user')

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)


class Question(SqlAlchemyBase):
    __tablename__ = 'questions'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    creator_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    topic = sqlalchemy.Column(sqlalchemy.String)

    user = orm.relation('User')
    messages = orm.relation('Message', back_populates='question')


class Message(SqlAlchemyBase):
    __tablename__ = 'messages'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    creator_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    response_to = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)  # На какое сообщение отвечает
    response_to_question = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('questions.id')) # На какой вопрос отвечает
    text = sqlalchemy.Column(sqlalchemy.String)
    question = orm.relation('Question')
    user = orm.relation('User')
