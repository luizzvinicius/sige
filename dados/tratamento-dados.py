import pandas as pd
import numpy as np

clientes_pd = pd.read_csv('dados/bronze/clientes.csv')
carros_vendas_pd = pd.read_csv('dados/bronze/carros_vendas.csv')

colunas_para_remover = ['Department', 'Job_Title', 'Experience_Years', 'Salary']
colunas_existentes_para_remover = [col for col in colunas_para_remover if col in clientes_pd.columns]
clientes_pd = clientes_pd.drop(columns=colunas_existentes_para_remover)

mapeamento_colunas = {
    'Employee_ID': 'id',
    'Name': 'nome',
    'Age': 'idade',
    'Gender': 'genero',
    'Education_Level': 'escolaridade',
    'Location': 'cidade',
}

clientes_pd = clientes_pd.rename(columns=mapeamento_colunas)

mapa_genero = {
    'Male': 'Masculino',
    'Female': 'Feminino'
}

mapa_escolaridade = {
    'Bachelor': 'Bacharelado',
    'Master': 'Mestrado',
    'PhD': 'Doutorado'
}

if 'genero' in clientes_pd.columns:
    clientes_pd['genero'] = clientes_pd['genero'].map(mapa_genero).fillna(clientes_pd['genero'])

if 'escolaridade' in clientes_pd.columns:
    clientes_pd['escolaridade'] = clientes_pd['escolaridade'].map(mapa_escolaridade).fillna(clientes_pd['escolaridade'])

print(clientes_pd.head())

colunas_remover = ['return_rate', 'average_delivery_days']
colunas_existentes = [col for col in colunas_remover if col in carros_vendas_pd.columns]
carros_vendas_pd = carros_vendas_pd.drop(columns=colunas_existentes)

mapeamento_colunas = {
    'order_id': 'id_pedido',
    'order_date': 'data_pedido',
    'year': 'ano',
    'region': 'regiao',
    'country': 'pais',
    'vehicle_model': 'modelo',
    'units_sold': 'unidades_vendidas',
    'average_vehicle_price_usd': 'preco_medio',
    'discount_usd': 'desconto',
    'net_revenue_usd': 'receita_liquida',
    'ending_inventory_units': 'estoque_final',
    'customer_rating': 'avaliacao_cliente'
}
carros_vendas_pd = carros_vendas_pd.rename(columns=mapeamento_colunas)

mapa_regioes = {
    'North America': 'América do Norte',
    'Europe': 'Europa',
    'Asia-Pacific': 'Ásia-Pacífico',
    'Latin America': 'América Latina',
    'Middle East': 'Oriente Médio',
}
if 'regiao' in carros_vendas_pd.columns:
    carros_vendas_pd['regiao'] = carros_vendas_pd['regiao'].map(mapa_regioes).fillna(carros_vendas_pd['regiao'])

mapa_paises = {
    'United States': 'Estados Unidos',
    'Canada': 'Canadá',
    'Mexico': 'México',
    'United Kingdom': 'Reino Unido',
    'Germany': 'Alemanha',
    'France': 'França',
    'Norway': 'Noruega',
    'China': 'China',
    'Japan': 'Japão',
    'South Korea': 'Coreia do Sul',
    'Australia': 'Austrália',
    'Brazil': 'Brasil',
    'Colombia': 'Colômbia',
    'Chile': 'Chile',
    'Israel': 'Israel',
    'Singapore': 'Cingapura',
    'Netherlands': 'Países Baixos',
    'Saudi Arabia': 'Arábia Saudita',
    'United Arab Emirates': 'Emirados Árabes Unidos'
}
if 'pais' in carros_vendas_pd.columns:
    carros_vendas_pd['pais'] = carros_vendas_pd['pais'].map(mapa_paises).fillna(carros_vendas_pd['pais'])

print(clientes_pd.head())
print(carros_vendas_pd.head())

ids_clientes = clientes_pd['id'].values
novos_ids = list(ids_clientes)

diferenca = len(carros_vendas_pd) - len(clientes_pd)
if diferenca > 0:
    rng = np.random.default_rng(seed=42)
    ids_aleatorios = rng.choice(ids_clientes, size=diferenca, replace=True)
    novos_ids.extend(ids_aleatorios)

carros_vendas_pd['id_cliente'] = novos_ids

dataset_completo = pd.merge(carros_vendas_pd, clientes_pd, left_on='id_cliente', right_on='id', how='left')

dataset_completo.to_csv('dados/ouro/dataset_completoo.csv', index=False)
