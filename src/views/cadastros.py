import flet as ft

def main(page: ft.Page):
    page.add(ft.Text("Cadastros"))
    page.add(ft.Text(f"Initial route: {page.route}"))

ft.run(main)