from flask import Flask, request, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

app = Flask(__name__)

# Habilitar CORS para todas as origens
CORS(app, origins=["http://localhost:3001"])

# Configuração do banco de dados
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '02101418',
    'database': 'meu_banco'
}

# Função para criar a conexão com o banco de dados
def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn

# Endpoint para cadastrar um novo usuário
@app.route('/usuarios', methods=['POST'])
def criar_usuario():
    try:
        novo_usuario = request.get_json()
        nome = novo_usuario['nome']
        email = novo_usuario['email']
        senha = novo_usuario['senha']  # A senha será recebida em texto simples

        # Gerar o hash da senha antes de salvar no banco de dados
        senha_hash = generate_password_hash(senha)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Inserir o usuário no banco de dados
        cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)", 
                       (nome, email, senha_hash))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "Usuário criado com sucesso!"}), 201

    except mysql.connector.Error as err:
        print(f"Erro no MySQL: {err}")
        return jsonify({'error': 'Erro ao conectar com o banco de dados'}), 500
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({'error': 'Erro inesperado no servidor'}), 500

# Endpoint para fazer login do usuário
@app.route('/login', methods=['POST'])
def login_usuario():
    try:
        dados_login = request.get_json()
        email = dados_login['email']
        senha = dados_login['senha']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Verifica se o email existe
        cursor.execute("SELECT senha FROM usuarios WHERE email = %s", (email,))
        resultado = cursor.fetchone()

        if resultado is None:
            return jsonify({'error': 'Usuário não encontrado'}), 404

        senha_armazenada = resultado[0]

        # Verifica se a senha fornecida é igual à armazenada no banco (comparação com hash)
        if not check_password_hash(senha_armazenada, senha):
            return jsonify({'error': 'Senha incorreta'}), 401

        return jsonify({'message': 'Login bem-sucedido!'}), 200

    except mysql.connector.Error as err:
        print(f"Erro no MySQL: {err}")
        return jsonify({'error': 'Erro ao conectar com o banco de dados'}), 500
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({'error': 'Erro inesperado no servidor'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
