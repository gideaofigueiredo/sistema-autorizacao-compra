import flet as ft

def mascara_moeda(e):
    valor = e.control.value
    apenas_numeros = ''.join(filter(str.isdigit, valor))
    if not apenas_numeros:
        e.control.value = ""
        e.control.update()
        return
    inteiro = int(apenas_numeros)
    texto_formatado = f"{inteiro / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    e.control.value = texto_formatado
    e.control.update()

def converter_para_float(valor_str):
    if not valor_str:
        return 0.0
    return float(valor_str.replace(".", "").replace(",", "."))

def mostrar_mensagem(page, texto, cor=None):
    snack = ft.SnackBar(content=ft.Text(texto), bgcolor=cor)
    if hasattr(page, "overlay"):
        page.overlay.append(snack)
        snack.open = True
    elif hasattr(page, "open"):
        page.open(snack)
    else:
        page.snack_bar = snack
        page.snack_bar.open = True
    page.update()
