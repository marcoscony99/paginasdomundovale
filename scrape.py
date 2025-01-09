import gspread
import json
import os
from google.oauth2.service_account import Credentials
from bs4 import BeautifulSoup
import requests
from datetime import datetime

# Obter o conteúdo da variável de ambiente 'GOOGLE_CREDENTIALS_JSON'
credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')

if not credentials_json:
    raise ValueError("A variável de ambiente 'GOOGLE_CREDENTIALS_JSON' não foi definida.")

# Defina o escopo para acessar a planilha
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Carregar as credenciais a partir da variável de ambiente
credentials_info = json.loads(credentials_json)
credentials = Credentials.from_service_account_info(credentials_info, scopes=scope)

# Autentique a conta de serviço
client = gspread.authorize(credentials)

# Abra a planilha pelo nome
spreadsheet = client.open("paginasdomundo")
worksheet = spreadsheet.sheet1  # Acessa a primeira aba da planilha

# Funções de scraping para cada site
def scrape_oglobo():
    # URL da página principal de O Globo
    url = 'https://oglobo.globo.com/'

    # Fazendo a requisição para a página
    response = requests.get(url)

    # Verificando se a requisição foi bem-sucedida
    if response.status_code == 200:
        # Criando o objeto BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Procurar a manchete principal
        headline_anchor = soup.find('a', class_=lambda x: x and 'container-sete-destaques__url' in x)

        if headline_anchor:
            # Tenta obter o link do atributo 'href'
            link_url = headline_anchor.get('href', "Link não encontrado")

            # Busca o título dentro do link
            title_element = headline_anchor.find('h2', class_=lambda x: x and 'container-sete-destaques__title' in x)
            title_text = title_element.get_text(strip=True) if title_element else "Título não encontrado"

            # Retorna os dados como dicionário
            return {'title': title_text, 'link': link_url}
        else:
            return {'title': "Manchete principal não encontrada.", 'link': None}
    else:
        return {'title': f"Falha ao acessar a página. Código de status: {response.status_code}", 'link': None}

def scrape_nyt():
    url = 'https://www.nytimes.com/'
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        headline_section = soup.find('section', class_=lambda x: x and 'story-wrapper' in x)

        if headline_section:
            headline_link = headline_section.find('a', href=True)
            if headline_link:
                link_url = headline_link['href']
                headline_title = headline_link.find('p')

                if headline_title:
                    title_text = headline_title.get_text(strip=True)
                    return {'title': title_text, 'link': link_url}

    return {'title': "Notícia não encontrada.", 'link': None}

def scrape_guardian():
    url = 'https://www.theguardian.com/international'
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('a', attrs={'aria-label': True, 'href': True})

        if articles:
            first_article = articles[0]
            title = first_article['aria-label']
            link = first_article['href']
            return {'title': title, 'link': f"https://www.theguardian.com{link}" if link.startswith('/') else link}

    return {'title': "Notícia não encontrada.", 'link': None}

def scrape_lemonde():
    url = 'https://www.lemonde.fr/'
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        main_article_div = soup.find('div', class_='article article--main')

        if main_article_div:
            headline_link = main_article_div.find('a', href=True)
            link_url = headline_link['href'] if headline_link else None
            headline_title = main_article_div.find('p', class_='article__title-label')
            title_text = headline_title.get_text(strip=True) if headline_title else None

            if link_url and title_text:
                return {'title': title_text, 'link': link_url}

    return {'title': "Manchete principal não encontrada.", 'link': None}

def scrape_smh():
    url = "https://www.smh.com.au/"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        headline = soup.find('h3', class_='_2XVos _1SXCB')

        if headline:
            title = headline.get_text(strip=True)
            link = headline.find('a', href=True)
            if link:
                complete_url = f"https://www.smh.com.au{link['href']}"
            else:
                complete_url = "Link não encontrado."
            return {'title': title, 'link': complete_url}
        else:
            return {'title': "Manchete principal não encontrada.", 'link': None}
    else:
        return {'title': f"Falha ao acessar a página: {response.status_code}", 'link': None}

def scrape_clarin():
    url = 'https://www.clarin.com/'
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        headline_article = soup.find('article')
        
        if headline_article:
            headline_h2 = headline_article.find('h2', class_='title')
            
            if headline_h2:
                title_text = headline_h2.get_text(strip=True)
                
                # Encontrar o link associado à manchete
                headline_link = headline_article.find('a', attrs={'aria-label': True})
                
                if headline_link:
                    link_url = headline_link['href']
                    # Garantir que o link seja absoluto (caso seja relativo)
                    if not link_url.startswith('http'):
                        link_url = 'https://www.clarin.com' + link_url
                else:
                    link_url = "Link não encontrado."
                
                return {'title': title_text, 'link': link_url}
            else:
                return {'title': "Título não encontrado.", 'link': None}
        else:
            return {'title': "Artigo não encontrado.", 'link': None}
    else:
        return {'title': f"Falha ao acessar a página: {response.status_code}", 'link': None}

def scrape_corriere():
    url = 'https://www.corriere.it/'
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        main_article = soup.find('h4', class_='title-art-hp is-line-h-106 is-medium')

        if main_article:
            title_link = main_article.find('a', class_='has-text-black')
            if title_link:
                title_text = title_link.get_text(strip=True)
                link_url = title_link['href']
                return {'title': title_text, 'link': link_url}
            else:
                return {'title': "Título não encontrado.", 'link': None}
        else:
            return {'title': "Manchete principal não encontrada.", 'link': None}
    else:
        return {'title': f"Falha ao acessar a página: {response.status_code}", 'link': None}

def scrape_elpais():
    url = 'https://elpais.com/america'
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        headline_h2 = soup.find('h2', class_='c_t')

        if headline_h2:
            headline_link = headline_h2.find('a')
            if headline_link and 'href' in headline_link.attrs:
                title_text = headline_link.get_text(strip=True)
                link_url = headline_link['href']
                complete_url = link_url if link_url.startswith("https") else f"https://elpais.com{link_url}"
                return {'title': title_text, 'link': complete_url}
            else:
                return {'title': "Link da notícia não encontrado.", 'link': None}
        else:
            return {'title': "Manchete não encontrada.", 'link': None}
    else:
        return {'title': f"Falha ao acessar a página. Código de status: {response.status_code}", 'link': None}


def scrape_thestar():
    # URL da página principal do The Star
    url = 'https://www.thestar.com/'

    # Fazendo a requisição para a página
    response = requests.get(url)

    # Verificando se a requisição foi bem-sucedida
    if response.status_code == 200:
        # Criando o objeto BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Buscando o elemento h3 com a classe "tnt-headline" que contém a manchete principal
        headline_h3 = soup.find('h3', class_="tnt-headline")

        if headline_h3:
            # Encontrando o link dentro do h3
            headline_link = headline_h3.find('a', class_="tnt-asset-link")

            if headline_link and 'href' in headline_link.attrs:
                # Extraindo o título e o link
                title_text = headline_link.get_text(strip=True)
                link_url = headline_link['href']

                # Construindo a URL completa
                complete_url = f"https://www.thestar.com{link_url}"

                # Retornando as informações como um dicionário
                return {
                    'title': title_text,
                    'link': complete_url
                }
            else:
                return {"error": "Link da notícia não encontrado."}
        else:
            return {"error": "Manchete não encontrada."}
    else:
        return {"error": f"Falha ao acessar a página: {response.status_code}"}
    

def scrape_lanacion():
    url = 'https://www.lanacion.com.py/'

    # Fazendo a requisição para a página
    response = requests.get(url)

    # Verificando se a requisição foi bem-sucedida
    if response.status_code == 200:
        # Criando o objeto BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Buscando a div com a classe "lay-home" que contém a manchete principal
        lay_home_div = soup.find('div', class_="lay-home")

        # Verificando se a div foi encontrada
        if lay_home_div:
            headline_h3 = lay_home_div.find('h3')
            headline_link_div = lay_home_div.find('div', class_="tc")

            if headline_h3 and headline_link_div:
                headline_link = headline_link_div.find('a')

                if headline_link and 'href' in headline_link.attrs:
                    title_text = headline_h3.get_text(strip=True)
                    link_url = headline_link['href']

                    # Construindo a URL completa se o link for relativo
                    complete_url = link_url if link_url.startswith('http') else f"https://www.lanacion.com.py{link_url}"

                    return {
                        'title': title_text,
                        'link': complete_url
                    }
    # Caso algum erro aconteça ou a estrutura da página não seja encontrada
    return {"error": "Estrutura da página não encontrada ou erro ao acessar."}


def scrape_eluniversal():
    url = 'https://www.eluniversal.com.mx/'

    # Fazendo a requisição para a página
    response = requests.get(url)

    # Verificando se a requisição foi bem-sucedida
    if response.status_code == 200:
        # Criando o objeto BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Encontrando o primeiro link com a classe específica para a manchete
        headline_link = soup.find('a', class_="cards-story-opener-fr")

        if headline_link and 'href' in headline_link.attrs:
            # Extraindo o título e o link
            title_text = headline_link.get('data-cta', '').strip()
            link_url = headline_link['href']

            # Construindo a URL completa se o link for relativo
            complete_url = link_url if link_url.startswith('http') else f"https://www.eluniversal.com.mx{link_url}"

            # Retornando como dicionário
            return {
                'title': title_text,
                'link': complete_url
            }
    # Caso algum erro aconteça ou a estrutura da página não seja encontrada
    return {"error": "Estrutura da página não encontrada ou erro ao acessar."}


def scrape_ynet():
    url = 'https://www.ynetnews.com/'

    # Fazendo a requisição para a página
    response = requests.get(url)

    # Verificando se a requisição foi bem-sucedida
    if response.status_code == 200:
        # Criando o objeto BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Encontrando o título da manchete dentro do h1 com a classe slotTitle
        headline_title = soup.find('h1', class_="slotTitle")
        title_text = headline_title.get_text(strip=True) if headline_title else None

        # Encontrando o link da manchete no primeiro href dentro da classe textDiv
        text_div = soup.find(class_="textDiv")
        if text_div:
            headline_link = text_div.find('a')
            if headline_link and 'href' in headline_link.attrs:
                link_url = headline_link['href']

                # Verificando se o link é relativo e ajustando para uma URL completa
                if not link_url.startswith('http'):
                    complete_url = f"https://www.ynetnews.com{link_url}"
                else:
                    complete_url = link_url

                return {
                    'title': title_text,
                    'link': complete_url
                }
            else:
                return {"error": "Link da notícia não encontrado."}
        else:
            return {"error": "Estrutura da manchete não encontrada."}
    else:
        return {"error": f"Falha ao acessar a página: {response.status_code}"}



def scrape_sowetan():
    url = 'https://www.sowetanlive.co.za/'

    # Fazendo a requisição para a página
    response = requests.get(url)

    # Verificando se a requisição foi bem-sucedida
    if response.status_code == 200:
        # Criando o objeto BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Encontrando o div com a classe first-article
        first_article = soup.find('div', class_='first-article')

        if first_article:
            # Extraindo o título do primeiro <h2> dentro do div
            title_element = first_article.find('h2')
            title_text = title_element.get_text(strip=True) if title_element else "Título não encontrado"

            # Extraindo o link do primeiro <a> que contém o h2
            link_element = title_element.find_parent('a', href=True) if title_element else None
            link_url = link_element['href'] if link_element else "Link não encontrado"

            # Concatenando com a URL base
            if link_url and link_url.startswith('/'):
                link_url = url.rstrip('/') + link_url  # Concatena a URL base com o href

            # Retorna o título e o link
            return {
                'title': title_text,
                'link': link_url
            }
    # Caso algum erro aconteça ou a estrutura da página não seja encontrada
    return {"error": "Falha ao acessar a página ou estrutura não encontrada."}


# Função para preencher a planilha com os resultados
def update_spreadsheet():
    row = 2  # Começar na segunda linha da planilha
    
    # Defina os sites que você quer raspar
    scraping_functions = [
        scrape_oglobo,  # Adicione as outras funções de scraping aqui
        scrape_nyt,
        scrape_guardian,
        scrape_lemonde,
        scrape_smh,
        scrape_clarin,
        scrape_corriere,
        scrape_elpais,
        scrape_thestar,
        scrape_lanacion,
        scrape_eluniversal,
        scrape_ynet,
        scrape_sowetan
    ]
    
    for scrape_function in scraping_functions:
        news_data = scrape_function()  # Realiza o scraping
        
        if news_data and news_data['link']:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Hora da raspagem
            worksheet.update_cell(row, 1, scrape_function.__name__.replace("scrape_", "").capitalize())  # País
            worksheet.update_cell(row, 2, news_data['link'])  # Link da notícia
            worksheet.update_cell(row, 3, news_data['title'])  # Título da notícia
            worksheet.update_cell(row, 4, current_time)  # Hora da raspagem
            row += 1  # Incrementa para a próxima linha

  
# Atualize a planilha com os dados de scraping
if __name__ == "__main__":
    update_spreadsheet()