"""Regras de tratamento do Indicador Operacional Mediatorie."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd


COLUNA_ENVIO = "Data do envio informativo"
COLUNA_VIGENCIA = "Vigência Inicio"
COLUNA_PRODUTO = "Descrição do produto"

COLUNAS_OBRIGATORIAS = [
    COLUNA_ENVIO,
    COLUNA_VIGENCIA,
    COLUNA_PRODUTO,
]


PRODUTOS_ODONTO = {
    "MASTER I SINDILIMPE SAMP ODONTO",
    "Essencial Unimed Odonto Até 99 vidas",
    "PLENO UNIMED ODONTO",
    "Pleno Unimed Odonto Até 29 vidas",
    "Plus Doc Unimed Odonto Acima 100 vidas",
    "BÁSICO ROL EMP SAMP ODONTO",
    "4971 - ESSENCIAL II DOC EMP SEMPRE",
    "MASTER I ROL + DOC + PLACA SAMP ODONTO",
    "MASTER I ROL + DOC SAMP ODONTO",
    "4658 - ESSENCIAL II EMP SEMPRE",
    "ESSENCIAL UNIMED ODONTO",
    "ESSENCIAL PLUS DOC UNIMED ODONTO",
    "ESSENCIAL PLUS UNIMED ODONTO",
    "MASTER I DOC SINTRAFARMA SAMP ODONTO",
    "ESSENCIAL FR UNIMED ODONTO",
    "Executivo Odonto AESP",
    "4658 - ESSENCIAL II EMP SEMPRE GRUPO 01",
    "Odonto - Essencial Emp Odonto CB",
    "Plus Doc Unimed Odonto Até 29 vidas",
    "Plus Unimed Odonto Até 99 vidas",
    "4658 - ESSENCIAL II EMP 100 DESCONTO",
    "MASTER I SINDUSCON SAMP ODONTO",
    "Pleno Adesao Unimed Odonto",
    "4658 - ESSENCIAL II EMP SEMPRE ATE 29",
    "Plus Unimed Odonto Acima 100 vidas",
    "4971 - ESSENCIAL II DOC EMP SEMPRE FARMA",
    "MASTER I DOC SINTRAMASSAS SAMP ODONTO",
    "MASTER I SINTRAMASSAS SAMP ODONTO",
    "Essencial Plus Doc Adesao Unimed Odonto",
    "Plus Doc Unimed Odonto 30 a 99 vidas",
    "Pleno Unimed Odonto 30 a 99 vidas",
    "Essencial Adesao Unimed Odonto",
    "3 - STANDARD - AESP ODONTO",
    "MASTER I SAMP ODONTO 30 OU + VIDAS",
    "Essencial Plus Adesao Unimed Odonto",
}


def _normalizar_texto(valor: object) -> str:
    """Padroniza caixa e espaços sem remover acentos."""

    if pd.isna(valor):
        return ""
    return re.sub(r"\s+", " ", str(valor).strip()).upper()


PRODUTOS_ODONTO_NORMALIZADOS = {
    _normalizar_texto(produto) for produto in PRODUTOS_ODONTO
}


def validar_colunas(dataframe: pd.DataFrame) -> None:
    colunas_ausentes = [
        coluna for coluna in COLUNAS_OBRIGATORIAS if coluna not in dataframe.columns
    ]
    if colunas_ausentes:
        raise KeyError(
            "A planilha não possui as colunas obrigatórias: "
            + ", ".join(colunas_ausentes)
        )


def processar_base(dataframe: pd.DataFrame, sla_dias: int = 4) -> pd.DataFrame:
    """Classifica cada registro como Dentro, Fora ou Sem data."""

    validar_colunas(dataframe)
    dados = dataframe.copy()

    dados[COLUNA_ENVIO] = pd.to_datetime(
        dados[COLUNA_ENVIO], errors="coerce", dayfirst=True
    )
    dados[COLUNA_VIGENCIA] = pd.to_datetime(
        dados[COLUNA_VIGENCIA], errors="coerce", dayfirst=True
    )

    produto_normalizado = dados[COLUNA_PRODUTO].map(_normalizar_texto)
    dados["Tipo"] = np.where(
        produto_normalizado.isin(PRODUTOS_ODONTO_NORMALIZADOS),
        "Odonto",
        "Saúde",
    )

    dados["Dias para efetivação"] = (
        dados[COLUNA_ENVIO] - dados[COLUNA_VIGENCIA]
    ).dt.days

    sem_data = dados[[COLUNA_ENVIO, COLUNA_VIGENCIA]].isna().any(axis=1)
    dentro = dados["Dias para efetivação"].le(sla_dias)
    dados["Prazo"] = np.select(
        [sem_data, dentro],
        ["Sem data", "Dentro"],
        default="Fora",
    )

    dados["Periodo"] = dados[COLUNA_VIGENCIA].dt.to_period("M")
    dados["Competência"] = dados[COLUNA_VIGENCIA].dt.strftime("%m/%Y")
    dados["Competência"] = dados["Competência"].fillna("Sem competência")

    return dados


def consolidar_mensal(dados: pd.DataFrame) -> pd.DataFrame:
    """Cria a tabela mensal usada pelos dois gráficos."""

    validos = dados.loc[
        dados["Prazo"].isin(["Dentro", "Fora"]) & dados["Periodo"].notna()
    ].copy()

    if validos.empty:
        return pd.DataFrame(
            columns=[
                "Periodo",
                "Comp",
                "Fora",
                "Dentro",
                "Total",
                "Percentual_Fora",
                "Percentual_Dentro",
            ]
        )

    mensal = (
        validos.groupby(["Periodo", "Prazo"], observed=True)
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    for coluna in ["Dentro", "Fora"]:
        if coluna not in mensal.columns:
            mensal[coluna] = 0

    mensal["Total"] = mensal["Dentro"] + mensal["Fora"]
    mensal["Percentual_Dentro"] = (
        mensal["Dentro"].div(mensal["Total"]).mul(100).round(2)
    )
    mensal["Percentual_Fora"] = (
        mensal["Fora"].div(mensal["Total"]).mul(100).round(2)
    )
    mensal["Comp"] = mensal["Periodo"].dt.strftime("%m/%Y")

    return mensal[
        [
            "Periodo",
            "Comp",
            "Fora",
            "Dentro",
            "Total",
            "Percentual_Fora",
            "Percentual_Dentro",
        ]
    ].sort_values("Periodo", ignore_index=True)


def resumo_operacional(dados: pd.DataFrame) -> dict[str, float | int]:
    validos = dados.loc[dados["Prazo"].isin(["Dentro", "Fora"])]
    dentro = int(validos["Prazo"].eq("Dentro").sum())
    fora = int(validos["Prazo"].eq("Fora").sum())
    total = dentro + fora

    return {
        "total": total,
        "dentro": dentro,
        "fora": fora,
        "percentual_dentro": round((dentro / total * 100), 2) if total else 0.0,
        "percentual_fora": round((fora / total * 100), 2) if total else 0.0,
        "sem_data": int(dados["Prazo"].eq("Sem data").sum()),
    }


def ranking_produtos_fora(dados: pd.DataFrame, limite: int = 10) -> pd.DataFrame:
    """Retorna os produtos com maior quantidade fora do SLA."""

    base = dados.loc[dados["Prazo"].isin(["Dentro", "Fora"])].copy()
    base[COLUNA_PRODUTO] = base[COLUNA_PRODUTO].fillna("Não informado").astype(str)

    if base.empty:
        return pd.DataFrame(columns=[COLUNA_PRODUTO, "Fora", "Total", "Percentual_Fora"])

    ranking = (
        base.groupby(COLUNA_PRODUTO, dropna=False)
        .agg(
            Fora=("Prazo", lambda serie: int(serie.eq("Fora").sum())),
            Total=("Prazo", "size"),
        )
        .reset_index()
    )
    ranking["Percentual_Fora"] = (
        ranking["Fora"].div(ranking["Total"]).mul(100).round(2)
    )

    return (
        ranking.sort_values(["Fora", "Total"], ascending=False)
        .head(limite)
        .sort_values("Fora", ascending=True)
        .reset_index(drop=True)
    )
