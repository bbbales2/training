#%%
import mldb2
import sys
import os
import re
appDir = '/home/bbales2/scraping/training/'
sys.path.append(appDir)
import database

session, engine = mldb2.getSession()

figures = session.query(mldb2.Figure).all()
targetEngine = database.getEngine(os.path.join(appDir, 'db.sql'))
targetSession = database.getSession(targetEngine)

#targetSession.query(database.Figure).delete()

#%%

for i, figure in enumerate(figures):
    filename = figure.filename.replace('.sml', '.jpg')
    paperUrl = 'http://www.sciencedirect.com/science/article/pii/{0}'.format(re.sub('[^A-Z0-9]', '', figure.paper.data['pii']))
    caption = ' '.join([s.string for s in figure.sentences])
    url = '/static/papers/{0}/{1}'.format(figure.paper.data['pii'], filename)
    targetSession.add(database.Figure(caption = caption, url = url, paperUrl = paperUrl))
    if i % 1000 == 0:
        print 'commit'
        targetSession.commit()
    print '{0}/{1}'.format(i, len(figures))
targetSession.commit()