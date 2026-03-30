import flet as ft
import json
import os
import time
from utils_path import get_data_path

def cadastros(page: ft.Page):
    empresa = ft.TextField(label="Empresa:")
    comprador = ft.TextField(label="Comprador:")
    rodape = ft.TextField(label="Rodapé:")

    def salvar_dados(e):
        page.splash = ft.ProgressBar()
        page.update()
        
        try:
            with open(os.path.join(get_data_path(), "dados_usuario.json"), "w", encoding='utf-8') as f:
                json.dump({
                    "empresa": empresa.value,
                    "comprador": comprador.value,
                    "rodape": rodape.value
                }, f, ensure_ascii=False, indent=4)
                
            time.sleep(0.3)
            
            empresa.value = ""
            comprador.value = ""
            rodape.value = ""
            
            snack = ft.SnackBar(ft.Text("Dados salvos com sucesso!"), bgcolor=ft.Colors.GREEN_600)
            if hasattr(page, "overlay"):
                page.overlay.append(snack)
                snack.open = True
            else:
                page.snack_bar = snack
                page.snack_bar.open = True
        finally:
            page.splash = None
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