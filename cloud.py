# coding: utf-8

from leancloud import Engine

from app import app

from leancloud import Query

import leancloud
#from leancloud import HttpsRedirectMiddleware
#app = HttpsRedirectMiddleware(app)
#engine = Engine(app)


@engine.define
def hello(**params):
    if 'name' in params:
        return 'Hello, {}!'.format(params['name'])
    else:
        return 'Hello, 720testCloud!'
@engine.define
def averageStars(movie):
    sum = 0
    query = Query('Review')
    try:
        reviews = query.find()
    except leancloud.LeanCloudError, e:
        print e
        raise e
    for review in reviews:
        sum += review.get('starts')
    return sum / len(reviews)
