# ==================================================================
# Registro de horas trabalhadas ou abono
# ==================================================================

import pandas as pd

from .save_load import (
    calcular_horas_trabalhadas,
    feriados_mes as feriados_mes,
    normalizar_registros,
    recalcular_saldos,
    registrar_feriados_mes as registrar_feriados_mes,
    validar_carga_normal,
)


def registrar(
    df,
    data,
    entrada=None,
    almoco_inicio=None,
    almoco_fim=None,
    saida=None,
    carga_normal=8,
    abono=None,
):
    carga_normal = validar_carga_normal(carga_normal)
    registros = normalizar_registros(df, carga_normal)
    data_dt = pd.to_datetime(data, errors="coerce")
    if pd.isna(data_dt):
        raise ValueError("A data informada é inválida.")
    data_dt = data_dt.normalize()

    if data_dt in set(registros["data"]):
        raise ValueError(f"Já existe um registro para {data_dt:%Y-%m-%d}.")

    motivo_abono = str(abono).strip() if abono is not None else ""
    if motivo_abono:
        entrada = almoco_inicio = almoco_fim = saida = ""
        horas = carga_normal
    else:
        horarios = (entrada, almoco_inicio, almoco_fim, saida)
        entrada, almoco_inicio, almoco_fim, saida = (
            "" if horario is None else str(horario).strip()
            for horario in horarios
        )
        horas = calcular_horas_trabalhadas(
            entrada,
            almoco_inicio,
            almoco_fim,
            saida,
        )

    novo_registro = pd.DataFrame([{
        "data": data_dt,
        "entrada": entrada,
        "almoco_inicio": almoco_inicio,
        "almoco_fim": almoco_fim,
        "saida": saida,
        "horas_trabalhadas": horas,
        "carga_normal": carga_normal,
        "abono": motivo_abono,
    }])
    return recalcular_saldos(
        pd.concat([registros, novo_registro], ignore_index=True),
        carga_normal,
    )
