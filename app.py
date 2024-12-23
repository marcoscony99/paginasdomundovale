from flask import Flask, jsonify, render_template
from flask_cors import CORS
import scrape  # Importa o módulo de scraping

app = Flask(__name__)
CORS(app)

# Rota principal
@app.route('/')
def index():
    return render_template('index.html')

# Rota para obter dados da planilha
@app.route('/get-news', methods=['GET'])
def get_news():
    try:
        # Obtem os dados da planilha usando a função do módulo `scrape`
        rows = scrape.worksheet.get_all_records()
        news_data = {
            row['label']: {
                'lat': float(row['lat'].strip('"')),
                'lng': float(row['lng'].strip('"')),
                'label': row['label'],
                'news': {
                    'title': row['Manchete'],
                    'link': row['Link'],
                    'time': row['Horário']
                }
            }
            for row in rows
        }
        return jsonify(news_data)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# Rota para executar o scraping
@app.route('/run-scraping', methods=['GET'])
def run_scraping():
    try:
        scrape.update_spreadsheet()  # Chama a função de atualização do módulo
        return jsonify({'status': 'success', 'message': 'Scraping e atualização do Google Sheets concluídos!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
