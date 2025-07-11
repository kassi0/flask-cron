import requests
import json
from datetime import datetime
import random
import time
import os
from pathlib import Path

# Range do tempo em segundos.
tempo = random.randrange(360, 7200)
#tempo = random.randrange(5, 15)
time.sleep(tempo)

# Caminho para o arquivo JSON que contém o ID do chamado
CAMINHO_JSON = Path(__file__).parent / "ticket_id.json"

# Formata a data e a hora
agora = datetime.now()
data = agora.strftime('%d/%m/%Y')
hora = agora.strftime('%H:%M')

# URL da API GLPI e Tokens de Autenticação
#url_glpi = 'https://sga.detran.ba.gov.br/apirest.php'
url_glpi = 'http://10.21.246.179/apirest.php'
app_token = 'Y8lRyzS0zpULnoNLXUAFtZp7kBdEkTSs1dzgey75'
user_token = 'Axa8urfhkEnIq3lyaUAOMeJjnnzAk0ePwnxawsVu'

# Token e chat_id do Telegram
bot_token = "6449310793:AAHXJ6Xhei4gbs1epuJnacspO_05yD8HaPM"
chat_id = 1475551961  # Seu chat_id

# Cabeçalhos padrão
base_headers = {
    'Content-Type': 'application/json',
    'App-Token': app_token,
    'Authorization': f'user_token {user_token}'
}

# Função para enviar mensagem no Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("Mensagem enviada com sucesso!")
    else:
        print(f"Falha ao enviar a mensagem: {response.status_code}, {response.text}")

# Mensagem no Telegram sobre feriado ou ausência do arquivo
def avisar_feriado_ou_ausencia():
    message = f"Olá Cássio, o arquivo ticket_id.json não foi encontrado. Hoje ({data}) pode ser feriado ou não há chamados para monitorar."
    send_telegram_message(message)

# Abrindo sessão para a API GLPI
def open_session():
    session_url = f'{url_glpi}/initSession'
    response = requests.get(session_url, headers=base_headers)
    if response.status_code == 200:
        session_token = response.json().get('session_token')
        print("Sessão iniciada com sucesso!")
        return session_token
    else:
        print(f"Erro ao iniciar a sessão: {response.status_code}, {response.text}")
        return None

# Adicionar uma nova resposta ao chamado
def add_followup(session_token, ticket_id):
    followup_data = {
        "input": {
            "itemtype": "Ticket",
            "items_id": ticket_id,
            "content": f"Atividades monitoradas e verificadas dia {data} às {hora}hs.",
            "users_id": 2253
        }
    }
    followup_url = f'{url_glpi}/Ticket/{ticket_id}/ITILFollowup'
    headers = base_headers.copy()
    headers['Session-Token'] = session_token
    
    response = requests.post(followup_url, headers=headers, data=json.dumps(followup_data))
    if response.status_code == 201:
        print(f"Resposta adicionada ao chamado {ticket_id} com sucesso!")
    else:
        print(f"Erro ao adicionar resposta ao chamado: {response.status_code}, {response.text}")

# Ler o ID do chamado do arquivo JSON
def ler_ticket_id(caminho_json):
    try:
        with open(caminho_json, 'r') as json_file:
            dados = json.load(json_file)
            return dados.get('ticket_id')
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        print(f"Erro ao ler o arquivo JSON: {e}")
        return None

# Função principal
def executar_funcao_principal():
    session_token = open_session()
    if session_token:
        ticket_id = ler_ticket_id(CAMINHO_JSON)
        if ticket_id:
            add_followup(session_token, ticket_id)
            message = f"Olá Cássio, seu chamado nº: {ticket_id} foi adicionado uma resposta em {data} às {hora}hs."
            send_telegram_message(message)
        else:
            print("Não foi possível encontrar o ID do chamado no arquivo JSON.")

# Verifica a existência do arquivo JSON
if __name__ == '__main__':
    if os.path.exists(CAMINHO_JSON):
        executar_funcao_principal()
    else:
        avisar_feriado_ou_ausencia()
