import os
import json
import requests
from flask import Flask, request, jsonify
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import re

app = Flask(__name__)

# Configurações do Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SAMPLE_SPREADSHEET_ID = 'SUA_PLANILHA_ID'  # Será substituído pelo ID real da planilha

# Configurações do Twilio (para WhatsApp)
TWILIO_ACCOUNT_SID = 'SUA_ACCOUNT_SID'  # Será substituído pelo SID real
TWILIO_AUTH_TOKEN = 'SEU_AUTH_TOKEN'  # Será substituído pelo token real
TWILIO_PHONE_NUMBER = 'whatsapp:+14155238886'  # Número do Twilio para WhatsApp

# Dicionário de produtos e preços (será preenchido a partir da planilha)
produtos = {
    "trufa de morango": 4.00,
    "trufa de maracujá": 4.00,
    "trufa de castanha": 4.00,
    "trufa de brigadeiro": 4.00,
    "trufa de paçoca": 4.00,
    "trufa de coco": 4.00,
    "mousse de maracujá": 7.00,
    "mousse de limão": 7.00,
    "torta de maracujá": 8.00,
    "torta de morango": 8.00,
    "torta de limão": 8.00,
    "torta de paçoca": 8.00,
    "torta de oreo": 8.00,
    "delícia de uva": 8.00,
    "pudim de leite": 8.00
}

# Dicionário de ingredientes (será preenchido a partir da planilha)
ingredientes = {
    "leite condensado": {"unidade": "g", "preco": 6.45},
    "uva verde": {"unidade": "g", "preco": 16.00},
    "limão": {"unidade": "g", "preco": 5.00},
    "maracujá": {"unidade": "kg", "preco": 15.00},
    "chantily": {"unidade": "litro", "preco": 20.00},
    "chocolate em barra": {"unidade": "g", "preco": 28.00},
    "creme de leite": {"unidade": "g", "preco": 3.39},
    "morango": {"unidade": "g", "preco": 10.00}
}

# Categorias para gastos pessoais
categorias_pessoais = {
    "uber": "Transporte",
    "táxi": "Transporte",
    "ônibus": "Transporte",
    "metrô": "Transporte",
    "almoço": "Alimentação",
    "jantar": "Alimentação",
    "lanche": "Alimentação",
    "café": "Alimentação",
    "cinema": "Lazer",
    "show": "Lazer",
    "teatro": "Lazer",
    "internet": "Contas",
    "luz": "Contas",
    "água": "Contas",
    "telefone": "Contas",
    "aluguel": "Moradia",
    "condomínio": "Moradia",
    "remédio": "Saúde",
    "consulta": "Saúde",
    "exame": "Saúde"
}

def setup_google_sheets():
    """Configura a conexão com o Google Sheets."""
    creds = None
    # O arquivo credentials.json deve estar no mesmo diretório
    if os.path.exists('credentials.json'):
        creds = service_account.Credentials.from_service_account_file(
            'credentials.json', scopes=SCOPES)
    
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    return sheet

def parse_venda_message(message):
    """
    Analisa a mensagem de venda e extrai as informações.
    Formato esperado: "Venda: [Produto] x[Quantidade] - [Forma de Pagamento] - [Observações]"
    Exemplo: "Venda: Trufa de Morango x2 - PIX - Cliente Maria"
    """
    try:
        # Verificar se é uma mensagem de venda
        if not message.lower().startswith('venda:'):
            return None
        
        # Remover o prefixo "Venda:"
        content = message[6:].strip()
        
        # Dividir por "-" para separar produto, pagamento e observações
        parts = content.split('-')
        
        if len(parts) < 2:
            return None  # Formato inválido
        
        # Extrair produto e quantidade
        produto_info = parts[0].strip()
        
        # Verificar se há indicação de quantidade (x2, x3, etc.)
        if 'x' in produto_info:
            produto_parts = produto_info.split('x')
            produto = produto_parts[0].strip().lower()
            quantidade = int(produto_parts[1].strip())
        else:
            produto = produto_info.lower()
            quantidade = 1
        
        # Extrair forma de pagamento
        pagamento = parts[1].strip()
        
        # Extrair observações (se houver)
        observacoes = parts[2].strip() if len(parts) > 2 else ""
        
        # Verificar se o produto existe no catálogo
        if produto not in produtos:
            return None  # Produto não encontrado
        
        # Obter o valor unitário do produto
        valor_unitario = produtos[produto]
        
        # Calcular o valor total
        valor_total = valor_unitario * quantidade
        
        # Formatar o nome do produto com a primeira letra maiúscula
        produto_formatado = ' '.join(word.capitalize() for word in produto.split())
        
        return {
            'tipo': 'venda',
            'data': datetime.now().strftime("%d/%m/%Y"),
            'produto': produto_formatado,
            'quantidade': quantidade,
            'valor_unitario': valor_unitario,
            'valor_total': valor_total,
            'pagamento': pagamento,
            'observacoes': observacoes
        }
    
    except Exception as e:
        print(f"Erro ao analisar mensagem de venda: {e}")
        return None

def parse_compra_message(message):
    """
    Analisa a mensagem de compra de ingredientes e extrai as informações.
    Formato esperado: "Compra: [Itens] - [Valor Total] - [Local] - [Forma de Pagamento] - [Observações]"
    Exemplo: "Compra: 3 leites condensados, 2 cremes de leite, 1 granulado - 50,00 - Atacadão - Cartão - Promoção"
    """
    try:
        # Verificar se é uma mensagem de compra
        if not message.lower().startswith('compra:'):
            return None
        
        # Remover o prefixo "Compra:"
        content = message[7:].strip()
        
        # Dividir por "-" para separar itens, valor, local, pagamento e observações
        parts = content.split('-')
        
        if len(parts) < 1:
            return None  # Formato inválido
        
        # Extrair itens
        itens_info = parts[0].strip()
        
        # Processar os itens (formato: "3 leites condensados, 2 cremes de leite")
        itens_list = itens_info.split(',')
        itens_processados = []
        
        for item in itens_list:
            item = item.strip()
            # Tentar extrair quantidade e nome do item
            match = re.match(r'(\d+)\s+(.+)', item)
            if match:
                quantidade = int(match.group(1))
                nome_item = match.group(2).strip().lower()
                itens_processados.append({
                    'nome': nome_item,
                    'quantidade': quantidade
                })
            else:
                # Se não conseguir extrair quantidade, assume 1
                itens_processados.append({
                    'nome': item.lower(),
                    'quantidade': 1
                })
        
        # Extrair valor total (se fornecido)
        valor_total = 0
        if len(parts) > 1 and parts[1].strip():
            valor_str = parts[1].strip().replace('R$', '').replace(',', '.').strip()
            try:
                valor_total = float(valor_str)
            except ValueError:
                valor_total = 0
        
        # Extrair local (se fornecido)
        local = ""
        if len(parts) > 2:
            local = parts[2].strip()
        
        # Extrair forma de pagamento (se fornecida)
        pagamento = ""
        if len(parts) > 3:
            pagamento = parts[3].strip()
        
        # Extrair observações (se fornecidas)
        observacoes = ""
        if len(parts) > 4:
            observacoes = parts[4].strip()
        
        return {
            'tipo': 'compra',
            'data': datetime.now().strftime("%d/%m/%Y"),
            'itens': itens_processados,
            'valor_total': valor_total,
            'local': local,
            'pagamento': pagamento,
            'observacoes': observacoes,
            'descricao': itens_info  # Descrição completa dos itens para registro
        }
    
    except Exception as e:
        print(f"Erro ao analisar mensagem de compra: {e}")
        return None

def parse_pessoal_message(message):
    """
    Analisa a mensagem de gasto pessoal e extrai as informações.
    Formato esperado: "Pessoal: [Descrição] - [Valor] - [Categoria] - [Forma de Pagamento] - [Observações]"
    Exemplo: "Pessoal: Uber volta do mercado - 20,00 - Transporte - Cartão - Urgente"
    """
    try:
        # Verificar se é uma mensagem de gasto pessoal
        if not message.lower().startswith('pessoal:'):
            return None
        
        # Remover o prefixo "Pessoal:"
        content = message[8:].strip()
        
        # Dividir por "-" para separar descrição, valor, categoria, pagamento e observações
        parts = content.split('-')
        
        if len(parts) < 1:
            return None  # Formato inválido
        
        # Extrair descrição
        descricao = parts[0].strip()
        
        # Extrair valor (se fornecido)
        valor = 0
        if len(parts) > 1 and parts[1].strip():
            valor_str = parts[1].strip().replace('R$', '').replace(',', '.').strip()
            try:
                valor = float(valor_str)
            except ValueError:
                valor = 0
        
        # Extrair ou inferir categoria
        categoria = ""
        if len(parts) > 2 and parts[2].strip():
            categoria = parts[2].strip()
        else:
            # Tentar inferir categoria com base na descrição
            descricao_lower = descricao.lower()
            for palavra_chave, cat in categorias_pessoais.items():
                if palavra_chave in descricao_lower:
                    categoria = cat
                    break
        
        # Extrair forma de pagamento (se fornecida)
        pagamento = ""
        if len(parts) > 3:
            pagamento = parts[3].strip()
        
        # Extrair observações (se fornecidas)
        observacoes = ""
        if len(parts) > 4:
            observacoes = parts[4].strip()
        
        return {
            'tipo': 'pessoal',
            'data': datetime.now().strftime("%d/%m/%Y"),
            'descricao': descricao,
            'valor': valor,
            'categoria': categoria,
            'pagamento': pagamento,
            'observacoes': observacoes
        }
    
    except Exception as e:
        print(f"Erro ao analisar mensagem de gasto pessoal: {e}")
        return None

def add_venda_to_sheets(venda_data):
    """Adiciona os dados da venda ao Google Sheets."""
    try:
        sheet = setup_google_sheets()
        
        # Encontrar a próxima linha vazia na aba de Registro de Vendas
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                   range='Registro de Vendas!A:G').execute()
        values = result.get('values', [])
        next_row = len(values) + 1
        
        # Se a próxima linha for menor que 5, ajustar para 5 (para pular os cabeçalhos)
        if next_row < 5:
            next_row = 5
        
        # Preparar os dados para inserção
        row_data = [
            venda_data['data'],
            venda_data['produto'],
            venda_data['quantidade'],
            venda_data['valor_unitario'],
            venda_data['valor_total'],
            venda_data['pagamento'],
            venda_data['observacoes']
        ]
        
        # Inserir os dados na planilha
        body = {
            'values': [row_data]
        }
        result = sheet.values().update(
            spreadsheetId=SAMPLE_SPREADSHEET_ID,
            range=f'Registro de Vendas!A{next_row}:G{next_row}',
            valueInputOption='USER_ENTERED',
            body=body).execute()
        
        return True
    
    except Exception as e:
        print(f"Erro ao adicionar venda à planilha: {e}")
        return False

def add_compra_to_sheets(compra_data):
    """Adiciona os dados da compra de ingredientes ao Google Sheets."""
    try:
        sheet = setup_google_sheets()
        
        # 1. Atualizar o estoque
        for item in compra_data['itens']:
            # Buscar o item no estoque
            result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                      range='Controle de Estoque!A:G').execute()
            values = result.get('values', [])
            
            item_encontrado = False
            for i, row in enumerate(values):
                if i < 4:  # Pular cabeçalhos
                    continue
                
                if len(row) > 1 and row[1].lower() == item['nome']:
                    # Item encontrado, atualizar quantidade
                    item_encontrado = True
                    row_num = i + 1
                    
                    # Obter quantidade atual
                    quantidade_atual = 0
                    if len(row) > 2:
                        try:
                            quantidade_atual = float(row[2])
                        except (ValueError, TypeError):
                            quantidade_atual = 0
                    
                    # Calcular nova quantidade
                    nova_quantidade = quantidade_atual + item['quantidade']
                    
                    # Atualizar quantidade
                    sheet.values().update(
                        spreadsheetId=SAMPLE_SPREADSHEET_ID,
                        range=f'Controle de Estoque!C{row_num}',
                        valueInputOption='USER_ENTERED',
                        body={'values': [[nova_quantidade]]}).execute()
                    
                    break
            
            # Se o item não foi encontrado, adicionar como novo
            if not item_encontrado:
                # Encontrar a próxima linha vazia
                next_row = len(values) + 1
                
                # Gerar código para o novo item
                codigo = f"ING{next_row-4:03d}"
                
                # Preparar dados do novo item
                new_item_data = [
                    codigo,
                    ' '.join(word.capitalize() for word in item['nome'].split()),
                    item['quantidade'],
                    "g",  # Unidade padrão
                    0,    # Preço unitário (a ser preenchido manualmente)
                    "=C{row}*E{row}".format(row=next_row),  # Fórmula para valor total
                    "",   # Marca
                    compra_data['local']  # Local de compra
                ]
                
                # Adicionar novo item
                sheet.values().update(
                    spreadsheetId=SAMPLE_SPREADSHEET_ID,
                    range=f'Controle de Estoque!A{next_row}:H{next_row}',
                    valueInputOption='USER_ENTERED',
                    body={'values': [new_item_data]}).execute()
        
        # 2. Registrar a compra na aba Via 1 - Negócios
        # Encontrar a próxima linha vazia
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                   range='Via 1 - Negócios!A:G').execute()
        values = result.get('values', [])
        next_row = len(values) + 1
        
        # Preparar os dados para inserção
        row_data = [
            compra_data['data'],
            compra_data['descricao'],
            "Ingredientes",  # Categoria
            compra_data['valor_total'],
            compra_data['pagamento'],
            compra_data['observacoes']
        ]
        
        # Inserir os dados na planilha
        body = {
            'values': [row_data]
        }
        result = sheet.values().update(
            spreadsheetId=SAMPLE_SPREADSHEET_ID,
            range=f'Via 1 - Negócios!A{next_row}:F{next_row}',
            valueInputOption='USER_ENTERED',
            body=body).execute()
        
        return True
    
    except Exception as e:
        print(f"Erro ao adicionar compra à planilha: {e}")
        return False

def add_pessoal_to_sheets(pessoal_data):
    """Adiciona os dados do gasto pessoal ao Google Sheets."""
    try:
        sheet = setup_google_sheets()
        
        # Encontrar a próxima linha vazia na aba Via 2 - Pessoal
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                   range='Via 2 - Pessoal!A:G').execute()
        values = result.get('values', [])
        next_row = len(values) + 1
        
        # Preparar os dados para inserção
        row_data = [
            pessoal_data['data'],
            pessoal_data['descricao'],
            pessoal_data['categoria'],
            pessoal_data['valor'],
            pessoal_data['pagamento'],
            pessoal_data['observacoes']
        ]
        
        # Inserir os dados na planilha
        body = {
            'values': [row_data]
        }
        result = sheet.values().update(
            spreadsheetId=SAMPLE_SPREADSHEET_ID,
            range=f'Via 2 - Pessoal!A{next_row}:F{next_row}',
            valueInputOption='USER_ENTERED',
            body=body).execute()
        
        return True
    
    except Exception as e:
        print(f"Erro ao adicionar gasto pessoal à planilha: {e}")
        return False

def send_whatsapp_message(to, message):
    """Envia uma mensagem de WhatsApp usando a API do Twilio."""
    try:
        url = f'https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json'
        data = {
            'To': f'whatsapp:{to}',
            'From': TWILIO_PHONE_NUMBER,
            'Body': message
        }
        auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        response = requests.post(url, data=data, auth=auth)
        return response.status_code == 201
    
    except Exception as e:
        print(f"Erro ao enviar mensagem WhatsApp: {e}")
        return False

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook para receber mensagens do WhatsApp via Twilio."""
    try:
        # Extrair a mensagem recebida
        incoming_msg = request.form.get('Body', '')
        sender = request.form.get('From', '').replace('whatsapp:', '')
        
        # Tentar analisar como venda
        data = parse_venda_message(incoming_msg)
        if data:
            # Adicionar a venda à planilha
            success = add_venda_to_sheets(data)
            
            if success:
                # Enviar confirmação
                response_msg = (
                    f"✅ Venda registrada com sucesso!\n\n"
                    f"Produto: {data['produto']}\n"
                    f"Quantidade: {data['quantidade']}\n"
                    f"Valor Total: R$ {data['valor_total']:.2f}\n"
                    f"Forma de Pagamento: {data['pagamento']}"
                )
            else:
                response_msg = "❌ Erro ao registrar a venda. Por favor, tente novamente."
            
            # Enviar resposta
            send_whatsapp_message(sender, response_msg)
            return jsonify({'status': 'success', 'type': 'venda'}), 200
        
        # Tentar analisar como compra
        data = parse_compra_message(incoming_msg)
        if data:
            # Adicionar a compra à planilha
            success = add_compra_to_sheets(data)
            
            if success:
                # Enviar confirmação
                itens_str = ", ".join([f"{item['quantidade']} {item['nome']}" for item in data['itens']])
                response_msg = (
                    f"✅ Compra registrada com sucesso!\n\n"
                    f"Itens: {itens_str}\n"
                    f"Valor Total: R$ {data['valor_total']:.2f}\n"
                    f"Local: {data['local']}\n"
                    f"Forma de Pagamento: {data['pagamento']}\n\n"
                    f"✓ Estoque atualizado automaticamente"
                )
            else:
                response_msg = "❌ Erro ao registrar a compra. Por favor, tente novamente."
            
            # Enviar resposta
            send_whatsapp_message(sender, response_msg)
            return jsonify({'status': 'success', 'type': 'compra'}), 200
        
        # Tentar analisar como gasto pessoal
        data = parse_pessoal_message(incoming_msg)
        if data:
            # Adicionar o gasto pessoal à planilha
            success = add_pessoal_to_sheets(data)
            
            if success:
                # Enviar confirmação
                response_msg = (
                    f"✅ Gasto pessoal registrado com sucesso!\n\n"
                    f"Descrição: {data['descricao']}\n"
                    f"Valor: R$ {data['valor']:.2f}\n"
                    f"Categoria: {data['categoria']}\n"
                    f"Forma de Pagamento: {data['pagamento']}"
                )
            else:
                response_msg = "❌ Erro ao registrar o gasto pessoal. Por favor, tente novamente."
            
            # Enviar resposta
            send_whatsapp_message(sender, response_msg)
            return jsonify({'status': 'success', 'type': 'pessoal'}), 200
        
        # Mensagem de formato inválido
        response_msg = (
            "⚠️ Formato inválido. Use um dos formatos:\n\n"
            "1) Para vendas:\n"
            "Venda: [Produto] x[Quantidade] - [Forma de Pagamento] - [Observações]\n"
            "Exemplo: Venda: Trufa de Morango x2 - PIX - Cliente Maria\n\n"
            "2) Para compras de ingredientes:\n"
            "Compra: [Itens] - [Valor Total] - [Local] - [Forma de Pagamento] - [Observações]\n"
            "Exemplo: Compra: 3 leites condensados, 2 cremes de leite - 50,00 - Atacadão - Cartão - Promoção\n\n"
            "3) Para gastos pessoais:\n"
            "Pessoal: [Descrição] - [Valor] - [Categoria] - [Forma de Pagamento] - [Observações]\n"
            "Exemplo: Pessoal: Uber volta do mercado - 20,00 - Transporte - Cartão - Urgente"
        )
        
        # Enviar resposta
        send_whatsapp_message(sender, response_msg)
        
        return jsonify({'status': 'success', 'type': 'invalid_format'}), 200
    
    except Exception as e:
        print(f"Erro no webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def create_credentials_file(credentials_json):
    """Cria o arquivo de credenciais do Google Sheets."""
    with open('credentials.json', 'w') as f:
        f.write(credentials_json)

def update_config(spreadsheet_id, twilio_sid, twilio_token):
    """Atualiza as configurações globais."""
    global SAMPLE_SPREADSHEET_ID, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
    SAMPLE_SPREADSHEET_ID = spreadsheet_id
    TWILIO_ACCOUNT_SID = twilio_sid
    TWILIO_AUTH_TOKEN = twilio_token

def load_products_from_sheet():
    """Carrega os produtos e preços da planilha."""
    try:
        sheet = setup_google_sheets()
        
        # Obter dados da aba Produtos
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                   range='Produtos!B:D').execute()
        values = result.get('values', [])
        
        # Atualizar o dicionário de produtos
        global produtos
        produtos = {}
        
        # Pular o cabeçalho
        for row in values[4:]:
            if len(row) >= 3:
                produto = row[0].lower()
                try:
                    preco = float(row[2].replace('R$', '').replace(',', '.').strip())
                    produtos[produto] = preco
                except (ValueError, IndexError):
                    pass
        
        return True
    
    except Exception as e:
        print(f"Erro ao carregar produtos da planilha: {e}")
        return False

def load_ingredients_from_sheet():
    """Carrega os ingredientes e preços da planilha."""
    try:
        sheet = setup_google_sheets()
        
        # Obter dados da aba Controle de Estoque
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                   range='Controle de Estoque!B:E').execute()
        values = result.get('values', [])
        
        # Atualizar o dicionário de ingredientes
        global ingredientes
        ingredientes = {}
        
        # Pular o cabeçalho
        for row in values[4:]:
            if len(row) >= 3:
                nome = row[0].lower()
                try:
                    unidade = row[2] if len(row) > 2 else "g"
                    preco = float(row[3].replace('R$', '').replace(',', '.').strip()) if len(row) > 3 else 0
                    ingredientes[nome] = {
                        "unidade": unidade,
                        "preco": preco
                    }
                except (ValueError, IndexError):
                    pass
        
        return True
    
    except Exception as e:
        print(f"Erro ao carregar ingredientes da planilha: {e}")
        return False

if __name__ == '__main__':
    # Este código seria executado quando o aplicativo é iniciado
    # Carregar produtos e ingredientes da planilha
    load_products_from_sheet()
    load_ingredients_from_sheet()
    
    # Iniciar o servidor Flask
    app.run(host='0.0.0.0', port=5000)
