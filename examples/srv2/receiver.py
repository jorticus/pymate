
__author__ = 'Jared Sanson <jared@jared.geek.nz>'
__version__ = 'v0.1'

from flask import Flask, abort, jsonify, make_response, request
from flask.json import JSONEncoder
import sqlalchemy as sql
import sqlalchemy.orm
from contextlib import contextmanager
from datetime import datetime
from .models import initialize_db, MxStatus, MxLogPage, FxStatus

engine = initialize_db()
Session = sql.orm.sessionmaker(bind=engine)

@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class CustomJSONEncoder(JSONEncoder):
    def default(self, o):
        try:
            if isinstance(o, datetime):
                return o.isoformat()
            if isinstance(o, MxStatus):
                return o.to_json()
            if isinstance(o, MxLogPage):
                return o.to_json()
            if isinstance(o, FxStatus):
                return o.to_json()
            iterable = iter(o)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, o)


app = Flask(__name__)
app.json_encoder = CustomJSONEncoder

@app.route('/')
def index():
    return "BachNET API {version}".format(version=__version__)


@app.route('/mate/mx-status', methods=['POST'])
def add_mx_status():
    if not request.json:
        abort(400)

    if not all(x in request.json for x in ['type', 'data', 'ts', 'tz']):
        raise Exception("Invalid schema - missing a required field")

    if request.json['type'] != 'mx-status':
        raise Exception("Invalid packet type")

    with session_scope() as session:
        status = MxStatus(request.json)
        session.add(status)

    return jsonify({'status': 'success'}), 201


@app.route('/mate/mx-status', methods=['GET'])
def get_current_mx_status():
    with session_scope() as session:
        status = session.query(MxStatus).order_by(sql.desc(MxStatus.timestamp)).first()

        if status:
            print("Status:", status)
            return jsonify(status)
        else:
            return jsonify({})


@app.route('/mate/mx-logpage', methods=['POST'])
def add_mx_logpage():
    if not request.json:
        abort(400)

    if not all(x in request.json for x in ['type', 'data', 'ts', 'tz', 'date']):
        raise Exception("Invalid schema - missing a required field")

    if request.json['type'] != 'mx-logpage':
        raise Exception("Invalid packet type")

    with session_scope() as session:
        logpage = MxLogPage(request.json)
        session.add(logpage)
        return jsonify({'status': 'success', 'id': logpage.id}), 201


@app.route('/mate/mx-logpage', methods=['GET'])
def get_mx_logpages():
    with session_scope() as session:
        page = session.query(MxLogPage).order_by(sql.desc(MxLogPage.timestamp)).first()
        return jsonify(page)


@app.route('/mate/fx-status', methods=['POST'])
def add_fx_status():
    if not request.json:
        abort(400)

    if not all(x in request.json for x in ['type', 'data', 'ts', 'tz']):
        raise Exception("Invalid schema - missing a required field")

    if request.json['type'] != 'fx-status':
        raise Exception("Invalid packet type")

    with session_scope() as session:
        status = FxStatus(request.json)
        session.add(status)

    return jsonify({'status': 'success'}), 201


@app.route('/mate/fx-status', methods=['GET'])
def get_current_fx_status():
    with session_scope() as session:
        status = session.query(FxStatus).order_by(sql.desc(FxStatus.timestamp)).first()

        if status:
            print("Status:", status)
            return jsonify(status)
        else:
            return jsonify({})

# @app.route('/mate/mx-logpage/<int:day>', methods=['GET'])
# def get_logpage(day):
#     return jsonify(logpage_table[day])


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(403)
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized'}), 403)


if __name__ == "__main__":
    app.run(debug=True)
