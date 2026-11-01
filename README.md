# dashboard-python

Dashboard de vendas em Python: **Streamlit** (frontend) + **FastAPI** (backend) + **SQLite** (banco).

## Estrutura

```
dashboard-python/
├── api/
│   └── main.py          # API FastAPI (healthcheck, produtos, vendas)
├── dashboard/
│   └── app.py           # Dashboard Streamlit (gráfico de barras por data)
├── database/
│   ├── app.db           # Banco SQLite (gerado automaticamente)
│   ├── connection.py    # Conexão e inicialização do banco
│   └── init.sql         # Migration inicial com a carga de dados
├── .gitignore
├── README.md
└── requirements.txt
```

## 1. Criar o ambiente virtual

**Windows (PowerShell):**

```powershell
cd dashboard-python
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> Se aparecer erro de política de execução, rode uma vez:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

**Linux / macOS:**

```bash
cd dashboard-python
python3 -m venv .venv
source .venv/bin/activate
```

## 2. Instalar as dependências

```powershell
pip install -r requirements.txt
```

## 3. Criar e popular o banco

O banco `database/app.db` é criado automaticamente na primeira subida da API.
Para criar/recriar manualmente a partir da migration:

```powershell
python -m database.connection
```

## 4. Subir a API

Execute a partir da raiz do projeto (`dashboard-python`):

```powershell
uvicorn api.main:app --reload --port 8000
```

Documentação interativa: http://localhost:8000/docs

## 5. Subir o dashboard

Em outro terminal, com o ambiente virtual ativado:

```powershell
streamlit run dashboard/app.py
```

Dashboard: http://localhost:8501

Se a API estiver em outro endereço, defina a variável de ambiente antes de rodar:

```powershell
$env:API_URL = "http://localhost:8000"
```

## Endpoints

| Método | Rota              | Descrição                                              |
| ------ | ----------------- | ------------------------------------------------------ |
| GET    | `/health`         | Healthcheck da API e do banco                          |
| GET    | `/produtos/{id}`  | Busca um produto por id                                |
| GET    | `/vendas`         | Total vendido por dia (`data_inicio` e `data_fim` opcionais) |

## Modelo de dados

- `produto` — `id`, `nome`, `valor`
- `venda` — `id_venda`, `data_venda`, `valor_total`
- `item_venda` — `id`, `id_venda`, `id_produto`, `quantidade`, `valor_unitario` (resolve a relação **N:N** entre venda e produto)

As datas de carga em `database/init.sql` são relativas ao dia atual, então o filtro
padrão do dashboard (últimos 30 dias) sempre retorna dados.
