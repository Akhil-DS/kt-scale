# ktgpt_ui_demo.py
# Streamlit UI for KTGPT task-based AI assistant

import streamlit as st
import os
import openai
import json
import tempfile

openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="KTGPT - AI DevOps Assistant", layout="wide")
st.title("🤖 KTGPT - AI-Powered DevOps Knowledge Assistant")

with st.sidebar:
    st.header("Configuration")
    repo_path = st.text_input("📂 Local repo path", value="./KTGPT_PoC_Demo")
    task = st.text_area("💡 What do you want to do?", "deploy keyvault kv-task")
    run_button = st.button("🚀 Run GPT Analysis")

MAX_FILES = 8
TARGET_EXTENSIONS = [".bicep", ".yml", ".sh", ".json", ".Dockerfile", ".tf"]

# === Functions ===
def gather_context(path):
    context = []
    for root, _, files in os.walk(path):
        for file in files:
            ext = os.path.splitext(file)[-1].lower()
            if ext in TARGET_EXTENSIONS or 'Dockerfile' in file:
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        context.append({"file": full_path, "content": content[:2000]})
                except Exception as e:
                    st.warning(f"Error reading {full_path}: {e}")
                if len(context) >= MAX_FILES:
                    return context
    return context

def build_prompt(intent, context):
    prompt = f"You are a DevOps knowledge transfer assistant.\nThe user wants to: {intent}\nHere are the relevant code files:\n"
    for file_data in context:
        prompt += f"\n--- FILE: {file_data['file']} ---\n{file_data['content']}"
    prompt += "\n\nExplain step-by-step what to clone, edit, or execute to complete the task."
    return prompt

def call_gpt(prompt):
    try:
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You help developers understand infrastructure code and pipelines."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"❌ GPT Error: {str(e)}"

# === UI Logic ===
if run_button:
    with st.spinner("🔍 Analyzing repository and preparing summary..."):
        context_files = gather_context(repo_path)
        if not context_files:
            st.error("No files found or invalid path.")
        else:
            st.success(f"Loaded {len(context_files)} files.")
            prompt = build_prompt(task, context_files)
            result = call_gpt(prompt)

            st.subheader("📘 AI KT Summary")
            st.markdown(result)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".md", mode="w", encoding="utf-8") as f:
                f.write(result)
                summary_path = f.name

            st.download_button(
                label="💾 Download Summary as Markdown",
                data=result,
                file_name="KTGPT_GPT_Summary.md",
                mime="text/markdown"
            )
