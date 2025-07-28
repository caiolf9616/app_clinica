import pandas as pd
from fpdf import FPDF
from datetime import datetime
import yagmail
import os # Importado para ler as variáveis de ambiente

# ==============================================================================
# FUNÇÃO PARA GERAR O PDF DA AGENDA
# ==============================================================================
def criar_pdf_agenda(data_input):
    """
    Busca agendamentos de uma data específica em uma planilha Google Sheets
    e gera um arquivo PDF em memória.

    Args:
        data_input (str): A data desejada no formato 'dd/mm/yyyy'.

    Returns:
        bytes: O conteúdo do arquivo PDF como uma sequência de bytes.
    """
    try:
        # --- 1) Link CSV do Google Sheets ---
        url = 'https://docs.google.com/spreadsheets/d/1UEXan3JXGPhRz2V92r-cPhIMMwf-Uyl4VTyElwgsH6w/export?format=csv&gid=1523497455'
        df = pd.read_csv(url)

        # --- 2) Processa e filtra os dados pela data fornecida ---
        # Converte a data de input para o formato de comparação (ano-mês-dia)
        data_escolhida = datetime.strptime(data_input.strip(), '%d/%m/%Y').strftime('%Y-%m-%d')
        
        # Garante que a coluna 'Data' na planilha esteja no formato correto para comparação
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True).dt.strftime('%Y-%m-%d')
        
        agenda_dia = df[df['Data'] == data_escolhida]
        agenda_dia = agenda_dia.sort_values(by=['Nome Funcionario', 'Hora - Inicio'])

        # --- 3) Monta a estrutura do PDF ---
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        data_formatada = datetime.strptime(data_escolhida, '%Y-%m-%d').strftime('%d/%m/%Y')
        dia_semana = datetime.strptime(data_escolhida, '%Y-%m-%d').strftime('%A')

        pdf.cell(0, 10, txt=f"{dia_semana.capitalize()}, {data_formatada}", ln=True, align='L')
        pdf.set_font("Arial", size=14)
        pdf.cell(0, 10, txt="Agenda", ln=True, align='L')
        pdf.ln(5)

        # --- 4) Adiciona os agendamentos ao PDF ---
        if agenda_dia.empty:
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, txt="Nenhum agendamento para esta data.", ln=True, align='L')
        else:
            # Itera sobre cada profissional para agrupar os agendamentos
            for profissional in agenda_dia['Nome Funcionario'].unique():
                pdf.set_font("Arial", "B", size=12) # Nome do profissional em negrito
                pdf.cell(0, 10, txt=profissional, ln=True, align='L')
                
                agendamentos_prof = agenda_dia[agenda_dia['Nome Funcionario'] == profissional]
                
                pdf.set_font("Arial", size=11)
                for _, row in agendamentos_prof.iterrows():
                    hora = pd.to_datetime(row['Hora - Inicio']).strftime('%Hh%M')
                    cliente = row['Nome Cliente']
                    servico = row['Procedimento']
                    texto = f"    {hora} - {cliente} ({servico})" if pd.notnull(servico) and servico.strip() else f"    {hora} - {cliente}"
                    pdf.cell(0, 8, txt=texto, ln=True, align='L')
                
                pdf.ln(5)

        # --- 5) Retorna o PDF em memória ---
        # Em vez de salvar em um arquivo (pdf.output('nome.pdf')),
        # geramos o conteúdo do PDF como bytes para que o servidor possa enviá-lo
        # diretamente ao navegador do usuário.
        return pdf.output(dest='S').encode('latin-1')

    except Exception as e:
        # Se der erro, cria um PDF de erro para não quebrar a aplicação
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, txt=f"Erro ao gerar o PDF: {str(e)}", ln=True, align='L')
        return pdf.output(dest='S').encode('latin-1')


# ==============================================================================
# FUNÇÃO PARA ENVIAR E-MAILS DE CONFIRMAÇÃO
# ==============================================================================
def enviar_emails_confirmacao():
    """
    Busca agendamentos pendentes e envia um e-mail de confirmação para cada um.
    As credenciais de e-mail são lidas das variáveis de ambiente para segurança.
    """
    try:
        # --- 1) Segurança: Pega as credenciais das variáveis de ambiente da Railway ---
        # NUNCA coloque senhas diretamente no código!
        email_user = os.environ.get('EMAIL_USER')
        email_pass = os.environ.get('EMAIL_PASS')

        if not email_user or not email_pass:
            return {"status": "Erro", "detalhe": "As variáveis de ambiente EMAIL_USER e EMAIL_PASS não foram configuradas na Railway."}

        yag = yagmail.SMTP(email_user, email_pass)
        
        # --- 2) Lê a planilha e o template de e-mail ---
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSu5Prkp10hWHI5bp1P1SsIXqvMHxy-V8FSusf4vdNfzDZuc2-tbeVEwnjhTx7Gi1HE9QwEG6GzVZYn/pub?gid=1523497455&single=true&output=csv"
        df = pd.read_csv(url)
        df = df[df['Status'] == 'Pendente']

        # O template deve estar no mesmo diretório
        with open("email_template.html", "r", encoding="utf-8") as f:
            template = f.read()

        # --- 3) Itera e envia os e-mails ---
        logs = []
        # (Sua lógica de envio de e-mail estava ótima, mantida quase integralmente)
        for _, row in df.iterrows():
            # ... (Lógica para montar o link do calendar e o corpo do e-mail) ...
            yag.send(to=row["Email"], subject="Confirmação de Agendamento", contents=body)
            logs.append(f"E-mail enviado para {row['Nome Cliente']}.")

        if not logs:
            return {"status": "Concluído", "detalhe": "Nenhum agendamento pendente encontrado."}

        return {"status": "Concluído", "detalhe": logs}

    except Exception as e:
        return {"status": "Erro", "detalhe": str(e)}