# ktgpt_ui_debug.py - Debugging version to trace output steps

import streamlit as st
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="KTGPT Debug", layout="wide")
st.title("🛠 Debugging KTGPT Output Issue")

task = st.text_area("💡 Enter your DevOps task", "deploy keyvault kv-task")
run_button = st.button("Run GPT Analysis")

def call_gpt(prompt, model="gpt-3.5-turbo"):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful DevOps assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ GPT Error: {str(e)}"

if run_button:
    st.write("📤 Submitting prompt to GPT...")
    sample_prompt = f"""You are a DevOps assistant. A user wants to: {task}. 
Provide specific file changes, variable edits, and scripts to execute."""
    st.code(sample_prompt, language="markdown")

    response = call_gpt(sample_prompt)
    st.write("📥 GPT Response:")
    if response:
        st.code(response, language="markdown")
    else:
        st.error("⚠️ GPT returned an empty or null response.")
