import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.conferencia_hora import _banco_ate_data, resumo_mensal, resumo_semanal
from scripts.inserir_hora import registrar
from scripts.save_load import COLUNAS


def _registros_feriado_semana():
    df = pd.DataFrame(columns=COLUNAS)
    for data in ["2026-10-26", "2026-10-27"]:
        df = registrar(
            df,
            data=data,
            entrada="08:00",
            almoco_inicio="12:00",
            almoco_fim="13:00",
            saida="18:00",
            carga_normal=8,
        )
    return df


def test_banco_ate_data_retorna_ultimo_banco_acumulado():
    df = pd.DataFrame(columns=COLUNAS)
    registro = registrar(
        df,
        data="2026-10-26",
        entrada="08:00",
        almoco_inicio="12:00",
        almoco_fim="13:00",
        saida="17:00",
        carga_normal=6,
    )

    resultado = _banco_ate_data(registro, "2026-10-31")

    assert isinstance(resultado, float)
    assert resultado == 2.0


def test_resumo_semanal_calcula_horas_meta_e_saldo():
    registro = _registros_feriado_semana()

    resultado = resumo_semanal(registro, data_referencia="2026-10-26")

    assert resultado["data_inicio"] == pd.Timestamp("2026-10-26").date()
    assert resultado["data_fim"] == pd.Timestamp("2026-11-01").date()
    assert resultado["horas_trabalhadas"] == 18.0
    assert resultado["meta_horas"] == 40.0
    assert resultado["progresso_percentual"] == pytest.approx(45.0)
    assert resultado["saldo_horas"] == 2.0
    assert resultado["banco_horas_acumulado"] == 2.0
    assert len(resultado["registros"]) == 2


def test_resumo_mensal_calcula_horas_meta_e_banco_acumulado():
    registro = _registros_feriado_semana()

    resultado = resumo_mensal(registro, 2026, 10)

    assert resultado["ano"] == 2026
    assert resultado["mes"] == 10
    assert resultado["horas_trabalhadas"] == 18.0
    assert resultado["meta_horas"] == pytest.approx(176.0)
    assert resultado["progresso_percentual"] == pytest.approx(10.227272727272728)
    assert resultado["saldo_horas_mes"] == 2.0
    assert resultado["banco_horas_acumulado"] == 2.0
    assert list(resultado["registros"]["data"]) == [
        pd.Timestamp("2026-10-26"),
        pd.Timestamp("2026-10-27"),
    ]