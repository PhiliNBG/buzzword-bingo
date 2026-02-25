$(function () {
    var URL_PREFIX = location.protocol + '//' + location.hostname + (location.port ? ':' + location.port : '');
    var g_username, g_uid, g_grid_size = 5;

    var createBingoCard = function (username, board, isOwnCard) {
        var $player = $('<div class="bingo-player">').addClass(isOwnCard ? 'own-card' : 'other-card');
        var $card = $('<div class="bingo-card grid-' + g_grid_size + '">');

        for (var i = 0; i < board.length; i++) {
            var $cell = $('<div class="bingo-cell">');
            // Only show words on your own card, not on other players' cards
            if (isOwnCard) {
                $cell.append($('<div>').text(board[i].phrase));
            } else {
                $cell.append($('<div>'));
            }
            if (board[i].marked) {
                $cell.addClass('marked');
            }
            $card.append($cell);
        }

        $player.append('<h2>' + username + '</h2>').append($card);
        return $player;
    };

    var refreshGame = function () {
        $.get(URL_PREFIX + '/game', { uid: g_uid }, function (data) {
            if (data.error) {
                alert(data.error);
                return;
            }
            
            $('#topic span').text(data.topic);
            $('#topic').show();
            $('#bingo').empty();
            
            if (data.players.length > 0) {
                g_grid_size = Math.round(Math.sqrt(data.players[0].bingo_board.length));
            }
            
            // Add your card first
            data.players.forEach(function (player) {
                if (player.username === g_username) {
                    $('#bingo').append(createBingoCard(player.username, player.bingo_board, true));
                }
            });
            
            // Add other players
            var others = data.players.filter(function (p) { return p.username !== g_username; });
            
            if (others.length > 0) {
                var $container = $('<div class="other-players-container">')
                    .append('<div class="other-players-header">Other Players (' + others.length + ')</div>');
                
                others.forEach(function (player) {
                    $container.append(createBingoCard(player.username, player.bingo_board, false));
                });
                
                $('#bingo').append($container);
            } else {
                $('#bingo').append('<div class="no-other-players">No other players yet. Share the room code!</div>');
            }
        });
    };

    $('#joinForm').submit(function (evt) {
        evt.preventDefault();
        g_username = $('#joinUsername').val();
        var room = $('#joinRoom').val();
        
        $.get(URL_PREFIX + '/join', { username: g_username, room: room }, function (data) {
            if (data.error) {
                alert(data.error);
            } else {
                g_uid = data.uid;
                $('#join').hide();
                $('#uid span').text(g_uid);
                $('#uid').show();
                refreshGame();
                setInterval(refreshGame, 3000);
            }
        });
    });

    $('#rejoinForm').submit(function (evt) {
        evt.preventDefault();
        g_username = $('#rejoinUsername').val();
        g_uid = $('#rejoinUID').val();
        $('#join').hide();
        $('#uid span').text(g_uid);
        $('#uid').show();
        refreshGame();
        setInterval(refreshGame, 3000);
    });

    $('#bingo').delegate('.bingo-player.own-card .bingo-cell', 'click', function () {
        var $cell = $(this);
        var cell = $cell.index();
        var marked = !$cell.hasClass('marked');
        
        $.get(URL_PREFIX + '/cell', { uid: g_uid, cell: cell, marked: marked }, function (data) {
            if (data.error) {
                alert(data.error);
            } else {
                $cell.toggleClass('marked', data.marked);
            }
        });
    });
});
