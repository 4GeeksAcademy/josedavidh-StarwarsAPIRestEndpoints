"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planet, Favorite
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)



@app.route("/people", methods=["GET"])
def get_people():
    people = People.query.all()
    return jsonify([item.serialize() for item in people]), 200

@app.route("/people/<int:people_id>", methods=["GET"])
def get_one_people(people_id=None):
    person = People.query.get(people_id)

    if person is None:
        return jsonify("User not found"), 404

    else:
        return jsonify(person.serialize())

@app.route("/planets", methods=["GET"])
def get_planet():
    planets = Planet.query.all()
    return jsonify([item.serialize() for item in planets]), 200

@app.route("/planets/<int:planet_id>", methods=["GET"])
def get_one_planet(planet_id=None):
    planet = Planet.query.get(planet_id)

    if planet is None:
        return jsonify("User not found"), 404

    else:
        return jsonify(planet.serialize()), 200

@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    body = request.json
    favorite = Favorite(user_id=body['user_id'], planet_id=planet_id)
    db.session.add(favorite)
    try:
        db.session.commit()
        return jsonify('Planet saved'), 201
    except Exception as error:
        db.session.rollback()
        return jsonify(f'error: {error}')

@app.route("/people-population",  methods=["GET"])
def populate_people():

    URL_PEOPLE = "https://swapi.tech/api/people?page=1&limit=50"
    response = requests.get(URL_PEOPLE)
    data = response.json()
    for person in data["results"]:
        response = requests.get(person["url"])
        person_data = response.json()
        person_data = person_data["result"]

        people = People()
        people.name = person_data["properties"]["name"]
        people.description = person_data["description"]
        people.eye_color = person_data["properties"]["eye_color"]

        db.session.add(people)

    try:
        db.session.commit()
        return jsonify("People saved"), 201

    except Exception as error:
        db.session.rollback()
        return jsonify(f"Error: {error.args}")

@app.route("/planet-population",  methods=["GET"])
def populate_planet():

    URL_PEOPLE = "https://swapi.tech/api/planets?page=1&limit=50"
    response = requests.get(URL_PEOPLE)
    data = response.json()
    for person in data["results"]:
        response = requests.get(person["url"])
        person_data = response.json()
        person_data = person_data["result"]

        people = Planet()
        people.name = person_data["properties"]["name"]
        people.description = person_data["description"]

        db.session.add(people)

    try:
        db.session.commit()
        return jsonify("People saved"), 201

    except Exception as error:
        db.session.rollback()
        return jsonify(f"Error: {error.args}")

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
