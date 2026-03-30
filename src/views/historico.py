import flet as ft
from pathlib import Path
import datetime
import webbrowser
import subprocess
import os
from utils_path import get_base_path

def historico(page: ft.Page):

    pdf_files = sorted(
        Path(os.path.join(get_base_path(), "storage")).glob("*.pdf"),
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
                ft.Button(
                    "Abrir",
                    on_click=lambda e, f=pdf_file: webbrowser.open(f.resolve().as_uri())),
                ft.Button(
                    "Abrir pasta",
                    on_click=lambda e, f=pdf_file: subprocess.Popen(f"explorer /select,\"{f.resolve()}\"")
                )
            ], alignment=ft.MainAxisAlignment.CENTER)
            for pdf_file in pdf_files
        ])

    ]

)