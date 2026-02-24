# Admin interface for Multiplayer Bingo

## Access
- **URL:** http://localhost:8081
- **Default password:** `admin`

## Features

### Game Status
- View current room code and topic
- See number of phrases and players
- List all connected players with their UIDs

### Change Topic
- Update the game topic in real-time

### Manage Phrases
- View all current phrases (one per line)
- Edit, add, or remove phrases
- Save changes to update the wordlist immediately
- Changes are persisted to the phrases file

### Reset Game
- Clear all players from the game
- Useful for starting fresh without restarting the server

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Get current game status |
| `/api/phrases` | GET | Get all phrases |
| `/api/phrases` | POST | Update phrases (JSON: `{"phrases": [...]}`) |
| `/api/topic` | POST | Update topic (JSON: `{"topic": "..."}`) |
| `/api/reset` | POST | Clear all players |
| `/api/login` | POST | Login (JSON: `{"password": "..."}`) |
| `/api/logout` | POST | Logout |
