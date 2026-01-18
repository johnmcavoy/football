from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///football.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

db = SQLAlchemy(app)

# Models
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    skill_rating = db.Column(db.Integer, default=5)  # 1-10 scale
    prefers_goal = db.Column(db.Boolean, default=False)
    total_goals = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Player {self.name}>'


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    opponent = db.Column(db.String(100))
    completed = db.Column(db.Boolean, default=False)
    our_score = db.Column(db.Integer, default=0)
    their_score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PlayerPosition(db.Model):
    """Tracks which position each player played in each stint"""
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    position = db.Column(db.String(20), nullable=False)  # GK, DEF, MID, ATT
    stint_number = db.Column(db.Integer, nullable=False)  # Which rotation
    minutes_played = db.Column(db.Integer, default=0)
    goals_scored = db.Column(db.Integer, default=0)

    game = db.relationship('Game', backref='positions')
    player = db.relationship('Player', backref='positions')


class Substitution(db.Model):
    """Tracks substitution recommendations and actual subs"""
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    minute = db.Column(db.Integer, nullable=False)
    player_out_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    player_in_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    completed = db.Column(db.Boolean, default=False)

    game = db.relationship('Game', backref='substitutions')
    player_out = db.relationship('Player', foreign_keys=[player_out_id])
    player_in = db.relationship('Player', foreign_keys=[player_in_id])


# Routes
@app.route('/')
def index():
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    total_players = Player.query.filter_by(active=True).count()
    total_games = Game.query.count()
    upcoming_games = Game.query.filter_by(completed=False).order_by(Game.date).limit(3).all()
    recent_games = Game.query.filter_by(completed=True).order_by(Game.date.desc()).limit(5).all()
    top_scorers = Player.query.filter_by(active=True).order_by(Player.total_goals.desc()).limit(5).all()

    return render_template('dashboard.html',
                         total_players=total_players,
                         total_games=total_games,
                         upcoming_games=upcoming_games,
                         recent_games=recent_games,
                         top_scorers=top_scorers)


@app.route('/players')
def players():
    all_players = Player.query.filter_by(active=True).order_by(Player.name).all()
    return render_template('players.html', players=all_players)


@app.route('/players/add', methods=['GET', 'POST'])
def add_player():
    if request.method == 'POST':
        player = Player(
            name=request.form['name'],
            skill_rating=int(request.form.get('skill_rating', 5)),
            prefers_goal=request.form.get('prefers_goal') == 'on'
        )
        db.session.add(player)
        db.session.commit()
        return redirect(url_for('players'))
    return render_template('add_player.html')


@app.route('/players/<int:player_id>/edit', methods=['GET', 'POST'])
def edit_player(player_id):
    player = Player.query.get_or_404(player_id)
    if request.method == 'POST':
        player.name = request.form['name']
        player.skill_rating = int(request.form.get('skill_rating', 5))
        player.prefers_goal = request.form.get('prefers_goal') == 'on'
        db.session.commit()
        return redirect(url_for('players'))
    return render_template('edit_player.html', player=player)


@app.route('/players/<int:player_id>/delete', methods=['POST'])
def delete_player(player_id):
    player = Player.query.get_or_404(player_id)
    player.active = False
    db.session.commit()
    return redirect(url_for('players'))


@app.route('/games')
def games():
    all_games = Game.query.order_by(Game.date.desc()).all()
    return render_template('games.html', games=all_games)


@app.route('/games/add', methods=['GET', 'POST'])
def add_game():
    if request.method == 'POST':
        game = Game(
            date=datetime.strptime(request.form['date'], '%Y-%m-%dT%H:%M'),
            opponent=request.form.get('opponent', 'Friendly Match')
        )
        db.session.add(game)
        db.session.commit()
        return redirect(url_for('games'))
    return render_template('add_game.html')


@app.route('/games/<int:game_id>')
def game_detail(game_id):
    game = Game.query.get_or_404(game_id)
    all_players = Player.query.filter_by(active=True).order_by(Player.name).all()

    # Get current lineup for this game
    current_positions = PlayerPosition.query.filter_by(game_id=game_id).all()

    # Convert players to JSON-serializable format
    players_json = [{'id': p.id, 'name': p.name} for p in all_players]

    # Convert positions to JSON-serializable format
    positions_json = [{'player_id': p.player_id, 'position': p.position} for p in current_positions]

    return render_template('game_detail.html',
                         game=game,
                         players=all_players,
                         players_json=players_json,
                         current_positions=current_positions,
                         positions_json=positions_json)


@app.route('/games/<int:game_id>/lineup', methods=['POST'])
def set_lineup(game_id):
    """Set the starting lineup for a game"""
    game = Game.query.get_or_404(game_id)

    # Clear existing positions for this stint
    stint = int(request.form.get('stint', 1))
    PlayerPosition.query.filter_by(game_id=game_id, stint_number=stint).delete()

    # Add new positions
    positions = ['GK', 'DEF1', 'DEF2', 'MID', 'ATT']
    for pos in positions:
        player_id = request.form.get(pos)
        if player_id:
            position = PlayerPosition(
                game_id=game_id,
                player_id=int(player_id),
                position=pos,
                stint_number=stint,
                minutes_played=0
            )
            db.session.add(position)

    db.session.commit()
    return redirect(url_for('game_detail', game_id=game_id))


@app.route('/games/<int:game_id>/recommend-subs')
def recommend_subs(game_id):
    """Generate substitution recommendations based on fairness"""
    game = Game.query.get_or_404(game_id)
    all_players = Player.query.filter_by(active=True).all()

    # Calculate playing time for each player
    player_stats = {}
    for player in all_players:
        total_minutes = db.session.query(db.func.sum(PlayerPosition.minutes_played))\
            .filter_by(player_id=player.id).scalar() or 0

        # Count positions played
        position_counts = db.session.query(
            PlayerPosition.position,
            db.func.count(PlayerPosition.id)
        ).filter_by(player_id=player.id).group_by(PlayerPosition.position).all()

        player_stats[player.id] = {
            'player': player,
            'total_minutes': total_minutes,
            'position_counts': dict(position_counts)
        }

    # Sort by least playing time
    recommendations = sorted(player_stats.items(), key=lambda x: x[1]['total_minutes'])

    return render_template('substitution_recommendations.html',
                         game=game,
                         recommendations=recommendations)


@app.route('/statistics')
def statistics():
    """Show fairness statistics"""
    players = Player.query.filter_by(active=True).all()

    stats = []
    for player in players:
        # Total minutes
        total_minutes = db.session.query(db.func.sum(PlayerPosition.minutes_played))\
            .filter_by(player_id=player.id).scalar() or 0

        # Position breakdown
        position_counts = db.session.query(
            PlayerPosition.position,
            db.func.sum(PlayerPosition.minutes_played)
        ).filter_by(player_id=player.id).group_by(PlayerPosition.position).all()

        # Goals
        total_goals = db.session.query(db.func.sum(PlayerPosition.goals_scored))\
            .filter_by(player_id=player.id).scalar() or 0

        stats.append({
            'player': player,
            'total_minutes': total_minutes,
            'positions': dict(position_counts),
            'total_goals': total_goals
        })

    # Sort by name
    stats.sort(key=lambda x: x['player'].name)

    return render_template('statistics.html', stats=stats)


# Initialize database
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
