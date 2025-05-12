# ktgpt_ui_gitfix.py — GPT 3.5/4 toggle, cost estimator, GitHub zip fallback

import streamlit as st
import os
import zipfile
import tempfile
import subprocess
from openai import OpenAI
import tiktoken
import platform

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
st.set_page_config(page_title="KTGPT Final", layout="wide")
st.title("✅ KTGPT - Clean Output + Cost + Git Fix")

# Sidebar
with st.sidebar:
    task = st.text_area("💡 Task", "deploy keyvault kv-task")
    model = st.radio("🤖 GPT Model", ["gpt-3.5-turbo", "gpt-4"])
    show_cost = st.checkbox("💸 Estimate token usage", value=True)
    repo_zip = st.file_uploader("📁 Upload zipped repo", type=["zip"])
    github_url = st.text_input("🔗 Or enter GitHub repo URL")
    run_button = st.button("🚀 Run")

def gather_files(path, max_files=10):
    extensions = [".bicep", ".yml", ".sh", ".json", ".Dockerfile", ".tf"]
    collected = []
    for root, _, files in os.walk(path):
        for file in files:
            if any(file.endswith(ext) or "Dockerfile" in file for ext in extensions):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        collected.append({"file": full_path, "content": content[:1500]})
                        if len(collected) >= max_files:
                            return collected
                except:
                    continue
    return collected

def build_prompt(task, files):
    prompt = f"User wants to: {task}\n\nAnalyze the code below and output only: changes needed, parameter edits, file names, script steps."
    for f in files:
        prompt += f"\n\n--- FILE: {f['file']} ---\n{f['content']}"
    return prompt

def estimate_tokens(prompt, model):
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(prompt))

def call_gpt(prompt, model="gpt-3.5-turbo"):
    try:
        res = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a DevOps assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ GPT Error: {str(e)}"

if run_button:
    tmp = tempfile.TemporaryDirectory()
    repo_path = None

    if repo_zip:
        with open(os.path.join(tmp.name, "repo.zip"), "wb") as f:
            f.write(repo_zip.read())
        with zipfile.ZipFile(os.path.join(tmp.name, "repo.zip")) as z:
            z.extractall(tmp.name)
        repo_path = tmp.name
        st.success("✅ ZIP extracted.")

    elif github_url:
        try:
            git_exe = "git.exe" if platform.system() == "Windows" else "git"
            subprocess.run([git_exe, "clone", github_url, tmp.name], check=True)
            repo_path = tmp.name
            st.success("✅ Repo cloned.")
        except Exception as e:
            st.error(f"❌ Git error: {e}")
            st.stop()

    if repo_path:
        files = gather_files(repo_path)
        if not files:
            st.error("No supported files found.")
            st.stop()

        prompt = build_prompt(task, files)

        if show_cost:
            token_count = estimate_tokens(prompt, model)
            rate = 0.0015 if model == "gpt-3.5-turbo" else 0.03
            est = round(token_count * rate / 1000, 4)
            st.info(f"🔢 Tokens: {token_count} | Est. cost: ${est}")

        with st.spinner("Calling GPT..."):
            result = call_gpt(prompt, model)

        st.subheader("📘 GPT Output")
        st.markdown(result)
        st.download_button("💾 Download", result, "ktgpt_summary.md", "text/markdown")
