import pandas as pd
from fpdf import FPDF
from datetime import datetime, timedelta
from urllib.parse import quote
import yagmail
import os
import traceback # Importamos para um log de erro mais detalhado

# ==============================================================================
# FUNÇÃO PARA GERAR O PDF DA AGENDA
# ==============================================================================
def criar_pdf_agenda(data_input):
    try:
        url = 'https://docs.google.com/spreadsheets/d/1UEXan3JXGPhRz2V92r-cPhIMMwf-Uyl4VTyElwgsH6w/export?format=csv&gid=1523497455'
        df = pd.read_csv(url)

        # Converte a data de input para o formato de comparação (ano-mês-dia)
        data_escolhida = datetime.strptime(data_input.strip(), '%d/%m/%Y').strftime('%Y-%m-%d')
        
        # Garante que a coluna 'Data' na planilha esteja no formato correto para comparação
        # Adicionado errors='coerce' para transformar datas inválidas em NaT (Not a Time)
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
        
        # Remove linhas onde a data não pôde ser convertida
        df.dropna(subset=['Data'], inplace=True)
        
        agenda_dia = df[df['Data'] == data_escolhida]
        agenda_dia = agenda_dia.sort_values(by=['Nome Funcionario', 'Hora - Inicio'])

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        data_formatada = datetime.strptime(data_escolhida, '%Y-%m-%d').strftime('%d/%m/%Y')
        dia_semana = datetime.strptime(data_escolhida, '%Y-%m-%d').strftime('%A')

        pdf.cell(0, 10, txt=f"{dia_semana.capitalize()}, {data_formatada}", ln=True, align='L')
        pdf.set_font("Arial", size=14)
        pdf.cell(0, 10, txt="Agenda", ln=True, align='L')
        pdf.ln(5)

        if agenda_dia.empty:
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, txt="Nenhum agendamento para esta data.", ln=True, align='L')
        else:
            for profissional in agenda_dia['Nome Funcionario'].unique():
                pdf.set_font("Arial", "B", size=12)
                pdf.cell(0, 10, txt=profissional, ln=True, align='L')
                
                agendamentos_prof = agenda_dia[agenda_dia['Nome Funcionario'] == profissional]
                
                pdf.set_font("Arial", size=11)
                for _, row in agendamentos_prof.iterrows():
                    # Adicionado um try-except para horas mal formatadas
                    try:
                        hora = pd.to_datetime(row['Hora - Inicio']).strftime('%Hh%M')
                    except:
                        hora = "Hora Inválida"
                        
                    cliente = row['Nome Cliente']
                    servico = row['Procedimento']
                    texto = f"    {hora} - {cliente} ({servico})" if pd.notnull(servico) and servico.strip() else f"    {hora} - {cliente}"
                    pdf.cell(0, 8, txt=texto, ln=True, align='L')
                
                pdf.ln(5)

        return pdf.output(dest='S').encode('latin-1')

    except Exception as e:
        # ==============================================================================
        # MUDANÇA IMPORTANTE: Imprime o erro no log da Railway antes de retornar
        # ==============================================================================
        print("!!!!!!!!!!!!! OCORREU UM ERRO AO GERAR O PDF !!!!!!!!!!!!!")
        traceback.print_exc() # Imprime o erro completo e detalhado
        # ==============================================================================
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, txt=f"Erro ao gerar o PDF: {str(e)}", ln=True, align='L')
        return pdf.output(dest='S').encode('latin-1')


# ==============================================================================
# FUNÇÃO PARA ENVIAR E-MAILS DE CONFIRMAÇÃO
# ==============================================================================
def enviar_emails_confirmacao():
    try:
        email_user = os.environ.get('EMAIL_USER')
        email_pass = os.environ.get('EMAIL_PASS')

        if not email_user or not email_pass:
            return {"status": "Erro", "detalhe": "As variáveis de ambiente EMAIL_USER e EMAIL_PASS não foram configuradas na Railway."}

        yag = yagmail.SMTP(email_user, email_pass)
        
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSu5Prkp10hWHI5bp1P1SsIXqvMHxy-V8FSusf4vdNfzDZuc2-tbeVEwnjhTx7Gi1HE9QwEG6GzVZYn/pub?gid=1523497455&single=true&output=csv"
        df = pd.read_csv(url)
        df = df[df['Status'] == 'Pendente']

        with open("email_template.html", "r", encoding="utf-8") as f:
            template = f.read()

        logs = []
        for _, row in df.iterrows():
            # ==============================================================================
            # BUG CORRIGIDO: O bloco que cria a variável 'body' estava faltando.
            # ==============================================================================
            cliente = row["Nome Cliente"]
            procedimento = row["Procedimento"]
            
            hora_inicio = str(row["Hora - Inicio"]).strip()
            if len(hora_inicio) > 5:
                hora_inicio = hora_inicio[:5]
            datahora = row["Data"] + " " + hora_inicio
            
            inicio = datetime.strptime(datahora, "%d/%m/%Y %H:%M")
            fim = inicio + timedelta(hours=1)
            start = inicio.strftime("%Y%m%dT%H%M%SZ")
            end = fim.strftime("%Y%m%dT%H%M%SZ")

            calendar_link = (f"https://www.google.com/calendar/render?action=TEMPLATE&text={quote(procedimento)}&dates={start}/{end}")
            
            body = (
                template
                .replace("{{cliente}}", cliente)
                .replace("{{procedimento}}", procedimento)
                .replace("{{datahora}}", inicio.strftime('%d/%m/%Y %H:%M'))
                .replace("{{calendar_link}}", calendar_link)
            )
            # ==============================================================================
            
            yag.send(to=row["Email"], subject="Confirmação de Agendamento", contents=body)
            logs.append(f"E-mail enviado para {row['Nome Cliente']}.")

        if not logs:
            return {"status": "Concluído", "detalhe": "Nenhum agendamento pendente encontrado."}

        return {"status": "Concluído", "detalhe": logs}

    except Exception as e:
        # ==============================================================================
        # MUDANÇA IMPORTANTE: Imprime o erro no log da Railway antes de retornar
        # ==============================================================================
        print("!!!!!!!!!!!!! OCORREU UM ERRO AO ENVIAR E-MAILS !!!!!!!!!!!!!")
        traceback.print_exc() # Imprime o erro completo e detalhado
        # ==============================================================================
        return {"status": "Erro", "detalhe": str(e)}