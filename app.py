import streamlit as st
import pandas as pd
import openai

# Configurar a chave da OpenAI
openai.api_key = st.secrets["openai_api_key"]  # Configure essa chave no ambiente Streamlit

st.set_page_config(page_title="Precificação MRO - Abecom", layout="wide")
st.title("📊 Precificação Automatizada de Produtos MRO")

st.markdown("Faça upload da planilha SAP para precificação automática com IA.")

uploaded_file = st.file_uploader("Upload da Planilha do Cliente (Excel)", type=["xlsx"])

if uploaded_file:
    # Tentar ler a primeira aba da planilha automaticamente, sem pular linhas
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = [col.strip().upper() for col in df.columns]

        # Verificar se todas as colunas esperadas estão presentes
        required_cols = ["CÓDIGO CLIENTE", "DESCRIÇÃO CURTA", "DESCRIÇÃO LONGA", "UNIDADE", "U.F. DEST"]
        if all(col in df.columns for col in required_cols):
            df = df[required_cols]
            df.columns = ["Codigo Cliente", "Descricao Curta", "Descricao Longa", "Unidade", "UF Destino"]

            st.subheader("Pré-visualização dos Dados:")
            st.dataframe(df.head(10))

            if st.button("🔍 Processar com IA GPT"):
                resultados = []
                for index, row in df.iterrows():
                    prompt = f"""
                    Você é um engenheiro especialista em produtos MRO da Abecom. Receba os dados abaixo e retorne:
                    - Código padrão do fabricante
                    - Marca
                    - Tipo de produto
                    - NCM
                    - Descrição técnica padrão (com dimensões)
                    - Família do produto

                    Dados:
                    Código Cliente: {row['Codigo Cliente']}
                    Descrição Curta: {row['Descricao Curta']}
                    Descrição Longa: {row['Descricao Longa']}
                    Unidade (Origem): {row['Unidade']}
                    UF Destino: {row['UF Destino']}
                    """

                    response = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[{"role": "system", "content": "Você é um especialista técnico da Abecom."},
                                 {"role": "user", "content": prompt}]
                    )

                    content = response.choices[0].message.content
                    resultados.append(content)

                df_resultados = pd.DataFrame(resultados, columns=["Resultado GPT"])
                st.subheader("Resultados da IA:")
                st.dataframe(df_resultados)

                final_df = pd.concat([df, df_resultados], axis=1)
                st.download_button("📥 Baixar Planilha Processada", data=final_df.to_csv(index=False),
                                   file_name="Planilha_Precificada.csv", mime="text/csv")
        else:
            st.error("A planilha deve conter as colunas: Código Cliente, Descrição Curta, Descrição Longa, Unidade, U.F. Dest")
    except Exception as e:
        st.error(f"Erro ao processar a planilha: {str(e)}")
else:
    st.info("Faça o upload de uma planilha válida para começar.")
