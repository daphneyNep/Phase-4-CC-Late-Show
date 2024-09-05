from flask import Flask, abort, request, jsonify, make_response
from flask_migrate import Migrate
from flask_restful import Api, Resource, reqparse 
from datetime import datetime, date
from models import db, Episode, Guest, Appearance
from flask_sqlalchemy import SQLAlchemy


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
        episodes = Episode.query.filter_by(id=id).first()
        if not episodes:
            return make_response({"error": "404: Episode not found"}, 404)  # Updated line
        
        return make_response(episodes.to_dict(), 200)

    def delete(self, id):
        episode = Episode.query.get(id)
        if episode is None:
            return {"error": "404: Episode not found"}, 404  # Updated line

        # Delete all associated appearances
        appearances = Appearance.query.filter_by(episode_id=id).all()
        for appearance in appearances:
            db.session.delete(appearance)

        # Delete the episode
        db.session.delete(episode)
        db.session.commit()


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

@app.route('/episodes', methods=['POST'])
def create_episode():
    data = request.get_json()
    if 'date' in data:
        try:
            data['date'] = parse_date(data['date'])  # Convert to date object
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    episode = Episode(**data)
    db.session.add(episode)
    db.session.commit()

    return jsonify(episode.to_dict()), 201

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


@app.route('/episodes/<int:id>', methods=['GET'])
def get_episode(id):
    episode = Episode.query.get(id)
    if episode is None:
        return jsonify({'error': 'Episode not found'}), 404
    return jsonify({
        'episode': episode.to_dict()
    })

@app.route('/appearances', methods=['POST'])
def create_appearance():
    data = request.get_json()

    # Check for required fields in the input data
    if not data:
        return jsonify({'error': 'No input data provided'}), 400

    rating = data.get('rating')
    episode_id = data.get('episode_id')
    guest_id = data.get('guest_id')

    # Validate that all required fields are present
    if rating is None or episode_id is None or guest_id is None:
        return jsonify({'error': 'Missing required fields: rating, episode_id, guest_id'}), 400

    # Create the new appearance
    try:
        appearance = Appearance(rating=rating, episode_id=episode_id, guest_id=guest_id)
        db.session.add(appearance)
        db.session.commit()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Return the newly created appearance with its id
    return jsonify({
        'id': appearance.id,
        'rating': appearance.rating,
        'episode_id': appearance.episode_id,
        'guest_id': appearance.guest_id
    }), 201
    

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