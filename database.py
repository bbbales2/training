import sqlalchemy
import sqlalchemy.ext.declarative
import os

Base = sqlalchemy.ext.declarative.declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key = True)
    name = sqlalchemy.Column(sqlalchemy.String)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

class Figure(Base):
    __tablename__ = 'figures'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key = True)
    caption = sqlalchemy.Column(sqlalchemy.String)
    url = sqlalchemy.Column(sqlalchemy.String)
    paperUrl = sqlalchemy.Column(sqlalchemy.String)

class FigureKeywords(Base):
    __tablename__ = 'figure_keywords'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key = True)
    keywords = sqlalchemy.Column(sqlalchemy.types.PickleType)
    figureId = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('figures.id'))

    figure = sqlalchemy.orm.relationship('Figure', backref = sqlalchemy.orm.backref('keywords'))

class Segmentation(Base):
    __tablename__ = 'segmentations'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key = True)
    data = sqlalchemy.Column(sqlalchemy.types.PickleType)

    userId = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    figureId = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('figures.id'))

    user = sqlalchemy.orm.relationship('User', backref = sqlalchemy.orm.backref('segmentations', order_by=id))
    figure = sqlalchemy.orm.relationship('Figure', backref = sqlalchemy.orm.backref('segmentations', order_by=id))

class Classification(Base):
    __tablename__ = 'classifications'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key = True)
    data = sqlalchemy.Column(sqlalchemy.types.PickleType)

    userId = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    figureId = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('figures.id'))

    user = sqlalchemy.orm.relationship('User', backref = sqlalchemy.orm.backref('classifications', order_by=id))
    figure = sqlalchemy.orm.relationship('Figure', backref = sqlalchemy.orm.backref('classifications', order_by=id))

def getEngine(path):
    engine = sqlalchemy.create_engine('sqlite:///{0}'.format(path), echo = False)

    Base.metadata.create_all(engine)

    return engine

def getSession(engine):
    Session = sqlalchemy.orm.sessionmaker()
    Session.configure(bind = engine)
    session = Session()

    return session
