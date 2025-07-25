@echo off
title aplicativo treinador de pronuncia pika de cachorro( esse é forte!)

:: Defina aqui o caminho completo para a pasta do seu projeto. Mantenha as aspas!
set "project_path=C:\CAMINHO\COMPLETO\PARA\SUA\PASTA"

echo Acessando a pasta do projeto...
cd /d "%project_path%"

:: Verifica se a instalacao ja foi feita (procurando pelo arquivo .installed)
if not exist ".installed" (
    echo.
    echo ==========================================================
    echo PRIMEIRA EXECUCAO DETECTADA. INSTALANDO DEPENDENCIAS...
    echo ==========================================================
    echo.
    
    :: Instala os pacotes do requirements.txt
    pip install -r requirements.txt
    
    echo.
    echo ==========================================================
    echo   DEPENDENCIAS INSTALADAS COM SUCESSO!
    echo ==========================================================
    echo.
    
    :: Cria o arquivo marcador para que a instalacao nao ocorra novamente
    echo installed > .installed
    
    pause
)

echo.
echo Iniciando o servidor...
echo Para parar o servidor, feche esta janela.
echo.

:: Executa o aplicativo Python
python3 webApp.py

echo.
echo O servidor foi encerrado.
pause