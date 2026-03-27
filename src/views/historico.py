import flet as ft
from pathlib import Path
import datetime
import webbrowser
import subprocess

def historico(page: ft.Page):

    pdf_files = sorted(
        Path("storage/").glob("*.pdf"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )
    
    return ft.View(
        route="/historico",
        controls=[
            ft.AppBar(
                title=ft.Text("Histórico"),
                bgcolor=ft.Colors.SURFACE_BRIGHT
        ),
        ft.Column([
            ft.Row([
                ft.Text(f"Arquivo: {pdf_file.name} - {datetime.datetime.fromtimestamp(pdf_file.stat().st_mtime)}"),
                ft.ElevatedButton(
                    "Abrir",
                    on_click=lambda e, f=pdf_file: webbrowser.open(f.resolve().as_uri())),
                ft.ElevatedButton(
                    "Abrir pasta",
                    on_click=lambda e, f=pdf_file: subprocess.Popen(f"explorer /select,\"{f.resolve()}\"")
                )
            ], alignment=ft.MainAxisAlignment.CENTER)
            for pdf_file in pdf_files
        ])

    ]

)