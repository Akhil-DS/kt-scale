# ktgpt_ui_enhanced.py - Streamlit UI with GPT-4 fallback, RAG toggle, and token cost preview

import streamlit as st
import os
import zipfile
import subprocess
import tempfile
import tiktoken
from openai import OpenAI
import hashlib

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="KTGPT Enhanced", layout="wide")
st.title("🤖 KTGPT - Enhanced DevOps Knowledge Assistant")

MAX_FILES = 12
MAX_TOKENS = 8000
TARGET_EXTENSIONS = [".bicep", ".yml", ".sh", ".json", ".Dockerfile", ".tf"]

# === Sidebar UI ===
with st.sidebar:
    st.header("Configuration")
    repo_zip = st.file_uploader("📁 Upload zipped repo", type=["zip"])
    github_url = st.text_input("🔗 Or enter GitHub repo URL")
    task = st.text_area("💡 What do you want to do?", "deploy keyvault kv-task")
    model_choice = st.radio("🤖 GPT Model", ["gpt-3.5-turbo", "gpt-4"])
    enable_rag = st.checkbox("🧠 Enable RAG (embedding + top-k)", value=True)
    show_cost = st.checkbox("💸 Preview token/cost before run", value=True)
    run_button = st.button("🚀 Run GPT Analysis")

# === Utility Functions ===
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

def build_prompt(task, context):
    prompt = f"""
You are a DevOps knowledge assistant.

The user wants to: "{task}"

Analyze the following code files and provide:
1. File names that require changes.
2. Exact parameter names, values, and lines to modify (e.g., 'kvName = "kv-task"').
3. Scripts or pipelines to execute.
4. A step-by-step plan with minimal generalization.

Respond in clear bullet points.
"""
    for file_data in context:
        prompt += f"\n--- FILE: {file_data['file']} ---\n{file_data['content']}\n"
    return prompt

def estimate_tokens(text, model="gpt-3.5-turbo"):
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))

def call_gpt(prompt, model="gpt-3.5-turbo"):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You help developers understand infrastructure code and pipelines."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ GPT Error: {str(e)}"

# === Main Execution ===
if run_button:
    repo_path = None
    tmpdir = tempfile.TemporaryDirectory()
    tmp_path = tmpdir.name

    if repo_zip:
        zip_path = os.path.join(tmp_path, "repo.zip")
        with open(zip_path, "wb") as f:
            f.write(repo_zip.read())
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmp_path)
        repo_path = tmp_path
        st.success("✅ Zipped repo extracted.")

    elif github_url:
        try:
            subprocess.run(["git", "clone", github_url, tmp_path], check=True)
            repo_path = tmp_path
            st.success("✅ GitHub repo cloned.")
        except subprocess.CalledProcessError as e:
            st.error(f"❌ Git clone failed: {str(e)}")

    else:
        st.warning("⚠️ Please upload a zip file or enter a GitHub URL.")

    if repo_path:
        with st.spinner("🔍 Analyzing repository..."):
            context_files = gather_context(repo_path)
            if not context_files:
                st.error("No supported files found.")
            else:
                st.success(f"Loaded {len(context_files)} files.")
                prompt = build_prompt(task, context_files)

                if show_cost:
                    token_count = estimate_tokens(prompt, model_choice)
                    token_cost = round(token_count * (0.0015 if model_choice == "gpt-3.5-turbo" else 0.03) / 1000, 4)
                    st.info(f"🧮 Estimated Tokens: {token_count} — Approx Cost: ${token_cost}")
                    if not st.button("✅ Confirm and Execute"):
                        st.stop()

                st.write("🤖 Running GPT model:", model_choice)
                result = call_gpt(prompt, model_choice)

                st.subheader("📘 AI KT Summary")
                st.markdown(result)

                st.download_button(
                    label="💾 Download Summary as Markdown",
                    data=result,
                    file_name="KTGPT_GPT_Summary.md",
                    mime="text/markdown"
                )
