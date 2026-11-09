# ===============================================================
# Conferência de registros de hora para o usuário
# ===============================================================

import calendar
from datetime import date, timedelta

import pandas as pd

from .save_load import (
    feriados_mes,
    normalizar_registros,
    recalcular_saldos,
    validar_carga_normal,
)

# Cálculo de dias úteis no mês
def dias_uteis_mes(ano, mes):
    if not 1 <= mes <= 12:
        raise ValueError("O mês deve estar entre 1 e 12.")
    return sum(
        1
        for semana in calendar.monthcalendar(ano, mes)
        for dia in semana[:5]
        if dia
    )


# Cálculo da meta mensal do usuário baseado na carga horária dele/a
def meta_mensal(ano, mes, carga_normal=8):
    carga_normal = validar_carga_normal(carga_normal)
    return float(dias_uteis_mes(ano, mes) * carga_normal)

# Cálculo do banco de horas extras
def _banco_ate_data(registros, data_limite):
    historico = registros[registros["data"] <= pd.Timestamp(data_limite)]
    if historico.empty:
        return 0.0
    return float(historico.iloc[-1]["banco_extra"])

# Resumo semanal de horas trabalhadas e banco
def resumo_semanal(df, data_referencia=None, carga_normal=8):
    carga_normal = validar_carga_normal(carga_normal)
    if data_referencia is None:
        data_referencia = date.today()
    data_referencia = pd.to_datetime(data_referencia, errors="coerce")
    if pd.isna(data_referencia):
        raise ValueError("A data de referência é inválida.")
    data_inicio = (data_referencia - timedelta(days=data_referencia.weekday())).normalize()
    data_fim = data_inicio + timedelta(days=6)

    registros = recalcular_saldos(normalizar_registros(df, carga_normal), carga_normal)
    registros_semana = registros[
        registros["data"].between(data_inicio, data_fim, inclusive="both")
    ]
    horas_semana = float(registros_semana["horas_trabalhadas"].sum())
    saldo_semana = float(registros_semana["saldo_horas"].sum())
    meta = float(sum(
        carga_normal
        for dia in range(7)
        if (data_inicio + timedelta(days=dia)).weekday() < 5
    ))

    return {
        "data_inicio": data_inicio.date(),
        "data_fim": data_fim.date(),
        "horas_trabalhadas": horas_semana,
        "meta_horas": meta,
        "progresso_percentual": (horas_semana / meta * 100) if meta else 0.0,
        "saldo_horas": saldo_semana,
        "banco_horas_acumulado": _banco_ate_data(registros, data_fim),
        "registros": registros_semana,
    }

# Resumo mensal de horas trabalhadas e banco
def resumo_mensal(df, ano, mes, carga_normal=8):
    carga_normal = validar_carga_normal(carga_normal)
    if not 1 <= mes <= 12:
        raise ValueError("O mês deve estar entre 1 e 12.")
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    data_fim = date(ano, mes, ultimo_dia)

    registros = recalcular_saldos(normalizar_registros(df, carga_normal), carga_normal)
    registros_mes = registros[
        (registros["data"].dt.year == ano)
        & (registros["data"].dt.month == mes)
    ]
    horas_mes = float(registros_mes["horas_trabalhadas"].sum())
    saldo_mes = float(registros_mes["saldo_horas"].sum())
    meta = meta_mensal(ano, mes, carga_normal)
    feriados = pd.DataFrame(feriados_mes(ano, mes), columns=["data", "abono"])

    return {
        "ano": ano,
        "mes": mes,
        "horas_trabalhadas": horas_mes,
        "meta_horas": meta,
        "progresso_percentual": (horas_mes / meta * 100) if meta else 0.0,
        "saldo_horas_mes": saldo_mes,
        "banco_horas_acumulado": _banco_ate_data(registros, data_fim),
        "feriados": feriados,
        "registros": registros_mes,
    }
