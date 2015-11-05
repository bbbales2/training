#%%
import sys
sys.path.append('/home/bbales2/scraping/training/')
import database

dbpath = '/home/bbales2/scraping/training/db.sql'

engine = database.getEngine(dbpath)
session = database.getSession(engine)

dbpath2 = '/home/bbales2/scraping/training/db2.sql'

engine2 = database.getEngine(dbpath2)
session2 = database.getSession(engine2)

#%%
figures = session.query(database.Figure).all()
#%%

import re
from miningTools import stemSentence
import gensim
import nltk
import shutil
import os

#%%

stopwords = stemSentence(' '.join(nltk.corpus.stopwords.words("english"))) + ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']

notword = re.compile(r'[^a-zA-Z -]')
loWords = []
for i, figure in enumerate(figures[0:500]):
    words = [word for word in stemSentence(figure.caption) if len(notword.sub('', word)) > 0 and word not in stopwords]

    loWords.append(words)

    print '{0}/{1}'.format(i, len(figures))
#%%
dictionary = gensim.corpora.dictionary.Dictionary(loWords)
dictionary.filter_extremes(no_below = 5, no_above = 0.5)
dictionary.compactify()
tfidf = gensim.models.tfidfmodel.TfidfModel(dictionary = dictionary)

dictionary.save('/home/bbales2/scraping/training/dictionary.db')
tfidf.save('/home/bbales2/scraping/training/tfidf.db')
#%%
for i, figure in enumerate(figures):
    keywords = tfidf[dictionary.doc2bow(loWords[i])]

    keywords = sorted(keywords, key = lambda x : x[1], reverse = True)

    keywords = [(dictionary[i], value) for i, value in keywords]

    session.add(database.FigureKeywords(keywords = keywords, figureId = figure.id))

    print '{0}/{1}'.format(i, len(figures))
    #print figure.caption
    #print keywords
#%%
session.commit()
#%%
corpus = [dictionary.doc2bow(text) for text in loWords[:]]
lda = gensim.models.ldamodel.LdaModel(corpus = corpus, num_topics = 20, id2word = dictionary, iterations = 500, passes = 5)

topicNames = []
for topic in lda.show_topics(20, 8, False, False):
    topicNames.append('_'.join([word[1] for word in topic]))

#%%
try:
    shutil.rmtree('/home/bbales2/scraping/ldaImages')
except:
    pass

os.mkdir('/home/bbales2/scraping/ldaImages')

for topicName in topicNames:
    os.mkdir(os.path.join('/home/bbales2/scraping/ldaImages', topicName))

for i, cor in enumerate(corpus):
    rankings = sorted(lda[cor], key = lambda x : x[1], reverse = True)

    topicName = topicNames[rankings[0][0]]
    score = int(numpy.floor(rankings[0][1] * 100))

    filename = figures[i].filename.replace('.sml', '.jpg')

    os.symlink('/home/bbales2/scraping/data/{0}/{1}'.format(figures[i].paper.data['pii'], filename), '/home/bbales2/scraping/ldaImages/{0}/{1}_{2}_{3}'.format(topicName, score, figures[i].id, filename))
