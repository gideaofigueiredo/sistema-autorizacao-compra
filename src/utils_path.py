import sys
import os

def get_base_path():
    """Retorna o caminho raiz do projeto, funcionará ao rodar como script Python ou Exe compilado"""
    if getattr(sys, 'frozen', False):
        # Estamos rodando dentro do executável compilado (.exe)
        # sys.executable aponta para o caminho onde app.exe está.
        return os.path.dirname(sys.executable)
    else:
        # Estamos rodando como "python src/main.py".
        # Caminho raiz é um nível acima do "src".
        # __file__ está em src/utils_path.py, então dirname é src/, dirname do dirname é a raiz.
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def get_data_path():
    """Retorna o caminho para a pasta %LOCALAPPDATA%/AutCompraSystem/storage"""
    appdata = os.getenv('LOCALAPPDATA', os.path.expanduser('~'))
    path = os.path.join(appdata, "AutCompraSystem", "storage")
    os.makedirs(path, exist_ok=True)
    return path

def get_documents_path():
    """Retorna o caminho para a pasta Documentos/Autorizacoes do usuário"""
    docs = os.path.join(os.path.expanduser('~'), "Documents", "Autorizacoes")
    os.makedirs(docs, exist_ok=True)
    return docs
