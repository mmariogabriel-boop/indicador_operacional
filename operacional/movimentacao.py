# %%
import pandas as pd
import numpy as np
import datetime as dt

# %%
df = pd.read_excel('Movimentações (4).xlsx')
df

# %%
# 1. Garantir que as colunas estão lidas estritamente como data/datetime
df['Dt.Modificação'] = pd.to_datetime(df['Dt.Modificação'], errors='coerce')
df['Dt.Entrada SAP'] = pd.to_datetime(df['Dt.Entrada SAP'], errors='coerce')

# 2. Função que calcula os dias úteis linha por linha, tratando os vazios
def calcular_dias_uteis(row):
    # Se qualquer uma das datas for nula (NaT/NaN), retorna NaN
    if pd.isnull(row['Dt.Modificação']) or pd.isnull(row['Dt.Entrada SAP']):
        return np.nan
    
    # Faz o cálculo seguro apenas com datas válidas
    return np.busday_count(
        str(row['Dt.Modificação'].date()), 
        str(row['Dt.Entrada SAP'].date())
    )

# 3. Aplica a função no DataFrame
df['dias_uteis'] = df.apply(calcular_dias_uteis, axis=1)

# %%
df['dias_uteis'] = df['dias_uteis'].astype('Int64')  # Converte para Int64, mantendo NaN como nulo

# %%
df

# %%
condicoes = [df['dias_uteis']<=4, df['dias_uteis']>4]
resultado = ['Dentro do prazo', 'Fora do prazo']

df['Indicador'] = np.select(
    [condicao.fillna(False).to_numpy(dtype=bool) for condicao in condicoes],
    resultado,
    default='Verificar'
)

# %%
df['Competencia'] = df['Dt.Modificação'].dt.to_period('M').astype(str)

# %%
df

# %%
dentro_do_prazo = df[df['Indicador']=='Dentro do prazo']
fora_do_prazo = df[df['Indicador']=='Fora do prazo']

# %%
dentro_do_prazo = dentro_do_prazo.groupby('Competencia').size().reset_index(name='Quantidade')
fora_do_prazo = fora_do_prazo.groupby('Competencia').size().reset_index(name='Quantidade')


# %%
indicador = pd.merge(dentro_do_prazo, fora_do_prazo, on='Competencia', how='outer', suffixes=('_Dentro', '_Fora')).fillna(0)
indicador['total'] = indicador['Quantidade_Dentro'] + indicador['Quantidade_Fora']

# %%
import matplotlib.pyplot as plt
import numpy as np

comp = indicador['Competencia'].astype(str)
dentro = indicador['Quantidade_Dentro'].astype(int)
fora = indicador['Quantidade_Fora'].astype(int)

width = 0.60

fig, ax = plt.subplots(figsize=(12, 6))

# Dentro do prazo
barra_dentro = ax.bar(
    comp,
    dentro,
    width,
    label='Dentro do prazo',
    color='green'
)

# Fora do prazo
barra_fora = ax.bar(
    comp,
    fora,
    width,
    bottom=dentro,
    label='Fora do prazo',
    color='red'
)

# Rótulos da parte verde
ax.bar_label(
    barra_dentro,
    labels=[f'{valor}' if valor > 0 else '' for valor in dentro],
    label_type='center',
    color='white',
    fontsize=10,
    fontweight='bold'
)

# Rótulos da parte vermelha
ax.bar_label(
    barra_fora,
    labels=[f'{valor}' if valor > 0 else '' for valor in fora],
    label_type='center',
    color='white',
    fontsize=10,
    fontweight='bold'
)

ax.set_title(
    'Indicador de Movimentações por Competência',
    fontsize=14,
    fontweight='bold'
)

ax.set_xlabel('Competência')
ax.set_ylabel('Quantidade')

ax.legend()

plt.xticks(rotation=45)

plt.tight_layout()
plt.show()


