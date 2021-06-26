from __future__ import annotations

import hashlib
from typing import List
from datetime import datetime

from mongoengine import signals
from flask_mongoengine import MongoEngine
from mongoengine.errors import DoesNotExist
from flask import Flask, request, Response, render_template

app = Flask(__name__)
app.config["MONGODB_SETTINGS"] = {
    "port": 27017,
    "db": "hoshdb",
    "host": "localhost",
}

db = MongoEngine()
db.init_app(app)


class Entry(db.DynamicDocument):

    timestamp = db.DateTimeField(default=datetime.now)
    word = db.StringField(max_length=200, required=True)

    HASH_TYPES: List[str] = [
        "md4",
        "md5",
        "sha1",
        "sha224",
        "sha256",
        "sha384",
        "sha512",
        "sha3_224",
        "sha3_256",
    ]

    meta = {
        "indexes": [
            {"fields": ["word"], "unique": True},
        ],
    }

    @classmethod
    def pre_save(cls, _, document: Entry, **__):
        word = document.word.encode("utf-8")
        for hash_type in cls.HASH_TYPES:
            setattr(document, hash_type, hashlib.new(hash_type, word).hexdigest())


signals.pre_save.connect(Entry.pre_save, sender=Entry)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search")
def search():
    q = request.args.get('word')
    try:
        entry = Entry.objects(word=q).get()
    except DoesNotExist:
        entry = Entry(word=q).save()
    finally:
        return Response(entry.to_json(), mimetype='application/json')


if __name__ == "__main__":
    app.run(debug=True)
