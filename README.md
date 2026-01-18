# Football Team Manager ⚽

A Flask-based web application for managing a 5-a-side football team with an AWS-style interface. Designed for coaches who want to ensure fair playing time, track player development, and optimize team lineups.

## Features

### Player Management
- **Player Roster**: Add, edit, and manage all team players
- **Skill Ratings**: Rate players on a 1-10 scale to help with team balance
- **Position Preferences**: Track which players prefer playing in goal
- **Goal Tracking**: Automatically track goals scored by each player

### Game Management
- **Schedule Games**: Add upcoming matches with date, time, and opponent
- **Visual Pitch Display**: See your team lineup on an interactive football pitch
- **Lineup Builder**: Easily assign players to positions (GK, DEF, MID, ATT)
- **Game History**: Track completed games with scores

### Fairness & Analytics
- **Playing Time Tracking**: Monitor total minutes played by each player
- **Position Distribution**: Ensure players get experience in various positions
- **Fairness Indicators**: Visual alerts when players need more playing time
- **Smart Substitution Recommendations**: AI-powered suggestions based on fairness metrics

### Statistics Dashboard
- **Overall Statistics**: View total players, games, and top scorers
- **Individual Player Stats**: Detailed breakdown of minutes, positions, and goals
- **Fairness Analysis**: Identify players who need more opportunities
- **Position Variety Tracking**: Ensure balanced development across all positions

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Quick Start

1. **Clone or download this repository**
   ```bash
   cd football
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the app**
   - Open your browser and go to: `http://localhost:5000`
   - The app is accessible from other devices on your network at: `http://YOUR_IP_ADDRESS:5000`

## Making the App Accessible Remotely

### Option 1: Local Network Access
The app is already configured to run on `0.0.0.0`, making it accessible to any device on your local network.

1. Find your computer's IP address:
   - **Linux/Mac**: `ifconfig` or `ip addr`
   - **Windows**: `ipconfig`

2. Access from other devices using: `http://YOUR_IP_ADDRESS:5000`

### Option 2: Internet Access (Advanced)

For access from anywhere, you have several options:

**A. Using ngrok (Easiest)**
```bash
# Install ngrok from https://ngrok.com/
ngrok http 5000
# Use the provided URL to access your app from anywhere
```

**B. Port Forwarding**
1. Configure your router to forward port 5000 to your computer
2. Access using your public IP address
3. Consider using a dynamic DNS service

**C. Deploy to a Cloud Service**
- Deploy to platforms like:
  - Heroku
  - AWS Elastic Beanstalk
  - Google Cloud Platform
  - DigitalOcean
  - PythonAnywhere

### Security Considerations

⚠️ **Important**: Before making your app publicly accessible:

1. **Change the secret key**:
   ```bash
   export SECRET_KEY='your-very-secure-random-key-here'
   ```

2. **Disable debug mode** in production:
   - Edit `app.py` and change: `debug=True` to `debug=False`

3. **Use HTTPS** for public access (ngrok provides this automatically)

4. **Consider adding authentication** if sharing with others

## Usage Guide

### Getting Started

1. **Add Your Players**
   - Click "Players" in the sidebar
   - Click "Add Player"
   - Enter player name, skill rating, and preferences
   - Repeat for all team members

2. **Schedule a Game**
   - Click "Games" in the sidebar
   - Click "Schedule Game"
   - Enter the date, time, and opponent

3. **Set Your Lineup**
   - Click on the game from the games list
   - Use the dropdowns to assign players to positions
   - See the lineup visualized on the pitch
   - Click "Set Lineup" to save

4. **Get Substitution Recommendations**
   - From the game detail page, click "Substitution Recommendations"
   - See which players should play more for fairness
   - Use the tips provided for optimal rotation timing

5. **Monitor Fairness**
   - Click "Statistics & Fairness" in the sidebar
   - Review playing time distribution
   - Identify players who need more opportunities
   - Check position variety for balanced development

### Best Practices

- **Before Each Game**: Check the Statistics page to see who needs more playing time
- **During Games**: Use the substitution recommendations to ensure fair rotation
- **After Games**: Update player stats and record any goals scored
- **Regular Reviews**: Monitor the fairness indicators to maintain equal opportunities

## Project Structure

```
football/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── football.db            # SQLite database (created automatically)
├── static/
│   └── css/
│       └── style.css      # AWS-style CSS
└── templates/
    ├── base.html          # Base template with layout
    ├── dashboard.html     # Main dashboard
    ├── players.html       # Player list
    ├── add_player.html    # Add player form
    ├── edit_player.html   # Edit player form
    ├── games.html         # Games list
    ├── add_game.html      # Add game form
    ├── game_detail.html   # Game details & lineup
    ├── substitution_recommendations.html
    └── statistics.html    # Fairness statistics
```

## Database Schema

The app uses SQLite with the following models:

- **Player**: Stores player information (name, skill, preferences, goals)
- **Game**: Tracks scheduled and completed games
- **PlayerPosition**: Records which position each player played in each game stint
- **Substitution**: Logs substitution recommendations and actual substitutions

## Tips for Coaches

### Fair Rotation Strategy
- **5-a-side typical game**: 40 minutes
- **Recommended substitution intervals**: Every 10 minutes
- **Rotation pattern**: Ensure each player sits out equally

### Using the App Effectively
1. **Pre-Season**: Add all players with accurate skill ratings
2. **Weekly**: Schedule upcoming games
3. **Pre-Game**: Review statistics and plan fair lineups
4. **During Game**: Follow substitution recommendations
5. **Post-Game**: Update goals and verify playing time

### Position Development
- Try to give each player experience in at least 3 different positions
- Rotate goalkeeper position unless a player strongly prefers it
- Use skill ratings to balance the team when needed

## Troubleshooting

**Database Issues**
- If you encounter database errors, delete `football.db` and restart the app (this will reset all data)

**Port Already in Use**
- Change the port in `app.py`: `app.run(host='0.0.0.0', port=5001, debug=True)`

**Can't Access from Other Devices**
- Check your firewall settings
- Ensure devices are on the same network
- Verify your IP address is correct

## Future Enhancements

Potential features to add:
- Player attendance tracking
- Practice session management
- Email/SMS notifications for game reminders
- Export statistics to PDF/Excel
- Multi-team management
- Player performance trends over time
- Weather integration for outdoor games
- Tournament bracket management

## Contributing

Feel free to fork this project and customize it for your team's needs!

## License

This project is open source and available for personal and educational use.

## Support

For questions or issues, please create an issue in the repository.

---

**Happy Coaching! ⚽🎉**
