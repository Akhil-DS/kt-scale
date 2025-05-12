# ktgpt_ui_demo.py (Enhanced for cloud upload or GitHub clone)
import streamlit as st
import os
import openai
import json
import tempfile
import zipfile
import subprocess

#openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="KTGPT - AI DevOps Assistant", layout="wide")
st.title("🤖 KTGPT - AI-Powered DevOps Knowledge Assistant")

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
        res = client.chat.completions.create(
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

# === Sidebar Upload/Clone ===
with st.sidebar:
    st.header("Repo Source")
    repo_zip = st.file_uploader("📁 Upload zipped repo", type=["zip"])
    github_url = st.text_input("🔗 Or enter GitHub repo URL")
    task = st.text_area("💡 What do you want to do?", "deploy keyvault kv-task")
    run_button = st.button("🚀 Run GPT Analysis")

# === Main UI Execution ===
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
        with st.spinner("🔍 Analyzing repository and preparing summary..."):
            context_files = gather_context(repo_path)
            if not context_files:
                st.error("No supported files found.")
            else:
                st.success(f"Loaded {len(context_files)} files.")
                prompt = build_prompt(task, context_files)
                result = call_gpt(prompt)

                st.subheader("📘 AI KT Summary")
                st.markdown(result)

                st.download_button(
                    label="💾 Download Summary as Markdown",
                    data=result,
                    file_name="KTGPT_GPT_Summary.md",
                    mime="text/markdown"
                )
