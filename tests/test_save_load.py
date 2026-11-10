import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.save_load import (
    COLUNAS,
    calcular_horas_trabalhadas,
    load,
    normalizar_registros,
    recalcular_saldos,
    registrar_feriados_mes,
    salvar,
)


def _dataframe_registros(registros):
    return pd.DataFrame(registros)


def test_load_cria_dataframe_vazio_quando_csv_nao_existe(tmp_path):
    arquivo = tmp_path / "horas.csv"

    resultado = load(arquivo)

    assert isinstance(resultado, pd.DataFrame)
    assert resultado.empty
    assert list(resultado.columns) == COLUNAS
    assert not arquivo.exists()


def test_load_le_csv_existente_e_completa_colunas_opcionais(tmp_path):
    arquivo = tmp_path / "horas.csv"
    pd.DataFrame([{
        "data": "2026-01-02",
        "horas_trabalhadas": 7.5,
    }]).to_csv(arquivo, index=False)

    resultado = load(arquivo)

    assert len(resultado) == 1
    assert resultado.loc[0, "data"] == pd.Timestamp("2026-01-02")
    assert resultado.loc[0, "horas_trabalhadas"] == 7.5
    assert resultado.loc[0, "carga_normal"] == 8
    assert resultado.loc[0, "saldo_horas"] == -0.5
    assert resultado.loc[0, "banco_extra"] == -0.5
    assert resultado.loc[0, "abono"] == ""


def test_normalizar_registros_ordena_dados_e_preenche_campos():
    df = _dataframe_registros([
        {
            "data": "2026-01-02",
            "horas_trabalhadas": 7,
            "carga_normal": 8,
        },
        {
            "data": "2026-01-01",
            "horas_trabalhadas": 9,
            "carga_normal": 8,
        },
    ])

    resultado = normalizar_registros(df)

    assert resultado["data"].tolist() == [
        pd.Timestamp("2026-01-01"),
        pd.Timestamp("2026-01-02"),
    ]
    assert resultado["entrada"].tolist() == ["", ""]
    assert resultado["abono"].tolist() == ["", ""]


@pytest.mark.parametrize(
    ("saida", "carga_normal", "esperado"),
    [
        ("15:50", 8, 8.0),
        ("16:10", 8, 8.0),
        ("15:49", 8, 7.82),
        ("16:11", 8, 8.18),
        ("13:50", 6, 6.0),
        ("14:10", 6, 6.0),
    ],
)
def test_normalizar_registros_aplica_tolerancia_de_dez_minutos(
    saida,
    carga_normal,
    esperado,
):
    df = _dataframe_registros([{
        "data": "2026-01-01",
        "entrada": "08:00",
        "saida": saida,
        "carga_normal": carga_normal,
    }])

    resultado = normalizar_registros(df)

    assert resultado.loc[0, "horas_trabalhadas"] == esperado


def test_recalcular_saldos_usa_carga_normal_de_cada_registro():
    df = _dataframe_registros([
        {
            "data": "2026-01-01",
            "horas_trabalhadas": 9,
            "carga_normal": 8,
        },
        {
            "data": "2026-01-02",
            "horas_trabalhadas": 5,
            "carga_normal": 6,
        },
    ])

    resultado = recalcular_saldos(df)

    assert resultado["saldo_horas"].tolist() == [1, -1]
    assert resultado["banco_extra"].tolist() == [1, 0]


@pytest.mark.parametrize(
    ("entrada", "almoco_inicio", "almoco_fim", "saida", "esperado"),
    [
        ("08:00", "12:00", "13:00", "17:00", 8),
        ("08:30", None, None, "16:30", 8),
    ],
)
def test_calcular_horas_trabalhadas(
    entrada,
    almoco_inicio,
    almoco_fim,
    saida,
    esperado,
):
    assert calcular_horas_trabalhadas(
        entrada,
        almoco_inicio,
        almoco_fim,
        saida,
    ) == esperado


@pytest.mark.parametrize(
    ("entrada", "almoco_inicio", "almoco_fim", "saida", "carga_normal", "esperado"),
    [
        ("08:00", "12:00", "13:00", "17:00", 6, 8.0),
        ("08:00", "12:00", "12:15", "17:00", 6, 8.75),
    ],
)
def test_calcular_horas_trabalhadas_respeita_regra_do_almoco_para_carga_6h(
    entrada,
    almoco_inicio,
    almoco_fim,
    saida,
    carga_normal,
    esperado,
):
    assert calcular_horas_trabalhadas(
        entrada,
        almoco_inicio,
        almoco_fim,
        saida,
        carga_normal=carga_normal,
    ) == esperado


@pytest.mark.parametrize(
    ("entrada", "almoco_inicio", "almoco_fim", "saida"),
    [
        ("08:00", "13:00", "12:00", "17:00"),
        ("08:00", "07:00", "08:30", "17:00"),
        ("08:00", "12:00", None, "17:00"),
        ("08:00", None, None, "08:00"),
        ("inválido", None, None, "17:00"),
    ],
)
def test_calcular_horas_trabalhadas_rejeita_horarios_invalidos(
    entrada,
    almoco_inicio,
    almoco_fim,
    saida,
):
    with pytest.raises(ValueError):
        calcular_horas_trabalhadas(
            entrada,
            almoco_inicio,
            almoco_fim,
            saida,
        )


def test_calcular_horas_trabalhadas_rejeita_almoco_longo_para_carga_6h():
    with pytest.raises(ValueError, match="15 minutos"):
        calcular_horas_trabalhadas(
            "08:00",
            "12:00",
            "13:00",
            "16:00",
            carga_normal=6,
        )


@pytest.mark.parametrize("carga_normal", [0, 7, 8.5, "inválida"])
def test_normalizar_registros_rejeita_carga_horaria_invalida(carga_normal):
    df = _dataframe_registros([{
        "data": "2026-01-01",
        "horas_trabalhadas": 8,
    }])

    with pytest.raises(ValueError, match="carga horária"):
        normalizar_registros(df, carga_normal)


def test_salvar_round_trip_csv(tmp_path):
    arquivo = tmp_path / "horas.csv"
    df = _dataframe_registros([{
        "data": "2026-01-01",
        "horas_trabalhadas": 5,
        "carga_normal": 6,
        "abono": "",
    }])

    salvar(df, arquivo)
    resultado = load(arquivo)

    assert arquivo.exists()
    assert resultado.loc[0, "horas_trabalhadas"] == 5
    assert resultado.loc[0, "carga_normal"] == 6
    assert resultado.loc[0, "saldo_horas"] == -1
    assert resultado.loc[0, "banco_extra"] == -1


def test_registrar_feriados_mes_nao_duplica_registros(tmp_path):
    df = load(tmp_path / "nao-existe.csv")

    primeira_carga = registrar_feriados_mes(df, 2026, 1)
    segunda_carga = registrar_feriados_mes(primeira_carga, 2026, 1)

    assert len(segunda_carga) == len(primeira_carga)
    feriado_ano_novo = segunda_carga[
        segunda_carga["data"] == pd.Timestamp("2026-01-01")
    ]
    assert len(feriado_ano_novo) == 1
    assert feriado_ano_novo.iloc[0]["horas_trabalhadas"] == 8
    assert feriado_ano_novo.iloc[0]["abono"]
