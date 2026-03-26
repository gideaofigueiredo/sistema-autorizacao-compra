import flet as ft

def cadastros(page: ft.Page):
    return ft.View(
        route="/cadastros",
        controls=[
            ft.AppBar(
                title=ft.Text("Cadastros"),
                bgcolor=ft.Colors.SURFACE_BRIGHT
        ),
        ft.Text("Página de Cadastros"),
    ]

)