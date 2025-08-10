#!/bin/bash

# Título exibido no terminal
echo "Aplicativo Treinador de Pronúncia Pika de Cachorro (esse é forte!)"
echo

# Caminho completo para a pasta do projeto — EDITE AQUI:
project_path="/Volumes/Files/apps/InglesFrances-2.0"

echo "Acessando a pasta do projeto..."
cd "$project_path" || { echo "Erro: pasta não encontrada!"; exit 1; }

# Verifica se o arquivo .installed existe
if [ ! -f ".installed" ]; then
    echo
    echo "=========================================================="
    echo " PRIMEIRA EXECUÇÃO DETECTADA. INSTALANDO DEPENDÊNCIAS..."
    echo "=========================================================="
    echo

    # Instala os pacotes do requirements.txt
    pip3 install -r requirements.txt

    echo
    echo "=========================================================="
    echo "  DEPENDÊNCIAS INSTALADAS COM SUCESSO!"
    echo "=========================================================="
    echo

    # Cria o arquivo marcador para não instalar de novo
    echo "installed" > .installed

    read -p "Pressione ENTER para continuar..."
fi

echo
echo "Iniciando o servidor..."
echo "Para parar o servidor, pressione Ctrl + C."
echo

# Executa o app Python
python3 webApp.py

echo
echo "O servidor foi encerrado."
read -p "Pressione ENTER para sair..."
