import requests
import json

# URL da API GLPI
url_glpi = 'https://sga.detran.ba.gov.br/apirest.php'

# Token de autenticação
app_token = 'Y8lRyzS0zpULnoNLXUAFtZp7kBdEkTSs1dzgey75'
user_token = 'Axa8urfhkEnIq3lyaUAOMeJjnnzAk0ePwnxawsVu'

# Caminho do JSON
caminho_especifico = '/root/kassio/ticket_id.json'

# Cabeçalhos para autenticação
headers = {
    'Content-Type': 'application/json',
    'App-Token': app_token,
    'Authorization': f'user_token {user_token}'
}

# Função para iniciar sessão na API GLPI
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

# Função para enviar uma mensagem via Telegram
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

# Função para abrir um novo chamado com grupo técnico e técnico responsável
def create_ticket(session_token, title, description, requester_id, group_id, technician_id):
    ticket_data = {
        "input": {
            "name": title,
            "content": description,
            "type": 2,  # Tipo de requisição
            "_users_id_requester": requester_id,  # ID do solicitante
            "itilcategories_id": group_id,  # ID do grupo técnico (categoria)
            "_users_id_assign": technician_id  # ID do técnico responsável
        }
    }
    create_ticket_url = f'{url_glpi}/Ticket'
    headers['Session-Token'] = session_token
    
    response = requests.post(create_ticket_url, headers=headers, data=json.dumps(ticket_data))
    
    if response.status_code == 201:
        ticket_id = response.json()['id']
        print("Chamado aberto com sucesso!")
        print(f"ID do chamado: {ticket_id}")
        
        # Salvar o ID do chamado em um arquivo JSON
        with open(caminho_especifico, 'w') as json_file:
            json.dump({'ticket_id': ticket_id}, json_file)
        print(f"ID do chamado salvo em '{caminho_especifico}'")

        # Enviar notificação via Telegram com o ID do chamado
        bot_token = "6449310793:AAHXJ6Xhei4gbs1epuJnacspO_05yD8HaPM"
        chat_id = 1475551961  # Seu chat_id
        message = f"Olá Cássio, seu chamado Nº: {ticket_id} foi ABERTO com sucesso."
        send_telegram_message(bot_token, chat_id, message)
        
    else:
        print(f"Erro ao abrir chamado: {response.status_code}, {response.text}")

if __name__ == '__main__':
    session_token = open_session()
    if session_token:
        # Dados do chamado
        titulo = "Atividades Rotineiras do ambiente de Produção - Linux"
        descricao = """Chamado aberto com o intuito de registrar as atividade rotineiras do ambiente de Produção relacionados abaixo:
- Rotina e-Cartas
- SGA
- SGA - Homologação
- OCS
- TeamPass
- ZABBIX
- GRAFANA
- WikiJs
- Portal Institucional
- E-DOC - Novo
- E-DOC - LEGADO - 10.21.1.120
- E-DOC - DADOS - 10.21.246.77
- SERVIDOR DB
- CMS
- RSYSLOG
- PAINEL MONITORAMENTO
- GRAYLOG"""
        
        id_solicitante = 1594  # ID do solicitante
        id_categoria = 986  # ID do grupo técnico
        id_tecnico = 2253  # ID do técnico responsável
        
        create_ticket(session_token, titulo, descricao, id_solicitante, id_categoria, id_tecnico)
