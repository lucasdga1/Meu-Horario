import streamlit as st
import pandas as pd
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import save_load, inserir_hora, conferencia_hora

st.title("🕧 Meu Horário!")
st.set_page_config(layout="wide")
st.markdown("""
## Este app foi construído com a finalidade de auxiliar as pessoas nos seus controles de carga horária de trabalho.
### O que este app faz:
1. Cria ou utiliza seus registros de hora de trabalhada em formato CSV;
2. Valida seus registros diários e abonos;
3. Verifica e registra a existência de feriados
4. Mostra os seus registros, saldos e bancos de hora, metas semanais e mensais para facilitar o acompanhamento
""")

st.divider()
st.markdown("## ⏱️Informe sua carga horária normal")
carga_normal = st.number_input("Carga horária",
                               min_value=6,
                               max_value=8,
                               value=6,
                               step=2)
meses = {
    "Janeiro": 1,
    "Fevereiro": 2,
    "Março": 3,
    "Abril": 4,
    "Maio": 5,
    "Junho": 6,
    "Julho": 7,
    "Agosto": 8,
    "Setembro": 9,
    "Outubro": 10,
    "Novembro": 11,
    "Dezembro": 12
}

mes_str = st.selectbox(
    "**Selecione o mês atual**",
    options=list(meses.keys())
)

mes_num = meses[mes_str]

st.write(f"Mês selecionado: **{mes_str}**")
st.write(f"Número do mês: **{mes_num}**")

ano = st.selectbox(
    "**Selecione o ano atual**",
    range(2026, 2036)
)
st.markdown("""
## Carregue um arquivo de horas ou crie um novo
""")
arquivo = st.file_uploader(
    "Selecione um arquivo", type="csv"
)

df = None
if arquivo is not None:
    st.write(f"Arquivo enviado✅: {arquivo.name}")
    resultado = save_load.load(arquivo, carga_normal)
    df = pd.DataFrame(resultado)

st.markdown("### Se desejar criar um arquivo novo insira o nome do novo arquivo abaixo e clique no botão abaixo")
nome_arquivo = st.text_input("📃Informe um nome para o seu novo arquivo:")
if st.button("**Crie um arquivo de horas novo**"):
    df = save_load.load(nome_arquivo, carga_normal)
    if df is not None: st.write("Arquivo criado!✅")

st.divider()

if df is not None:
    df = save_load.registrar_feriados_mes(df, ano, mes_num, carga_normal)

    st.markdown("""### ⏱️Este é o seu registro de horas atualizado:""")
    st.dataframe(df)