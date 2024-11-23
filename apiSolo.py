from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
import pandas as pd
from scipy import stats

app = Flask(__name__)
CORS(app)

# Conectar ao banco de dados MySQL
def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",  # Seu usuário do MySQL
        password="02101418",  # Sua senha do MySQL
        database="meu_banco"  # Nome do banco de dados
    )
    return conn

# Rota para obter todos os dados da tabela solo
@app.route('/api/solo', methods=['GET'])
def get_solo():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM solo")
    dados = cursor.fetchall()
    conn.close()
    return jsonify(dados)

# Rota para inserir novos dados do solo no banco de dados
@app.route('/api/solo', methods=['POST'])
def add_solo():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO solo (ph, umidade, temperatura, nitrogenio, fosforo, potassio, microbioma)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
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
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM solo")
    dados = cursor.fetchall()
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

# Rota para análise estatística dos dados
@app.route('/api/analise_estatistica', methods=['GET'])
def analise_estatistica():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM solo")
    dados = cursor.fetchall()
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
        "resumo_estatistico": resumo_estatistico,
        "correlacoes": correlacoes,
        "p_values": p_values
    })

# Inicializar a tabela no banco de dados
def inicializar_banco():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS solo (
        id INT AUTO_INCREMENT PRIMARY KEY,
        ph FLOAT,
        umidade FLOAT,
        temperatura FLOAT,
        nitrogenio FLOAT,
        fosforo FLOAT,
        potassio FLOAT,
        microbioma FLOAT
    )
    ''')
    conn.commit()
    conn.close()

# Inicialização da aplicação
if __name__ == '__main__':
    inicializar_banco()  # Cria a tabela solo caso ainda não exista
    app.run(debug=True)
