import flet as ft
import gspread
import asyncio
from datetime import datetime
from gerarpdf import gerar_pdf
import os
import pandas as pd
from db_manager import db

from views.historico import historico
from views.fornecedores import fornecedores
from views.cadastros import cadastros

nome_app = "AutCompraSystem"
caminho_creds = os.path.join(os.getenv('APPDATA'), nome_app, "creds.json")

if not os.path.exists(os.path.join(os.getenv('APPDATA'), nome_app)):
    os.makedirs(os.path.join(os.getenv('APPDATA'), nome_app))

def obter_planilha_master():
    gc = gspread.service_account(filename=caminho_creds)
    return gc.open("AutComprasMaster").sheet1

ROUTES = {
    "/": None,
    "/historico": historico,
    "/fornecedores": fornecedores,
    "/cadastros": cadastros,
}

def mascara_moeda(e):
    valor = e.control.value
    apenas_numeros = ''.join(filter(str.isdigit, valor))
    if not apenas_numeros:
        e.control.value = ""
        e.control.update()
        return
    inteiro = int(apenas_numeros)
    texto_formatado = f"{inteiro / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    e.control.value = texto_formatado
    e.control.update()

def converter_para_float(valor_str):
    if not valor_str:
        return 0.0
    return float(valor_str.replace(".", "").replace(",", "."))

def mostrar_mensagem(page, texto, cor=None):
    snack = ft.SnackBar(content=ft.Text(texto), bgcolor=cor)
    if hasattr(page, "overlay"):
        page.overlay.append(snack)
        snack.open = True
    elif hasattr(page, "open"):
        page.open(snack)
    else:
        page.snack_bar = snack
        page.snack_bar.open = True
    page.update()

def main(page: ft.Page):
    page.title = "AutCompraSystem"
    try:
        page.window.maximized = True
    except AttributeError:
        page.window_maximized = True

    def sincronizar_dados(e):
        mostrar_mensagem(page, "Iniciando sincronização com Google Sheets...")
        
        pendentes = db.obter_pendentes_sincronizacao()
        if not pendentes:
            mostrar_mensagem(page, "Tudo já está sincronizado!")
            return
            
        try:
            wks = obter_planilha_master()
            for registro in pendentes:
                linha = [
                    registro["numero_gerado"],
                    registro["data"],
                    registro["fornecedor"],
                    registro["orcamento"],
                    registro["placa"],
                    registro["km"],
                    f"{registro['valor_pecas']:.2f}".replace(".", ","),
                    f"{registro['valor_mao_de_obra']:.2f}".replace(".", ","),
                    registro["observacao"]
                ]
                wks.insert_row(linha, index=2)
                db.marcar_como_sincronizado(registro["id"])
                
            mostrar_mensagem(page, f"{len(pendentes)} registro(s) sincronizado(s) com sucesso!", ft.Colors.GREEN_600)
            
        except Exception as ex:
            mostrar_mensagem(page, f"Erro ao sincronizar: {str(ex)}", ft.Colors.RED_600)

    def build_appbar() -> ft.AppBar:
        return ft.AppBar(
            title=ft.Text("Sistema de Autorização de Compras"),
            bgcolor=ft.Colors.BLUE_500,
            actions=[
                ft.IconButton(ft.Icons.SYNC, tooltip="Sincronizar Planilha", on_click=sincronizar_dados),
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
        
        # Carregar fornecedores do arquivo local para funcionar offline
        opcoes_forn = []
        caminho_forn = "storage/AutComprasMaster - Fornecedores.csv"
        if os.path.exists(caminho_forn):
            try:
                df_forn = pd.read_csv(caminho_forn, encoding="utf-8", sep=",")
                df_forn = df_forn.fillna("")
                # Usando iterrows para iterar de maneira segura independente do nome da coluna exata.
                # Como str(row.nome_razao_social) é usado em fornecedores.py, 
                # sabemos que nome_razao_social deve existir.
                if 'nome_razao_social' in df_forn.columns:
                    opcoes_forn = [ft.DropdownOption(str(row.nome_razao_social)) for row in df_forn.itertuples()]
            except Exception:
                pass

        fornecedor = ft.Dropdown(
            label="Fornecedor:",
            editable=True,
            options=opcoes_forn,
            menu_height=300,
            width=500,
        )
        orcamento = ft.TextField(label="Número do orçamento:", width=500)
        placa = ft.TextField(label="Placa:", width=500)
        km = ft.TextField(label="KM:", width=500)
        
        valor_pecas = ft.TextField(
            label="Valor das peças:",
            width=500,
            on_change=mascara_moeda,
            prefix=ft.Text("R$ ")
        )
        valor_mao_de_obra = ft.TextField(
            label="Valor da mão de obra:",
            width=500,
            on_change=mascara_moeda,
            prefix=ft.Text("R$ ")
        )
        observacao = ft.TextField(label="Observações:", width=1010, multiline=True, max_lines=3)

        def enviar(e):
            if not fornecedor.value:
                mostrar_mensagem(page, "Fornecedor é obrigatório!", ft.Colors.RED_500)
                return

            numero = db.obter_e_incrementar_numero_local()
            
            p_float = converter_para_float(valor_pecas.value)
            mo_float = converter_para_float(valor_mao_de_obra.value)
            total = p_float + mo_float
            
            dados = {
                "numero": numero,
                "data": data,
                "fornecedor": fornecedor.value,
                "orcamento": orcamento.value,
                "placa": placa.value,
                "km": km.value,
                "valor_pecas": p_float,
                "valor_mao_de_obra": mo_float,
                "total_autorizado": total,
                "observacao": observacao.value,
            }

            try:
                db.salvar_autorizacao_local(dados)
                gerar_pdf(dados)
                mostrar_mensagem(page, "Autorização gerada e salva offline com sucesso!", ft.Colors.GREEN_600)
            except Exception as ex:
                mostrar_mensagem(page, f"Erro ao salvar: {str(ex)}", ft.Colors.RED_500)

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