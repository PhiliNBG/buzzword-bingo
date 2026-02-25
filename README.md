# Multiplayer Bingo

A web-based multiplayer Bingo game with a real-time admin interface. Players join a room with a shared topic, and each gets a unique bingo card. The admin can manage phrases, change topics, and monitor players.

## Features

- **Multiplayer Support**: Multiple players can join the same room
- **Unique Bingo Cards**: Each player gets a randomly shuffled bingo card
- **Real-time Updates**: Players see all marked cells from other players
- **Admin Interface**: Web-based dashboard to manage the game
- **Customizable Grid Size**: Support for 3x3, 4x4, and 5x5 grids
- **Persistent Phrases**: Phrase changes are saved to file

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)

## Quick Start

```bash
python bingo.py --room MYROOM --phrases phrases.txt
```

This starts:
- **Game Server**: http://localhost:8080
- **Admin Interface**: http://localhost:8081 (password: `admin`)

## Usage

### Command Line Options

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--room` | Yes | - | Room code for players to join |
| `--phrases` | Yes | - | Phrases file (one phrase per line) |
| `--port` | No | `8080` | Game server port |
| `--admin-port` | No | `8081` | Admin interface port |
| `--topic` | No | `Generic Bingo` | Game topic |
| `--admin-password` | No | `admin` | Admin password |
| `--grid-size` | No | `5` | Grid size: 3, 4, or 5 |

### Examples

**Basic usage:**
```bash
python bingo.py --room PARTY --phrases phrases.txt
```

**Custom ports and topic:**
```bash
python bingo.py --room BIRTHDAY --phrases phrases.txt --port 9000 --admin-port 9001 --topic "Birthday Bingo"
```

**Custom grid size (3x3):**
```bash
python bingo.py --room QUICK --phrases phrases.txt --grid-size 3
```

**Change admin password:**
```bash
python bingo.py --room SECURE --phrases phrases.txt --admin-password mysecret
```

## How to Play

### For Players

1. Open http://localhost:8080 in your browser
2. **First time**: Enter your name and the room code, click "Join Room"
3. **Rejoining**: If disconnected, enter your name and UID to rejoin
4. Click cells on your bingo card to mark them
5. All players can see each other's marked cells in real-time

### For Admins

1. Open http://localhost:8081
2. Login with the admin password (default: `admin`)
3. Use the dashboard to:
   - View game status (room, topic, players)
   - Change the topic
   - Edit phrases (one per line)
   - Adjust grid size
   - Reset the game (clear all players)

## Project Structure

```
madeinpython/
├── bingo.py          # Main Python application
├── phrases.txt       # Phrases file (one per line)
├── README.md         # This file
├── html/             # Game frontend
│   ├── index.html    # Game page
│   ├── bingo.js      # Game logic
│   └── style.css     # Game styles
└── admin/            # Admin frontend
    ├── index.html    # Admin dashboard
    ├── login.html    # Admin login page
    └── README.md     # Admin documentation
```

## API Endpoints

### Game API (Port 8080)

| Endpoint | Method | Parameters | Description |
|----------|--------|------------|-------------|
| `/join` | GET | `room`, `username` | Join a room, returns UID |
| `/game` | GET | `uid` | Get game state and all players |
| `/cell` | GET | `uid`, `cell`, `marked` | Mark/unmark a cell |

### Admin API (Port 8081)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Get current game status |
| `/api/phrases` | GET | Get all phrases |
| `/api/phrases` | POST | Update phrases |
| `/api/topic` | POST | Update topic |
| `/api/grid_size` | POST | Update grid size |
| `/api/reset` | POST | Clear all players |
| `/api/login` | POST | Admin login |
| `/api/logout` | POST | Admin logout |

## Phrases File Format

The phrases file contains one phrase per line:

```
Phrase one
Phrase two
Phrase three
```

**Minimum phrases required:**
- 3x3 grid: 9 phrases
- 4x4 grid: 16 phrases
- 5x5 grid: 25 phrases

## License

This project is provided as-is for educational and entertainment purposes.
