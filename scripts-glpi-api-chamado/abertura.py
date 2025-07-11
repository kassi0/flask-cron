import requests
import json
import holidays
import datetime
import os
from pathlib import Path

# Tokens sensíveis - Substitua pelos valores reais ou configure como variáveis de ambiente
APP_TOKEN = "Y8lRyzS0zpULnoNLXUAFtZp7kBdEkTSs1dzgey75"  # Substitua pelo token do GLPI
USER_TOKEN = "Axa8urfhkEnIq3lyaUAOMeJjnnzAk0ePwnxawsVu"  # Substitua pelo token do usuário GLPI
BOT_TOKEN = "6449310793:AAHXJ6Xhei4gbs1epuJnacspO_05yD8HaPM"  # Substitua pelo token do bot Telegram
CHAT_ID = "1475551961"  # Substitua pelo chat ID do Telegram
#URL_GLPI = "https://sga.detran.ba.gov.br/apirest.php"  # URL do GLPI
URL_GLPI = 'http://10.21.246.179/apirest.php' # URL do GLPI Homologação
#CAMINHO_JSON = "/root/kassio/ticket_id.json"  # Caminho para salvar o JSON com o ID do chamado
CAMINHO_JSON = Path(__file__).parent / "ticket_id.json"


# Data atual
hoje = datetime.datetime.now().date()

# Cria objeto de feriados do Brasil, estado da Bahia
feriados_ba = holidays.Brazil(years=hoje.year, state='BA')
nome = feriados_ba.get(hoje)

def eh_feriado():
    """Verifica se a data atual é feriado na Bahia."""
    return hoje in feriados_ba

def open_session():
    """Inicia sessão na API GLPI."""
    session_url = f'{URL_GLPI}/initSession'
    headers = {
        'Content-Type': 'application/json',
        'App-Token': APP_TOKEN,
        'Authorization': f'user_token {USER_TOKEN}'
    }
    try:
        response = requests.get(session_url, headers=headers)
        response.raise_for_status()
        session_token = response.json().get('session_token')
        print("Sessão iniciada com sucesso!")
        return session_token
    except requests.RequestException as e:
        print(f"Erro ao iniciar a sessão GLPI: {e}")
        return None

def send_telegram_message(token, chat_id, message):
    """Envia uma mensagem para um chat do Telegram."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        print("Mensagem enviada com sucesso!")
    except requests.RequestException as e:
        print(f"Falha ao enviar mensagem no Telegram: {e}")

def create_ticket(session_token, title, description, requester_id, group_id, technician_id):
    """Cria um ticket na API GLPI."""
    ticket_data = {
        "input": {
            "name": title,
            "content": description,
            "type": 2,
            "_users_id_requester": requester_id,
            "itilcategories_id": group_id,
            "_users_id_assign": technician_id
        }
    }
    create_ticket_url = f'{URL_GLPI}/Ticket'
    headers = {
        'Content-Type': 'application/json',
        'App-Token': APP_TOKEN,
        'Session-Token': session_token
    }
    
    try:
        response = requests.post(create_ticket_url, headers=headers, data=json.dumps(ticket_data))
        response.raise_for_status()
        ticket_id = response.json()['id']
        print(f"Chamado aberto com sucesso! ID: {ticket_id}")
        
        # Salvar o ID do chamado
        os.makedirs(os.path.dirname(CAMINHO_JSON), exist_ok=True)
        with open(CAMINHO_JSON, 'w') as json_file:
            json.dump({'ticket_id': ticket_id}, json_file)
        
        message = f"Olá Cássio, seu chamado Nº: {ticket_id} foi ABERTO com sucesso."
        send_telegram_message(BOT_TOKEN, CHAT_ID, message)
    except requests.RequestException as e:
        print(f"Erro ao abrir chamado: {e}")

# Função para criar ticket em dia útil."""
def funcao_se_nao_feriado():
    session_token = open_session()
    if session_token:
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
            - GRAYLOG
            - Carga SGAD"""
        id_solicitante = 1594
        id_categoria = 986
        id_tecnico = 2253
        
        create_ticket(session_token, titulo, descricao, id_solicitante, id_categoria, id_tecnico)

# Função para dias de feriado.
def funcao_se_feriado():
    nome = feriados_ba.get(hoje) or "feriado"
    print(f"{hoje} - Hoje é {nome}! Relaxar e curtir!")
    message = f"{hoje} - Hoje é {nome}! Sem chamado rotineiro! Relaxar e curtir!"
    send_telegram_message(BOT_TOKEN, CHAT_ID, message)

if __name__ == "__main__":
    if eh_feriado():
        funcao_se_feriado()
    else:
        funcao_se_nao_feriado()
