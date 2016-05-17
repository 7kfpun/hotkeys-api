import csv
import logging
import os
import uuid
from datetime import datetime

import requests
from flask import Flask, Response, jsonify, request
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy_utils import UUIDType, force_auto_coercion

force_auto_coercion()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

DEBUG = True


class Hotkey(db.Model):

    """Hotket model."""

    id = db.Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    order = db.Column(db.Integer)
    name = db.Column(db.String)
    platform = db.Column(db.String)
    group = db.Column(db.String)
    type = db.Column(db.String)
    uri = db.Column(db.String)
    shortcut = db.Column(db.String)
    description = db.Column(db.String)

    def __init__(self, order, name, platform, group, type_, uri, shortcut, description):
        """__init__."""
        self.order = order
        self.name = name
        self.platform = platform
        self.group = group
        self.type = type_
        self.uri = uri
        self.shortcut = shortcut
        self.description = description

    def __str__(self):
        """__str__."""
        return self.shortcut


class SearchUrl(db.Model):

    """ChatRecord model."""

    id = db.Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String)
    platform = db.Column(db.String)
    group = db.Column(db.String)
    type = db.Column(db.String)
    url = db.Column(db.Text)
    created_datetime = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, name, platform, group, type_, url):
        """__init__."""
        self.name = name
        self.platform = platform
        self.group = group
        self.type = type_
        self.url = url

    def __str__(self):
        """__str__."""
        return self.url


@app.route('/', methods=['GET'])
def hello():
    """Hello world."""
    return 'Hello world'


def clean_uris(url):
    """Clean uris."""
    url = url.replace('http://', '').replace('https://', '')
    uris = url.split('/', 3)
    if len(uris) <= 1:
        return uris
    elif len(uris) == 2:
        return [uris[0], '/'.join([uris[0], uris[1]])]
    else:
        return [uris[0], '/'.join([uris[0], uris[1]]), '/'.join([uris[0], uris[1], uris[2]])]


@app.route('/api/hotkeys/', methods=['GET'])
def get_hotkets():
    """GET hotkeys."""
    name = request.args.get('name')
    platform = request.args.get('platform')
    group = request.args.get('group')
    type_ = request.args.get('type')
    url = request.args.get('url', '')

    if name or platform or group or type_ or url:
        search_url = SearchUrl(name, platform, group, type_, url)
        db.session.add(search_url)
        db.session.commit()

        uris = clean_uris(url)
        print(uris)
        logging.info(uris)
        query = Hotkey.query.filter(
            Hotkey.uri.in_(uris)
        ).order_by(Hotkey.group).order_by(Hotkey.order)

        #  return jsonify(results=query.all())
        return jsonify(results=[{
            'id': h.id,
            'order': h.order,
            'name': h.name,
            'platform': h.platform,
            'group': h.group,
            'type': h.type,
            'uri': h.uri,
            'shortcut': h.shortcut,
            'description': h.description,
        } for h in query.all()])

    else:
        return jsonify(results=[])


@app.route('/api/hotkeys/pull_update/', methods=['GET'])
def pull_update():
    """Pull_update."""
    CSV_URL = 'http://docs.google.com/spreadsheets/d/1JH-eQdWAXx70T5XkGTfz4jgXTMvG9Fpm96ANnyRpnkQ/pub?gid=0&single=true&output=csv'  # noqa

    with requests.Session() as s:
        download = s.get(CSV_URL)

        decoded_content = download.content.decode('utf-8')

        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        my_list = list(cr)

        Hotkey.query.delete()

        for row in my_list[1:]:
            logging.info(row)
            print(row)
            hotkey = Hotkey(*row)
            db.session.add(hotkey)
            db.session.commit()

    return Response(status=200)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=DEBUG)
