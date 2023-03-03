# from sensorhub example
# https://github.com/enkwolf/pwp-course-sensorhub-api-example/blob/master/sensorhub/resources/sensor.py

import json
from jsonschema import validate, ValidationError
from flask import Response, request, url_for, abort
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from boardgametracker.models import Map
from boardgametracker.models import Game
from boardgametracker import db
from boardgametracker.constants import *
import datetime
from datetime import datetime
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType
from boardgametracker import cache

class MapCollection(Resource):
    @cache.cached(timeout=5)
    def get(self, game=None):
        '''
        Get all maps
        If game given, all for that game
        
        From exercise 2,
        https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/implementing-rest-apis-with-flask/
        '''
        data_object = []

        # do the query for all
        if game is None:
            maps = Map.query.all()
            
        # do the query for given game
        else:
            thisgame = game.serialize()
            maps = Map.query.filter_by(game_id=thisgame["id"])

        for map in maps:
            data_object.append({
                'name': map.name,
                'game_id': map.game_id
            })
            
        response = data_object
        
        return response, 200
    
    def post(self, game=None):
        '''
        Add a new map
        Cannot add a map without a game
        
        From exercise 2,
        https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/implementing-rest-apis-with-flask/
        '''
        
        if game is None:
        # check the correct error message
        # game needs to exists
            abort(400)
        else:
            thisgame = game.serialize()
        
        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, Map.get_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))
        try:
            map = Map(
                name=request.json["name"],
                game_id=thisgame["id"]
            )
            db.session.add(map)
            db.session.commit()
        except KeyError:
            abort(400)

        return Response(status=201)
    
class MapItem(Resource):
    def get(self, map):
        '''
        Get information about a map
        
        
        From exercise 2 material,
        https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/implementing-rest-apis-with-flask/
        '''

        return map.serialize()
        
    def put(self, map):
        '''
        Change information of a map
        
        
        From exercise 2,
        https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/implementing-rest-apis-with-flask/
        '''
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json, Map.get_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        map.deserialize(request.json)
        try:
            db.session.add(map)
            db.session.commit()
        except IntegrityError:
            raise Conflict(409)
            
    def delete(self, map):
        '''
        Delete a map
        
        From https://github.com/enkwolf/pwp-course-sensorhub-api-example/blob/master/sensorhub/resources/sensor.py
        ''' 
        db.session.delete(map)
        db.session.commit()

        return Response(status=204)
