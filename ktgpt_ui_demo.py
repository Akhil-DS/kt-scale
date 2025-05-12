# openai_gpt_test.py — standalone script to verify OpenAI client call

import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

prompt = "You are a helpful assistant. What are the key steps to deploy a Key Vault using Bicep?"

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You help with cloud infrastructure."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.2
)

print("=== GPT Response ===")
print(response.choices[0].message.content.strip())
