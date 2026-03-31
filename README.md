# AutCompraSystem 🚗📦

O **AutCompraSystem** é um aplicativo desktop desenvolvido com Python e Flet, projetado para facilitar a emissão, gestão e organização de autorizações de compra de peças e serviços automotivos.

<img width="1913" height="980" alt="image" src="https://github.com/user-attachments/assets/f75e4236-468c-4d4e-8771-a853a28d3744" />

## ✨ Funcionalidades

- **Emissão de Autorizações**: Geração de documentos com numeração sequencial automática por mês/ano (ex: 0324-001).
- **Geração de PDF**: Criação automática de PDFs formatados com logotipo personalizado e detalhes do fornecedor, veículo e valores.
- **Gestão de Fornecedores**: Cadastro local de fornecedores.
- **Sincronização em Nuvem**: Integração bidirecional com o Google Sheets (Planilha) para backup e centralização de dados.
- **Modo Offline**: Utiliza SQLite local para permitir o uso sem internet, sincronizando os dados posteriormente.
- **Histórico**: Acesso rápido aos documentos PDF gerados anteriormente.

## 🛠️ Tecnologias Utilizadas

- **Linguagem**: [Python 3.10+](cite: 3)
- **Framework UI**: [Flet](cite: 3) (Flutter para Python)
- **Base de Dados**: SQLite
- **PDF**: FPDF2
- **Integração**: GSpread (Google Sheets API)
