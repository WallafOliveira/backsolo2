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

# Rota para obter todas as condições anormais
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

# Função para inicializar o banco de dados e criar a tabela
def inicializar_banco():
    if not os.path.exists(os.path.join(os.getcwd(), 'data')):
        os.makedirs(os.path.join(os.getcwd(), 'data'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS solo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ph REAL,
        umidade REAL,
        temperatura REAL,
        nitrogenio REAL,
        fosforo REAL,
        potassio REAL,
        microbioma REAL
    )
    ''')
    conn.commit()
    conn.close()

# Inicializar a aplicação
if __name__ == '__main__':
    inicializar_banco()  # Cria a tabela caso ainda não exista
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
