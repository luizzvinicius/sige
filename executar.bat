@echo off
setlocal
cd /d "%~dp0"

set "VENV_PY=%~dp0.venv\Scripts\python.exe"

echo ============================================
echo   SIGE - Inicializacao completa do projeto
echo ============================================
echo.

REM ---------- Etapa 1: dependencias ----------
set "BASE_PY="
where python >nul 2>nul
if not errorlevel 1 set "BASE_PY=python"
if not defined BASE_PY (
    where py >nul 2>nul
    if not errorlevel 1 set "BASE_PY=py -3"
)
if not defined BASE_PY (
    echo [ERRO] Python nao encontrado no PATH. Instale o Python 3 e tente novamente.
    pause
    exit /b 1
)

if exist "%VENV_PY%" (
    echo [1/6] Ambiente virtual .venv encontrado.
) else (
    echo [1/6] Criando ambiente virtual .venv ...
    %BASE_PY% -m venv .venv
    if errorlevel 1 (
        echo [ERRO] Falha ao criar o ambiente virtual.
        pause
        exit /b 1
    )
)

echo [2/6] Instalando dependencias (requirements.txt) ...
"%VENV_PY%" -m pip install --upgrade pip
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERRO] Falha ao instalar as dependencias.
    pause
    exit /b 1
)

REM ---------- Etapa 2: inicializacao do sistema ----------
echo [3/6] Tratando os dados (dados\tratamento-dados.py) ...
"%VENV_PY%" "dados\tratamento-dados.py"
if errorlevel 1 (
    echo [ERRO] Falha na etapa de tratamento dos dados.
    pause
    exit /b 1
)

echo [4/6] Gerando database\commands.sql (database\csv-to-sql.py) ...
if exist "database\commands.sql" del /q "database\commands.sql"
if exist "database\app.db" del /q "database\app.db"
"%VENV_PY%" "database\csv-to-sql.py"
if errorlevel 1 (
    echo [ERRO] Falha ao gerar o script de carga do banco.
    pause
    exit /b 1
)

echo [5/6] Criando o banco SQLite (database\connection.py) ...
"%VENV_PY%" -m database.connection
if errorlevel 1 (
    echo [ERRO] Falha ao criar o banco de dados.
    pause
    exit /b 1
)

REM ---------- Etapa 3: aplicacoes ----------
echo [6/6] Iniciando backend (FastAPI) e frontend (Streamlit) ...
start "SIGE - API (FastAPI)" cmd /k ""%VENV_PY%" -m uvicorn api.main:app --reload --port 8000"
timeout /t 3 /nobreak >nul
start "SIGE - Dashboard (Streamlit)" cmd /k ""%VENV_PY%" -m streamlit run dashboard\app.py"

echo.
echo ============================================
echo  Backend (docs) : http://localhost:8000/docs
echo  Dashboard       : http://localhost:8501
echo ============================================
echo Feche as janelas abertas para encerrar os servicos.
pause
