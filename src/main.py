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
    page.appbar = ft.AppBar(
            leading_width=40,
            title=ft.Text("Sistema de Autorização de Compras"),
            center_title=False,
            bgcolor=ft.Colors.BLUE_500,
            actions=[
                ft.IconButton(ft.icons.Icons.HISTORY, tooltip="Histórico"),
                ft.IconButton(ft.icons.Icons.PEOPLE, tooltip="Fornecedores"),
                ft.IconButton(ft.icons.Icons.TEXT_SNIPPET_OUTLINED, tooltip="Cadastros"),
                ft.PopupMenuButton(
                    items=[
                        ft.PopupMenuItem("Perfil"),
                        ft.PopupMenuItem(),  # divisor
                        ft.PopupMenuItem("Sair"),
                    ]
                ),
            ],
        )
    titulo_pagina = ft.Text("\nNova autorização de compra", size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_500, align=ft.Alignment.CENTER)
    subtitulo_pagina = ft.Text("Preencha todos os campos obrigatórios para gerar a autorização\n\n", size=16, color=ft.Colors.GREY_700, align=ft.Alignment.CENTER)
    #CAMPOS DE TEXTO
    data = datetime.now().strftime("%d/%m/%Y")
    fornecedor = ft.Dropdown(label = "Fornecedor: ", editable=True, options=[
        ft.DropdownOption(row[1]) for row in pd.DataFrame(wks2.get_all_records()).itertuples()
    ], expand=False, menu_height=300, width=500)
    orcamento = ft.TextField(label = "Número do orçamento: ", width=500)
    placa = ft.TextField(label = "Placa: ", width=500)
    km = ft.TextField(label = "KM: ", width=500)
    valor_pecas = ft.TextField(label = "Valor das peças: ", width=500,input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string=""))
    valor_mao_de_obra = ft.TextField(label = "Valor da mão de obra: ", width=500)
    observacao = ft.TextField(label = "Observações: ", width=1010, multiline=True, max_lines=3)

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

    benviar = ft.Button("Enviar", on_click=enviar, icon=ft.icons.Icons.SEND)
    
    layout = ft.Column([
        ft.Row([fornecedor, orcamento], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([placa, km], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([valor_pecas, valor_mao_de_obra], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([observacao], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([benviar], alignment=ft.MainAxisAlignment.CENTER)
    ], spacing=20, expand=True)

    page.add(titulo_pagina, subtitulo_pagina, layout)

ft.run(main)