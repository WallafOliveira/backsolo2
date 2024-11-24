from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
import pandas as pd
from scipy import stats

app = Flask(__name__)
CORS(app)

# Caminho para o banco de dados SQLite dentro da pasta persistente do Render
db_path = os.path.join(os.getcwd(), 'data', 'meu_banco.db')

# Função para conectar ao banco de dados SQLite
def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Permite acessar as colunas por nome
    return conn

# Rota para obter todos os dados da tabela solo
@app.route('/api/solo', methods=['GET'])
def get_solo():
    conn = get_db_connection()
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

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(''' 
        INSERT INTO solo (ph, umidade, temperatura, nitrogenio, fosforo, potassio, microbioma)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (data['ph'], data['umidade'], data['temperatura'], data['nitrogenio'], data['fosforo'], data['potassio'], data['microbioma']))
    conn.commit()
    conn.close()

    return jsonify({"message": "Dados inseridos com sucesso"}), 201

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
