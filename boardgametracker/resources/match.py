"""
Functions for match class objects

from sensorhub example
https://github.com/enkwolf/pwp-course-sensorhub-api-example/blob/master/sensorhub/resources/sensor.py
"""
import json
from datetime import datetime

from flask import Response, request, abort, url_for
from flask_restful import Resource
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import Conflict, BadRequest, UnsupportedMediaType

from boardgametracker import db, cache
from boardgametracker.constants import *
from boardgametracker.models import Match, PlayerResult, TeamResult, Game
from boardgametracker.utils import BGTBuilder


class MatchCollection(Resource):
    """
    Collection of matches
    """

    @cache.cached(timeout=5)
    def get(self):
        """
        Get all matches
        From exercise 2,
        https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/implementing-rest-apis-with-flask/

        modified to use MasonBuilder after ex3, and added YAML
        https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/exercise-3-api-documentation-and-hypermedia/
        ---
        tags:
            - match
        description: Get all matches
        responses:
            200:
                description: List of matches
                content:
                    application/json:
                        example:
                            - date: 31.12.2012T20:30:00
                              turns: 1
                              game_name: CS:GO
                              ruleset_name: Competitive
                              map_name: Dust
        """

        body = BGTBuilder()
        body.add_namespace("BGT", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.matchcollection"))
        body.add_control_all_matches()
        body.add_control_all_players()
        body.add_control_all_teams()
        body.add_control_all_games()
        body.add_control_add_match()
        body["items"] = []

        for match in Match.query.all():
            # use serializer and BGTBuilder
            item = BGTBuilder(match.serialize(long=True))
            # create controls for all items
            item.add_control("self", url_for("api.matchitem", match=match))
            item.add_control("profile", MATCH_PROFILE)
            body["items"].append(item)

        response = Response(json.dumps(body), 200, mimetype=MASON)

        return response

    def post(self):
        """
        Add a new match

        From exercise 2,
        https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/implementing-rest-apis-with-flask/

        Added also Mason stuff from:
        https://github.com/enkwolf/pwp-course-sensorhub-api-example/blob/master/sensorhub/resources/sensor.py

        And OpenAPI stuff from:
        https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/exercise-3-api-documentation-and-hypermedia/#openapi-structure

        OpenAPI:
        ---
        tags:
            - match
        description: Add a new match
        requestBody:
            description: JSON containing data for the match
            content:
                application/json:
                    schema:
                        $ref: '#/components/schemas/Match'
                    example:
                        date: '2022-12-25 00:00:00.000000'
                        turns: 21
                        game_id: 1
                        ruleset_id: 1
                        map_id: 2

        responses:
            201:
                description: Match added
                headers:
                    Location:
                        description: URI of the match
                        schema:
                            type: string
                        example: "asdfadf"
            400:
                description: Key error
        """
        if not request.mimetype == JSON:
            raise UnsupportedMediaType
        try:
            validate(request.json, Match.get_schema())
        except ValidationError as err:
            raise BadRequest(description=str(err))

        # TODO: serializer?
        # TODO: game?
        match = Match(
            date=datetime.fromisoformat(request.json["date"]),
            turns=request.json["turns"],
            game_id=request.json["game_id"],
            ruleset_id=request.json["ruleset_id"],
            map_id=request.json["map_id"]

        )
        try:
            db.session.add(match)
            db.session.commit()

        # If a field is missing raise except
        except KeyError:
            db.session.rollback()
            abort(400)

        return Response(status=201, headers={
            "Location": url_for("api.matchitem", match=match)
                })



class MatchItem(Resource):
    """
    One item of match
    """

    def get(self, match):
        """
        Get information about a match
        From exercise 2 material,
        https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/implementing-rest-apis-with-flask/

        Added also Mason stuff from
        https://github.com/enkwolf/pwp-course-sensorhub-api-example/blob/master/sensorhub/resources/sensor.py

        ---
        tags:
            - match
        description: Get one match
        parameters:
            - $ref: '#/components/parameters/match_id'
        responses:
            200:
                description: Match's information
                content:
                    application/json:
                        example:
                            - date: 2008-08-12T12:20:30
                              turns: 5
                              game_name: CS:GO
                              map_name: Sauna
                              ruleset_name: Gungame
                              player_results:
                                player: John
                                team: Foxes
                                points: 20
                              team_results:
        """
        # this serializer cannot give the results, the controls add them again
        body = BGTBuilder()
        body["item"] = BGTBuilder(match.serialize(long=True))
        body.add_namespace("BGT", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.matchitem", match=match))
        body.add_control("profile", MATCH_PROFILE)
        body.add_control_put("edit",
                             "Edit this match",
                             url_for("api.matchitem", match=match),
                             schema=Match.get_schema())
        body.add_control_get_game(game=match.game)
        body.add_control_all_matches()

        # do controls for results

        # if player_result exists, add route to edit player_result
        if match.player_result is not None:
            body["player_results"] = []
            # for each "row" in this game's results:
            for player_result in match.player_result:
                item = BGTBuilder(player_result.serialize(long=False))
                item.add_control("self", url_for("api.playerresultitem", player_result=player_result, match=match))
                item.add_control_put("edit",
                                     "Edit this row of playerresults",
                                     url_for("api.playerresultitem", player_result=player_result, match=match),
                                     PlayerResult.get_schema()
                                     )
                body["player_results"].append(item)

        # always add "add" control for a row of results
        # this is not inside results, should it be?
        body.add_control_post("BGT:add-player-result",
                              "Add a row of playerresults",
                              url_for("api.playerresultcollection", match=match),
                              PlayerResult.get_schema())

        # # if result exists, add route to edit result
        if match.team_result is not None:
            body["team_results"] = []
            for team_result in match.team_result:
                item = BGTBuilder(team_result.serialize(long=False))
                item.add_control("self", url_for("api.teamresultitem", team_result=team_result, match=match))
                item.add_control_put("edit",
                                     "Edit this row of teamresults",
                                     url_for("api.teamresultitem", team_result=team_result, match=match),
                                     TeamResult.get_schema()
                                     )
                body["team_results"].append(item)

        # always add "add" control for a row of results
        # this is not inside results, should it be?
        body.add_control_post("BGT:add-team-result",
                              "Add a row of teamresults",
                              url_for("api.teamresultcollection", match=match),
                              TeamResult.get_schema()
                              )

        response = Response(json.dumps(body), 200, mimetype=MASON)
        return response

    def put(self, match):
        """
        Change information of a match
        From exercise 2,
        https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/implementing-rest-apis-with-flask/

        ---
        tags:
            - match
        description: Modify a match
        parameters:
            - $ref: '#/components/parameters/match_id'
        requestBody:
            description: JSON containing new data for the match
            content:
                application/json:
                    schema:
                        $ref: '#/components/schemas/Match'
                    example:
                        date: "2008-08-12T12:20:30"
                        turns: 20
                        game_id: 2
                        ruleset_id: 1
                        map_id: 5
        responses:
            204:
                description: Match modified, return new URI
                headers:
                    Location:
                        description: URI of the match
                        schema:
                            type: string
                        example: "/api/Game/3"
            409:
                description: Integrity error
        """
        if not request.mimetype == JSON:
            raise UnsupportedMediaType
        try:
            validate(request.json, Match.get_schema())
        except ValidationError as err:
            raise BadRequest(description=str(err))

        # match-info has date and turns,
        # TODO: and game?
        match.date = datetime.fromisoformat(request.json["date"])
        match.turns = request.json["turns"]
        match.game_id = request.json["game_id"]
        match.ruleset_id = request.json["ruleset_id"]
        match.map_id = request.json["map_id"]

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise Conflict(409)

        return Response(status=204, headers={
            "Location": url_for("api.matchitem", match=match)
                }
                        )

    def delete(self, match):
        """
        Delete a match
        From
        https://github.com/enkwolf/pwp-course-sensorhub-api-example/blob/master/sensorhub/resources/sensor.py

        ---
        tags:
            - match
        description: Delete a match
        parameters:
            - $ref: '#/components/parameters/match_id'
        responses:
            204:
                description: Match deleted, nothing to return
        """

        db.session.delete(match)
        db.session.commit()

        return Response(status=204)
