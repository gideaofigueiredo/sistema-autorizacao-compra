import flet as ft

def historico(page: ft.Page):
    return ft.View(
        route="/historico",
        controls=[
            ft.AppBar(
                title=ft.Text("Histórico"),
                bgcolor=ft.Colors.SURFACE_BRIGHT
        ),
        ft.Text("Página de Histórico"),
    ]

)