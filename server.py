import gensim
import json
import numpy
import traceback
import os
import sqlalchemy.orm
import itertools
import md5
import database

import functools
import flask
import flask.ext.login
import flask.ext.session

login_manager = flask.ext.login.LoginManager()
session = flask.ext.session.Session()

appDir = os.path.abspath(os.path.dirname(__file__))
engine = database.getEngine(os.path.join(appDir, 'db.sql'))

def logexceptions(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            traceback.print_exc()

            return { 'status' : False, 'msg' : str(e) }

    return inner

app = flask.Flask('digibookie')
app.config.from_object({ 'DEBUG' : True,
                         'SECRET_KEY' : 'something',
                         'SESSION_TYPE' : 'filesystem' })

login_manager.login_view = '/login'

figIndex = 0
figures = [figure.id for figure in database.getSession(engine).query(database.Figure).all()]

#tmpArray = enumerate()

#for i, figure in tmpArray:
#    print i
#    if len(figure.classifications) + len(figure.segmentations) == 0:
#        figures.append(figure.id)

@login_manager.user_loader
def load_user(user_id):
    return flask.g.session.query(database.User).get(user_id)

@app.before_request
def before_request():
    flask.g.session = database.getSession(engine)

@app.teardown_request
def teardown_request(exception):
    session = getattr(flask.g, 'session', None)
    if session is not None:
        session.commit()
        session.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    username = flask.request.args.get('username', None)

    if username:
        user = flask.g.session.query(database.User).filter(database.User.name == username).first()

        if not user:
            user = database.User(name = username)
            flask.g.session.add(user)
            flask.g.session.commit()

        flask.ext.login.login_user(user)

        flask.flash('Logged in successfully.')

        return flask.redirect('/')

    return flask.render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
@flask.ext.login.login_required
def logout():
    flask.ext.login.logout_user()
    return flask.redirect('/login')

@app.route('/doSegmentation', methods=['POST'])
@flask.ext.login.login_required
def doSegmentation():
    segmentationData = json.loads(flask.request.form['data'])

    figure = flask.g.session.query(database.Figure).get(segmentationData['id'])

    if figure:
        flask.g.session.add(database.Segmentation(data = segmentationData['lines'], userId = flask.ext.login.current_user.get_id(), figureId = segmentationData['id']))

    return flask.json.jsonify({})

@app.route('/doClassification', methods=['POST'])
@flask.ext.login.login_required
def doClassification():
    classificationData = json.loads(flask.request.form['data'])

    figure = flask.g.session.query(database.Figure).get(classificationData['id'])

    if figure:
        flask.g.session.add(database.Classification(data = classificationData['categories'], userId = flask.ext.login.current_user.get_id(), figureId = classificationData['id']))

    return flask.json.jsonify({})

@app.route('/')
@flask.ext.login.login_required
def index():
    global figIndex

    figureId = flask.request.args.get('figureId', None)

    if not figureId:
        while 1:
            figure = flask.g.session.query(database.Figure).get(figures[figIndex])
            
            figIndex += 1
            
            if len(figure.classifications) + len(figure.segmentations) == 0:
                if os.path.exists(os.path.join(appDir, figure.url[1:])):
                    break
    else:
        figure = flask.g.session.query(database.Figure).get(figureId)

    data = { 'segmentations' : len(flask.ext.login.current_user.segmentations),
             'classifications' : len(flask.ext.login.current_user.classifications),
             'username' : flask.ext.login.current_user.name,
             'data' : json.dumps({ 'url' : figure.url,
                                   'id' : figure.id,
                                   'keywords' : figure.keywords[0].keywords }),
             'paperUrl' : figure.paperUrl,
             'caption' : figure.caption }

    return flask.render_template('index.html', **data)

if __name__ == '__main__':
    app.secret_key = 'yadydydydyd'
    app.config['SESSION_TYPE'] = 'filesystem'

    login_manager.init_app(app)
    session.init_app(app)

    app.run(debug = True)
