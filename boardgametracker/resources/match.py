"""
Functions for match class objects

from sensorhub example
https://github.com/enkwolf/pwp-course-sensorhub-api-example/blob/master/sensorhub/resources/sensor.py
"""
import json
from datetime import datetime

from boardgametracker import db, cache
from boardgametracker.constants import *
from boardgametracker.models import Match, PlayerResult, TeamResult
from boardgametracker.utils import BGTBuilder
from flask import Response, request, abort, url_for
from flask_restful import Resource
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import Conflict, BadRequest, UnsupportedMediaType


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

        modified to use MasonBuilder after ex3

        """

        body = BGTBuilder()
        body.add_namespace("BGT", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.matchcollection"))
        body.add_control_add_match()
        body["items"] = []

        for match in Match.query.all():
            # use serializer and BGTBuilder
            item = BGTBuilder(match.serialize(long=True))
            # create controls for all items
            item.add_control("self", url_for("api.match", match=match.id))
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
        """
        if not request.mimetype == "application/json":
            raise UnsupportedMediaType
        try:
            validate(request.json, Match.get_schema())
        except ValidationError as err:
            raise BadRequest(description=str(err))

        # TODO: serializer?
        # TODO: game?
        match = Match(
            date=datetime.fromisoformat(request.json["date"]),
            turns=request.json["turns"]
        )
        try:
            db.session.add(match)
            db.session.commit()

        # If a field is missing raise except
        except KeyError:
            db.session.rollback()
            abort(400)

        return Response(status=201, headers={
            "Location": url_for("api.match", match=match.id)
                }
            )


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
        """
        # get match, use serializer for data
        db_match = Match.query.filter_by(id=match).first()
        body = BGTBuilder(db_match.serialize(long=True))
        body.add_namespace("BGT", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.match", match=body["id"]))
        body.add_control("profile", MATCH_PROFILE)
        body.add_control_put("edit", "TODO:title", url_for("api.match", match=body["id"]),
                             schema=Match.get_schema())
        body.add_control_match_collection()

        # do controls for results
        # do not use them as their own resource anymore
        # TODO: change urls, titles, check the ctrl-name
        # TODO: probably need match id into the ctrl-name?
        # TODO: results need their id in the put?

        # if result exists, add route to edit result
        if body["results"]["player_results"] is not None:
            # for each "row" in this games results:
            for row, list in enumerate(body["results"]["player_results"]):
                body.add_control_put(f"BGT:edit-player-result-{row}",
                                     f"TODO:edit-pres-title-{row}",
                                     f"TODO:edit-pres-url-{row}",
                                     PlayerResult.get_schema())

        # always add "add" control for a row of results
        body.add_control_post("BGT:add-player-result",
                              "TODO:add-pres-title",
                              "TODO:add-pres-url",
                              PlayerResult.get_schema())

        # if result exists, add route to edit result
        if body["results"]["team_results"] is not None:
            for row, list in enumerate(body["results"]["team_results"]):
                body.add_control_put(f"BGT:edit-team-result-{row}",
                                     f"TODO:edit-tres-title-{row}",
                                     f"TODO:edit-tres-url-{row}",
                                     TeamResult.get_schema())

        # always add "add" control for a row of results
        body.add_control_post("BGT:add-team-result",
                              "TODO:add-tres-title",
                              "TODO:add-tres-url",
                              TeamResult.get_schema())

        response = Response(json.dumps(body), 200, mimetype=MASON)
        return response

    def put(self, match):
        """
        Change information of a match
        From exercise 2,
        https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/implementing-rest-apis-with-flask/
        """
        if not request.mimetype == "application/json":
            raise UnsupportedMediaType
        try:
            validate(request.json, Match.get_schema())
        except ValidationError as err:
            raise BadRequest(description=str(err))

        # match-info has date and turns,
        # TODO: and game?
        match.date = datetime.fromisoformat(request.json["date"])
        match.turns = request.json["turns"]

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise Conflict(409)

        return Response(status=204)

    def delete(self, match):
        """
        Delete a match
        From
        https://github.com/enkwolf/pwp-course-sensorhub-api-example/blob/master/sensorhub/resources/sensor.py
        """
        db.session.delete(match)
        db.session.commit()

        return Response(status=204)
