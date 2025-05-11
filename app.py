import streamlit as st
import json

st.title("KTGPT PoC - DevOps Discovery Tool")

uploaded_file = st.file_uploader("Upload KTGPT JSON output", type=["json"])

if uploaded_file:
    data = json.load(uploaded_file)
    st.write(f"📦 {len(data)} findings:")
    for entry in data:
        st.markdown(f"**[{entry['category']}]** `{entry['file']} (Line {entry['line']})`  
{entry['content']}")
