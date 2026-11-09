import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.inserir_hora import registrar
from scripts.save_load import COLUNAS

def test_registro():
    df = pd.DataFrame(columns=COLUNAS)

    resultado = registrar(
        df,
        data="2026-10-26",
        entrada="08:00",
        almoco_inicio="12:00",
        almoco_fim="13:00",
        saida="16:00",
        carga_normal=8,
    )

    assert isinstance(resultado, pd.DataFrame)
    assert not resultado.empty
    assert len(resultado) == 1
    assert resultado.loc[0, "data"] == pd.Timestamp("2026-10-26")
    assert resultado.loc[0, "horas_trabalhadas"] == 7
    assert resultado.loc[0, "saldo_horas"] == -1
    assert resultado.loc[0, "banco_extra"] == -1