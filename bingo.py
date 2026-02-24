#!/usr/bin/env python3
"""Multiplayer Bingo - Python Implementation with Admin Interface

Usage:
    python bingo.py --room <ROOM_CODE> --phrases <PHRASES_FILE> [--port PORT] [--admin-port ADMIN_PORT] [--topic TOPIC] [--html HTML_DIR]

Example:
    python bingo.py --room MYROOM --phrases phrases.txt --port 8080 --admin-port 8081
"""

import argparse
import json
import os
import random
import string
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


# Global game state
class GameState:
    def __init__(self):
        self.phrases = []
        self.phrases_file = ""
        self.players = []
        self.room = ""
        self.topic = ""
        self.admin_password = "admin"  # Default admin password
        self.grid_size = 5  # Default 5x5 grid


bingo = GameState()


class BingoCell:
    def __init__(self, phrase="", marked=False):
        self.phrase = phrase
        self.marked = marked

    def to_dict(self):
        return {"phrase": self.phrase, "marked": self.marked}


class Player:
    def __init__(self, username, uid, bingo_board):
        self.username = username
        self.uid = uid
        self.bingo_board = bingo_board

    def to_dict(self):
        return {
            "username": self.username,
            "uid": self.uid,
            "bingo_board": [cell.to_dict() for cell in self.bingo_board]
        }


def generate_uid():
    """Generate a random UID."""
    return ''.join(random.choices(string.digits, k=10))


def shuffle_phrases(phrases):
    """Shuffle and return a new list of phrases."""
    shuffled = phrases.copy()
    random.shuffle(shuffled)
    return shuffled


def load_phrases(phrases_file):
    """Load phrases from a text file with each phrase on its own line."""
    with open(phrases_file, 'r') as f:
        return [line.strip() for line in f if line.strip()]


def save_phrases(phrases_file, phrases):
    """Save phrases to a text file with each phrase on its own line."""
    with open(phrases_file, 'w') as f:
        for phrase in phrases:
            f.write(phrase + '\n')


class AdminHandler(SimpleHTTPRequestHandler):
    """HTTP handler for admin interface."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(os.path.dirname(__file__), 'admin'), **kwargs)

    def send_json_response(self, data, status=200):
        """Send a JSON response."""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_html_response(self, content, status=200):
        """Send an HTML response."""
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def check_admin_auth(self):
        """Check admin authentication from session cookie."""
        cookie = self.headers.get('Cookie', '')
        for c in cookie.split(';'):
            c = c.strip()
            if c.startswith('admin_auth='):
                return c[11:] == bingo.admin_password
        return False

    def do_GET(self):
        """Handle GET requests for admin interface."""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == '/api/status':
            if not self.check_admin_auth():
                self.send_json_response({"error": "Unauthorized"}, 401)
                return
            self.send_json_response({
                "room": bingo.room,
                "topic": bingo.topic,
                "phrases_count": len(bingo.phrases),
                "players_count": len(bingo.players),
                "grid_size": bingo.grid_size,
                "players": [p.to_dict() for p in bingo.players]
            })
        elif path == '/api/phrases':
            if not self.check_admin_auth():
                self.send_json_response({"error": "Unauthorized"}, 401)
                return
            self.send_json_response({"phrases": bingo.phrases})
        elif path == '/login':
            # Serve login page
            self.serve_login_page()
        elif path == '/':
            # Serve admin dashboard (requires auth)
            if not self.check_admin_auth():
                self.send_response(302)
                self.send_header('Location', '/login')
                self.end_headers()
                return
            self.serve_admin_dashboard()
        else:
            # Serve static files
            super().do_GET()

    def do_POST(self):
        """Handle POST requests for admin interface."""
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')

        if path == '/api/login':
            data = json.loads(body) if body else {}
            password = data.get('password', '')
            if password == bingo.admin_password:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Set-Cookie', f'admin_auth={bingo.admin_password}; Path=/; HttpOnly')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode())
            else:
                self.send_json_response({"error": "Invalid password"}, 401)

        elif path == '/api/logout':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Set-Cookie', 'admin_auth=; Path=/; Max-Age=0; HttpOnly')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode())

        elif path == '/api/phrases':
            if not self.check_admin_auth():
                self.send_json_response({"error": "Unauthorized"}, 401)
                return
            data = json.loads(body) if body else {}
            phrases = data.get('phrases', [])
            if not phrases:
                self.send_json_response({"error": "No phrases provided"}, 400)
                return
            # Update phrases
            bingo.phrases = [p.strip() for p in phrases if p.strip()]
            # Save to file
            try:
                save_phrases(bingo.phrases_file, bingo.phrases)
                self.send_json_response({"success": True, "count": len(bingo.phrases)})
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)

        elif path == '/api/topic':
            if not self.check_admin_auth():
                self.send_json_response({"error": "Unauthorized"}, 401)
                return
            data = json.loads(body) if body else {}
            topic = data.get('topic', '')
            if not topic:
                self.send_json_response({"error": "No topic provided"}, 400)
                return
            bingo.topic = topic
            self.send_json_response({"success": True, "topic": bingo.topic})

        elif path == '/api/reset':
            if not self.check_admin_auth():
                self.send_json_response({"error": "Unauthorized"}, 401)
                return
            # Clear all players
            bingo.players = []
            self.send_json_response({"success": True})

        elif path == '/api/grid_size':
            if not self.check_admin_auth():
                self.send_json_response({"error": "Unauthorized"}, 401)
                return
            data = json.loads(body) if body else {}
            grid_size = data.get('grid_size', 5)
            if grid_size not in [3, 4, 5]:
                self.send_json_response({"error": "Grid size must be 3, 4 or 5"}, 400)
                return
            bingo.grid_size = grid_size
            self.send_json_response({"success": True, "grid_size": bingo.grid_size})

        else:
            self.send_response(404)
            self.end_headers()

    def serve_login_page(self):
        """Serve the login page."""
        html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Admin Login - Multiplayer Bingo</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css">
    <style>
        body { background: #f5f5f5; display: flex; align-items: center; justify-content: center; height: 100vh; }
        .login-form { max-width: 400px; width: 100%; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div class="login-form">
        <h2 class="text-center mb-4">Admin Login</h2>
        <form id="loginForm">
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" class="form-control" id="password" required>
            </div>
            <button type="submit" class="btn btn-primary btn-block">Login</button>
        </form>
        <p id="error" class="text-danger mt-3"></p>
    </div>
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <script>
        $('#loginForm').submit(function(e) {
            e.preventDefault();
            $.ajax({
                url: '/api/login',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ password: $('#password').val() }),
                success: function() {
                    window.location.href = '/';
                },
                error: function(xhr) {
                    $('#error').text(xhr.responseJSON?.error || 'Login failed');
                }
            });
        });
    </script>
</body>
</html>'''
        self.send_html_response(html)

    def serve_admin_dashboard(self):
        """Serve the admin dashboard."""
        html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Admin Dashboard - Multiplayer Bingo</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css">
    <style>
        .phrase-list { max-height: 400px; overflow-y: auto; }
        .phrase-item { padding: 5px 10px; border-bottom: 1px solid #eee; }
        .phrase-item:last-child { border-bottom: none; }
        #phrasesText { font-family: monospace; }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <span class="navbar-brand">Multiplayer Bingo Admin</span>
        <button class="btn btn-outline-light btn-sm" id="logoutBtn">Logout</button>
    </nav>
    <main class="container mt-4">
        <div class="row">
            <div class="col-md-6">
                <div class="card mb-4">
                    <div class="card-header">Game Status</div>
                    <div class="card-body">
                        <p><strong>Room:</strong> <span id="room"></span></p>
                        <p><strong>Topic:</strong> <span id="topic"></span></p>
                        <p><strong>Grid Size:</strong> <span id="gridSize"></span></p>
                        <p><strong>Phrases:</strong> <span id="phrasesCount"></span></p>
                        <p><strong>Players:</strong> <span id="playersCount"></span></p>
                        <button class="btn btn-warning btn-sm" id="resetBtn">Reset Game (Clear Players)</button>
                    </div>
                </div>
                <div class="card mb-4">
                    <div class="card-header">Change Topic</div>
                    <div class="card-body">
                        <form id="topicForm">
                            <div class="form-group">
                                <input type="text" class="form-control" id="newTopic" placeholder="New topic">
                            </div>
                            <button type="submit" class="btn btn-primary btn-sm">Update Topic</button>
                        </form>
                    </div>
                </div>
                <div class="card mb-4">
                    <div class="card-header">Grid Size</div>
                    <div class="card-body">
                        <form id="gridForm">
                            <div class="form-group">
                                <select class="form-control" id="gridSizeSelect">
                                    <option value="3">3x3 (9 phrases)</option>
                                    <option value="4">4x4 (16 phrases)</option>
                                    <option value="5">5x5 (25 phrases)</option>
                                </select>
                            </div>
                            <button type="submit" class="btn btn-primary btn-sm">Update Grid Size</button>
                            <small class="form-text text-muted">Note: Changing grid size requires players to rejoin</small>
                        </form>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card mb-4">
                    <div class="card-header">Manage Phrases</div>
                    <div class="card-body">
                        <form id="phrasesForm">
                            <div class="form-group">
                                <label for="phrasesText">Phrases (one per line)</label>
                                <textarea class="form-control" id="phrasesText" rows="15"></textarea>
                            </div>
                            <button type="submit" class="btn btn-primary btn-sm">Save Phrases</button>
                            <span id="saveStatus" class="ml-2"></span>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        <div class="card mb-4">
            <div class="card-header">Current Players</div>
            <div class="card-body">
                <div id="playersList" class="phrase-list"></div>
            </div>
        </div>
    </main>
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <script>
        function loadStatus() {
            $.get('/api/status', function(data) {
                $('#room').text(data.room);
                $('#topic').text(data.topic);
                $('#gridSize').text(data.grid_size + 'x' + data.grid_size);
                $('#gridSizeSelect').val(data.grid_size);
                $('#phrasesCount').text(data.phrases_count);
                $('#playersCount').text(data.players_count);
                // Update players list
                var $list = $('#playersList');
                $list.empty();
                if (data.players.length === 0) {
                    $list.append('<p class="text-muted">No players yet</p>');
                } else {
                    data.players.forEach(function(p) {
                        $list.append('<div class="phrase-item"><strong>' + p.username + '</strong> (UID: ' + p.uid + ')</div>');
                    });
                }
            }).fail(function() {
                window.location.href = '/login';
            });
        }

        function loadPhrases() {
            $.get('/api/phrases', function(data) {
                $('#phrasesText').val(data.phrases.join('\\n'));
            }).fail(function() {
                window.location.href = '/login';
            });
        }

        $('#topicForm').submit(function(e) {
            e.preventDefault();
            $.ajax({
                url: '/api/topic',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ topic: $('#newTopic').val() }),
                success: function() {
                    $('#newTopic').val('');
                    loadStatus();
                },
                error: function(xhr) {
                    alert(xhr.responseJSON?.error || 'Failed to update topic');
                }
            });
        });

        $('#gridForm').submit(function(e) {
            e.preventDefault();
            $.ajax({
                url: '/api/grid_size',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ grid_size: parseInt($('#gridSizeSelect').val()) }),
                success: function() {
                    loadStatus();
                    alert('Grid size updated. Players need to rejoin for changes to take effect.');
                },
                error: function(xhr) {
                    alert(xhr.responseJSON?.error || 'Failed to update grid size');
                }
            });
        });

        $('#phrasesForm').submit(function(e) {
            e.preventDefault();
            var phrases = $('#phrasesText').val().split('\\n').filter(function(p) { return p.trim(); });
            $.ajax({
                url: '/api/phrases',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ phrases: phrases }),
                success: function(data) {
                    $('#saveStatus').text('Saved! (' + data.count + ' phrases)').removeClass('text-danger').addClass('text-success');
                    setTimeout(function() { $('#saveStatus').text(''); }, 2000);
                    loadStatus();
                },
                error: function(xhr) {
                    $('#saveStatus').text('Error: ' + (xhr.responseJSON?.error || 'Failed')).removeClass('text-success').addClass('text-danger');
                }
            });
        });

        $('#resetBtn').click(function() {
            if (confirm('Are you sure you want to clear all players?')) {
                $.post('/api/reset', function() {
                    loadStatus();
                }).fail(function() {
                    alert('Failed to reset');
                });
            }
        });

        $('#logoutBtn').click(function() {
            $.post('/api/logout', function() {
                window.location.href = '/login';
            });
        });

        // Initial load
        loadStatus();
        loadPhrases();
        // Refresh status every 5 seconds
        setInterval(loadStatus, 5000);
    </script>
</body>
</html>'''
        self.send_html_response(html)

    def log_message(self, format, *args):
        """Override to customize logging."""
        print(f"[Admin] {self.address_string()} - {format % args}")


class BingoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(os.path.dirname(__file__), 'html'), **kwargs)

    def send_json_response(self, data):
        """Send a JSON response."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # API endpoints
        if path == '/join':
            self.handle_join(query)
        elif path == '/game':
            self.handle_game(query)
        elif path == '/cell':
            self.handle_cell(query)
        else:
            # Serve static files
            super().do_GET()

    def handle_join(self, query):
        """Handle /join endpoint - add a new player."""
        room = query.get('room', [''])[0]
        username = query.get('username', [''])[0]

        # Validate room code
        if room != bingo.room:
            self.send_json_response({"error": "Invalid room code"})
            return

        # Validate username
        if not username:
            self.send_json_response({"error": "Missing username"})
            return

        # Check username uniqueness
        for player in bingo.players:
            if player.username == username:
                self.send_json_response({"error": "Username already taken"})
                return

        # Create player with shuffled bingo board
        uid = generate_uid()
        # Calculate required phrases based on grid size
        required_phrases = bingo.grid_size * bingo.grid_size
        if len(bingo.phrases) < required_phrases:
            self.send_json_response({"error": f"Not enough phrases. Need {required_phrases}, have {len(bingo.phrases)}"})
            return
        # Take only the required number of phrases for the grid
        shuffled_phrases = shuffle_phrases(bingo.phrases)[:required_phrases]
        bingo_board = [BingoCell(phrase=phrase) for phrase in shuffled_phrases]
        player = Player(username=username, uid=uid, bingo_board=bingo_board)
        bingo.players.append(player)

        print(f"Player {username} joined with UID {uid}")
        self.send_json_response({"uid": uid})

    def handle_game(self, query):
        """Handle /game endpoint - return all game data."""
        uid = query.get('uid', [''])[0]

        if not uid:
            self.send_json_response({"error": "Missing UID"})
            return

        # Validate UID
        for player in bingo.players:
            if player.uid == uid:
                response = {
                    "topic": bingo.topic,
                    "players": [p.to_dict() for p in bingo.players]
                }
                self.send_json_response(response)
                return

        self.send_json_response({"error": "Invalid UID"})

    def handle_cell(self, query):
        """Handle /cell endpoint - update a bingo cell."""
        uid = query.get('uid', [''])[0]
        cell = query.get('cell', [''])[0]
        marked = query.get('marked', [''])[0]

        # Validate UID
        if not uid:
            self.send_json_response({"error": "Missing UID"})
            return

        # Validate cell
        if not cell:
            self.send_json_response({"error": "Missing cell"})
            return

        try:
            cell_index = int(cell)
        except ValueError:
            self.send_json_response({"error": "Invalid cell"})
            return

        # Validate marked
        if not marked:
            self.send_json_response({"error": "Missing marked"})
            return

        marked_bool = marked.lower() == 'true'

        # Find player
        player_index = -1
        for i, player in enumerate(bingo.players):
            if player.uid == uid:
                player_index = i
                break

        if player_index < 0:
            self.send_json_response({"error": "Invalid UID"})
            return

        # Validate cell index
        if cell_index < 0 or cell_index >= len(bingo.players[player_index].bingo_board):
            self.send_json_response({"error": "Cell out of bounds"})
            return

        # Update cell
        bingo.players[player_index].bingo_board[cell_index].marked = marked_bool
        self.send_json_response({"marked": marked_bool})

    def log_message(self, format, *args):
        """Override to customize logging."""
        print(f"{self.address_string()} - {format % args}")


def main():
    parser = argparse.ArgumentParser(description='Multiplayer Bingo')
    parser.add_argument('--port', type=str, default='8080', help='Port to listen on (game server)')
    parser.add_argument('--admin-port', type=str, default='8081', help='Port for admin interface')
    parser.add_argument('--phrases', type=str, required=True, help='Phrases file to use')
    parser.add_argument('--html', type=str, default='./html', help='Path to HTML directory')
    parser.add_argument('--room', type=str, required=True, help='Room code for players to join')
    parser.add_argument('--topic', type=str, default='Generic Bingo', help='Topic for the game')
    parser.add_argument('--admin-password', type=str, default='admin', help='Admin interface password')
    parser.add_argument('--grid-size', type=int, default=5, choices=[3, 4, 5], help='Grid size: 3x3, 4x4 or 5x5')

    args = parser.parse_args()

    # Load phrases
    try:
        bingo.phrases = load_phrases(args.phrases)
    except Exception as e:
        print(f"Error loading phrases: {e}")
        return

    bingo.phrases_file = args.phrases
    bingo.room = args.room
    bingo.topic = args.topic
    bingo.admin_password = args.admin_password
    bingo.grid_size = args.grid_size

    print("Starting up Multiplayer Bingo...")
    print(f"Room Code: {bingo.room}")
    print(f"Topic: {bingo.topic}")
    print(f"Grid Size: {bingo.grid_size}x{bingo.grid_size}")
    print(f"Admin password: {bingo.admin_password}")

    # Start game server
    game_server_address = ('', int(args.port))
    game_httpd = HTTPServer(game_server_address, BingoHandler)
    game_thread = threading.Thread(target=game_httpd.serve_forever)
    game_thread.daemon = True
    game_thread.start()
    print(f"Game server running on http://localhost:{args.port}")

    # Start admin server
    admin_server_address = ('', int(args.admin_port))
    admin_httpd = HTTPServer(admin_server_address, AdminHandler)
    print(f"Admin interface running on http://localhost:{args.admin_port}")

    try:
        admin_httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        admin_httpd.shutdown()


if __name__ == '__main__':
    main()
