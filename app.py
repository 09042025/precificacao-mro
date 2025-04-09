
import streamlit as st
import pandas as pd
import openai
from PIL import Image
import base64

# Configuração da página deve vir antes de qualquer outro comando Streamlit
st.set_page_config(page_title="Precificação MRO - Abecom", layout="wide")

# Instanciando cliente da OpenAI compatível com versão >= 1.0.0
client = openai.OpenAI(api_key=st.secrets["openai_api_key"])

# Carregar imagem de fundo e logo com layout ajustado
def set_background_and_logo():
    background_image_path = "b9bfac41-1ece-449a-ae79-62e7eb405277.jpg"
    logo_path = "Sem título.png"

    # Definir fundo estilizado
    with open(background_image_path, "rb") as image_file:
        encoded_bg = base64.b64encode(image_file.read()).decode()
        st.markdown(
            f"""
            <style>
                .stApp {{
                    background-image: url("data:image/jpg;base64,{encoded_bg}");
                    background-size: cover;
                    background-position: center top;
                    background-repeat: no-repeat;
                    background-attachment: fixed;
                    color: white;
                }}
                .main .block-container {{
                    background-color: rgba(0, 0, 0, 0.7);
                    padding: 2rem;
                    border-radius: 15px;
                    box-shadow: 0 0 20px rgba(0,0,0,0.4);
                }}
                h1, h2, h3, h4, h5, h6, label, .stButton, .stMarkdown, .stDataFrameContainer {{
                    color: white !important;
                }}
                .stButton>button {{
                    background-color: #1e90ff;
                    color: white;
                    border-radius: 10px;
                    border: none;
                    padding: 0.5em 1em;
                }}
            </style>
            """,
            unsafe_allow_html=True
        )

    # Exibir logo no topo centralizado
    logo = Image.open(logo_path)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image(logo, width=120)

set_background_and_logo()

st.markdown("## 📊 Precificação Automatizada de Produtos MRO")
st.markdown("### Faça upload da planilha SAP para precificação automática com IA.")

uploaded_file = st.file_uploader("Upload da Planilha do Cliente (Excel)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
        df.columns = [col.strip().upper() for col in df.columns]

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

                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Você é um especialista técnico da Abecom."},
                            {"role": "user", "content": prompt}
                        ]
                    )

                    content = response.choices[0].message.content
                    resultados.append(content)

                df_resultados = pd.DataFrame(resultados, columns=["Resultado GPT"])
                st.subheader("Resultados da IA:")
                st.dataframe(df_resultados)

                final_df = pd.concat([df, df_resultados], axis=1)
                st.download_button("📅 Baixar Planilha Processada", data=final_df.to_csv(index=False),
                                   file_name="Planilha_Precificada.csv", mime="text/csv")
        else:
            st.error("A planilha deve conter as colunas: Código Cliente, Descrição Curta, Descrição Longa, Unidade, U.F. Dest")
    except Exception as e:
        st.error(f"Erro ao processar a planilha: {str(e)}")
else:
    st.info("Faça o upload de uma planilha válida para começar.")
