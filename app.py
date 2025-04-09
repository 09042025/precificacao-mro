
import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Precificação Automatizada Abecom", layout="wide")
st.title("📦 Precificação Inteligente de Itens MRO - Abecom")
st.markdown("Faça upload da planilha do cliente com os dados. A IA buscará os preços, NCM, marca e demais dados automaticamente.")

uploaded_file = st.file_uploader("Upload da planilha do cliente (Excel)", type=["xlsx"])

if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        aba_estoque = None

        for aba in xls.sheet_names:
            if "estoque" in aba.lower():
                aba_estoque = aba
                break

        if not aba_estoque:
            st.error("A planilha não possui uma aba de estoque. Verifique se há uma aba com o nome contendo 'estoque'.")
        else:
            df_base = pd.read_excel(xls, sheet_name=0)
            df_estoque = pd.read_excel(xls, sheet_name=aba_estoque)

            df_base.columns = df_base.columns.str.upper().str.strip()
            df_estoque.columns = df_estoque.columns.str.upper().str.strip()

            if not {"CÓDIGO CLIENTE", "DESCRIÇÃO CURTA", "DESCRIÇÃO LONGA"}.issubset(df_base.columns):
                st.error("A planilha base precisa conter as colunas: CÓDIGO CLIENTE, DESCRIÇÃO CURTA e DESCRIÇÃO LONGA.")
            else:
                def extrair_codigo_padrao(texto):
                    padrao = re.search(r"\b\d{3,5}[- ]?(ZZ|2Z|2RS|RS|NR)?\b", str(texto).upper())
                    return padrao.group(0).replace(" ", "") if padrao else ""

                df_base["CÓDIGO PADRÃO"] = df_base["DESCRIÇÃO CURTA"].apply(extrair_codigo_padrao)
                df_base.loc[df_base["CÓDIGO PADRÃO"] == "", "CÓDIGO PADRÃO"] = df_base["DESCRIÇÃO LONGA"].apply(extrair_codigo_padrao)

                def buscar_preco(codigo):
                    if not codigo:
                        return None
                    filtro = df_estoque[df_estoque["CÓDIGO"].astype(str).str.contains(codigo, na=False)]
                    return filtro.head(1)["PREÇO"].values[0] if not filtro.empty else None

                df_base["PREÇO CUSTO"] = df_base["CÓDIGO PADRÃO"].apply(buscar_preco)

                def definir_ncm(codigo):
                    if "620" in codigo:
                        return "84821010"
                    elif "630" in codigo:
                        return "84822010"
                    return ""

                df_base["NCM"] = df_base["CÓDIGO PADRÃO"].apply(definir_ncm)
                df_base["MARCA"] = df_base["DESCRIÇÃO LONGA"].str.extract(r"\b(SKF|FAG|TIMKEN|NSK|NTN)\b", expand=False)
                df_base["TIPO PRODUTO"] = df_base["DESCRIÇÃO LONGA"].apply(lambda x: "ROLAMENTO" if "ROLAMENTO" in str(x).upper() else "")
                df_base["DESCONTO"] = ""  # campo para preenchimento manual posterior

                st.success("Planilha processada com sucesso! Veja os primeiros resultados abaixo:")
                st.dataframe(df_base.head(10))

                output = BytesIO()
                df_base.to_excel(output, index=False)
                st.download_button("📥 Baixar planilha preenchida (parcial)", data=output.getvalue(), file_name="Planilha_Preenchida_Abecom.xlsx")

    except Exception as e:
        st.error(f"Erro ao processar: {e}")
