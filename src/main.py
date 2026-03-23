import flet as ft
import gspread
from datetime import datetime
from gerarpdf import gerar_pdf
import os
import pandas as pd

# AUTENTICACAO
nome_app = "AutCompraSystem"
caminho_creds = os.path.join(os.path.join(os.getenv('APPDATA'), nome_app), "creds.json")

# Verifica se a pasta existe, se não, cria (útil na primeira execução)
if not os.path.exists(os.path.join(os.getenv('APPDATA'), nome_app)):
    os.makedirs(os.path.join(os.getenv('APPDATA'), nome_app))

print(f"Buscando credenciais em: {caminho_creds}")
gc = gspread.service_account(filename=caminho_creds)

wks = gc.open("AutComprasMaster").sheet1
wks2 = gc.open("AutComprasMaster").worksheet("Fornecedores")

def main(page: ft.Page):
    page.title = "AutCompraSystem"
    page.add(ft.Text(value="SISTEMA DE AUTORIZACAO DE COMPRAS\n", align=ft.Alignment.CENTER))
    
    #CAMPOS DE TEXTO
    data = datetime.now().strftime("%d/%m/%Y")
    fornecedor = ft.Dropdown(label = "Fornecedor: ", editable=True, options=[
        ft.DropdownOption(row[1]) for row in pd.DataFrame(wks2.get_all_records()).itertuples()
    ], align=ft.Alignment.CENTER)
    orcamento = ft.TextField(label = "Número do orçamento: ", align=ft.Alignment.CENTER)
    placa = ft.TextField(label = "Placa: ", align=ft.Alignment.CENTER)
    km = ft.TextField(label = "KM: ", align=ft.Alignment.CENTER)
    valor_pecas = ft.TextField(label = "Valor das peças: ", input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string=""),align=ft.Alignment.CENTER)
    valor_mao_de_obra = ft.TextField(label = "Valor da mão de obra: ", align=ft.Alignment.CENTER)
    observacao = ft.TextField(label = "Observações: ", align=ft.Alignment.CENTER)

    #BOTAO DE ENVIO
    def enviar(e):
        ultimo_numero = str(int(wks.cell(2, 1).value[-3:])+1).zfill(3)
        numero = f"{datetime.now().strftime('%m%y')}"+f"-{ultimo_numero}"
        page.add(ft.Text(f"Registro enviado: {numero}", align=ft.Alignment.CENTER))
        wks.insert_row([numero, data, fornecedor.value, orcamento.value, placa.value, km.value, valor_pecas.value, valor_mao_de_obra.value, observacao.value], index=2)
        
        dados = {
        "numero": numero,
        "data": data,
        "fornecedor": fornecedor.value,
        "orcamento": orcamento.value,
        "placa": placa.value,
        "km": km.value,
        "valor_pecas": valor_pecas.value,
        "valor_mao_de_obra": valor_mao_de_obra.value,
        "observacao": observacao.value
        }

        #GERAR PDF
        gerar_pdf(dados)

        #LIMPA OS CAMPOS DE TEXTO APÓS O ENVIO
        fornecedor.value = ""
        orcamento.value = ""
        placa.value = ""
        km.value = ""
        valor_pecas.value = ""
        valor_mao_de_obra.value = ""
        observacao.value = ""

    benviar = ft.Button("Enviar", on_click=enviar, align=ft.Alignment.CENTER)
    
    layout = ft.Column([
        # primeira linha
        ft.Row([fornecedor, orcamento]),

        # demais linhas
        ft.Row([placa, km]),
        ft.Row([valor_pecas, valor_mao_de_obra]),
        ft.Row([observacao]),
    ], spacing=10)

    page.add(layout)
    page.add(benviar)

ft.run(main)