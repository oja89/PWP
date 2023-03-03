# from sensorhub example
# https://github.com/enkwolf/pwp-course-sensorhub-api-example/blob/master/sensorhub/api.py

from flask import Blueprint
from flask_restful import Api

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

# after api creation to avoid circular imports
from boardgametracker.resources.player import PlayerCollection, PlayerItem
from boardgametracker.resources.team import TeamCollection, TeamItem
from boardgametracker.resources.game import GameCollection, GameItem
from boardgametracker.resources.match import MatchCollection, MatchItem
from boardgametracker.resources.ruleset import RulesetCollection, RulesetItem
from boardgametracker.resources.map import MapCollection, MapItem

api.add_resource(PlayerCollection, "/player/")
api.add_resource(PlayerItem, "/player/<player:player>/")

api.add_resource(TeamCollection, "/team/")
api.add_resource(TeamItem, "/team/<team:team>/")

api.add_resource(MatchCollection, "/match/")
api.add_resource(MatchItem, "/match/<match:match>/")

api.add_resource(GameCollection, "/game/")
api.add_resource(GameItem, "/game/<game:game>/")

# 2 routes for rulesets
api.add_resource(RulesetCollection, 
    "/ruleset/",
    "/game/<game:game>/ruleset/"
    )
api.add_resource(RulesetItem, 
    "/game/<game:game>/ruleset/"
    "/ruleset/<ruleset:ruleset>/"
    )
    
# 2 routes for map
api.add_resource(MapCollection,
    "/map/",
    "/game/<game:game>/map/"
    )
api.add_resource(MapItem,
    "/map/<map:map>/",
    "/game/<game:game>/map/<map:map>/"
    )