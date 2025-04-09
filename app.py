
import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Precificação Automatizada Abecom", layout="wide")
st.title("📦 Precificação Inteligente de Itens MRO - Abecom")
st.markdown("Faça upload da planilha do cliente com as descrições. A IA buscará os preços, NCM, marca e demais dados automaticamente.")

uploaded_file = st.file_uploader("Upload da planilha do cliente (Excel)", type=["xlsx"])

# Simulando o banco de dados da Abecom (estoque, preços e dados técnicos)
banco_abeco = pd.DataFrame({
    "CÓDIGO": ["6205-2Z", "6306-2RS", "6004-ZZ"],
    "PREÇO": [5.78, 9.20, 4.50],
    "NCM": ["84821010", "84821010", "84821010"],
    "MARCA": ["SKF", "FAG", "NSK"],
    "TIPO": ["ROLAMENTO", "ROLAMENTO", "ROLAMENTO"]
})

if uploaded_file:
    try:
        df_base = pd.read_excel(uploaded_file)
        df_base.columns = df_base.columns.str.upper().str.strip()

        if not {"CÓDIGO CLIENTE", "DESCRIÇÃO CURTA", "DESCRIÇÃO LONGA"}.issubset(df_base.columns):
            st.error("A planilha base precisa conter as colunas: CÓDIGO CLIENTE, DESCRIÇÃO CURTA e DESCRIÇÃO LONGA.")
        else:
            def extrair_codigo_padrao(texto):
                padrao = re.search(r"\b\d{3,5}[- ]?(ZZ|2Z|2RS|RS|NR)?\b", str(texto).upper())
                return padrao.group(0).replace(" ", "") if padrao else ""

            df_base["CÓDIGO PADRÃO"] = df_base["DESCRIÇÃO CURTA"].apply(extrair_codigo_padrao)
            df_base.loc[df_base["CÓDIGO PADRÃO"] == "", "CÓDIGO PADRÃO"] = df_base["DESCRIÇÃO LONGA"].apply(extrair_codigo_padrao)

            df_base = df_base.merge(banco_abeco, how="left", left_on="CÓDIGO PADRÃO", right_on="CÓDIGO")
            df_base.drop(columns=["CÓDIGO_y"], inplace=True)
            df_base.rename(columns={"CÓDIGO_x": "CÓDIGO CLIENTE", "PREÇO": "PREÇO CUSTO", "TIPO": "TIPO PRODUTO"}, inplace=True)
            df_base["DESCONTO"] = ""  # campo manual posterior

            st.success("Planilha processada com sucesso! Veja os primeiros resultados abaixo:")
            st.dataframe(df_base.head(10))

            output = BytesIO()
            df_base.to_excel(output, index=False)
            st.download_button("📥 Baixar planilha preenchida (IA)", data=output.getvalue(), file_name="Planilha_Preenchida_Abecom.xlsx")

    except Exception as e:
        st.error(f"Erro ao processar: {e}")
