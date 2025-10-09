from flask import Flask, request, jsonify, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'

DATABASE = 'restaurant.db'

def get_db_connection():
    """Retorna uma nova conexão com o banco de dados."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.commit()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400
    hashed_password = generate_password_hash(password)
    try:
        with get_db_connection() as conn:
            conn.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hashed_password))
            conn.commit()
        return jsonify({'message': 'Cadastro realizado com sucesso!'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email já cadastrado'}), 409

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    with get_db_connection() as conn:
        user = conn.execute('SELECT password FROM users WHERE email = ?', (email,)).fetchone()
    if user and check_password_hash(user['password'], password):
        session['user'] = email
        return jsonify({'message': 'Login realizado com sucesso!'}), 200
    return jsonify({'error': 'Credenciais inválidas'}), 401

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
