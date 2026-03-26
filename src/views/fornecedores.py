import flet as ft

def fornecedores(page: ft.Page):
    return ft.View(
        route="/fornecedores",
        controls=[
            ft.AppBar(
                title=ft.Text("Fornecedores"),
                bgcolor=ft.Colors.SURFACE_BRIGHT
        ),
        ft.Text("Página de Fornecedores"),
    ]

)