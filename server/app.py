from flask import Flask, abort, request, jsonify, make_response
from flask_migrate import Migrate
from flask_restful import Api, Resource, reqparse 
from datetime import datetime, date
from models import db, Episode, Guest, Appearance

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

db.init_app(app)
migrate = Migrate(app, db)
api = Api(app)


def parse_date(date_string):
    try:
        # Convert string to a Python date object (Assuming 'YYYY-MM-DD' format)
        return datetime.strptime(date_string, "%Y-%m-%d").date()
    except ValueError:
        # Handle incorrect format
        raise ValueError("Incorrect date format. Expected 'YYYY-MM-DD'.")
    
class EpisodeResource(Resource):
    def get(self, id):
        # Retrieve the episode by ID
        episode = db.session.get(Episode, id)
        if episode is None:
            return {"error": "Episode not found"}, 404

        # Prepare the response data
        response = {
            "id": episode.id,
            "date": episode.date.strftime("%m/%d/%y"),  # Format date as 'm/d/yy'
            "number": episode.number,
            "guests": [
                {
                    "id": guest.id,
                    "name": guest.name,
                    "occupation": guest.occupation
                }
                for guest in episode.guests
            ]
        }
        return jsonify(response), 200
    def delete(self, id):
        # Retrieve the episode by ID
        episode = db.session.get(Episode, id)
        if episode is None:
            # Return the error message with the required format
            return {"error": "404: Episode not found"}, 404

        # Delete all associated appearances
        appearances = Appearance.query.filter_by(episode_id=id).all()
        for appearance in appearances:
            db.session.delete(appearance)

        # Delete the episode
        db.session.delete(episode)
        db.session.commit()

        # Return an empty response body with status code 204
        return {}, 204



        
class EpisodeListResource(Resource):
    def get(self):
        # Query all episodes
        episodes = Episode.query.all()
        return [episode.to_dict(only=('id', 'title', 'description', 'date', 'number')) for episode in episodes], 200


# Add the resource to the API
api.add_resource(EpisodeListResource, '/episodes')
api.add_resource(EpisodeResource, '/episodes/<int:id>')

@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

@app.route('/episodes', methods=["GET"])
def get_episodes():
    try:
        # Query all episodes from the database
        episodes = Episode.query.all()

        # Format the episodes data
        episodes_list = [
            {
                "id": episode.id,
                "date": episode.date.strftime('%m/%d/%y'),  # Format date to 'm/d/yy'
                "number": episode.number
            } for episode in episodes
        ]

        return make_response(jsonify(episodes_list), 200)
    except Exception as e:
        return make_response({'message': str(e)}, 500)


@app.route('/episodes/<int:id>', methods=["GET", "DELETE"])
def episode_by_id(id):
    episode = Episode.query.get(id)
    
    if not episode:
        return make_response(jsonify({'message': f'Episode {id} not found'}), 404)

    if request.method == "GET":
        return make_response(jsonify(episode.to_dict()), 200)

    elif request.method == "DELETE":
        db.session.delete(episode)
        db.session.commit()
        return make_response({}, 204)

@app.route('/appearances', methods=["POST"])
def create_appearance():
    try:
        # Get JSON data from the request
        data = request.get_json()

        # Validate required fields are present
        if not data or 'rating' not in data or 'episode_id' not in data or 'guest_id' not in data:
            return make_response(jsonify({'error': '400: Validation error.'}), 400)

        # Validate that the episode and guest exist
        episode = Episode.query.get(data['episode_id'])
        guest = Guest.query.get(data['guest_id'])

        if not episode:
            return make_response(jsonify({'error': '400: Validation error.'}), 400)
        if not guest:
            return make_response(jsonify({'error': '400: Validation error.'}), 400)

        # Additional validation for rating (if needed)
        if not (1 <= data['rating'] <= 10):  # Assuming rating should be between 1 and 10
            return make_response(jsonify({'error': '400: Validation error.'}), 400)

        # Create new Appearance object
        new_appearance = Appearance(
            rating=data['rating'],
            episode_id=data['episode_id'],
            guest_id=data['guest_id']
        )

        # Add to the database
        db.session.add(new_appearance)
        db.session.commit()

        # Prepare the response data
        response = {
            "id": new_appearance.id,
            "rating": new_appearance.rating,
            "episode": {
                "id": episode.id,
                "date": episode.date.strftime('%m/%d/%y'),  # Format date as 'm/d/yy'
                "number": episode.number
            },
            "guest": {
                "id": guest.id,
                "name": guest.name,
                "occupation": guest.occupation
            }
        }

        # Return the created appearance with detailed data
        return make_response(jsonify(response), 201)

    except Exception as e:
        # Handle any other exceptions and return the error response
        return make_response(jsonify({'error': '400: Validation error.'}), 400)
    
    
@app.route('/guests', methods=["GET"])
def get_guests():
    try:
        # Query all guests from the database
        guests = Guest.query.all()

        # If there are no guests found, return an empty list
        if not guests:
            return make_response(jsonify([]), 200)

        # Format the guests data
        guests_list = [
            {
                "id": guest.id,
                "name": guest.name,
                "occupation": guest.occupation
            } for guest in guests
        ]

        return make_response(jsonify(guests_list), 200)
    except Exception as e:
        return make_response({'message': str(e)}, 500)

if __name__ == "__main__":
    app.run(port=5555, debug=True)