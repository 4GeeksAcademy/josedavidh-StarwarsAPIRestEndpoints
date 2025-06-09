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

#A partir de aqui inicia la solución a las instrucciones del proyecto

#Lista todos los registros de people en la base de datos
@app.route("/people", methods=["GET"])
def get_people():
    people = People.query.all()
    return jsonify([item.serialize() for item in people]), 200

#Muestra la información de un solo personaje según su id
@app.route("/people/<int:people_id>", methods=["GET"])
def get_one_people(people_id=None):
    person = People.query.get(people_id)

    if person is None:
        return jsonify("User not found"), 404

    else:
        return jsonify(person.serialize())

#Lista todos los registros de planets en la base de datos
@app.route("/planets", methods=["GET"])
def get_planet():
    planets = Planet.query.all()
    return jsonify([item.serialize() for item in planets]), 200

#Muestra la información de un solo planeta según su id
@app.route("/planets/<int:planet_id>", methods=["GET"])
def get_one_planet(planet_id=None):
    planet = Planet.query.get(planet_id)

    if planet is None:
        return jsonify("User not found"), 404

    else:
        return jsonify(planet.serialize()), 200

#Lista todos los usuarios del blog
@app.route("/users", methods=["GET"])
def get_users():
    users = User.query.all()

    if not users:
        return jsonify({"message": "No users found"}), 404
    
    return jsonify([{
        "id": user.id,
        "lastname": user.lastname,
        "email": user.email
    } for user in users]), 200

#Lista todos los favoritos que pertenecen al usuario actual
@app.route("/users/favorites", methods=["GET"])
def get_user_favorites():
    user_id = request.args.get("user_id", type = int)

#Añade un nuevo planet favorito al usuario actual con el id = planet_id
@app.route("/favorite/planet/<int:planet_id>", methods=["POST"])
def add_favorite_planet(planet_id):
    body = request.json
    favorite = Favorite(user_id=body["user_id"], planet_id=planet_id)
    db.session.add(favorite)
    try:
        db.session.commit()
        return jsonify("Planet saved"), 201
    except Exception as error:
        db.session.rollback()
        return jsonify(f"error: {error}")
    
#Añade un nuevo people favorito al usuario actual con el id = people_id
@app.route("/favorite/people/<int:people_id>", methods=["POST"])
def add_favorite_people(people_id):
    body = request.json
    favorite = Favorite(user_id=body["user_id"], people_id=people_id)
    db.session.add(favorite)
    try:
        db.session.commit()
        return jsonify("Character saved"), 201
    except Exception as error:
        db.session.rollback()
        return jsonify(f"error: {error}")

#Elimina un planet favorito con el id = planet_id
@app.route("/favorite/planet/<int:planet_id>", methods=["DELETE"])
def delete_favorite_planet(planet_id):
    body = request.json
    favorite = Favorite.query.filter_by(user_id=body["user_id"], planet_id=planet_id).first()
    if not favorite:
        return jsonify("Favorite not found"), 404
    db.session.delete(favorite)
    db.session.commit()
    return jsonify("Planet favorite deleted"), 200

#Elimina un people favorito con el id = people_id
@app.route("/favorite/people/<int:people_id>", methods=["DELETE"])
def delete_favorite_people(people_id):
    body = request.json
    favorite = Favorite.query.filter_by(user_id=body["user_id"], people_id=people_id).first()
    if not favorite:
        return jsonify("Favorite not found"), 404
    db.session.delete(favorite)
    db.session.commit()
    return jsonify("People favorite deleted"), 200

#Endpoint para poblar la base de datos con personajes (people) obtenidos desde la API externa swapi.tech
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

#Endpoint para poblar la base de datos con planetas obtenidos desde la API externa swapi.tech
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