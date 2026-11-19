import hashlib
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import conferencia_hora, inserir_hora, save_load


st.set_page_config(
    page_title="Meu Horário",
    page_icon="🕐",
    layout="wide",
)

st.markdown(
    """
    <style>
    [data-testid="stMetric"] {
        background: #52528C;
        border: 1px solid rgba(255, 255, 240, 0.18);
        border-radius: 12px;
        padding: 16px;
    }
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
        color: #FFFFF0;
    }
    .bloco-inicial {
        background: rgba(82, 82, 140, 0.25);
        border-left: 5px solid #52528C;
        border-radius: 10px;
        padding: 18px 20px;
        margin-bottom: 16px;
    }
    .registro-horario {
        background: rgba(82, 82, 140, 0.18);
        border: 1px solid rgba(255, 255, 240, 0.16);
        border-radius: 12px;
        padding: 14px;
        height: 100%;
    }
    .registro-horario [data-testid="stNumberInput"] {
        min-width: 72px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

MESES = {
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
    "Dezembro": 12,
}

HORARIOS_INICIAIS = {
    "entrada": (8, 0),
    "almoco_inicio": (12, 0),
    "almoco_fim": (13, 0),
    "saida": (17, 0),
}


def formatar_horario(chave_hora, chave_minuto):
    return f"{st.session_state[chave_hora]:02d}:{st.session_state[chave_minuto]:02d}"


for campo, (hora, minuto) in HORARIOS_INICIAIS.items():
    chave_hora = f"registro_{campo}_hora"
    chave_minuto = f"registro_{campo}_minuto"
    if chave_hora not in st.session_state:
        st.session_state[chave_hora] = hora
    if chave_minuto not in st.session_state:
        st.session_state[chave_minuto] = minuto


if "registros_df" not in st.session_state:
    st.session_state.registros_df = pd.DataFrame(columns=save_load.COLUNAS)
    st.session_state.registros_origem = None
    st.session_state.upload_carregado = None


st.title("🕐 Meu Horário")
st.caption("Controle simples de carga horária, abonos, saldo e banco de horas")

st.markdown(
    """
    <div class="bloco-inicial">
    <strong>Como usar</strong><br>
    1. Defina sua carga e escolha o período.<br>
    2. Carregue um CSV ou crie um novo registro.<br>
    3. Adicione suas horas ou abonos e acompanhe os resultados.
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Configurações")
    carga_normal = st.number_input(
        "Carga horária diária",
        min_value=6,
        max_value=8,
        value=8,
        step=2,
        help="A carga normal pode ser de 6 ou 8 horas.",
    )

    mes_selecionado = st.selectbox(
        "Mês de referência",
        options=list(MESES.keys()),
        key="mes_atual",
    )
    mes_numero = MESES[mes_selecionado]

    ano_selecionado = st.selectbox(
        "Ano de referência",
        range(2026, 2036),
        key="ano_atual",
    )

    st.divider()
    nome_download = (
        st.session_state.registros_origem[1]
        if st.session_state.registros_origem is not None
        else ""
    )
    if st.session_state.registros_origem is not None:
        if not nome_download.lower().endswith(".csv"):
            nome_download = f"{nome_download}.csv"
        st.download_button(
            "Baixar registro em CSV",
            data=save_load.recalcular_saldos(
                st.session_state.registros_df,
                carga_normal,
            ).to_csv(index=False),
            file_name=nome_download,
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.caption("O download ficará disponível após carregar ou criar um arquivo.")


aba_arquivo, aba_registro, aba_semanal, aba_mensal = st.tabs(
    ["Arquivo", "Registrar", "Resumo semanal", "Resumo mensal"]
)


with aba_arquivo:
    st.subheader("Prepare seus registros")

    coluna_upload, coluna_novo = st.columns(2, gap="large")

    with coluna_upload:
        st.markdown("**Carregar arquivo existente**")
        arquivo = st.file_uploader(
            "Selecione um arquivo CSV",
            type="csv",
            help="O arquivo deve seguir o formato usado pelo app.",
        )

        if arquivo is not None:
            chave_upload = (
                arquivo.name,
                hashlib.sha256(arquivo.getvalue()).hexdigest(),
            )
            if st.session_state.upload_carregado != chave_upload:
                try:
                    arquivo.seek(0)
                    st.session_state.registros_df = save_load.load(
                        arquivo,
                        carga_normal,
                    )
                    st.session_state.registros_origem = ("upload", arquivo.name)
                    st.session_state.upload_carregado = chave_upload
                    st.success(f"Arquivo carregado: **{arquivo.name}**")
                except (ValueError, pd.errors.ParserError) as erro:
                    st.error(f"Não foi possível carregar o arquivo: {erro}")

    with coluna_novo:
        st.markdown("**Criar novo arquivo**")
        nome_arquivo = st.text_input(
            "Nome do arquivo",
            placeholder="Ex.: horas_2026",
        )
        if st.button("Criar novo registro", type="primary", use_container_width=True):
            if nome_arquivo.strip():
                try:
                    st.session_state.registros_df = save_load.load(
                        nome_arquivo.strip(),
                        carga_normal,
                    )
                    st.session_state.registros_origem = (
                        "novo",
                        nome_arquivo.strip(),
                    )
                    st.success("Novo registro criado.")
                except ValueError as erro:
                    st.error(f"Não foi possível criar o registro: {erro}")
            else:
                st.warning("Informe um nome para o novo arquivo.")

    st.divider()

    df = st.session_state.registros_df
    if st.session_state.registros_origem is not None:
        try:
            df = save_load.registrar_feriados_mes(
                df,
                ano_selecionado,
                mes_numero,
                carga_normal,
            )
            st.session_state.registros_df = df
        except ValueError as erro:
            st.error(f"Não foi possível atualizar os feriados: {erro}")

        st.subheader("Registro atual")
        if df.empty:
            st.info("O arquivo ainda não possui registros.")
        else:
            st.dataframe(
                df,
                hide_index=True,
                use_container_width=True,
                height=320,
            )
    else:
        st.info("Carregue um arquivo existente ou crie um novo para começar.")


with aba_registro:
    st.subheader("Adicionar um dia")

    data = st.date_input(
        "Data do registro",
        value=date.today(),
        format="DD/MM/YYYY",
    )
    tipo_registro = st.radio(
        "Tipo de registro",
        ["Horas trabalhadas", "Abono"],
        horizontal=True,
    )

    df = st.session_state.registros_df

    if tipo_registro == "Abono":
        motivo_abono = st.text_input(
            "Motivo do abono",
            placeholder="Ex.: consulta médica",
        )
        if st.button("Adicionar abono", type="primary", use_container_width=True):
            if not motivo_abono.strip():
                st.warning("Informe o motivo do abono.")
            else:
                try:
                    st.session_state.registros_df = inserir_hora.registrar(
                        df=df,
                        data=data,
                        carga_normal=carga_normal,
                        abono=motivo_abono,
                    )
                    st.session_state.registros_origem = (
                        st.session_state.registros_origem
                        if st.session_state.registros_origem is not None
                        else ("novo", "registro_horas")
                    )
                    st.success("Abono registrado com sucesso.")
                except ValueError as erro:
                    st.error(str(erro))
    else:
        st.caption("Ajuste separadamente as horas e os minutos usando os controles de cada campo.")
        colunas_horarios = st.columns(4, gap="small")
        horarios_formatados = {}

        for coluna, campo in zip(
            colunas_horarios,
            ("entrada", "almoco_inicio", "almoco_fim", "saida"),
        ):
            rotulos = {
                "entrada": "Entrada",
                "almoco_inicio": "Início do almoço",
                "almoco_fim": "Fim do almoço",
                "saida": "Saída",
            }
            chave_hora = f"registro_{campo}_hora"
            chave_minuto = f"registro_{campo}_minuto"

            with coluna:
                st.markdown('<div class="registro-horario">', unsafe_allow_html=True)
                st.markdown(f"**{rotulos[campo]}**")

                coluna_hora, coluna_minuto = st.columns(2)
                with coluna_hora:
                    st.number_input(
                        "Hora",
                        min_value=0,
                        max_value=23,
                        step=1,
                        key=chave_hora,
                        help="Formato HH",
                    )
                with coluna_minuto:
                    st.selectbox(
                        "Minuto",
                        options=list(range(0, 60, 5)),
                        format_func=lambda minuto: f"{minuto:02d}",
                        key=chave_minuto,
                        help="Formato MM",
                    )

                st.markdown("</div>", unsafe_allow_html=True)

            horarios_formatados[campo] = formatar_horario(
                chave_hora,
                chave_minuto,
            )

        entrada = horarios_formatados["entrada"]
        almoco_inicio = horarios_formatados["almoco_inicio"]
        almoco_fim = horarios_formatados["almoco_fim"]
        saida = horarios_formatados["saida"]

        try:
            horas_previstas = save_load.calcular_horas_trabalhadas(
                entrada,
                almoco_inicio,
                almoco_fim,
                saida,
                carga_normal=carga_normal,
            )
            st.success(
                f"Prévia: **{horas_previstas:.2f} horas trabalhadas** "
                f"({entrada} às {saida}, intervalo das "
                f"{almoco_inicio} às {almoco_fim})."
            )
        except ValueError as erro:
            st.warning(f"Confira os horários: {erro}")

        if st.button("Adicionar registro", type="primary", use_container_width=True):
            try:
                st.session_state.registros_df = inserir_hora.registrar(
                    df=df,
                    data=data,
                    entrada=entrada,
                    almoco_inicio=almoco_inicio,
                    almoco_fim=almoco_fim,
                    saida=saida,
                    carga_normal=carga_normal,
                    abono=None,
                )
                st.session_state.registros_origem = (
                    st.session_state.registros_origem
                    if st.session_state.registros_origem is not None
                    else ("novo", "registro_horas")
                )
                st.success("Horários registrados com sucesso.")
            except ValueError as erro:
                st.error(str(erro))


with aba_semanal:
    st.subheader("Seu resumo semanal")
    data_referencia = st.date_input(
        "Data de referência",
        value=date.today(),
        key="data_referencia_semanal",
        format="DD/MM/YYYY",
    )

    try:
        resumo_semanal = conferencia_hora.resumo_semanal(
            st.session_state.registros_df,
            data_referencia,
            carga_normal,
        )
        st.caption(
            f"Semana de {resumo_semanal['data_inicio']:%d/%m/%Y} "
            f"a {resumo_semanal['data_fim']:%d/%m/%Y}"
        )

        colunas = st.columns(5)
        indicadores = [
            ("Horas trabalhadas", f"{resumo_semanal['horas_trabalhadas']:.2f} h"),
            ("Meta semanal", f"{resumo_semanal['meta_horas']:.2f} h"),
            ("Progresso", f"{resumo_semanal['progresso_percentual']:.1f}%"),
            ("Saldo da semana", f"{resumo_semanal['saldo_horas']:+.2f} h"),
            ("Banco acumulado", f"{resumo_semanal['banco_horas_acumulado']:+.2f} h"),
        ]
        for coluna, (rotulo, valor) in zip(colunas, indicadores):
            coluna.metric(rotulo, valor)

        st.markdown("**Registros da semana**")
        if resumo_semanal["registros"].empty:
            st.info("Não há registros nesta semana.")
        else:
            st.dataframe(
                resumo_semanal["registros"],
                hide_index=True,
                use_container_width=True,
            )
    except ValueError as erro:
        st.error(f"Não foi possível calcular o resumo semanal: {erro}")


with aba_mensal:
    st.subheader("Seu resumo mensal")

    ano_resumo = st.selectbox(
        "Ano do resumo",
        range(2026, 2036),
        key="ano_resumo_mensal",
    )
    mes_resumo = st.selectbox(
        "Mês do resumo",
        options=list(MESES.keys()),
        key="mes_resumo_mensal",
    )
    mes_resumo_numero = MESES[mes_resumo]

    try:
        resumo_mensal = conferencia_hora.resumo_mensal(
            st.session_state.registros_df,
            ano_resumo,
            mes_resumo_numero,
            carga_normal,
        )

        colunas = st.columns(5)
        indicadores = [
            ("Horas trabalhadas", f"{resumo_mensal['horas_trabalhadas']:.2f} h"),
            ("Meta mensal", f"{resumo_mensal['meta_horas']:.2f} h"),
            ("Progresso", f"{resumo_mensal['progresso_percentual']:.1f}%"),
            ("Saldo do mês", f"{resumo_mensal['saldo_horas_mes']:+.2f} h"),
            ("Banco acumulado", f"{resumo_mensal['banco_horas_acumulado']:+.2f} h"),
        ]
        for coluna, (rotulo, valor) in zip(colunas, indicadores):
            coluna.metric(rotulo, valor)

        coluna_registros, coluna_feriados = st.columns(2, gap="large")

        with coluna_registros:
            st.markdown("**Registros do mês**")
            if resumo_mensal["registros"].empty:
                st.info("Não há registros neste mês.")
            else:
                st.dataframe(
                    resumo_mensal["registros"],
                    hide_index=True,
                    use_container_width=True,
                )

        with coluna_feriados:
            st.markdown("**Feriados do mês**")
            if resumo_mensal["feriados"].empty:
                st.info("Não há feriados cadastrados para este mês.")
            else:
                st.dataframe(
                    resumo_mensal["feriados"],
                    hide_index=True,
                    use_container_width=True,
                )
    except ValueError as erro:
        st.error(f"Não foi possível calcular o resumo mensal: {erro}")
