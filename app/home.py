import streamlit as st
import pandas as pd
from datetime import date, time
import hashlib
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
    options=list(meses.keys()),
    key="mes_atual",
)

mes_num = meses[mes_str]

st.write(f"Mês selecionado: **{mes_str}**")
st.write(f"Número do mês: **{mes_num}**")

ano = st.selectbox(
    "**Selecione o ano atual**",
    range(2026, 2036),
    key="ano_atual",
)
st.markdown("""
## Carregue um arquivo de horas ou crie um novo
""")
arquivo = st.file_uploader(
    "Selecione um arquivo", type="csv"
)

if "registros_df" not in st.session_state:
    st.session_state.registros_df = pd.DataFrame(columns=save_load.COLUNAS)
    st.session_state.registros_origem = None
    st.session_state.upload_carregado = None

if arquivo is not None:
    st.write(f"Arquivo enviado✅: {arquivo.name}")
    chave_upload = (
        arquivo.name,
        hashlib.sha256(arquivo.getvalue()).hexdigest(),
    )
    if st.session_state.upload_carregado != chave_upload:
        arquivo.seek(0)
        st.session_state.registros_df = save_load.load(arquivo, carga_normal)
        st.session_state.registros_origem = ("upload", arquivo.name)
        st.session_state.upload_carregado = chave_upload

st.markdown("### Se desejar criar um arquivo novo insira o nome do novo arquivo abaixo e clique no botão abaixo")
nome_arquivo = st.text_input("📃Informe um nome para o seu novo arquivo:")
if st.button("**Crie um arquivo de horas novo**"):
    if nome_arquivo.strip():
        st.session_state.registros_df = save_load.load(nome_arquivo, carga_normal)
        st.session_state.registros_origem = ("novo", nome_arquivo.strip())
        st.write("Arquivo criado!✅")
    else:
        st.error("Informe um nome para o novo arquivo.")

st.divider()

df = st.session_state.registros_df
if st.session_state.registros_origem is not None:
    df = save_load.registrar_feriados_mes(df, ano, mes_num, carga_normal)
    st.session_state.registros_df = df

    st.markdown("""### ⏱️Este é o seu registro de horas atualizado:""")
    st.dataframe(df)

st.divider()

st.markdown("## **Registre suas horas de trabalho**")
registro = None
abono = None
data = st.date_input(
    "Escolha uma data",
    value=date.today()
)
abono = st.selectbox(
    "Você pegou abono nesta data?",
    ["Sim", "Não"]
)
if abono == "Sim":
    abono = st.text_input("Qual o motivo do abono?")
    if st.button("**Adicionar abono**"):
        st.session_state.registros_df = inserir_hora.registrar(
            df=df,
            data=data,
            carga_normal=carga_normal,
            abono=abono,
        )
        if st.session_state.registros_origem is None:
            st.session_state.registros_origem = (
                "novo",
                nome_arquivo.strip() or "registro_horas",
            )
        st.dataframe(st.session_state.registros_df)
elif abono == "Não":
    abono = None
    entrada = st.time_input(
        "Horário de entrada",
        value=time(8, 0),
        step = 300
    ).strftime("%H:%M")
    almoco_inicio = st.time_input(
        "Horário de início do almoço",
        value=time(8, 0),
        step = 300
    ).strftime("%H:%M")
    almoco_fim = st.time_input(
        "Horário fim do almoço",
        value=time(8, 0),
        step = 300
    ).strftime("%H:%M")
    saida = st.time_input(
        "Horário de saída",
        value=time(8, 0),
        step = 300
    ).strftime("%H:%M")
    
    if st.button("**Adicionar registro de horas**"):
        st.session_state.registros_df = inserir_hora.registrar(
            df=df,
            data=data,
            entrada=entrada,
            almoco_inicio=almoco_inicio,
            almoco_fim=almoco_fim,
            saida=saida,
            carga_normal=carga_normal,
            abono=abono
        )
        if st.session_state.registros_origem is None:
            st.session_state.registros_origem = (
                "novo",
                nome_arquivo.strip() or "registro_horas",
            )
        st.dataframe(st.session_state.registros_df)

st.divider()

st.markdown("## **Seu resumo semanal**")
data_ref = st.date_input(
    "Escolha uma data de referência para o resumo",
    value=date.today(),
    key="data_referencia_semanal",
)
resumo_sem = conferencia_hora.resumo_semanal(
    st.session_state.registros_df,
    data_ref,
    carga_normal
)
st.caption(
    f"Período: {resumo_sem['data_inicio']:%d/%m/%Y} a "
    f"{resumo_sem['data_fim']:%d/%m/%Y}"
)
colunas_semanais = st.columns(5)
colunas_semanais[0].metric(
    "Horas trabalhadas",
    f"{resumo_sem['horas_trabalhadas']:.2f} h",
)
colunas_semanais[1].metric(
    "Meta semanal",
    f"{resumo_sem['meta_horas']:.2f} h",
)
colunas_semanais[2].metric(
    "Progresso",
    f"{resumo_sem['progresso_percentual']:.1f}%",
)
colunas_semanais[3].metric(
    "Saldo da semana",
    f"{resumo_sem['saldo_horas']:+.2f} h",
)
colunas_semanais[4].metric(
    "Banco acumulado",
    f"{resumo_sem['banco_horas_acumulado']:+.2f} h",
)
st.markdown("### Registros da semana")
if resumo_sem["registros"].empty:
    st.info("Não há registros nesta semana.")
else:
    st.dataframe(resumo_sem["registros"], hide_index=True, use_container_width=True)

st.divider()

st.markdown("## **Seu resumo mensal**")
ano_ref = st.selectbox(
    "**Selecione o ano do resumo mensal**",
    range(2026, 2036),
    key="ano_resumo_mensal",
)
mes_ref = st.selectbox(
    "**Selecione o mês do resumo mensal**",
    options=list(meses.keys()),
    key="mes_resumo_mensal",
)
mes_ref_num = meses[mes_ref]
resumo_mes = conferencia_hora.resumo_mensal(
    st.session_state.registros_df,
    ano_ref,
    mes_ref_num,
    carga_normal
)
colunas_mensais = st.columns(5)
colunas_mensais[0].metric(
    "Horas trabalhadas",
    f"{resumo_mes['horas_trabalhadas']:.2f} h",
)
colunas_mensais[1].metric(
    "Meta mensal",
    f"{resumo_mes['meta_horas']:.2f} h",
)
colunas_mensais[2].metric(
    "Progresso",
    f"{resumo_mes['progresso_percentual']:.1f}%",
)
colunas_mensais[3].metric(
    "Saldo do mês",
    f"{resumo_mes['saldo_horas_mes']:+.2f} h",
)
colunas_mensais[4].metric(
    "Banco acumulado",
    f"{resumo_mes['banco_horas_acumulado']:+.2f} h",
)
st.markdown("### Registros do mês")
if resumo_mes["registros"].empty:
    st.info("Não há registros neste mês.")
else:
    st.dataframe(resumo_mes["registros"], hide_index=True, use_container_width=True)

st.markdown("### Feriados do mês")
if resumo_mes["feriados"].empty:
    st.info("Não há feriados cadastrados para este mês.")
else:
    st.dataframe(resumo_mes["feriados"], hide_index=True, use_container_width=True)

st.divider()

st.markdown("## **Faça download do seu arquivo para utilizá-lo de novo**")

nome_download = (
    st.session_state.registros_origem[1]
    if st.session_state.registros_origem is not None
    else nome_arquivo.strip()
)
if st.session_state.registros_origem is not None and nome_download:
    if not nome_download.lower().endswith(".csv"):
        nome_download = f"{nome_download}.csv"

    st.download_button(
        label="**Baixar registro de horas**",
        data=save_load.recalcular_saldos(st.session_state.registros_df).to_csv(index=False),
        file_name=nome_download,
        mime="text/csv",
    )