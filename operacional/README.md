# Indicador Operacional Mediatorie

Painel Streamlit para acompanhar as efetivações de Saúde e Odonto, com indicadores de cumprimento do SLA, gráficos mensais em quantidade e percentual e ranking dos produtos fora do prazo.

## Como executar no Windows

Abra o PowerShell na pasta do projeto e execute:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

O navegador abrirá o painel. Envie a base pelo menu lateral.

Se quiser que a base abra automaticamente, coloque o Excel na pasta do projeto com o nome:

```text
base_efetivacao.xlsx
```

## Colunas obrigatórias do Excel

- `Data do envio informativo`
- `Vigência Inicio`
- `Descrição do produto`

## Regras usadas

- O prazo padrão é de 4 dias e pode ser alterado no menu lateral.
- `Dentro`: dias entre a vigência e o envio menores ou iguais ao SLA.
- `Fora`: dias entre a vigência e o envio maiores que o SLA.
- `Sem data`: uma das duas datas está vazia; o registro não entra no cálculo percentual.
- Os produtos da lista odontológica dos códigos anteriores são classificados como `Odonto`; os demais são classificados como `Saúde`.

## Arquivos principais

- `app.py`: tela, filtros, KPIs e gráficos.
- `processamento.py`: regras de classificação e consolidação.
- `assets/logo_mediatorie.png`: identidade visual usada no cabeçalho.
