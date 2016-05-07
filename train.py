#%%
import numpy
import matplotlib.pyplot as plt
import sklearn.linear_model

import os

os.chdir('/home/bbales2/scraping/training')
import database

engine = database.getEngine('db.sql')
session = database.getSession(engine)
#%%
figures = session.query(database.Figure).all()

classifications = session.query(database.Classification).all()

categories = set()

for cls in classifications:
    for ca in cls.data:
        if len(ca) > 0:
            categories.add(ca)

categories = sorted(list(categories))
categories = dict([(name, i) for i, name in enumerate(categories)])

data = []
target = []

for i, cls in enumerate(classifications):
    if len(cls.data[0]) > 0:
        data.append(cls.figure.features[0].data)

        target.append(categories[cls.data[0]])

data = numpy.array(data)
target = numpy.array(target)
#%%
import sklearn.datasets
import sklearn.cross_validation
lgr = sklearn.linear_model.LogisticRegression(C = 0.001)
lgr.fit(data, target)
scores = sklearn.cross_validation.cross_val_score(lgr, data, target, cv = 3)
print scores
#%%
output = {}

labels = [t[0] for t in sorted(categories.items(), key = lambda x : x[1])]

#for i, fig in enumerate(figures):
#    if len(fig.features) > 0:
#        output[fig.id] = dict(zip(labels, lgr.predict_proba(fig.features[0].data)[0]))

features = session.query(database.FigureFeatures).all()

for i, feature in enumerate(features):
    output[feature.figureId] = dict(zip(labels, lgr.predict_proba(numpy.array([feature.data]))[0]))

    print "{0}/{1}".format(i, len(features))

import json

f = open('rankings', 'w')
f.write(json.dumps(output))
f.close()
