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

import subprocess

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

app = flask.Flask('training')
app.config.from_object({ 'DEBUG' : True,
                         'SECRET_KEY' : 'something',
                         'SESSION_TYPE' : 'filesystem' })

login_manager.login_view = '/login'

def reload_rankings():
    global fixIndex
    global rankings
    global categories
    global rankByCat

    figIndex = 0
    #figures = [figure.id for figure in database.getSession(engine).query(database.Figure).all()]

    f = open('rankings', 'r')
    rankings = json.loads(f.read())
    f.close()

    categories = rankings.items()[0][1].keys()

    rankByCat = {}
    for cat in categories:
        rankByCat[cat] = sorted(rankings.items(), key = lambda x : x[1][cat], reverse = True)

reload_rankings()

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

    if username == 'garfield':
        user = flask.g.session.query(database.User).filter(database.User.name == username).first()

        if not user:
            user = database.User(name = username)
            flask.g.session.add(user)
            flask.g.session.commit()

        flask.ext.login.login_user(user)

        flask.flash('Logged in successfully.')

        return flask.redirect('/gallery')

    return flask.render_template('login.html')

@app.route('/recompute', methods = ['GET'])
@flask.ext.login.login_required
def recompute():
    subprocess.call("python train.py".split())

    reload_rankings()

    return flask.redirect('/gallery')

@app.route('/logout', methods = ['GET', 'POST'])
@flask.ext.login.login_required
def logout():
    flask.ext.login.logout_user()
    return flask.redirect('/gallery')

@app.route('/doSegmentation', methods=['POST'])
@flask.ext.login.login_required
def doSegmentation():
    segmentationData = json.loads(flask.request.form['data'])

    figure = flask.g.session.query(database.Figure).get(segmentationData['id'])

    if figure:
        flask.g.session.add(database.Segmentation(data = segmentationData['lines'], userId = flask.ext.login.current_user.get_id(), figureId = segmentationData['id']))

    return flask.json.jsonify({})

@app.route('/removeClassifications', methods=['POST'])
@flask.ext.login.login_required
def removeClassification():
    classificationData = json.loads(flask.request.form['data'])

    figure = flask.g.session.query(database.Figure).get(classificationData['id'])

    for cls in figure.classifications:
        flask.g.session.delete(cls)

    return flask.json.jsonify({})

@app.route('/doClassification', methods=['POST'])
@flask.ext.login.login_required
def doClassification():
    classificationData = json.loads(flask.request.form['data'])

    figure = flask.g.session.query(database.Figure).get(classificationData['id'])

    if figure:
        flask.g.session.add(database.Classification(data = classificationData['categories'], userId = flask.ext.login.current_user.get_id(), figureId = classificationData['id']))

    return flask.json.jsonify({})

@app.route('/save_notes', methods = ['POST'])
@flask.ext.login.login_required
def save_notes():
    figureId = flask.request.form.get('figureId', None)
    string = flask.request.form.get('string', None)
    category = flask.request.form.get('category', None)

    figure = flask.g.session.query(database.Figure).get(figureId)

    for note in figure.notes:
        flask.g.session.delete(note)

    for classification in figure.classifications:
        flask.g.session.delete(classification)

    flask.g.session.add(database.Classification(data = [category], userId = flask.ext.login.current_user.get_id(), figureId = figureId))

    note = database.Note(string = string, figureId = figureId)
    flask.g.session.add(note)

    return flask.json.jsonify({})

@app.route('/get_info', methods = ['POST'])
@flask.ext.login.login_required
def get_info():
    figureId = flask.request.form.get('figureId', None)
    token = flask.request.form.get('token', None)

    figure = flask.g.session.query(database.Figure).get(figureId)

    if len(figure.notes) == 0:
        notes = { 'id' : None,
                  'string' : None }
    else:
        notes = { 'id' : figure.notes[0].id,
                  'string' : figure.notes[0].string }

    return flask.json.jsonify({ 'figureId' : figureId,
                                'token' : token,
                                'notes' : notes,
                                'caption' : figure.caption,
                                'category' : figure.classifications[-1].data[0] if len(figure.classifications) > 0 else '',
                                'paperUrl' : figure.paperUrl })

@app.route('/')
@flask.ext.login.login_required
def index():
    global figIndex
    return flask.redirect('/gallery')

    figureId = flask.request.args.get('figureId', None)

    if not figureId:
        while 1:
            rank = rankByCat['superalloy microstructure'][figIndex]

            figure = flask.g.session.query(database.Figure).get(rank[0])
            
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
                                   'rankings' : rank[1] }),
             'paperUrl' : figure.paperUrl,
             'caption' : figure.caption }

    return flask.render_template('index.html', **data)

@app.route('/gallery_page')
@flask.ext.login.login_required
def gallery_page():
    category = flask.request.args.get('category', None)
    start = int(flask.request.args.get('start', None))
    predict = flask.request.args.get('predict', None) == 'true'
    token = flask.request.args.get('token', None)

    if not predict:
        figureIds = []
        for cls in flask.g.session.query(database.Classification).all():
            if cls.data[0] == category:
                figureIds.append(cls.figureId)

        total = len(figureIds)
        figureIds = figureIds[start : start + 39]
    else:
        figureIds = [figureId for figureId, rank in rankByCat[category][start : start + 39]]
        total = len(rankings)

    figData = []
    for figureId in figureIds:
        figure = flask.g.session.query(database.Figure).get(figureId)

        correct = False
        if len(figure.classifications) > 0:
            correct = figure.classifications[-1].data[0] == category

        figData.append( { 'token' : token,
                          'url' : figure.url,
                          'id' : figure.id,
                          'paperUrl' : figure.paperUrl,
                          #'rankings' : rank,
                          'classified' : len(figure.classifications) > 0,
                          'correct' : correct } )

    return flask.json.jsonify(figures = figData, total = total)

@app.route('/gallery')
@flask.ext.login.login_required
def gallery():
    data = { 'segmentations' : len(flask.ext.login.current_user.segmentations),
             'classifications' : len(flask.ext.login.current_user.classifications),
             'username' : flask.ext.login.current_user.name,
             'categories' : sorted(categories, key = lambda x : x[:5] == 'super', reverse = True) }
    #'data' : json.dumps({  })

    return flask.render_template('gallery.html', **data)

if __name__ == '__main__':
    app.secret_key = 'yadydydydyd'
    app.config['SESSION_TYPE'] = 'filesystem'

    login_manager.init_app(app)
    session.init_app(app)

    app.run(host='frog.cs.ucsb.edu', debug = True)#)
