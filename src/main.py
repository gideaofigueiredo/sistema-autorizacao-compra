import flet as ft
import gspread
import asyncio
from datetime import datetime
from gerarpdf import gerar_pdf
import os
import pandas as pd

from views.historico import historico
from views.fornecedores import fornecedores
from views.cadastros import cadastros

nome_app = "AutCompraSystem"
caminho_creds = os.path.join(os.getenv('APPDATA'), nome_app, "creds.json")

if not os.path.exists(os.path.join(os.getenv('APPDATA'), nome_app)):
    os.makedirs(os.path.join(os.getenv('APPDATA'), nome_app))

gc = gspread.service_account(filename=caminho_creds)
wks = gc.open("AutComprasMaster").sheet1
wks2 = gc.open("AutComprasMaster").worksheet("Fornecedores")

ROUTES = {
    "/": None,  # view principal definida inline
    "/historico": historico,
    "/fornecedores": fornecedores,
    "/cadastros": cadastros,
}

def main(page: ft.Page):
    page.title = "AutCompraSystem"

    def build_appbar() -> ft.AppBar:
        return ft.AppBar(
            title=ft.Text("Sistema de Autorização de Compras"),
            bgcolor=ft.Colors.BLUE_500,
            actions=[
                ft.IconButton(ft.Icons.HISTORY, tooltip="Histórico",
                    on_click=lambda e: asyncio.ensure_future(page.push_route("/historico"))),
                ft.IconButton(ft.Icons.PEOPLE, tooltip="Fornecedores",
                    on_click=lambda e: asyncio.ensure_future(page.push_route("/fornecedores"))),
                ft.IconButton(ft.Icons.TEXT_SNIPPET_OUTLINED, tooltip="Cadastros",
                    on_click=lambda e: asyncio.ensure_future(page.push_route("/cadastros"))),
                ft.PopupMenuButton(
                    items=[
                        ft.PopupMenuItem("Perfil"),
                        ft.PopupMenuItem(),
                        ft.PopupMenuItem("Sair"),
                    ],
                ),
            ],
        )

    def build_home_view() -> ft.View:
        data = datetime.now().strftime("%d/%m/%Y")
        fornecedor = ft.Dropdown(
            label="Fornecedor:",
            editable=True,
            options=[ft.DropdownOption(row[1]) for row in pd.DataFrame(wks2.get_all_records()).itertuples()],
            menu_height=300,
            width=500,
        )
        orcamento = ft.TextField(label="Número do orçamento:", width=500)
        placa = ft.TextField(label="Placa:", width=500)
        km = ft.TextField(label="KM:", width=500)
        valor_pecas = ft.TextField(
            label="Valor das peças:",
            width=500,
            input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string=""),
        )
        valor_mao_de_obra = ft.TextField(label="Valor da mão de obra:", width=500)
        observacao = ft.TextField(label="Observações:", width=1010, multiline=True, max_lines=3)

        def enviar(e):
            ultimo_numero = str(int(wks.cell(2, 1).value[-3:]) + 1).zfill(3)
            numero = f"{datetime.now().strftime('%m%y')}-{ultimo_numero}"

            wks.insert_row([
                numero, data, fornecedor.value, orcamento.value,
                placa.value, km.value, valor_pecas.value,
                valor_mao_de_obra.value, observacao.value
            ], index=2)

            gerar_pdf({
                "numero": numero, "data": data,
                "fornecedor": fornecedor.value, "orcamento": orcamento.value,
                "placa": placa.value, "km": km.value,
                "valor_pecas": valor_pecas.value,
                "valor_mao_de_obra": valor_mao_de_obra.value,
                "observacao": observacao.value,
            })

            for campo in [fornecedor, orcamento, placa, km, valor_pecas, valor_mao_de_obra, observacao]:
                campo.value = ""
            page.update()

        return ft.View(
            route="/",
            controls=[
                build_appbar(),
                ft.Column([
                    ft.Row([
                        ft.Text("\nNova autorização de compra", size=30,
                                weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_500)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([
                        ft.Text("Preencha todos os campos obrigatórios\n", size=16, color=ft.Colors.GREY_700)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([fornecedor, orcamento], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([placa, km], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([valor_pecas, valor_mao_de_obra], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([observacao], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([
                        ft.Button("Enviar", on_click=enviar, icon=ft.Icons.SEND)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                ], spacing=20, scroll=ft.ScrollMode.AUTO),
            ],
        )

    def route_change(e):
        page.views.clear()
        page.views.append(build_home_view())

        if page.route in ROUTES and page.route != "/":
            page.views.append(ROUTES[page.route](page))

        page.update()

    async def view_pop(e):
        if e.view is not None:
            page.views.remove(e.view)
            top_view = page.views[-1]
            await page.push_route(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    route_change(None)

ft.run(main)