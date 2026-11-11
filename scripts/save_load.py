# ===========================================================================
# Carrega os csv de registro de horas ou cria novo
# Verifica carga horária do usuário
# Normaliza registros
# Verifica feriados
# ============================================================================




from datetime import datetime
from pathlib import Path
from typing import IO, Union

import pandas as pd
from workalendar.america import Brazil, BrazilDistritoFederal


COLUNAS = [
    "data",
    "entrada",
    "almoco_inicio",
    "almoco_fim",
    "saida",
    "horas_trabalhadas",
    "carga_normal",
    "saldo_horas",
    "banco_extra",
    "abono",
]


def validar_carga_normal(carga_normal):
    try:
        carga_normal = float(carga_normal)
    except (TypeError, ValueError) as erro:
        raise ValueError("A carga horária deve ser 6 ou 8 horas.") from erro

    if carga_normal not in (6, 8):
        raise ValueError("A carga horária deve ser 6 ou 8 horas.")
    return carga_normal


def calcular_horas_trabalhadas(entrada, almoco_inicio, almoco_fim, saida, carga_normal=None):
    if not entrada or not saida:
        raise ValueError("Informe os horários de entrada e saída.")
    if bool(almoco_inicio) != bool(almoco_fim):
        raise ValueError("Informe os dois horários do intervalo ou deixe ambos vazios.")

    formato = "%H:%M"
    try:
        hora_entrada = datetime.strptime(entrada, formato)
        hora_saida = datetime.strptime(saida, formato)
        if almoco_inicio:
            hora_inicio_intervalo = datetime.strptime(almoco_inicio, formato)
            hora_fim_intervalo = datetime.strptime(almoco_fim, formato)
    except (TypeError, ValueError) as erro:
        raise ValueError(
            "Horários inválidos. Use o formato HH:MM, por exemplo, 08:30."
        ) from erro

    if hora_saida <= hora_entrada:
        raise ValueError("A saída deve ser posterior à entrada no mesmo dia.")

    intervalo = 0.0
    if almoco_inicio:
        if hora_inicio_intervalo >= hora_fim_intervalo:
            raise ValueError("O fim do intervalo deve ser posterior ao início.")
        if hora_inicio_intervalo < hora_entrada or hora_fim_intervalo > hora_saida:
            raise ValueError("O intervalo deve ocorrer entre a entrada e a saída.")
        intervalo = (hora_fim_intervalo - hora_inicio_intervalo).total_seconds()

    segundos = (hora_saida - hora_entrada).total_seconds() - intervalo
    if segundos <= 0:
        raise ValueError("O total de horas trabalhadas deve ser maior que zero.")

    horas_trabalhadas = round(segundos / 3600, 2)
    if carga_normal == 6 and almoco_inicio:
        limite_almoco = 15 * 60
        if intervalo > limite_almoco and horas_trabalhadas < 8:
            raise ValueError(
                "Para carga de 6 horas, o intervalo de almoço deve ter no máximo 15 minutos, salvo quando a jornada ultrapassar 8 horas trabalhadas."
            )

    return horas_trabalhadas


def normalizar_registros(df, carga_normal=8):
    carga_normal = validar_carga_normal(carga_normal)
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Os registros devem ser fornecidos em um DataFrame.")

    registros = df.copy()
    if "data" not in registros.columns:
        raise ValueError("O arquivo precisa conter a coluna 'data'.")

    datas = pd.to_datetime(registros["data"], errors="coerce")
    if datas.isna().any():
        linhas = (datas.index[datas.isna()] + 2).tolist()
        raise ValueError(f"Data inválida ou ausente nas linhas: {linhas}.")
    registros["data"] = datas.dt.normalize()

    for coluna in ("entrada", "almoco_inicio", "almoco_fim", "saida"):
        if coluna not in registros.columns:
            registros[coluna] = ""
        registros[coluna] = registros[coluna].astype("string").fillna("")

    if "abono" not in registros.columns:
        registros["abono"] = ""
    registros["abono"] = registros["abono"].astype("string").fillna("").str.strip()

    if "carga_normal" not in registros.columns:
        registros["carga_normal"] = carga_normal
    else:
        cargas_originais = registros["carga_normal"]
        cargas = pd.to_numeric(cargas_originais, errors="coerce")
        invalidas = (
            cargas.isna()
            & cargas_originais.notna()
            & cargas_originais.astype(str).str.strip().ne("")
        )
        if invalidas.any():
            linhas = (cargas.index[invalidas] + 2).tolist()
            raise ValueError(f"Carga horária inválida nas linhas: {linhas}.")
        cargas = cargas.fillna(carga_normal)
        invalidas = ~cargas.isin((6, 8))
        if invalidas.any():
            linhas = (cargas.index[invalidas] + 2).tolist()
            raise ValueError(f"Carga horária inválida nas linhas: {linhas}.")
        registros["carga_normal"] = cargas.astype(float)

    if "horas_trabalhadas" not in registros.columns:
        registros["horas_trabalhadas"] = float("nan")
    horas_originais = registros["horas_trabalhadas"]
    horas = pd.to_numeric(horas_originais, errors="coerce")
    invalidas = horas.isna() & horas_originais.notna() & horas_originais.astype(str).str.strip().ne("")
    if invalidas.any():
        linhas = (horas.index[invalidas] + 2).tolist()
        raise ValueError(f"Horas trabalhadas inválidas nas linhas: {linhas}.")

    for indice in horas.index[horas.isna()]:
        if registros.at[indice, "abono"]:
            horas.at[indice] = registros.at[indice, "carga_normal"]
        else:
            horas.at[indice] = calcular_horas_trabalhadas(
                registros.at[indice, "entrada"],
                registros.at[indice, "almoco_inicio"],
                registros.at[indice, "almoco_fim"],
                registros.at[indice, "saida"],
                carga_normal=registros.at[indice, "carga_normal"],
            )
    if (horas < 0).any():
        raise ValueError("As horas trabalhadas não podem ser negativas.")
    desvio_carga = (horas - registros["carga_normal"]).abs().round(2)
    tolerancia_horas = round(10 / 60, 2)
    horas.loc[desvio_carga <= tolerancia_horas] = registros.loc[
        desvio_carga <= tolerancia_horas, "carga_normal"
    ]
    registros["horas_trabalhadas"] = horas.astype(float)

    if registros["data"].duplicated().any():
        datas_duplicadas = (
            registros.loc[registros["data"].duplicated(keep=False), "data"]
            .dt.strftime("%Y-%m-%d")
            .unique()
            .tolist()
        )
        raise ValueError(f"Há mais de um registro para estas datas: {datas_duplicadas}.")

    return registros.sort_values("data", kind="stable").reset_index(drop=True)


def recalcular_saldos(df, carga_normal=8):
    registros = normalizar_registros(df, carga_normal)
    registros["saldo_horas"] = (
        registros["horas_trabalhadas"] - registros["carga_normal"]
    ).round(2)
    registros["banco_extra"] = registros["saldo_horas"].cumsum().round(2)
    colunas = COLUNAS + [coluna for coluna in registros.columns if coluna not in COLUNAS]
    return registros.reindex(columns=colunas)


def feriados_mes(ano, mes):
    if not 1 <= mes <= 12:
        raise ValueError("O mês deve estar entre 1 e 12.")

    nomes_por_data = {}
    for calendario in (Brazil(), BrazilDistritoFederal()):
        for data_feriado, nome in calendario.holidays(ano):
            if data_feriado.month == mes:
                nomes_por_data.setdefault(data_feriado, set()).add(nome)

    return [
        (data_feriado, ", ".join(sorted(nomes)))
        for data_feriado, nomes in sorted(nomes_por_data.items())
    ]


def registrar_feriados_mes(df, ano, mes, carga_normal=8):
    carga_normal = validar_carga_normal(carga_normal)
    registros = normalizar_registros(df, carga_normal)
    datas_registradas = set(registros["data"].dt.date)
    novos_registros = []

    for data_feriado, nome in feriados_mes(ano, mes):
        if data_feriado.weekday() < 5 and data_feriado not in datas_registradas:
            novos_registros.append({
                "data": pd.Timestamp(data_feriado),
                "entrada": "",
                "almoco_inicio": "",
                "almoco_fim": "",
                "saida": "",
                "horas_trabalhadas": carga_normal,
                "carga_normal": carga_normal,
                "abono": nome,
            })

    if novos_registros:
        registros = pd.concat(
            [registros, pd.DataFrame(novos_registros)],
            ignore_index=True,
        )
    return recalcular_saldos(registros, carga_normal)


def load(arquivo: Union[str, Path, IO], carga_normal=8):
    carga_normal = validar_carga_normal(carga_normal)
    if hasattr(arquivo, "read"):
        dados = pd.read_csv(arquivo, sep=";")
    else:
        caminho = Path(arquivo)
        if caminho.exists():
            dados = pd.read_csv(caminho, sep=";")
        else:
            dados = pd.DataFrame(columns=COLUNAS)
    return recalcular_saldos(dados, carga_normal)


def salvar(df, arquivo: Union[str, Path]):
    caminho = Path(arquivo)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    recalcular_saldos(df).to_csv(caminho, index=False)

if __name__ == "__main__":
    carga_normal = validar_carga_normal()
    horas = calcular_horas_trabalhadas()
    df = normalizar_registros()
    saldos = recalcular_saldos()
    planilha = load()
    novo_df = salvar()