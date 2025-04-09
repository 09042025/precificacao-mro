
import streamlit as st
import pandas as pd
import re
import openai
from io import BytesIO

st.set_page_config(page_title="Precificação Automatizada Abecom", layout="wide")
st.title("📦 Precificação Inteligente de Itens MRO - Abecom")
st.markdown("Faça upload da planilha do cliente com os dados. A IA buscará os preços, NCM, marca e demais dados automaticamente.")

# Configure sua chave da API da OpenAI
api_key = st.secrets.get("OPENAI_API_KEY", "")
if not api_key:
    st.error("A chave da API OpenAI não foi encontrada. Verifique se está definida em st.secrets.")
else:
    openai.api_key = api_key

def consultar_agente(descricao_curta, descricao_longa):
    prompt = f"""
    Você é um especialista técnico em itens MRO da Abecom. Com base na descrição curta e longa a seguir, informe:
    - Código padrão do item (ex: 6205-2Z)
    - NCM sugerido
    - Tipo de produto (ex: Rolamento)
    - Marca provável

    Descrição curta: {descricao_curta}
    Descrição longa: {descricao_longa}
    """
    try:
        resposta = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return resposta['choices'][0]['message']['content']
    except Exception as e:
        st.warning(f"Falha na consulta GPT: {e}")
        return "FALHA GPT"

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
            st.warning("Nenhuma aba com nome contendo 'estoque' foi encontrada no arquivo. Usando base interna da IA como fallback.")
            dados_estoque = {
                "CÓDIGO": ["6205-2Z", "6305-2RS"],
                "PREÇO": [5.78, 8.45]
            }
            df_estoque = pd.DataFrame(dados_estoque)
        else:
            df_estoque = pd.read_excel(xls, sheet_name=aba_estoque)

        df_base = pd.read_excel(xls, sheet_name=0)
        df_base.columns = df_base.columns.str.upper().str.strip()
        df_estoque.columns = df_estoque.columns.str.upper().str.strip()

        if not {"CÓDIGO CLIENTE", "DESCRIÇÃO CURTA", "DESCRIÇÃO LONGA"}.issubset(df_base.columns):
            st.error("A planilha base precisa conter as colunas: CÓDIGO CLIENTE, DESCRIÇÃO CURTA e DESCRIÇÃO LONGA.")
        else:
            respostas = []
            progress = st.progress(0)

            for i, row in df_base.iterrows():
                st.write(f"Consultando IA para: {row['DESCRIÇÃO CURTA']} | {row['DESCRIÇÃO LONGA']}")
                resposta = consultar_agente(row["DESCRIÇÃO CURTA"], row["DESCRIÇÃO LONGA"])
                respostas.append(resposta)
                progress.progress((i + 1) / len(df_base))

            df_base["RESPOSTA GPT"] = respostas

            def extrair_codigo_padrao(texto):
                padrao = re.search(r"\b\d{3,5}[- ]?(ZZ|2Z|2RS|RS|NR)?\b", str(texto).upper())
                return padrao.group(0).replace(" ", "") if padrao else ""

            df_base["CÓDIGO PADRÃO"] = df_base["RESPOSTA GPT"].apply(lambda x: extrair_codigo_padrao(x))

            def buscar_preco(codigo):
                if not codigo:
                    return None
                filtro = df_estoque[df_estoque["CÓDIGO"].astype(str).str.contains(codigo, na=False)]
                return filtro.head(1)["PREÇO"].values[0] if not filtro.empty else None

            df_base["PREÇO CUSTO"] = df_base["CÓDIGO PADRÃO"].apply(buscar_preco)

            def definir_ncm(gpt_resp):
                padrao_ncm = re.search(r"\bNCM:?\s*(\d{8})\b", gpt_resp)
                return padrao_ncm.group(1) if padrao_ncm else ""

            def extrair_marca(gpt_resp):
                padrao_marca = re.search(r"\bSKF|FAG|TIMKEN|NSK|NTN\b", gpt_resp.upper())
                return padrao_marca.group(0) if padrao_marca else ""

            def extrair_tipo(gpt_resp):
                padrao_tipo = re.search(r"(?i)tipo.*?:\s*(\w+)", gpt_resp)
                return padrao_tipo.group(1).upper() if padrao_tipo else ""

            df_base["NCM"] = df_base["RESPOSTA GPT"].apply(definir_ncm)
            df_base["MARCA"] = df_base["RESPOSTA GPT"].apply(extrair_marca)
            df_base["TIPO PRODUTO"] = df_base["RESPOSTA GPT"].apply(extrair_tipo)
            df_base["DESCONTO"] = ""

            st.success("Planilha processada com sucesso! Veja os primeiros resultados abaixo:")
            st.dataframe(df_base.head(10))

            output = BytesIO()
            df_base.to_excel(output, index=False)
            st.download_button("📥 Baixar planilha preenchida (parcial)", data=output.getvalue(), file_name="Planilha_Preenchida_Abecom.xlsx")

    except Exception as e:
        st.error(f"Erro ao processar: {e}")
