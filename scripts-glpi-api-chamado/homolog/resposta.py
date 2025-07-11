import requests
import json
from datetime import datetime
import random
import time

# Range do tempo em segundos.
tempo = random.randrange(120, 7200)
time.sleep(tempo)

# Id do usuário para Resposta
user_id=2253

# Caminho para o arquivo JSON que contém o ID do chamado
caminho_json = '/root/kassio/ticket_id.json'

# Formata a data e a hora
agora = datetime.now()
data = agora.strftime('%d/%m/%Y')
hora = agora.strftime('%H:%M')

# URL da API GLPI
url_glpi = 'https://sga.detran.ba.gov.br/apirest.php'

# Token de autenticação
app_token = 'Y8lRyzS0zpULnoNLXUAFtZp7kBdEkTSs1dzgey75'
user_token = 'Axa8urfhkEnIq3lyaUAOMeJjnnzAk0ePwnxawsVu'

# Cabeçalhos para autenticação
headers = {
    'Content-Type': 'application/json',
    'App-Token': app_token,
    'Authorization': f'user_token {user_token}'
}

# Abrindo sessão para a API GLPI
def open_session():
    session_url = f'{url_glpi}/initSession'
    response = requests.get(session_url, headers=headers)
    if response.status_code == 200:
        session_token = response.json()['session_token']
        print("Sessão iniciada com sucesso!")
        return session_token
    else:
        print(f"Erro ao iniciar a sessão: {response.status_code}")
        return None

# Função para adicionar uma nova resposta ao chamado
def add_followup(session_token, ticket_id):
    followup_data = {
        "input": {
            "itemtype": "Ticket",
            "items_id": ticket_id,
            "content": f"Atividades monitoradas e verificadas dia {data} às {hora}hs.",
            "users_id": user_id  # ID do usuário que adiciona a resposta
        }
    }
    followup_url = f'{url_glpi}/Ticket/{ticket_id}/ITILFollowup'
    headers['Session-Token'] = session_token
    
    response = requests.post(followup_url, headers=headers, data=json.dumps(followup_data))
    
    if response.status_code == 201:
        print(f"Resposta adicionada ao chamado {ticket_id} com sucesso!")
    else:
        print(f"Erro ao adicionar resposta ao chamado: {response.status_code}, {response.text}")

# Função do Telegram
def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message
    }

    response = requests.post(url, data=data)
    
    if response.status_code == 200:
        print("Mensagem enviada com sucesso!")
    else:
        print(f"Falha ao enviar a mensagem. Código de status: {response.status_code}")
        print(response.text)

def telegram():
    bot_token = "6449310793:AAHXJ6Xhei4gbs1epuJnacspO_05yD8HaPM"
    chat_id = 1475551961  # Seu chat_id
    message = f"Olá Cássio, seu chamado nº: {ticket_id} foi adicionado uma resposta {data} às {hora}hs."
    send_telegram_message(bot_token, chat_id, message)

# Função para ler o ID do chamado do arquivo JSON
def ler_ticket_id(caminho_json):
    try:
        with open(caminho_json, 'r') as json_file:
            dados = json.load(json_file)
            return dados['ticket_id']
    except (FileNotFoundError, KeyError) as e:
        print(f"Erro ao ler o arquivo JSON: {e}")
        return None

# Onde puxa as funções.
if __name__ == '__main__':
    session_token = open_session()
    if session_token:
        # Ler o ID do chamado existente
        ticket_id = ler_ticket_id(caminho_json)
        
        if ticket_id:
            # Adiciona uma resposta ao chamado com a data e hora
            add_followup(session_token, ticket_id)
            telegram()

        else:
            print("Não foi possível encontrar o ID do chamado.")

