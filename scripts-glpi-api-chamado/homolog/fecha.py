import requests
import json
import os

ticket_caminho = '/root/kassio/ticket_id.json'
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

# Função para adicionar a solução ao chamado
def add_solution(session_token, ticket_id, solution):
    solution_data = {
        "input": {
            "items_id": ticket_id,
            "users_id": 2253,
            "content": "Atividades monitoradas e verificadas",
            "itemtype": "Ticket",
            "solutiontypes_id": 2,  # Tipo de solução (3: Solução do pedido)
        }
    }
    
    # Endpoint corrigido para adicionar solução ao chamado
    add_solution_url = f'{url_glpi}/Ticket/{ticket_id}/ITILSolution'
    headers['Session-Token'] = session_token
    
    solution_response = requests.post(add_solution_url, headers=headers, data=json.dumps(solution_data))
    
    if solution_response.status_code == 201:
        print(f"Solução adicionada ao chamado {ticket_id} com sucesso.")
        return True
    else:
        print(f"Erro ao adicionar solução: {solution_response.status_code}, {solution_response.text}")
        return False

# Telegram API
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
    message = f"Olá Cássio, seu chamado Nº: {ticket_id} foi FECHADO com sucesso."
    send_telegram_message(bot_token, chat_id, message)

# Função para fechar o chamado
def close_ticket(session_token, ticket_id):
    close_ticket_data = {
        "input": {
            "status": 6  # Status 6: Fechado
        }
    }
    close_ticket_url = f'{url_glpi}/Ticket/{ticket_id}'
    headers['Session-Token'] = session_token
    
    close_response = requests.put(close_ticket_url, headers=headers, data=json.dumps(close_ticket_data))
    
    if close_response.status_code == 200:
        print(f"Chamado {ticket_id} fechado com sucesso.")
        telegram()
        os.system(f'rm -rf {ticket_caminho}')
    else:
        print(f"Erro ao fechar o chamado: {close_response.status_code}, {close_response.text}")

# Função para ler o ID do chamado salvo em ticket_id.json
def get_ticket_id():
    try:
        #caminho_especifico = '/root/kassio/ticket_id.json'
        with open(ticket_caminho, 'r') as json_file:
            data = json.load(json_file)
            return data['ticket_id']
    except FileNotFoundError:
        print("Erro: arquivo 'ticket_id.json' não encontrado.")
        return None

# Exemplo de uso
if __name__ == '__main__':
    session_token = open_session()
    if session_token:
        ticket_id = get_ticket_id()
        if ticket_id:
            solucao = "Atividades monitoradas e verificadas"
            # Adicionar solução primeiro
            if add_solution(session_token, ticket_id, solucao):
                # Se a solução foi adicionada com sucesso, fechar o chamado
                close_ticket(session_token, ticket_id)
        else:
            print("Erro: Não foi possível obter o ID do chamado.")
