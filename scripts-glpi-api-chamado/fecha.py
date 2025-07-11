import requests
import json
import os
from pathlib import Path

# Caminho para o arquivo JSON que contém o ID do chamado
#ticket_caminho = '/root/kassio/homolog/ticket_id.json'
CAMINHO_JSON = Path(__file__).parent / "ticket_id.json"

# URL da API GLPI
#url_glpi = 'https://sga.detran.ba.gov.br/apirest.php'
url_glpi = 'http://10.21.246.179/apirest.php'

# Tokens de autenticação
app_token = 'Y8lRyzS0zpULnoNLXUAFtZp7kBdEkTSs1dzgey75'
user_token = 'Axa8urfhkEnIq3lyaUAOMeJjnnzAk0ePwnxawsVu'

# Telegram
bot_token = "6449310793:AAHXJ6Xhei4gbs1epuJnacspO_05yD8HaPM"
chat_id = 1475551961  # Seu chat_id

# Cabeçalhos para autenticação
headers = {
    'Content-Type': 'application/json',
    'App-Token': app_token,
    'Authorization': f'user_token {user_token}'
}

# Função para enviar mensagem via Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("Mensagem enviada com sucesso!")
    else:
        print(f"Falha ao enviar a mensagem: {response.status_code}, {response.text}")

# Aviso de feriado ou ausência do arquivo
def avisar_feriado_ou_ausencia():
    message = (
        "Olá Cássio, o arquivo 'ticket_id.json' não foi encontrado. "
        "Hoje pode ser feriado ou não há chamados para monitorar."
    )
    send_telegram_message(message)

# Abrir sessão para a API GLPI
def open_session():
    session_url = f'{url_glpi}/initSession'
    response = requests.get(session_url, headers=headers)
    if response.status_code == 200:
        session_token = response.json().get('session_token')
        print("Sessão iniciada com sucesso!")
        return session_token
    else:
        print(f"Erro ao iniciar a sessão: {response.status_code}, {response.text}")
        return None

# Adicionar solução ao chamado
def add_solution(session_token, ticket_id):
    solution_data = {
        "input": {
            "items_id": ticket_id,
            "users_id": 2253,
            "content": "Atividades monitoradas e verificadas",
            "itemtype": "Ticket",
            "solutiontypes_id": 2  # Tipo de solução (2: Solução do pedido)
        }
    }
    add_solution_url = f'{url_glpi}/Ticket/{ticket_id}/ITILSolution'
    headers['Session-Token'] = session_token
    
    response = requests.post(add_solution_url, headers=headers, data=json.dumps(solution_data))
    if response.status_code == 201:
        print(f"Solução adicionada ao chamado {ticket_id} com sucesso.")
        return True
    else:
        print(f"Erro ao adicionar solução: {response.status_code}, {response.text}")
        return False

# Fechar o chamado
def close_ticket(session_token, ticket_id):
    close_ticket_data = {"input": {"status": 6}}  # Status 6: Fechado
    close_ticket_url = f'{url_glpi}/Ticket/{ticket_id}'
    headers['Session-Token'] = session_token
    
    response = requests.put(close_ticket_url, headers=headers, data=json.dumps(close_ticket_data))
    if response.status_code == 200:
        print(f"Chamado {ticket_id} fechado com sucesso.")
        send_telegram_message(f"Olá Cássio, seu chamado Nº: {ticket_id} foi FECHADO com sucesso.")
        os.remove(CAMINHO_JSON)  # Remove o arquivo após fechar o chamado
    else:
        print(f"Erro ao fechar o chamado: {response.status_code}, {response.text}")

# Ler o ID do chamado do arquivo JSON
def get_ticket_id():
    try:
        with open(CAMINHO_JSON, 'r') as json_file:
            data = json.load(json_file)
            return data.get('ticket_id')
    except FileNotFoundError:
        print("Erro: arquivo 'ticket_id.json' não encontrado.")
        return None

# Lógica principal
if __name__ == '__main__':
    if os.path.exists(CAMINHO_JSON):  # Verifica se o arquivo existe
        session_token = open_session()
        if session_token:
            ticket_id = get_ticket_id()
            if ticket_id:
                # Primeiro adiciona a solução
                if add_solution(session_token, ticket_id):
                    # Se a solução for adicionada com sucesso, fecha o chamado
                    close_ticket(session_token, ticket_id)
            else:
                print("Erro: Não foi possível obter o ID do chamado.")
    else:
        avisar_feriado_ou_ausencia()
