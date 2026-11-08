from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR.parent / "dados" / "ouro" / "dataset_completo.csv"
SQL_PATH = BASE_DIR / "commands.sql"


def sql_text(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def gerar_sql_regioes_paises() -> list[str]:
    dados = pd.read_csv(CSV_PATH, usecols=["regiao", "pais"])
    regioes = dados.groupby("regiao").size().index.tolist()
    paises = (
        dados.groupby(["regiao", "pais"])
        .size()
        .reset_index()[["regiao", "pais"]]
    )
    id_regiao = {nome: i for i, nome in enumerate(regioes, start=1)}

    linhas_sql = ["BEGIN TRANSACTION;", ""]
    linhas_sql.extend(
        f"INSERT INTO regiao (id_regiao, nome) VALUES ({i}, {sql_text(nome)});"
        for i, nome in enumerate(regioes, start=1)
    )
    linhas_sql.append("")
    linhas_sql.extend(
        "INSERT INTO pais (id_pais, nome, id_regiao) "
        f"VALUES ({i}, {sql_text(pais)}, {id_regiao[regiao]});"
        for i, (regiao, pais) in enumerate(
            paises.itertuples(index=False, name=None), start=1
        )
    )
    linhas_sql.extend(["", "COMMIT;"])
    return linhas_sql


def gerar_sql_clientes() -> list[str]:
    colunas = ["id", "nome", "idade", "genero", "escolaridade", "cidade"]
    clientes = pd.read_csv(CSV_PATH, usecols=colunas).drop_duplicates()
    linhas_sql = ["BEGIN TRANSACTION;", ""]

    for id_cliente, nome, idade, genero, escolaridade, cidade in clientes.itertuples(
        index=False, name=None
    ):
        linhas_sql.append(
            "INSERT INTO cliente "
            "(id_cliente, nome, idade, genero, escolaridade, cidade) "
            f"VALUES ({int(id_cliente)}, {sql_text(nome)}, {int(idade)}, "
            f"{sql_text(genero)}, {sql_text(escolaridade)}, {sql_text(cidade)});"
        )

    linhas_sql.extend(["", "COMMIT;"])
    return linhas_sql


def gerar_sql_carros() -> list[str]:
    carros = (
        pd.read_csv(CSV_PATH, usecols=["modelo", "ano"])
        .groupby(["modelo", "ano"])
        .size()
        .reset_index()[["modelo", "ano"]]
    )
    linhas_sql = ["BEGIN TRANSACTION;", ""]

    for id_carro, (modelo, ano) in enumerate(
        carros.itertuples(index=False, name=None), start=1
    ):
        linhas_sql.append(
            "INSERT INTO carro (id_carro, ano_carro, modelo_carro) "
            f"VALUES ({id_carro}, {int(ano)}, {sql_text(modelo)});"
        )

    linhas_sql.extend(["", "COMMIT;"])
    return linhas_sql


def gerar_sql_preco_carro() -> list[str]:
    carros = (
        pd.read_csv(CSV_PATH, usecols=["modelo", "ano"])
        .groupby(["modelo", "ano"])
        .size()
        .reset_index()[["modelo", "ano"]]
    )
    id_carro = {
        (modelo, ano): i
        for i, (modelo, ano) in enumerate(
            carros.itertuples(index=False, name=None), start=1
        )
    }

    paises = (
        pd.read_csv(CSV_PATH, usecols=["regiao", "pais"])
        .groupby(["regiao", "pais"])
        .size()
        .reset_index()["pais"]
    )
    id_pais = {pais: i for i, pais in enumerate(paises, start=1)}

    precos = (
        pd.read_csv(CSV_PATH, usecols=["ano", "pais", "modelo", "preco_medio"])
        .groupby(["ano", "pais", "modelo"])["preco_medio"]
        .mean()
        .reset_index()
    )
    linhas_sql = ["BEGIN TRANSACTION;", ""]

    for ano, pais, modelo, preco_medio in precos.itertuples(
        index=False, name=None
    ):
        linhas_sql.append(
            "INSERT INTO preco_carro "
            "(id_carro, id_pais, preco_carro, ano_referencia) "
            f"VALUES ({id_carro[(modelo, ano)]}, {id_pais[pais]}, "
            f"{round(float(preco_medio), 2)}, {int(ano)});"
        )

    linhas_sql.extend(["", "COMMIT;"])
    return linhas_sql


def gerar_sql_pedidos_e_itens() -> list[str]:
    carros = (
        pd.read_csv(CSV_PATH, usecols=["modelo", "ano"])
        .groupby(["modelo", "ano"])
        .size()
        .reset_index()[["modelo", "ano"]]
    )
    id_carro = {
        (modelo, ano): i
        for i, (modelo, ano) in enumerate(
            carros.itertuples(index=False, name=None), start=1
        )
    }

    paises = (
        pd.read_csv(CSV_PATH, usecols=["regiao", "pais"])
        .groupby(["regiao", "pais"])
        .size()
        .reset_index()["pais"]
    )
    id_pais = {pais: i for i, pais in enumerate(paises, start=1)}

    preco_carro = {
        (ano, pais, modelo): round(float(valor), 2)
        for ano, pais, modelo, valor in (
            pd.read_csv(CSV_PATH, usecols=["ano", "pais", "modelo", "preco_medio"])
            .groupby(["ano", "pais", "modelo"])["preco_medio"]
            .mean()
            .reset_index()
            .itertuples(index=False, name=None)
        )
    }

    colunas_pedido = [
        "id_pedido",
        "id_cliente",
        "data_pedido",
        "ano",
        "pais",
        "modelo",
        "desconto",
        "avaliacao_cliente",
    ]
    pedidos = pd.read_csv(CSV_PATH, usecols=colunas_pedido)[colunas_pedido]
    linhas_sql = ["BEGIN TRANSACTION;", ""]

    for id_item_pedido, linha in enumerate(
        pedidos.itertuples(index=False, name=None), start=1
    ):
        (
            id_pedido,
            id_cliente,
            data_pedido,
            ano,
            pais,
            modelo,
            desconto,
            avaliacao,
        ) = linha
        preco_item = preco_carro[(ano, pais, modelo)]
        total_pedido = round(preco_item - float(desconto), 2)
        avaliacao_sql = "NULL" if pd.isna(avaliacao) else f"{float(avaliacao)}"

        linhas_sql.append(
            "INSERT INTO pedido "
            "(id_pedido, id_cliente, data_pedido, id_pais, total_pedido, "
            "avaliacao_cliente) "
            f"VALUES ({sql_text(id_pedido)}, {int(id_cliente)}, "
            f"{sql_text(data_pedido)}, {id_pais[pais]}, {total_pedido}, "
            f"{avaliacao_sql});"
        )
        linhas_sql.append(
            "INSERT INTO item_pedido "
            "(id_item_pedido, id_pedido, id_carro, quantidade, preco_item, "
            "desconto) "
            f"VALUES ({id_item_pedido}, {sql_text(id_pedido)}, "
            f"{id_carro[(modelo, ano)]}, 1, {preco_item}, "
            f"{float(desconto)});"
        )

    linhas_sql.extend(["", "COMMIT;"])
    return linhas_sql


def main() -> None:
    sql_regioes_paises = gerar_sql_regioes_paises()
    sql_clientes = gerar_sql_clientes()
    sql_carros = gerar_sql_carros()
    sql_preco_carro = gerar_sql_preco_carro()
    sql_pedidos = gerar_sql_pedidos_e_itens()
    linhas_sql = (
        sql_regioes_paises
        + [""]
        + sql_clientes
        + [""]
        + sql_carros
        + [""]
        + sql_preco_carro
        + [""]
        + sql_pedidos
        + [""]
    )

    SQL_PATH.write_text("\n".join(linhas_sql), encoding="utf-8")
    print("Script executado com sucesso.")


if __name__ == "__main__":
    main()
