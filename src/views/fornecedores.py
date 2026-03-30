import flet as ft
from db_manager import db

def fornecedores(page: ft.Page):
    nome_input = ft.TextField(label="Nome/Razão Social", expand=True)
    cpf_cnpj_input = ft.TextField(label="CPF/CNPJ", width=300)

    lista_fornecedores = ft.ListView(expand=True, spacing=10)

    def atualizar_lista():
        lista_fornecedores.controls.clear()
        fornecedores_db = db.obter_todos_fornecedores()
        for f in fornecedores_db:
            status = " (Pendente de Sincronização)" if f.get("sincronizado") == 0 else ""
            lista_fornecedores.controls.append(
                ft.ListTile(
                    title=ft.Text(f"{f['nome_razao_social']}{status}"),
                    subtitle=ft.Text(f['cpf_cnpj']),
                    leading=ft.Icon(ft.Icons.BUSINESS),
                )
            )
        if page.route == "/fornecedores":
            page.update()

    def cadastrar(e):
        nome = nome_input.value.strip()
        cpf_cnpj = cpf_cnpj_input.value.strip()
        if not nome:
            snack = ft.SnackBar(content=ft.Text("Nome/Razão Social é obrigatório!"), bgcolor=ft.Colors.RED_500)
            if hasattr(page, "overlay"):
                page.overlay.append(snack)
                snack.open = True
            elif hasattr(page, "open"):
                page.open(snack)
            page.update()
            return

        try:
            db.salvar_fornecedor_local(nome, cpf_cnpj)
            snack = ft.SnackBar(content=ft.Text("Fornecedor cadastrado offline com sucesso!"), bgcolor=ft.Colors.GREEN_600)
            nome_input.value = ""
            cpf_cnpj_input.value = ""
            atualizar_lista()
        except Exception as ex:
            snack = ft.SnackBar(content=ft.Text(f"Erro ao cadastrar: {ex}"), bgcolor=ft.Colors.RED_500)

        if hasattr(page, "overlay"):
            page.overlay.append(snack)
            snack.open = True
        elif hasattr(page, "open"):
            page.open(snack)
        page.update()

    atualizar_lista()

    return ft.View(
        route="/fornecedores",
        controls=[
            ft.AppBar(
                title=ft.Text("Fornecedores"),
                bgcolor=ft.Colors.SURFACE_BRIGHT
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Cadastrar Novo Fornecedor", size=20, weight=ft.FontWeight.BOLD),
                    ft.Row([nome_input, cpf_cnpj_input, ft.Button("Cadastrar", on_click=cadastrar, icon=ft.Icons.SAVE)]),
                    ft.Divider(),
                    ft.Text("Fornecedores Cadastrados", size=20, weight=ft.FontWeight.BOLD),
                    lista_fornecedores
                ]),
                padding=20,
                expand=True
            )
        ]
    )