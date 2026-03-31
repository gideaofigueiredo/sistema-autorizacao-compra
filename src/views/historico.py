import flet as ft
from pathlib import Path
import os
import webbrowser
from utils_path import get_documents_path
from db_manager import db
from gerarpdf import gerar_pdf
from utils_ui import mascara_moeda, converter_para_float, mostrar_mensagem

def historico(page: ft.Page):
    autorizacoes = db.obter_ultimas_autorizacoes(50)
    lista_controles = []

    def load_data():
        lista_controles.clear()
        autorizacoes_novas = db.obter_ultimas_autorizacoes(50)
        for auth in autorizacoes_novas:
            lista_controles.append(criar_linha_historico(auth))
        lista_auths.controls = lista_controles
        page.update()

    def excluir_auth(id_registro, numero_gerado):
        # 1. db
        db.excluir_autorizacao(id_registro)
        # 2. PDF
        pdf_path = os.path.join(get_documents_path(), f"Autorização de Compra {numero_gerado}.pdf")
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception:
                pass 
        
        mostrar_mensagem(page, f"Autorização {numero_gerado} excluída com sucesso!", ft.Colors.GREEN)
        load_data()

    def confirmar_exclusao(id_registro, numero_gerado):
        def fechar(e):
            dialog.open = False
            page.update()
            
        def confirmar(e):
            dialog.open = False
            page.update()
            excluir_auth(id_registro, numero_gerado)

        dialog = ft.AlertDialog(
            title=ft.Text("Confirmar Exclusão"),
            content=ft.Text(f"Tem certeza que deseja apagar a autorização {numero_gerado}?\nEssa ação é permanente e excluirá o PDF gerado fisicamente."),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar),
                ft.TextButton("Excluir", on_click=confirmar, style=ft.ButtonStyle(color=ft.Colors.RED)),
            ]
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def abrir_edicao(auth):
        fornecedores_db = db.obter_todos_fornecedores()
        opcoes_forn = [ft.DropdownOption(f["nome_razao_social"]) for f in fornecedores_db if f.get("nome_razao_social")]
        
        fornecedor = ft.Dropdown(label="Fornecedor:", editable=True, options=opcoes_forn, value=auth["fornecedor"], menu_height=300, width=500,)
        orcamento = ft.TextField(label="Nº Orçamento:", value=auth["orcamento"])
        placa = ft.TextField(label="Placa:", value=auth["placa"])
        km = ft.TextField(label="KM:", value=auth["km"])
        
        val_pecas = f"{auth['valor_pecas']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        val_mo = f"{auth['valor_mao_de_obra']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        valor_pecas = ft.TextField(label="Valor Peças:", value=val_pecas, on_change=mascara_moeda, prefix=ft.Text("R$ "))
        valor_mao_de_obra = ft.TextField(label="Valor Mão de Obra:", value=val_mo, on_change=mascara_moeda, prefix=ft.Text("R$ "))
        observacao = ft.TextField(label="Observações:", value=auth["observacao"], multiline=True, max_lines=3)

        def fechar_dialog(e):
            dialog.open = False
            page.update()

        def salvar_edicao(e):
            if not fornecedor.value:
                mostrar_mensagem(page, "Fornecedor é obrigatório!", ft.Colors.RED)
                return
            
            p_float = converter_para_float(valor_pecas.value)
            mo_float = converter_para_float(valor_mao_de_obra.value)
            total = p_float + mo_float
            
            dados = {
                "numero": auth["numero_gerado"],
                "data": auth["data"],
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
                db.atualizar_autorizacao_local(auth["id"], dados)
                gerar_pdf(dados) # Regera PDF por cima do antigo
                mostrar_mensagem(page, "Autorização atualizada e PDF reescrito com sucesso!", ft.Colors.GREEN)
                dialog.open = False
                load_data()
            except Exception as ex:
                mostrar_mensagem(page, f"Erro ao atualizar: {ex}", ft.Colors.RED)
                dialog.open = False
                page.update()

        campos = ft.Column([
            fornecedor, orcamento, placa, km, valor_pecas, valor_mao_de_obra, observacao
        ], scroll=ft.ScrollMode.AUTO, expand=True)

        dialog = ft.AlertDialog(
            title=ft.Text(f"Editando Autorização Nº {auth['numero_gerado']}"),
            content=ft.Container(content=campos, width=500, height=450),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar_dialog),
                ft.TextButton("Atualizar & Regerar PDF", on_click=salvar_edicao),
            ]
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def criar_linha_historico(auth):
        pdf_path = os.path.join(get_documents_path(), f"Autorização de Compra {auth['numero_gerado']}.pdf")
        path_obj = Path(pdf_path)
        
        tem_arquivo = path_obj.exists()
        sincr = auth["sincronizado"] == 1
        
        btn_abrir = ft.IconButton(
            ft.Icons.FILE_OPEN, 
            tooltip="Abrir PDF", 
            disabled=not tem_arquivo,
            on_click=lambda e, p=path_obj: webbrowser.open(p.resolve().as_uri()) if p.exists() else None
        )
        
        btn_editar = ft.IconButton(
            ft.Icons.EDIT,
            icon_color=ft.Colors.BLUE,
            tooltip="Editar" if not sincr else "Apenas autorizações pendentes podem ser editadas",
            disabled=sincr,
            on_click=lambda e, a=auth: abrir_edicao(a)
        )
        
        btn_excluir = ft.IconButton(
            ft.Icons.DELETE,
            icon_color=ft.Colors.RED,
            tooltip="Excluir" if not sincr else "Apenas autorizações pendentes podem ser excluídas",
            disabled=sincr,
            on_click=lambda e: confirmar_exclusao(auth["id"], auth["numero_gerado"])
        )

        status_icon = ft.Icon(
            ft.Icons.CLOUD_DONE if sincr else ft.Icons.CLOUD_OFF,
            color=ft.Colors.GREEN if sincr else ft.Colors.GREY,
            tooltip="Sincronizado" if sincr else "Pendente na Nuvem",
            size=20
        )

        return ft.Card(
            content=ft.Container(
                padding=10,
                content=ft.Row([
                    ft.Row([
                        status_icon,
                        ft.Text(f"Nº {auth['numero_gerado']}", weight="bold"),
                        ft.Text(f"- {auth['fornecedor']} - {auth['data']}")
                    ], expand=True),
                    btn_abrir,
                    btn_editar,
                    btn_excluir
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            )
        )

    lista_auths = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    for auth in autorizacoes:
        lista_controles.append(criar_linha_historico(auth))
    
    lista_auths.controls = lista_controles

    return ft.View(
        route="/historico",
        controls=[
            ft.AppBar(
                title=ft.Text("Histórico de Autorizações"),
                bgcolor=ft.Colors.SURFACE_BRIGHT
            ),
            ft.Container(
                padding=20,
                expand=True,
                content=ft.Column([
                    lista_auths
                ])
            )
        ]
    )