"""Painel Streamlit do Indicador Operacional Mediatorie."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from processamento import (
    COLUNA_PRODUTO,
    COLUNAS_OBRIGATORIAS,
    consolidar_mensal,
    processar_base,
    ranking_produtos_fora,
    resumo_operacional,
)


BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "assets" / "logo_mediatorie.png"
ARQUIVO_PADRAO = BASE_DIR / "base_efetivacao.xlsx"

VERDE = "#86BC25"
VERDE_ESCURO = "#5F8E16"
VERMELHO = "#D64545"
GRAFITE = "#4B4F4D"
FUNDO = "#F5F7F2"


st.set_page_config(
    page_title="Indicador Operacional | Mediatorie",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    f"""
    <style>
        .stApp {{ background-color: {FUNDO}; }}
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #FFFFFF 0%, #F0F4EA 100%);
            border-right: 1px solid #DDE6D3;
        }}
        [data-testid="stMetric"] {{
            background-color: #FFFFFF;
            border: 1px solid #E2E8DC;
            border-left: 5px solid {VERDE};
            border-radius: 12px;
            padding: 15px 16px;
            box-shadow: 0 4px 14px rgba(75, 79, 77, 0.06);
        }}
        [data-testid="stMetricLabel"] {{ color: #667064; }}
        [data-testid="stMetricValue"] {{ color: {GRAFITE}; }}
        div[data-baseweb="tab-list"] {{ gap: 8px; }}
        button[data-baseweb="tab"] {{
            background-color: #FFFFFF;
            border-radius: 9px 9px 0 0;
            padding: 10px 18px;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: {VERDE_ESCURO};
            border-bottom-color: {VERDE};
        }}
        .mediatorie-header {{
            padding: 6px 0 18px 0;
        }}
        .mediatorie-kicker {{
            color: {VERDE_ESCURO};
            font-size: 0.85rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }}
        .mediatorie-title {{
            color: {GRAFITE};
            font-size: 2.05rem;
            font-weight: 750;
            line-height: 1.15;
            margin: 4px 0;
        }}
        .mediatorie-subtitle {{ color: #69736A; font-size: 1rem; }}
        .block-container {{ padding-top: 1.4rem; max-width: 1500px; }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def ler_excel_upload(conteudo: bytes) -> pd.DataFrame:
    return pd.read_excel(BytesIO(conteudo))


@st.cache_data(show_spinner=False)
def ler_excel_local(caminho: str, ultima_alteracao: float) -> pd.DataFrame:
    del ultima_alteracao  # participa da chave do cache
    return pd.read_excel(caminho)


def percentual_br(valor: float) -> str:
    return f"{valor:.2f}%".replace(".", ",")


def cabecalho() -> None:
    logo, texto = st.columns([1.1, 4.9])
    with logo:
        st.image(str(LOGO_PATH), width=230)
    with texto:
        st.markdown(
            """
            <div class="mediatorie-header">
                <div class="mediatorie-kicker">Gestão de operações</div>
                <div class="mediatorie-title">Indicador Operacional</div>
                <div class="mediatorie-subtitle">
                    Acompanhamento das efetivações de Saúde e Odonto.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def grafico_percentual(mensal: pd.DataFrame, meta: float, titulo: str) -> go.Figure:
    fig = go.Figure()

    fig.add_bar(
        x=mensal["Comp"],
        y=mensal["Percentual_Dentro"],
        name="Dentro do SLA",
        marker_color=VERDE,
        text=mensal["Percentual_Dentro"].map(percentual_br),
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="#FFFFFF", size=12),
        customdata=mensal[["Dentro", "Total"]],
        hovertemplate=(
            "<b>%{x}</b><br>Dentro: %{customdata[0]:,.0f}"
            "<br>Total: %{customdata[1]:,.0f}<br>Percentual: %{y:.2f}%<extra></extra>"
        ),
    )
    fig.add_bar(
        x=mensal["Comp"],
        y=mensal["Percentual_Fora"],
        name="Fora do SLA",
        marker_color=VERMELHO,
        text=mensal["Percentual_Fora"].map(percentual_br),
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="#FFFFFF", size=12),
        customdata=mensal[["Fora", "Total"]],
        hovertemplate=(
            "<b>%{x}</b><br>Fora: %{customdata[0]:,.0f}"
            "<br>Total: %{customdata[1]:,.0f}<br>Percentual: %{y:.2f}%<extra></extra>"
        ),
    )
    fig.add_hline(
        y=meta,
        line_color=GRAFITE,
        line_dash="dot",
        line_width=2,
        annotation_text=f"Meta {percentual_br(meta)}",
        annotation_position="top right",
    )
    fig.update_layout(
        title=dict(
            text=f"{titulo}<br><sup>Participação mensal das efetivações dentro e fora do SLA</sup>",
            x=0.01,
        ),
        barmode="stack",
        barnorm="percent",
        height=470,
        margin=dict(l=35, r=25, t=85, b=55),
        legend=dict(orientation="h", y=1.11, x=1, xanchor="right"),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(family="Arial", color=GRAFITE),
        hovermode="x unified",
        uniformtext_minsize=10,
        uniformtext_mode="hide",
    )
    fig.update_yaxes(
        title="Percentual",
        range=[0, 100],
        ticksuffix="%",
        dtick=20,
        gridcolor="#E8EDE4",
        zeroline=False,
    )
    fig.update_xaxes(title="Competência", showgrid=False)
    return fig


def grafico_quantidade(mensal: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for coluna, nome, cor in [
        ("Dentro", "Dentro do SLA", VERDE),
        ("Fora", "Fora do SLA", VERMELHO),
    ]:
        fig.add_bar(
            x=mensal["Comp"],
            y=mensal[coluna],
            name=nome,
            marker_color=cor,
            text=mensal[coluna],
            textposition="inside",
            textfont=dict(color="#FFFFFF"),
            hovertemplate=f"<b>%{{x}}</b><br>{nome}: %{{y:,.0f}}<extra></extra>",
        )

    fig.update_layout(
        title=dict(text="Volume mensal<br><sup>Quantidade de efetivações por situação</sup>", x=0.01),
        barmode="stack",
        height=410,
        margin=dict(l=30, r=20, t=80, b=50),
        legend=dict(orientation="h", y=1.12, x=1, xanchor="right"),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(family="Arial", color=GRAFITE),
        hovermode="x unified",
        uniformtext_minsize=9,
        uniformtext_mode="hide",
    )
    fig.update_yaxes(title="Efetivações", gridcolor="#E8EDE4", zeroline=False)
    fig.update_xaxes(title="Competência", showgrid=False)
    return fig


def grafico_ranking(dados: pd.DataFrame) -> go.Figure | None:
    ranking = ranking_produtos_fora(dados)
    ranking = ranking.loc[ranking["Fora"].gt(0)].copy()
    if ranking.empty:
        return None

    nomes = ranking[COLUNA_PRODUTO].map(
        lambda texto: texto if len(texto) <= 38 else texto[:35] + "..."
    )
    fig = go.Figure(
        go.Bar(
            x=ranking["Fora"],
            y=nomes,
            orientation="h",
            marker_color=VERMELHO,
            text=ranking["Fora"],
            textposition="outside",
            customdata=ranking[[COLUNA_PRODUTO, "Total", "Percentual_Fora"]],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>Fora: %{x:,.0f}"
                "<br>Total: %{customdata[1]:,.0f}"
                "<br>Percentual fora: %{customdata[2]:.2f}%<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title=dict(text="Atenção por produto<br><sup>Produtos com mais efetivações fora do SLA</sup>", x=0.01),
        height=410,
        margin=dict(l=20, r=45, t=80, b=50),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(family="Arial", color=GRAFITE),
        showlegend=False,
    )
    fig.update_xaxes(title="Quantidade fora", gridcolor="#E8EDE4", zeroline=False)
    fig.update_yaxes(title=None)
    return fig


def exibir_kpis(dados: pd.DataFrame) -> None:
    resumo = resumo_operacional(dados)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Efetivações", f"{resumo['total']:,}".replace(",", "."))
    col2.metric("Dentro do SLA", f"{resumo['dentro']:,}".replace(",", "."))
    col3.metric("Fora do SLA", f"{resumo['fora']:,}".replace(",", "."))
    col4.metric("Cumprimento do SLA", percentual_br(resumo["percentual_dentro"]))

    if resumo["sem_data"]:
        st.caption(
            f"⚠️ {resumo['sem_data']} registro(s) sem uma das datas obrigatórias "
            "não entram no cálculo do SLA."
        )


def exibir_secao(dados: pd.DataFrame, titulo: str, meta: float) -> None:
    if dados.empty:
        st.info(f"Não existem registros para {titulo.lower()} nos filtros selecionados.")
        return

    exibir_kpis(dados)
    mensal = consolidar_mensal(dados)
    if mensal.empty:
        st.warning("Não existem registros com datas válidas para montar os gráficos.")
        return

    st.plotly_chart(
        grafico_percentual(mensal, meta, f"Cumprimento do SLA — {titulo}"),
        use_container_width=True,
        config={"displaylogo": False, "locale": "pt-BR"},
    )

    coluna_grafico, coluna_ranking = st.columns([1.15, 0.85])
    with coluna_grafico:
        st.plotly_chart(
            grafico_quantidade(mensal),
            use_container_width=True,
            config={"displaylogo": False, "locale": "pt-BR"},
        )
    with coluna_ranking:
        ranking = grafico_ranking(dados)
        if ranking is None:
            st.success("Nenhum produto fora do SLA nos filtros selecionados.")
        else:
            st.plotly_chart(
                ranking,
                use_container_width=True,
                config={"displaylogo": False, "locale": "pt-BR"},
            )

    with st.expander("Ver consolidação mensal"):
        tabela = mensal.drop(columns="Periodo").rename(
            columns={
                "Percentual_Fora": "% Fora",
                "Percentual_Dentro": "% Dentro",
            }
        )
        st.dataframe(
            tabela,
            use_container_width=True,
            hide_index=True,
            column_config={
                "% Fora": st.column_config.NumberColumn(format="%.2f%%"),
                "% Dentro": st.column_config.NumberColumn(format="%.2f%%"),
            },
        )


cabecalho()

with st.sidebar:
    st.markdown("### Controles")
    arquivo = st.file_uploader("Base de efetivações", type=["xlsx"])
    sla_dias = st.number_input(
        "Prazo máximo do SLA (dias)", min_value=0, max_value=60, value=4, step=1
    )
    meta_sla = st.slider(
        "Meta de cumprimento (%)", min_value=0, max_value=100, value=95, step=1
    )
    st.caption("Dentro do SLA = diferença entre as duas datas menor ou igual ao prazo.")


try:
    if arquivo is not None:
        dados_brutos = ler_excel_upload(arquivo.getvalue())
        origem = arquivo.name
    elif ARQUIVO_PADRAO.exists():
        dados_brutos = ler_excel_local(
            str(ARQUIVO_PADRAO), ARQUIVO_PADRAO.stat().st_mtime
        )
        origem = ARQUIVO_PADRAO.name
    else:
        st.info(
            "Envie a planilha Excel no menu lateral para carregar o indicador. "
            "Se preferir carregamento automático, salve o arquivo como "
            "`base_efetivacao.xlsx` na pasta do projeto."
        )
        st.markdown("#### Colunas obrigatórias")
        st.code("\n".join(COLUNAS_OBRIGATORIAS), language=None)
        st.stop()

    dados = processar_base(dados_brutos, int(sla_dias))
except (KeyError, ValueError, OSError) as erro:
    st.error(f"Não foi possível processar a planilha: {erro}")
    st.stop()


with st.sidebar:
    st.divider()
    tipos_disponiveis = sorted(dados["Tipo"].dropna().unique().tolist())
    tipos = st.multiselect("Segmento", tipos_disponiveis, default=tipos_disponiveis)

    periodos_disponiveis = (
        dados.loc[dados["Periodo"].notna(), ["Periodo", "Competência"]]
        .drop_duplicates()
        .sort_values("Periodo")["Competência"]
        .tolist()
    )
    if dados["Competência"].eq("Sem competência").any():
        periodos_disponiveis.append("Sem competência")
    competencias = st.multiselect(
        "Competência", periodos_disponiveis, default=periodos_disponiveis
    )
    st.caption(f"Fonte: {origem}")


dados_filtrados = dados.loc[
    dados["Tipo"].isin(tipos) & dados["Competência"].isin(competencias)
].copy()

if dados_filtrados.empty:
    st.warning("Nenhum registro corresponde aos filtros selecionados.")
    st.stop()


aba_geral, aba_saude, aba_odonto, aba_base = st.tabs(
    ["Visão geral", "Saúde", "Odonto", "Base tratada"]
)

with aba_geral:
    exibir_secao(dados_filtrados, "Visão geral", float(meta_sla))

with aba_saude:
    exibir_secao(
        dados_filtrados.loc[dados_filtrados["Tipo"].eq("Saúde")],
        "Saúde",
        float(meta_sla),
    )

with aba_odonto:
    exibir_secao(
        dados_filtrados.loc[dados_filtrados["Tipo"].eq("Odonto")],
        "Odonto",
        float(meta_sla),
    )

with aba_base:
    st.subheader("Base tratada")
    st.caption("Use os filtros da barra lateral para restringir os registros.")
    colunas_exibir = [
        coluna
        for coluna in [
            "Competência",
            "Tipo",
            COLUNA_PRODUTO,
            "Vigência Inicio",
            "Data do envio informativo",
            "Dias para efetivação",
            "Prazo",
        ]
        if coluna in dados_filtrados.columns
    ]
    st.dataframe(
        dados_filtrados[colunas_exibir],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Vigência Inicio": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "Data do envio informativo": st.column_config.DateColumn(format="DD/MM/YYYY"),
        },
    )
