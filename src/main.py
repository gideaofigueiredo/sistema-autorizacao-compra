import flet as ft
import gspread
import asyncio
from datetime import datetime
from gerarpdf import gerar_pdf
import os
from db_manager import db
import pathlib
import webbrowser
import subprocess
from utils_path import get_base_path, get_data_path, get_documents_path
from utils_ui import mascara_moeda, converter_para_float, mostrar_mensagem

from views.historico import historico
from views.fornecedores import fornecedores
from views.cadastros import cadastros

nome_app = "AutCompraSystem"
caminho_creds = os.path.join(get_data_path(), "creds.json")

def obter_planilha_master():
    gc = gspread.service_account(filename=caminho_creds)
    return gc.open("AutComprasMaster")

ROUTES = {
    "/": None,
    "/historico": historico,
    "/fornecedores": fornecedores,
    "/cadastros": cadastros,
}


def main(page: ft.Page):
    page.title = "AutCompraSystem"
    try:
        page.window.maximized = True
    except AttributeError:
        page.window_maximized = True

    def sincronizar_dados(e):
        page.splash = ft.ProgressBar()
        page.update()
        mostrar_mensagem(page, "Iniciando sincronização com Google Sheets...")
        
        pendentes_auth = db.obter_pendentes_sincronizacao()
        pendentes_forn = db.obter_fornecedores_pendentes()
        
        if not pendentes_auth and not pendentes_forn:
            page.splash = None
            mostrar_mensagem(page, "Tudo já está sincronizado!")
            page.update()
            return
            
        try:
            planilha = obter_planilha_master()
            if pendentes_auth:
                wks = planilha.sheet1
                for registro in pendentes_auth:
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
            
            if pendentes_forn:
                wks_forn = planilha.worksheet("Fornecedores")
                for registro_f in pendentes_forn:
                    linha_f = [
                        registro_f["nome_razao_social"],
                        registro_f["cpf_cnpj"]
                    ]
                    # The user requested to append at the top (index=2) for fornecedores as well
                    wks_forn.insert_row(linha_f, index=2)
                    db.marcar_fornecedor_sincronizado(registro_f["id"])
                    
            msgs_sucesso = []
            if pendentes_auth: msgs_sucesso.append(f"{len(pendentes_auth)} autorização(ões)")
            if pendentes_forn: msgs_sucesso.append(f"{len(pendentes_forn)} fornecedor(es)")
                
            mostrar_mensagem(page, f"{', '.join(msgs_sucesso)} sincronizado(s) com sucesso!", ft.Colors.GREEN_600)
            
        except Exception as ex:
            mostrar_mensagem(page, f"Erro ao sincronizar: {str(ex)}", ft.Colors.RED_600)
        finally:
            page.splash = None
            page.update()

    def restaurar_dados_nuvem(e):
        page.splash = ft.ProgressBar()
        page.update()
        mostrar_mensagem(page, "Restaurando dados do Google Sheets. Aguarde...")
        try:
            planilha = obter_planilha_master()
            wks = planilha.sheet1
            wks_forn = planilha.worksheet("Fornecedores")
            
            auth_rows = wks.get_all_values()[1:] # Pula cabeçalho
            forn_rows = wks_forn.get_all_values()[1:]
            
            db.sincronizar_de_nuvem(auth_rows, forn_rows)
            mostrar_mensagem(page, "Dados restaurados da nuvem com sucesso!", ft.Colors.GREEN_600)
            
            page.views.clear()
            page.views.append(build_home_view())
            page.update()
        except Exception as ex:
            mostrar_mensagem(page, f"Erro ao restaurar: {str(ex)}", ft.Colors.RED_600)
        finally:
            page.splash = None
            page.update()

    def abrir_pasta_configuracao(e):
        path = get_data_path()
        subprocess.Popen(f'explorer "{path}"')
        mostrar_mensagem(page, "Pasta de configurações aberta.")

    def build_appbar() -> ft.AppBar:
        return ft.AppBar(
            title=ft.Text("Sistema de Autorização de Compras"),
            bgcolor=ft.Colors.BLUE_500,
            actions=[
                ft.IconButton(ft.Icons.FOLDER_SPECIAL, tooltip="Configurações (Logotipo)", on_click=abrir_pasta_configuracao),
                ft.IconButton(ft.Icons.SYNC, tooltip="Sincronizar Planilha", on_click=sincronizar_dados),
                ft.IconButton(ft.Icons.HISTORY, tooltip="Histórico",
                    on_click=lambda e: asyncio.ensure_future(page.push_route("/historico"))),
                ft.IconButton(ft.Icons.PEOPLE, tooltip="Fornecedores",
                    on_click=lambda e: asyncio.ensure_future(page.push_route("/fornecedores"))),
                ft.IconButton(ft.Icons.TEXT_SNIPPET_OUTLINED, tooltip="Cadastros",
                    on_click=lambda e: asyncio.ensure_future(page.push_route("/cadastros"))),
                ft.PopupMenuButton(
                    items=[
                        ft.PopupMenuItem("Restaurar do Google Sheets", icon=ft.Icons.CLOUD_DOWNLOAD, on_click=restaurar_dados_nuvem),
                        ft.PopupMenuItem("Perfil"),
                        ft.PopupMenuItem(),
                        ft.PopupMenuItem("Sair"),
                    ],
                ),
            ],
        )

    def build_home_view() -> ft.View:
        data = datetime.now().strftime("%d/%m/%Y")
        
        # Carregar fornecedores do banco de dados local para funcionar offline
        opcoes_forn = []
        try:
            fornecedores_db = db.obter_todos_fornecedores()
            opcoes_forn = [ft.DropdownOption(f["nome_razao_social"]) for f in fornecedores_db if f.get("nome_razao_social")]
        except Exception:
            pass
            
        ultimo_gerado_container = ft.Container(visible=False)

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
                
                # Exibe a última gerada logo abaixo do formulário
                arquivo_path = pathlib.Path(os.path.join(get_documents_path(), f"Autorização de Compra {numero}.pdf"))
                ultimo_gerado_container.visible = True
                ultimo_gerado_container.content = ft.Column([
                    ft.Text("\nÚltima Autorização Gerada:", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_500),
                    ft.Row([
                        ft.Text(f"{arquivo_path.name}"),
                        ft.Button("Abrir Arquivo", icon=ft.Icons.FILE_OPEN, on_click=lambda e: webbrowser.open(arquivo_path.resolve().as_uri())),
                        ft.Button("Abrir Pasta", icon=ft.Icons.FOLDER_OPEN, on_click=lambda e: subprocess.Popen(f'explorer /select,"{arquivo_path.resolve()}"'))
                    ], alignment=ft.MainAxisAlignment.CENTER)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                
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
                    ultimo_gerado_container,
                    ft.Container(height=40) # Espaço adicional final
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