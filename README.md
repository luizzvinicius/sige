# dashboard-python

Dashboard de vendas em Python: **Streamlit** (frontend) + **FastAPI** (backend) + **SQLite** (banco).

## Estrutura

```
dashboard-python/
├── api/
│   ├── main.py          # API FastAPI (healthcheck e /api/dados)
│   └── dados.py         # CSV com a camada bronze e ouro e script de tratamento
├── dashboard/
│   ├── app.py           # Dashboard
│   └── data.py          # Camada de acesso a dados do dashboard
├── database/
│   ├── app.db           # Banco SQLite (gerado automaticamente)
│   ├── connection.py    # Conexão e inicialização do banco
│   ├── csv-to-sql.py
│   └── schema.sql       # Migration inicial com a carga de dados
├── .gitignore
├── executar.bat         # Script de inicialização do projeto
├── README.md
└── requirements.txt
```

## 1. Criar o ambiente virtual

### 1.1 Inicializar projeto completo

Execute a partir da raiz do projeto (`dashboard-python`):  
Não precisa seguir com os outros passos de inicialização

```bash
./executar.bat
```

### 1.2 Executar por etapas

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

## 4. Inicializar a API

Execute a partir da raiz do projeto (`dashboard-python`):

```powershell
uvicorn api.main:app --reload --port 8000
```

Documentação interativa: http://localhost:8000/docs

## 5. Inicializar o dashboard

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

| Método | Rota         | Descrição                                                    |
| ------ | ------------ | ------------------------------------------------------------ |
| GET    | `/health`    | Healthcheck da API e do banco                                 |
| GET    | `/api/dados` | Dataset de vendas em JSON, com os filtros do dashboard        |

### `GET /api/dados`

Todos os filtros são opcionais; sem eles, a API retorna o dataset completo.
Filtros de lista podem ser repetidos na query string (ex.: `?regiao=Europa&regiao=Ásia-Pacífico`).

| Parâmetro         | Descrição                                                        |
| ----------------- | ---------------------------------------------------------------- |
| `data_inicio`     | Início do período de análise (`AAAA-MM-DD`)                      |
| `data_fim`        | Fim do período de análise (`AAAA-MM-DD`)                         |
| `regiao`          | Região (repetível)                                               |
| `pais`            | País (repetível); precisa pertencer à região informada           |
| `modelo`          | Modelo do veículo (repetível)                                    |
| `ano`             | Ano do modelo do veículo (repetível)                             |
| `genero`          | Gênero do cliente (repetível)                                    |
| `escolaridade`    | Escolaridade do cliente (repetível)                              |
| `idade_min`       | Idade mínima do cliente                                          |
| `idade_max`       | Idade máxima do cliente                                          |

Cada parâmetro é validado.  
Valores inválidos retornam `422` com a mensagem de erro.

Exemplo de resposta:

```json
{
  "total_registros": 12000,
  "dados": [
    {
      "id_pedido": "TSLA-000682",
      "data_pedido": "2022-01-01",
      "total_pedido": 80885.92,
      "avaliacao_cliente": 3.65,
      "regiao": "América Latina",
      "pais": "Colômbia",
      "cliente": "Paula Douglas",
      "idade": 25,
      "genero": "Feminino",
      "escolaridade": "Mestrado",
      "cidade": "Seattle",
      "modelo": "Model S",
      "ano_modelo": 2022,
      "quantidade": 1,
      "preco_item": 82096.38,
      "desconto": 1210.46,
      "faturamento": 82096.38,
      "receita_liquida": 80885.92
    }
  ]
}
```