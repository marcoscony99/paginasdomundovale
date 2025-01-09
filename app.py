from flask import Flask, jsonify, render_template
from flask_cors import CORS
import gspread
import json
import os
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from scrape import (
    scrape_oglobo, scrape_nyt, scrape_guardian, scrape_lemonde, scrape_smh,
    scrape_clarin, scrape_corriere, scrape_elpais, scrape_thestar, scrape_lanacion,
    scrape_eluniversal, scrape_ynet, update_spreadsheet
)
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuração de acesso ao Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Obter o conteúdo da variável de ambiente 'GOOGLE_CREDENTIALS_JSON'
credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')

if credentials_json is None:
    raise ValueError("A variável de ambiente 'GOOGLE_CREDENTIALS_JSON' não foi definida.")
else:
    print("Credenciais JSON carregadas com sucesso!")
    credentials_info = json.loads(credentials_json)
    print("Tipo de credencial:", credentials_info.get("type"))

# Carregar as credenciais a partir da variável de ambiente
credentials = Credentials.from_service_account_info(credentials_info, scopes=scope)

# Verificar se as credenciais precisam ser atualizadas
if credentials.expired and credentials.refresh_token:
    credentials.refresh(Request())

# Configurar a variável de ambiente para o script de scraping
os.environ['GOOGLE_CREDENTIALS_JSON'] = json.dumps(credentials_info)

# Autorizar e acessar a planilha
client = gspread.authorize(credentials)
spreadsheet = client.open("paginasdomundo")
worksheet = spreadsheet.sheet1  # Primeira aba da planilha

# Função para carregar dados do Google Sheets
def get_sheet_data():
    rows = worksheet.get_all_records()
    return rows

# Rota para servir a página HTML
@app.route('/')
def index():
    return render_template('index.html')

# Rota para obter os dados do Google Sheets em JSON
@app.route('/get-news', methods=['GET'])
def get_news():
    sheet_data = get_sheet_data()
    news_data = {}
    for row in sheet_data:
        country = row['label']
        news_data[country] = {
            'lat': float(row['lat'].strip('"')) if row['lat'] else 0,
            'lng': float(row['lng'].strip('"')) if row['lng'] else 0,
            'label': country,
            'news': {
                'title': row['Manchete'],
                'link': row['Link'],
                'time': row['Horário']
            }
        }
    return jsonify(news_data)

# Rota para rodar os scrapers e atualizar a planilha
@app.route('/update-news', methods=['GET'])
def update_news():
    try:
        print("Iniciando o scraper e atualização da planilha...")
        update_spreadsheet()  # Função importada do scrape.py
        return jsonify({"message": "Planilha atualizada com sucesso!"}), 200
    except Exception as e:
        print(f"Erro: {str(e)}")
        return jsonify({"message": f"Erro ao atualizar a planilha: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
