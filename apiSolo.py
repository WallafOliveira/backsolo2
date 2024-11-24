from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)

# Caminho para o banco de dados SQLite dentro da pasta persistente do Render
# Usando uma variável de ambiente para configurar o caminho
db_path = os.getenv('DATABASE_URL', os.path.join(os.getcwd(), 'data', 'meu_banco.db'))

# Função para conectar ao banco de dados SQLite
def get_db_connection():
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Permite acessar as colunas por nome
        return conn
    except sqlite3.DatabaseError as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

# Rota para obter todos os dados da tabela solo
@app.route('/api/solo', methods=['GET'])
def get_solo():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Erro ao conectar ao banco de dados"}), 500
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM solo")
    dados = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify(dados)

# Rota para inserir novos dados do solo no banco de dados
@app.route('/api/solo', methods=['POST'])
def add_solo():
    data = request.get_json()
    print(f"Dados recebidos: {data}")  # Log para verificar os dados recebidos

    # Verificando se todos os campos necessários estão presentes
    required_fields = ["ph", "umidade", "temperatura", "nitrogenio", "fosforo", "potassio", "microbioma"]
    if not all(key in data for key in required_fields):
        return jsonify({"error": "Campos obrigatórios ausentes"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Erro ao conectar ao banco de dados"}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO solo (ph, umidade, temperatura, nitrogenio, fosforo, potassio, microbioma)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (data['ph'], data['umidade'], data['temperatura'], data['nitrogenio'], data['fosforo'], data['potassio'], data['microbioma']))
        conn.commit()
        conn.close()
        return jsonify({"message": "Dados inseridos com sucesso"}), 201
    except sqlite3.DatabaseError as e:
        conn.close()
        return jsonify({"error": f"Erro ao inserir dados: {str(e)}"}), 500

# Rota para obter condições anormais e recomendações
@app.route('/api/condicoes_anormais', methods=['GET'])
def get_condicoes_anormais():
    faixa_ideal = {
        "ph": (6.0, 7.5),
        "umidade": (25, 40),
        "temperatura": (15, 30),
        "nitrogenio": (20, 50),
        "fosforo": (10, 30),
        "potassio": (15, 40),
        "microbioma": (4.5, 6.0)
    }

    tratamentos_recomendados = {
        "ph": "Adicionar calcário para aumentar o pH.",
        "umidade": "Irrigar a área para aumentar a umidade.",
        "temperatura": "Usar mulching para controlar a temperatura.",
        "nitrogenio": "Adicionar adubo nitrogenado.",
        "fosforo": "Adicionar fertilizantes fosfatados.",
        "potassio": "Adicionar fertilizantes ricos em potássio.",
        "microbioma": "Incorporar matéria orgânica ao solo."
    }

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Erro ao conectar ao banco de dados"}), 500
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM solo")
    dados = [dict(row) for row in cursor.fetchall()]
    conn.close()

    condicoes_anormais = []
    for row in dados:
        condicoes = {}
        for parametro, (min_ideal, max_ideal) in faixa_ideal.items():
            valor = row[parametro]
            if valor < min_ideal:
                condicoes[parametro] = f"Baixo ({valor}). Ação: aumentar."
            elif valor > max_ideal:
                condicoes[parametro] = f"Alto ({valor}). Ação: reduzir."
        if condicoes:
            condicoes_anormais.append({
                "id": row["id"],
                "condicoes": condicoes,
                "tratamentos": {parametro: tratamentos_recomendados[parametro] for parametro in condicoes.keys()}
            })

    return jsonify(condicoes_anormais)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
