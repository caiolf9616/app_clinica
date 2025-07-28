from flask import Flask, request, jsonify, make_response
from datetime import datetime
import os

# --- 1) Importa as funções que fazem o trabalho pesado do nosso novo arquivo helpers.py ---
from helpers import criar_pdf_agenda, enviar_emails_confirmacao

# --- 2) Inicia a aplicação Flask ---
app = Flask(__name__)

# ==============================================================================
# ROTA PRINCIPAL (/)
# Adicionada para corrigir o erro "Not Found" 404.
# É uma boa prática ter uma rota principal que informa o status da API.
# ==============================================================================
@app.route('/')
def home():
    return "<h1>API da Clínica está no ar!</h1><p>Endpoints disponíveis: /generate_agenda_pdf e /send_confirmation.</p>"

# ==============================================================================
# ROTA PARA GERAR O PDF DA AGENDA
# ==============================================================================
@app.route('/generate_agenda_pdf', methods=['POST'])
def generate_agenda_pdf_route():
    """
    Endpoint para gerar um PDF da agenda de um dia.
    Recebe uma data via JSON. Se nenhuma data for enviada, usa a data de hoje.
    """
    # Pega a data enviada no corpo da requisição POST. Ex: {"data": "25/07/2025"}
    data_req = request.json.get('data')

    # Se nenhuma data for fornecida, usa o dia de hoje como padrão
    data_para_pdf = data_req if data_req else datetime.now().strftime('%d/%m/%Y')
    
    # --- Chama a função helper para criar o PDF ---
    # Toda a complexidade está escondida na função, mantendo o servidor limpo.
    pdf_bytes = criar_pdf_agenda(data_para_pdf)
    
    # --- Monta e retorna a resposta HTTP com o PDF ---
    # Isso fará com que o navegador do usuário mostre o PDF ou inicie o download.
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=Agenda_{data_para_pdf.replace("/", "-")}.pdf'
    
    return response

# ==============================================================================
# ROTA PARA ENVIAR E-MAILS DE CONFIRMAÇÃO
# ==============================================================================
@app.route('/send_confirmation', methods=['POST'])
def send_confirmation_route():
    """
    Endpoint para iniciar o processo de envio de e-mails de confirmação
    para todos os agendamentos com status "Pendente".
    """
    # Chama a função que faz todo o trabalho e retorna um log do que aconteceu
    resultado = enviar_emails_confirmacao()
    
    # Retorna o log como uma resposta JSON
    if resultado['status'] == 'Erro':
        return jsonify(resultado), 500 # Retorna código de erro 500
    else:
        return jsonify(resultado)

# ==============================================================================
# O bloco 'if __name__ == "__main__"' foi removido.
# Para produção, o Gunicorn (definido no Procfile) é quem inicia o servidor.
# Este bloco só é usado para rodar o app localmente com "python app.py".
# Manter o código limpo e focado no deploy de produção é uma boa prática.
# ==============================================================================