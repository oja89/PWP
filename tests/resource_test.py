# from https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/testing-flask-applications-part-2/

# which is based onhttp://flask.pocoo.org/docs/1.0/testing/

import datetime
import os
import pytest
import tempfile
import json

from werkzeug.datastructures import Headers
from flask.testing import FlaskClient
from sqlalchemy import event
from sqlalchemy.engine import Engine

from boardgametracker import create_app, db
from boardgametracker.models import Player, Match, Game, Map, Ruleset

from datetime import datetime

# from https://github.com/enkwolf/pwp-course-sensorhub-api-example/blob/master/tests/resource_test.py
# which from # https://stackoverflow.com/questions/16416001/set-http-headers-for-all-requests-in-a-flask-test

TEST_KEY = "thisisatestkey"


class AuthHeaderClient(FlaskClient):

    def open(self, *args, **kwargs):
        api_key_headers = Headers({
            'BGT-api-key': TEST_KEY
        })
        headers = kwargs.pop('headers', Headers())
        headers.extend(api_key_headers)
        kwargs['headers'] = headers
        return super().open(*args, **kwargs)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()



@pytest.fixture
def client():
    '''
    
    from https://github.com/enkwolf/pwp-course-sensorhub-api-example/blob/master/tests/resource_test.py
    '''
    db_fd, db_fname = tempfile.mkstemp()
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True
    }
    
    app = create_app(config)
    
    with app.app_context():
        db.create_all()
        _populate_db()
        
    app.test_client_class = AuthHeaderClient
    yield app.test_client()
    
    os.close(db_fd)
    #os.unlink(db_fname)
    # ^this gives error about permissions in win32
 
# Create a dummy database for testing 
def _populate_db():
    g = Game(name="CS:GO")
    db.session.add(g)
    g = Game(name="Battlefield")
    db.session.add(g)
    
    r = Ruleset(name="competitive", game_id=1)
    db.session.add(r)
    r = Ruleset(name="domination", game_id=2)
    db.session.add(r)
    
    map = Map(name="dust", game_id=1)
    db.session.add(map)
    map = Map(name="verdun", game_id=2)
    db.session.add(map)
    map = Map(name="amiens", game_id=2)
    db.session.add(map)
    map = Map(name="sauna", game_id=1)
    db.session.add(map)
    
    match = Match(date=datetime.now(), turns=30, game_id=1, ruleset_id=1, map_id=1)
    db.session.add(match)
    match = Match(date=datetime.now(), turns=2, game_id=2, ruleset_id=1, map_id=2)
    db.session.add(match)
    
    for i in range(1, 4):
        p = Player(
            name=f"John-{i}"
            
        )
        db.session.add(p)
    db.session.commit()

def _get_player_json():
    """
    Creates a valid player JSON object to be used for PUT and POST tests.
    """
    
    return {"name": "John"}
    
def _get_uplayer_json():
    """
    Creates a unvalid player JSON object to be used for PUT and POST tests.
    """
    
    return {"name": 123}
    
def _get_match_json():
    """
    Creates a valid match JSON object to be used for PUT and POST tests.
    """
    
    return{"date":"2022-12-25", "turns":500, "game_id":1, "ruleset_id":1, ":map_id":1}
    
def _get_game_json():
    """
    Creates a valid game JSON object to be used for PUT and POST tests.
    """
    
    return{"name": "newgame"}
    
def _get_map_json():
    """
    Creates a valid game JSON object to be used for PUT and POST tests.
    """
    
    return{"name":"newmap", "game_id":1}
    
class TestPlayerCollection(object):

    RESOURCE_URL = "/api/player/"
    
    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert len(body) == 3
        for item in body:
            assert "name" in item
            
    def test_post_valid_request(self, client):
        valid = _get_player_json()
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        
        # Name is unique. Check that can't add with same name
        valid["name"] = "John-1"
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409

        # TODO CREATE KEYERROR

        
class TestPlayerItem(object):

    RESOURCE_URL = "/api/player/John-1/"
    INVALID_URL = "/api/player/John-100/"
        
    def test_delete_valid(self, client):
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 404      
        
    def test_delete_missing(self, client):
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404  
        
    # TODO TEST PUT
    
    
class TestMatchCollection(object):
    RESOURCE_URL = "/api/match/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert len(body) == 2
        for item in body:
            assert "date" in item
            assert "turns" in item
            assert "results" in item
            assert "game_name" in item
            assert "game_name" in item
            assert "map_name" in item
            assert "ruleset_name" in item
            
    def test_post_valid_request(self, client):
        valid = _get_match_json()
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201


        # TODO CREATE KEYERROR
    
class TestMatchItem(object):

    RESOURCE_URL = "/api/match/1/"
    INVALID_URL = "/api/match/x/"
        
    def test_delete_valid(self, client):
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 404      
        
    def test_delete_missing(self, client):
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404  
        
    # TODO TEST PUT

class TestGameCollection(object):
    RESOURCE_URL = "/api/game/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert len(body) == 2
        for item in body:
            assert "name" in item
            
    def test_post_valid_request(self, client):
        valid = _get_game_json()
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201


        # TODO CREATE KEYERROR
    
class TestGameItem(object):

    RESOURCE_URL = "/api/game/CS:GO/"
    INVALID_URL = "/api/game/invalid/"
        
    def test_delete_valid(self, client):
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 404      
        
    def test_delete_missing(self, client):
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404  
        
    # TODO TEST PUT
    
class TestMapCollection(object):
    RESOURCE_URL = "/api/map/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert len(body) == 4
        for item in body:
            assert "name" in item
            assert "id" in item
            assert "game" in item
            assert "matches" in item
            
    def test_post_valid_request(self, client):
        valid = _get_map_json()
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201


        # TODO CREATE KEYERROR
    
class TestMapItem(object):

    RESOURCE_URL = "/api/map/1/"
    INVALID_URL = "/api/map/invalid/"
        
    def test_delete_valid(self, client):
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 404      
        
    def test_delete_missing(self, client):
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404  
        
    # TODO TEST PUT