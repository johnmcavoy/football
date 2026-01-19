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
    man_of_the_match_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    man_of_the_match = db.relationship('Player', foreign_keys=[man_of_the_match_id])


class PlayerPosition(db.Model):
    """Tracks which position each player played in each stint"""
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    position = db.Column(db.String(20), nullable=False)  # GK, DEF, MID, ATT
    stint_number = db.Column(db.Integer, nullable=False)  # Which rotation
    minutes_played = db.Column(db.Integer, default=0)
    goals_scored = db.Column(db.Integer, default=0)
    performance_rating = db.Column(db.Integer, nullable=True)  # 1-10 scale, optional

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


class GameAvailability(db.Model):
    """Tracks which players are available for each game"""
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    game = db.relationship('Game', backref='availabilities')
    player = db.relationship('Player', backref='availabilities')


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


@app.route('/games/<int:game_id>/stats', methods=['POST'])
def update_game_stats(game_id):
    """Update post-game statistics including goals, ratings, and man of the match"""
    game = Game.query.get_or_404(game_id)

    # Update game info
    game.our_score = int(request.form.get('our_score', 0))
    game.their_score = int(request.form.get('their_score', 0))
    game.completed = request.form.get('completed') == 'on'

    # Update man of the match
    man_of_match_id = request.form.get('man_of_the_match_id')
    if man_of_match_id:
        game.man_of_the_match_id = int(man_of_match_id)
    else:
        game.man_of_the_match_id = None

    # Update player statistics
    positions = PlayerPosition.query.filter_by(game_id=game_id).all()
    for pos in positions:
        # Update goals
        goals_key = f'goals_{pos.id}'
        if goals_key in request.form:
            goals = request.form.get(goals_key)
            pos.goals_scored = int(goals) if goals else 0

        # Update performance rating (optional)
        rating_key = f'rating_{pos.id}'
        if rating_key in request.form:
            rating = request.form.get(rating_key)
            if rating and rating.strip():
                pos.performance_rating = int(rating)
            else:
                pos.performance_rating = None

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


@app.route('/games/<int:game_id>/auto-plan', methods=['GET', 'POST'])
def auto_plan_game(game_id):
    """Automatically generate a fair rotation plan for the entire game"""
    game = Game.query.get_or_404(game_id)
    all_players = Player.query.filter_by(active=True).all()

    if request.method == 'POST':
        # Check if this is saving availability or saving the plan
        if 'availability' in request.form:
            # Save player availability
            GameAvailability.query.filter_by(game_id=game_id).delete()

            for player in all_players:
                available = request.form.get(f'player_{player.id}') == 'on'
                availability = GameAvailability(
                    game_id=game_id,
                    player_id=player.id,
                    available=available
                )
                db.session.add(availability)

            db.session.commit()
            # Redirect to GET to generate the plan
            return redirect(url_for('auto_plan_game', game_id=game_id))
        else:
            # Save the rotation plan to the database
            # Clear existing positions for this game
            PlayerPosition.query.filter_by(game_id=game_id).delete()

            # Get the plan data from the form
            import json
            plan_data = json.loads(request.form.get('plan_data', '[]'))

            for rotation in plan_data:
                stint = rotation['stint']
                for pos_key, player_id in rotation['positions'].items():
                    if player_id:
                        position = PlayerPosition(
                            game_id=game_id,
                            player_id=int(player_id),
                            position=pos_key,
                            stint_number=stint,
                            minutes_played=rotation['duration']
                        )
                        db.session.add(position)

            db.session.commit()
            return redirect(url_for('game_detail', game_id=game_id))

    # GET request - check if availability is set
    availabilities = GameAvailability.query.filter_by(game_id=game_id).all()

    # If availability not set, show selection page
    if not availabilities:
        return render_template('player_availability.html',
                             game=game,
                             players=all_players)

    # Get available players only
    available_player_ids = [a.player_id for a in availabilities if a.available]
    available_players = [p for p in all_players if p.id in available_player_ids]

    num_players = len(available_players)
    if num_players < 5:
        return render_template('auto_plan.html',
                             game=game,
                             error=f"You need at least 5 available players to generate a rotation plan. Currently only {num_players} players are marked as available. Please go back and update availability.")

    # Calculate player stats for fairness (use available_players for this game)
    player_stats = {}
    for player in available_players:
        total_minutes = db.session.query(db.func.sum(PlayerPosition.minutes_played))\
            .filter_by(player_id=player.id).scalar() or 0

        # Count how many times they've played each position
        position_history = {}
        position_counts = db.session.query(
            PlayerPosition.position,
            db.func.count(PlayerPosition.id)
        ).filter_by(player_id=player.id).group_by(PlayerPosition.position).all()

        for pos, count in position_counts:
            position_history[pos] = count

        player_stats[player.id] = {
            'player': player,
            'total_minutes': total_minutes,
            'position_history': position_history,
            'times_on_pitch': 0  # Track for this game plan
        }

    # Generate rotation plan
    # For 5-a-side, we need 5 players on at a time
    # Standard game is 40 minutes, we'll create rotations every 10 minutes
    game_duration = 40  # minutes
    rotation_interval = 10  # minutes
    num_rotations = game_duration // rotation_interval
    positions = ['GK', 'DEF1', 'DEF2', 'MID', 'ATT']

    rotation_plan = []

    # Track which players have played which positions in THIS game
    game_position_tracker = {p.id: {pos: 0 for pos in positions} for p in available_players}

    for stint in range(1, num_rotations + 1):
        rotation = {
            'stint': stint,
            'start_time': (stint - 1) * rotation_interval,
            'end_time': stint * rotation_interval,
            'duration': rotation_interval,
            'positions': {}
        }

        # Sort players by who needs playing time most
        players_sorted = sorted(
            available_players,
            key=lambda p: (
                player_stats[p.id]['total_minutes'],  # Historical minutes (lower is better)
                player_stats[p.id]['times_on_pitch']  # Times in this game (lower is better)
            )
        )

        # Assign positions for this rotation
        assigned_players = []

        # First, assign goalkeeper - prioritize those who prefer it and haven't played it much
        gk_candidates = sorted(
            players_sorted,
            key=lambda p: (
                not p.prefers_goal,  # Prefer those who like goal
                game_position_tracker[p.id]['GK'],  # Haven't played GK in this game
                player_stats[p.id]['position_history'].get('GK', 0)  # Historical GK time
            )
        )
        rotation['positions']['GK'] = gk_candidates[0].id
        assigned_players.append(gk_candidates[0].id)
        player_stats[gk_candidates[0].id]['times_on_pitch'] += 1
        game_position_tracker[gk_candidates[0].id]['GK'] += 1

        # Assign other positions
        for position in ['DEF1', 'DEF2', 'MID', 'ATT']:
            # Get players not yet assigned in this rotation
            position_candidates = [p for p in players_sorted if p.id not in assigned_players]

            # Sort by who needs this position most
            position_candidates = sorted(
                position_candidates,
                key=lambda p: (
                    game_position_tracker[p.id].get(position, 0),  # Haven't played this position in game
                    player_stats[p.id]['position_history'].get(position, 0),  # Historical position count
                    player_stats[p.id]['total_minutes']  # Overall minutes
                )
            )

            if position_candidates:
                selected = position_candidates[0]
                rotation['positions'][position] = selected.id
                assigned_players.append(selected.id)
                player_stats[selected.id]['times_on_pitch'] += 1
                game_position_tracker[selected.id][position] += 1

        rotation_plan.append(rotation)

    # Calculate bench periods for each player
    player_summary = []
    for player in available_players:
        stints_playing = sum(1 for r in rotation_plan
                            if player.id in r['positions'].values())
        minutes_playing = stints_playing * rotation_interval
        minutes_benched = game_duration - minutes_playing

        # Get positions they'll play
        positions_playing = []
        for rotation in rotation_plan:
            for pos, pid in rotation['positions'].items():
                if pid == player.id:
                    positions_playing.append(f"{pos} ({rotation['start_time']}-{rotation['end_time']}min)")

        player_summary.append({
            'player': player,
            'minutes_playing': minutes_playing,
            'minutes_benched': minutes_benched,
            'stints': stints_playing,
            'positions': positions_playing,
            'fairness_score': 'Fair' if minutes_playing >= game_duration * 0.4 else 'Needs More Time'
        })

    return render_template('auto_plan.html',
                         game=game,
                         rotation_plan=rotation_plan,
                         player_summary=player_summary,
                         all_players=available_players,
                         game_duration=game_duration)


@app.route('/statistics')
def statistics():
    """Show fairness statistics"""
    players = Player.query.filter_by(active=True).all()

    stats = []
    for player in players:
        # Total minutes
        total_minutes = db.session.query(db.func.sum(PlayerPosition.minutes_played))\
            .filter_by(player_id=player.id).scalar() or 0

        # Games played (count distinct games)
        games_played = db.session.query(db.func.count(db.func.distinct(PlayerPosition.game_id)))\
            .filter_by(player_id=player.id).scalar() or 0

        # Games available (count distinct games they were marked available)
        games_available = db.session.query(db.func.count(db.func.distinct(GameAvailability.game_id)))\
            .filter(GameAvailability.player_id == player.id, GameAvailability.available == True).scalar() or 0

        # If no availability data exists (old games), use games_played as proxy
        if games_available == 0 and games_played > 0:
            games_available = games_played

        # Position breakdown
        position_counts = db.session.query(
            PlayerPosition.position,
            db.func.sum(PlayerPosition.minutes_played)
        ).filter_by(player_id=player.id).group_by(PlayerPosition.position).all()

        # Goals
        total_goals = db.session.query(db.func.sum(PlayerPosition.goals_scored))\
            .filter_by(player_id=player.id).scalar() or 0

        # Calculate minutes per game attended
        minutes_per_game = total_minutes / games_available if games_available > 0 else 0

        stats.append({
            'player': player,
            'total_minutes': total_minutes,
            'games_played': games_played,
            'games_available': games_available,
            'minutes_per_game': minutes_per_game,
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
