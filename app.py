# =======================================================
# PRINTS PARA DEBUG - VAMOS VER ATÉ ONDE O CÓDIGO CHEGA
# =======================================================
print("--- PASSO 1: O ARQUIVO APP.PY COMEÇOU A SER LIDO.")

from flask import Flask, request, jsonify, make_response
from datetime import datetime
import os

print("--- PASSO 2: OS MÓDULOS PADRÃO FORAM IMPORTADOS.")

from helpers import criar_pdf_agenda, enviar_emails_confirmacao

print("--- PASSO 3: O ARQUIVO HELPERS.PY FOI IMPORTADO COM SUCESSO.")

app = Flask(__name__)

print("--- PASSO 4: A APLICAÇÃO FLASK FOI CRIADA. SE CHEGOU ATÉ AQUI, O ERRO NÃO ESTÁ NA INICIALIZAÇÃO.")
# =======================================================
# FIM DOS PRINTS DE DEBUG
# =======================================================


@app.route('/')
def home():
    return "<h1>API da Clínica no ar!</h1><p>Use os endpoints /send_confirmation ou /generate_agenda_pdf.</p>"

@app.route('/generate_agenda_pdf', methods=['POST'])
def generate_agenda_pdf_route():
    data_req = request.json.get('data')
    data_para_pdf = data_req if data_req else datetime.now().strftime('%d/%m/%Y')
    pdf_bytes = criar_pdf_agenda(data_para_pdf)
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=Agenda_{data_para_pdf.replace("/", "-")}.pdf'
    return response

@app.route('/send_confirmation', methods=['POST'])
def send_confirmation_route():
    resultado = enviar_emails_confirmacao()
    if resultado['status'] == 'Erro':
        return jsonify(resultado), 500
    else:
        return jsonify(resultado)