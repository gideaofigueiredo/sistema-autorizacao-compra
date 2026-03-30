import flet as ft
import json
import os
from utils_path import get_base_path

def cadastros(page: ft.Page):
    empresa = ft.TextField(label="Empresa:")
    comprador = ft.TextField(label="Comprador:")
    rodape = ft.TextField(label="Rodapé:")

    def salvar_dados(e):
        with open(os.path.join(get_base_path(), "storage", "dados_usuario.json"), "w", encoding='utf-8') as f:
            json.dump({
                "empresa": empresa.value,
                "comprador": comprador.value,
                "rodape": rodape.value
            }, f, ensure_ascii=False, indent=4)
        ft.SnackBar("Dados salvos com sucesso!").open=True
        page.update()

    return ft.View(
        route="/cadastros",
        controls=[
            ft.AppBar(
                title=ft.Text("Cadastros"),
                bgcolor=ft.Colors.SURFACE_BRIGHT
        ),
        ft.Text("Textos padrão para os documentos gerados"),
        empresa,
        comprador,
        rodape,
        ft.Button("Salvar", on_click=salvar_dados)
    ]
)