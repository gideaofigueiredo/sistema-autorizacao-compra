from fpdf import FPDF, XPos, YPos
from fpdf.enums import CellBordersLayout
from fpdf.fonts import FontFace
from datetime import datetime
import json
import os
from utils_path import get_base_path, get_data_path, get_documents_path

def gerar_pdf(dados: dict):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10) 

    # Carrega JSON (prioriza AppData, faz fallback para storage padrão do sistema)
    json_appdata = os.path.join(get_data_path(), "dados_usuario.json")
    if os.path.exists(json_appdata):
        with open(json_appdata, "r", encoding="utf-8") as f:
            dados_padrao = json.load(f)
    else:
        json_fallback = os.path.join(get_base_path(), "storage", "dados_usuario.json")
        if os.path.exists(json_fallback):
            with open(json_fallback, "r", encoding="utf-8") as f:
                dados_padrao = json.load(f)
        else:
            dados_padrao = {"empresa": "Nome da Empresa", "comprador": "Comprador Padrão", "rodape": "Rodapé Padrão"}

    logo_appdata_png = os.path.join(get_data_path(), "logo.png")
    logo_appdata_jpg = os.path.join(get_data_path(), "logo.jpg")
    
    logo_path = None
    if os.path.exists(logo_appdata_png):
        logo_path = logo_appdata_png
    elif os.path.exists(logo_appdata_jpg):
        logo_path = logo_appdata_jpg
    else:
        logo_fallback = os.path.join(get_base_path(), "src", "assets", "logo.svg")
        if os.path.exists(logo_fallback):
            logo_path = logo_fallback

    pdf.set_font("helvetica", size=13)
    with pdf.table(gutter_height=3, gutter_width=3) as table:
        row = table.row()
        if logo_path:
            row.cell("", img=logo_path, img_fill_width=True, align="C")
        else:
            row.cell("")
        row.cell(f"{dados_padrao['empresa']}\nAutorização de Compra", colspan=3,align="C")
        pdf.set_font("helvetica", size=12, style="B")
        row.cell(f"Nº {dados['numero']}", align="C")

    pdf.ln(3)
    pdf.set_font("helvetica", size=10)
    with pdf.table(headings_style=FontFace(emphasis=None)) as table:
        row = table.row()
        row.cell(f"Emitido por: {dados_padrao['comprador']}")
        row.cell(f"Data de emissão: {datetime.now().strftime('%d/%m/%Y')} às {datetime.now().strftime('%H:%M:%S')}")

    pdf.set_font("helvetica", size=12, style="B")
    pdf.ln(10)
    pdf.cell(190, 10,text="Dados da Autorização", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_font("helvetica", size=10)
    pdf.cell(190, 10, text="Documento oficial para liberação de serviços", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

    pdf.ln(10)
    pdf.set_font("helvetica", size=10)
    with pdf.table() as table:
        row = table.row(style=FontFace(fill_color=(178, 178, 178)))
        row.cell("Fornecedor:", border=CellBordersLayout.TOP | CellBordersLayout.LEFT | CellBordersLayout.RIGHT)
        row.cell("Nº do orçamento:", border=CellBordersLayout.TOP | CellBordersLayout.LEFT | CellBordersLayout.RIGHT)

        row = table.row()
        row.cell(f"{dados['fornecedor']}", border=CellBordersLayout.BOTTOM | CellBordersLayout.LEFT | CellBordersLayout.RIGHT)
        row.cell(f"{dados['orcamento']}", border=CellBordersLayout.BOTTOM | CellBordersLayout.RIGHT)

    pdf.ln(5)
    with pdf.table() as table:
        row = table.row(style=FontFace(fill_color=(178, 178, 178)))
        row.cell("Placa do veículo:", border=CellBordersLayout.TOP | CellBordersLayout.LEFT | CellBordersLayout.RIGHT)
        row.cell("Quilometragem:", border=CellBordersLayout.RIGHT | CellBordersLayout.TOP)

        row = table.row()
        row.cell(f"{dados['placa']}", border=CellBordersLayout.BOTTOM | CellBordersLayout.LEFT | CellBordersLayout.RIGHT)
        row.cell(f"{dados['km']}", border=CellBordersLayout.BOTTOM | CellBordersLayout.RIGHT)

    def format_brl(valor):
        return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    pdf.ln(10)
    with pdf.table() as table:
        row = table.row(style=FontFace(fill_color=(178, 178, 178)))
        row.cell("Detalhamento de valores", colspan=2, border=CellBordersLayout.TOP | CellBordersLayout.LEFT | CellBordersLayout.RIGHT, align="C")

        row = table.row(style=FontFace(emphasis="B", fill_color=(220, 220, 220)))
        row.cell("Valor das Peças", align="C")
        row.cell("Valor da Mão de Obra", align="C")

        row = table.row()
        row.cell(f"R$ {format_brl(dados['valor_pecas'])}", align="C")
        row.cell(f"R$ {format_brl(dados['valor_mao_de_obra'])}", align="C")

    pdf.ln(10)
    with pdf.table() as table:
        row = table.row(style=FontFace(fill_color=(178, 178, 178)))
        row.cell("Valor total autorizado", colspan=2, border=CellBordersLayout.TOP | CellBordersLayout.LEFT | CellBordersLayout.RIGHT, align="C")

        row = table.row()
        total_value = dados.get('total_autorizado', float(dados['valor_pecas']) + float(dados['valor_mao_de_obra']))
        row.cell(f"R$ {format_brl(total_value)}", colspan=2,align="C")

    pdf.ln(10)
    with pdf.table() as table:
        row = table.row(style=FontFace(fill_color=(178, 178, 178)))
        row.cell("Observações", colspan=2, border=CellBordersLayout.TOP | CellBordersLayout.LEFT | CellBordersLayout.RIGHT, align="C")

        row = table.row()
        row.cell(f"{dados['observacao']}", colspan=2, align="L")
    
    pdf.ln(5)
    pdf.set_font("helvetica", size=10)
    pdf.write(text="Favor informar o número da Autorização de Compra na nota fiscal.")

    pdf.set_y(-20)
    pdf.set_font("helvetica", size=8)
    pdf.write(text=f"{dados_padrao['rodape']}")

    output_path = os.path.join(get_documents_path(), f"Autorização de Compra {dados['numero']}.pdf")
    pdf.output(output_path)