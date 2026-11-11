# Meu Horário

Aplicação para registrar e acompanhar horas trabalhadas, saldo de horas e banco
de horas. A interface foi construída com Streamlit e os registros podem ser
carregados e baixados em formato CSV.

## Objetivos

- Facilitar o registro diário de horários de entrada, almoço e saída.
- Permitir registrar abonos e feriados.
- Calcular horas trabalhadas, saldo diário e banco de horas acumulado.
- Apresentar resumos semanais e mensais com metas e progresso.
- Permitir continuar usando os dados por meio de arquivos CSV.

## Aplicação

**Acesse o app:** [Meu Horário no Streamlit](https://meu-horario.streamlit.app/)


## Funcionalidades e regras

- Importação de registros em CSV e criação de uma planilha nova.
- Validação de carga horária normal de 6 ou 8 horas.
- Cálculo de horas trabalhadas, saldo e banco acumulado.
- Tolerância de 10 minutos em torno da carga normal: diferenças de até 10
  minutos para mais ou para menos são ajustadas para a carga cheia.
- Para carga normal de 6 horas, o intervalo de almoço é limitado a 15 minutos,
  exceto quando a jornada total chega a 8 horas trabalhadas.
- Registro de feriados brasileiros e do Distrito Federal.
- Resumos por semana e por mês, com horas, meta, progresso, saldo e banco.
- Download dos registros atualizados em CSV.

## Tecnologias

- Python 3.12 (versão usada na integração contínua)
- Streamlit
- pandas e NumPy
- workalendar
- pytest

## Como executar localmente

1. Clone o repositório e entre na pasta do projeto:

   ```powershell
   git clone https://github.com/lucasdga1/Meu-Horario.git
   cd Meu-Horario
   ```

2. Crie e ative um ambiente virtual:

   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   No macOS ou Linux, use:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Instale as dependências:

   ```powershell
   py -m pip install streamlit pandas numpy workalendar pytest
   ```

   Em macOS ou Linux, use `python -m pip` no lugar de `py -m pip`.

4. Inicie o app:

   ```powershell
   streamlit run app\home.py
   ```

   O Streamlit exibirá no terminal o endereço local da aplicação.

## Testes

Com o ambiente virtual ativado e as dependências instaladas, execute:

```powershell
py -m pytest -q
```

No macOS ou Linux:

```bash
python -m pytest -q
```

## Estrutura do projeto

```text
Meu-Horario/
|-- .github/
|   `-- workflows/
|       `-- ci.yml                 # Integração contínua e execução dos testes
|-- .streamlit/
|   `-- config.toml                # Configuração visual do Streamlit
|-- app/
|   `-- home.py                    # Interface e fluxo principal da aplicação
|-- scripts/
|   |-- conferencia_hora.py        # Resumos semanais e mensais
|   |-- inserir_hora.py            # Inclusão de registros e abonos
|   `-- save_load.py               # Validação, cálculos e operações CSV
|-- tests/
|   |-- test_conferencia.py        # Testes dos resumos
|   |-- test_inserir_hora.py       # Testes de inclusão de registros
|   `-- test_save_load.py          # Testes de validação e arquivos
|-- .gitignore
|-- LICENSE
|-- requirements.txt               # Dependências do projeto
`-- README.MD
```

## Formato dos registros

O CSV usa as seguintes colunas:

| Coluna | Descrição |
|---|---|
| `data` | Data do registro |
| `entrada` | Horário de entrada |
| `almoco_inicio` | Início do intervalo |
| `almoco_fim` | Fim do intervalo |
| `saida` | Horário de saída |
| `horas_trabalhadas` | Total de horas trabalhadas |
| `carga_normal` | Carga horária normal do registro |
| `saldo_horas` | Diferença entre as horas trabalhadas e a carga normal |
| `banco_extra` | Banco de horas acumulado |
| `abono` | Motivo do abono, se aplicável |

Use um CSV exportado pelo app como modelo para preparar um arquivo próprio.

## Contribuições

Contribuições são bem-vindas. Para propor uma mudança:

1. Abra uma issue para descrever o problema ou a melhoria.
2. Faça um fork e crie uma branch para sua alteração.
3. Implemente a mudança e adicione ou atualize os testes correspondentes.
4. Execute `py -m pytest -q` e abra um pull request com uma descrição clara.

## Contato e suporte

Para relatar erros, sugerir melhorias ou tirar dúvidas, abra uma
[issue no GitHub](https://github.com/lucasdga1/Meu-Horario/issues).

## Licença

Este projeto está sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE).
