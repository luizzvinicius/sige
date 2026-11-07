"""Gera os inserts de regiao e pais a partir do dataset ouro."""

from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR.parent / "dados" / "ouro" / "dataset_completo.csv"
SQL_PATH = BASE_DIR / "commands.sql"


def sql_text(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> None:
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
    linhas_sql.extend(["", "COMMIT;", ""])
    SQL_PATH.write_text("\n".join(linhas_sql), encoding="utf-8")
    print(f"Gerado {SQL_PATH}: {len(regioes)} regioes, {len(paises)} paises.")


if __name__ == "__main__":
    main()
