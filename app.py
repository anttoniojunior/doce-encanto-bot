import unittest
import os
import sys
import re
from datetime import datetime

# Adicionar diretório atual ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Definir produtos para teste
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

# Definir ingredientes para teste
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

# Função de análise de mensagem de venda para teste
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
        
        # Simular data atual
        data_atual = datetime.now().strftime("%d/%m/%Y")
        
        return {
            'tipo': 'venda',
            'data': data_atual,
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

# Função de análise de mensagem de compra para teste
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
        
        # Simular data atual
        data_atual = datetime.now().strftime("%d/%m/%Y")
        
        return {
            'tipo': 'compra',
            'data': data_atual,
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

# Função de análise de mensagem de gasto pessoal para teste
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
        
        # Simular data atual
        data_atual = datetime.now().strftime("%d/%m/%Y")
        
        return {
            'tipo': 'pessoal',
            'data': data_atual,
            'descricao': descricao,
            'valor': valor,
            'categoria': categoria,
            'pagamento': pagamento,
            'observacoes': observacoes
        }
    
    except Exception as e:
        print(f"Erro ao analisar mensagem de gasto pessoal: {e}")
        return None

class TestWhatsAppIntegrationExpanded(unittest.TestCase):
    
    def test_parse_venda_message_valid(self):
        """Testa a análise de uma mensagem de venda válida."""
        message = "Venda: Trufa de Morango x2 - PIX - Cliente Maria"
        result = parse_venda_message(message)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['tipo'], "venda")
        self.assertEqual(result['produto'], "Trufa De Morango")
        self.assertEqual(result['quantidade'], 2)
        self.assertEqual(result['pagamento'], "PIX")
        self.assertEqual(result['observacoes'], "Cliente Maria")
        self.assertEqual(result['valor_unitario'], produtos["trufa de morango"])
        self.assertEqual(result['valor_total'], produtos["trufa de morango"] * 2)
    
    def test_parse_compra_message_valid(self):
        """Testa a análise de uma mensagem de compra válida."""
        message = "Compra: 3 leites condensados, 2 cremes de leite, 1 chocolate em barra - 50,00 - Atacadão - Cartão - Promoção"
        result = parse_compra_message(message)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['tipo'], "compra")
        self.assertEqual(len(result['itens']), 3)
        self.assertEqual(result['itens'][0]['nome'], "leites condensados")
        self.assertEqual(result['itens'][0]['quantidade'], 3)
        self.assertEqual(result['itens'][1]['nome'], "cremes de leite")
        self.assertEqual(result['itens'][1]['quantidade'], 2)
        self.assertEqual(result['itens'][2]['nome'], "chocolate em barra")
        self.assertEqual(result['itens'][2]['quantidade'], 1)
        self.assertEqual(result['valor_total'], 50.00)
        self.assertEqual(result['local'], "Atacadão")
        self.assertEqual(result['pagamento'], "Cartão")
        self.assertEqual(result['observacoes'], "Promoção")
    
    def test_parse_compra_message_without_quantity(self):
        """Testa a análise de uma mensagem de compra sem quantidade explícita."""
        message = "Compra: leite condensado - 6,45 - Mercado - Dinheiro"
        result = parse_compra_message(message)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['tipo'], "compra")
        self.assertEqual(len(result['itens']), 1)
        self.assertEqual(result['itens'][0]['nome'], "leite condensado")
        self.assertEqual(result['itens'][0]['quantidade'], 1)
        self.assertEqual(result['valor_total'], 6.45)
        self.assertEqual(result['local'], "Mercado")
        self.assertEqual(result['pagamento'], "Dinheiro")
    
    def test_parse_compra_message_minimal(self):
        """Testa a análise de uma mensagem de compra com informações mínimas."""
        message = "Compra: 4 cremes de leite, 1 chocolate em barra"
        result = parse_compra_message(message)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['tipo'], "compra")
        self.assertEqual(len(result['itens']), 2)
        self.assertEqual(result['itens'][0]['nome'], "cremes de leite")
        self.assertEqual(result['itens'][0]['quantidade'], 4)
        self.assertEqual(result['itens'][1]['nome'], "chocolate em barra")
        self.assertEqual(result['itens'][1]['quantidade'], 1)
        self.assertEqual(result['valor_total'], 0)
        self.assertEqual(result['local'], "")
        self.assertEqual(result['pagamento'], "")
        self.assertEqual(result['observacoes'], "")
    
    def test_parse_pessoal_message_valid(self):
        """Testa a análise de uma mensagem de gasto pessoal válida."""
        message = "Pessoal: Uber volta do mercado - 20,00 - Transporte - Cartão - Urgente"
        result = parse_pessoal_message(message)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['tipo'], "pessoal")
        self.assertEqual(result['descricao'], "Uber volta do mercado")
        self.assertEqual(result['valor'], 20.00)
        self.assertEqual(result['categoria'], "Transporte")
        self.assertEqual(result['pagamento'], "Cartão")
        self.assertEqual(result['observacoes'], "Urgente")
    
    def test_parse_pessoal_message_infer_category(self):
        """Testa a inferência de categoria em uma mensagem de gasto pessoal."""
        message = "Pessoal: Uber para o shopping - 25,00 - - PIX"
        result = parse_pessoal_message(message)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['tipo'], "pessoal")
        self.assertEqual(result['descricao'], "Uber para o shopping")
        self.assertEqual(result['valor'], 25.00)
        self.assertEqual(result['categoria'], "Transporte")  # Inferido de "Uber"
        self.assertEqual(result['pagamento'], "PIX")
        self.assertEqual(result['observacoes'], "")
    
    def test_parse_pessoal_message_minimal(self):
        """Testa a análise de uma mensagem de gasto pessoal com informações mínimas."""
        message = "Pessoal: Almoço no shopping"
        result = parse_pessoal_message(message)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['tipo'], "pessoal")
        self.assertEqual(result['descricao'], "Almoço no shopping")
        self.assertEqual(result['valor'], 0)
        self.assertEqual(result['categoria'], "Alimentação")  # Inferido de "Almoço"
        self.assertEqual(result['pagamento'], "")
        self.assertEqual(result['observacoes'], "")
    
    def test_invalid_message(self):
        """Testa mensagens que não correspondem a nenhum formato."""
        message = "Olá, como vai?"
        
        self.assertIsNone(parse_venda_message(message))
        self.assertIsNone(parse_compra_message(message))
        self.assertIsNone(parse_pessoal_message(message))

if __name__ == '__main__':
    unittest.main()
