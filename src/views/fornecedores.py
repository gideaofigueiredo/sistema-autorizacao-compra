import flet as ft
import pandas as pd

def fornecedores(page: ft.Page):

    fornecedor = pd.read_csv("storage/AutComprasMaster - Fornecedores.csv", encoding="utf-8", sep=",")
    fornecedor = fornecedor.fillna("")

    return ft.View(
        route="/fornecedores",
        controls=[
            ft.AppBar(
                title=ft.Text("Fornecedores"),
                bgcolor=ft.Colors.SURFACE_BRIGHT
        ),
        ft.ListView(
            controls=[
                ft.ListTile(
                    title=ft.Text(str(row.nome_razao_social)),
                    subtitle=ft.Text(str(row.cpf_cnpj)),
                    expand=True
                ) for row in fornecedor.itertuples(index=False)
            ], expand=True
        )
    ]

)