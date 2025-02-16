from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}  # Almacena el estado de las partidas
players = {}  # Almacena los jugadores en cada sala
turns = {}  # Lleva control de los turnos (X primero)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game/<room_id>')
def game(room_id):
    return render_template('index.html', room=room_id)

@socketio.on('connect')
def handle_connect():
    print('Usuario conectado')

@socketio.on('join')
def handle_join(data):
    room = data['room']
    name = data['name']
    join_room(room)

    if room not in rooms:
        rooms[room] = [""] * 9  # Tablero vacío
        players[room] = []
        turns[room] = "X"  # X siempre inicia

    if name not in players[room]:
        if len(players[room]) < 2:  # Solo pueden haber 2 jugadores
            players[room].append(name)
        else:
            emit('error', {'message': 'La sala ya está llena'}, room=request.sid)
            return

    emit('update', {'board': rooms[room], 'players': players[room], 'turn': turns[room]}, room=room)

@socketio.on('move')
def handle_move(data):
    room = data['room']
    position = int(data['position'])
    player = data['player']

    if rooms[room][position] == "" and player == turns[room]:  # Verifica si la celda está vacía y si es su turno
        rooms[room][position] = player  # Marca la celda

        winner = check_winner(rooms[room])
        if winner:
            emit("game_over", {"winner": player}, room=room)
            return
        
        # Cambiar turno
        turns[room] = "O" if turns[room] == "X" else "X"
        emit("update_board", {"board": rooms[room], "turn": turns[room]}, room=room)
    else:
        emit('error', {'message': 'Movimiento inválido'}, room=request.sid)

def check_winner(board):
    winning_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Filas
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columnas
        [0, 4, 8], [2, 4, 6]  # Diagonales
    ]

    for combo in winning_combinations:
        if board[combo[0]] != "" and board[combo[0]] == board[combo[1]] == board[combo[2]]:
            return board[combo[0]]
    return None

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=9000, debug=True)
