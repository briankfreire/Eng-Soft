from flask import Flask, request, jsonify, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'

def init_db():
    conn = sqlite3.connect('restaurant.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400
    hashed_password = generate_password_hash(password)
    try:
        conn = sqlite3.connect('restaurant.db')
        c = conn.cursor()
        c.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hashed_password))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Cadastro realizado com sucesso!'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email já cadastrado'}), 409

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    conn = sqlite3.connect('restaurant.db')
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    if user and check_password_hash(user[0], password):
        session['user'] = email
        return jsonify({'message': 'Login realizado com sucesso!'}), 200
    return jsonify({'error': 'Credenciais inválidas'}), 401

if __name__ == '__main__':
    init_db()
    app.run(debug=True)