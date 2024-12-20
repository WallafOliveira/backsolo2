from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
import pandas as pd
from datetime import datetime
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

    colunas_mapeadas = {
        "id": "Id",
        "ph": "Ph",
        "umidade": "Umidade",
        "temperatura": "Temperatura",
        "nitrogenio": "Nitrogênio",
        "fosforo": "Fósforo",
        "potassio": "Potássio",
        "microbioma": "Microbioma",
        "data_hora": "Data e Hora"
    }

    dados_formatados = []
    for dado in dados:
        dado_formatado = {colunas_mapeadas[k]: v for k, v in dado.items()}
        dados_formatados.append(dado_formatado)

    return jsonify(dados_formatados)

# Rota para inserir novos dados do solo no banco de dados
@app.route('/api/solo', methods=['POST'])
def add_solo():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()

    data_hora_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        INSERT INTO solo (ph, umidade, temperatura, nitrogenio, fosforo, potassio, microbioma, data_hora)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data['ph'], data['umidade'], data['temperatura'], data['nitrogenio'], data['fosforo'], data['potassio'], data['microbioma'], data_hora_atual))
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

    if not condicoes_anormais:
        return jsonify({"message": "Todos os parâmetros estão dentro da faixa ideal."})

    return jsonify(condicoes_anormais)

# Rota para análise estatística dos dados
@app.route('/api/analise_estatistica', methods=['GET'])
def analise_estatistica():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM solo")
    dados = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if not dados:
        return jsonify({"message": "Não há dados para análise."}), 404

    df = pd.DataFrame(dados)
    resumo_estatistico = df.describe().to_dict()

    correlacoes = df.corr(method='pearson').to_dict()

    p_values = {}
    for col in df.columns[1:]:  # Ignorando a coluna 'id'
        _, p_value = stats.pearsonr(df['ph'], df[col])
        p_values[col] = p_value

    return jsonify({
        "message": "Análise estatística realizada com sucesso.",
        "resumo_estatistico": resumo_estatistico,
        "correlacoes": correlacoes,
        "p_values": p_values
    })

# Inicializar a tabela no banco de dados
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
        microbioma REAL,
        data_hora TEXT
    )
    ''')
    conn.commit()
    conn.close()

# Inicialização da aplicação
if __name__ == '__main__':
    inicializar_banco()  # Cria a tabela solo caso ainda não exista
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))