import os
import re
import json
from rich import print

PATTERNS = {
    "Tool Version": [
        r"nodeVersion\s*[:=]\s*[\"']?\d{2}[\.x\"']?",
        r"FROM\s+node:?\d{2}[\.x]?",
        r"nvm use \d{2}",
        r"python\s?\d\.\d+",
        r"terraform\s?\d\.\d+",
        r"az\s+--version"
    ],
    "Secrets / Credentials": [
        r"client(Id|Secret)|tenant(Id)?",
        r"AZURE_\w+_KEY",
        r"password\s*=\s*[\"']?.+[\"']?"
    ],
    "Pipeline Tasks": [
        r"- task:\s*[\w\-\.]+",
        r"script:\s*.+",
        r"job:\s*[\w\-]+"
    ],
    "IaC Modules": [
        r"module\s+\w+\s*=\s*\{",
        r"resource\s+\w+\s+\"\w+\"\s*\{",
        r"parameter\s+\"?\w+\"?\s*:"
    ],
    "Documentation Keywords": [
        r"Knowledge Transfer",
        r"Dependencies:",
        r"Owner:"
    ]
}

TARGET_EXTENSIONS = [".yml", ".yaml", ".json", ".sh", ".bicep", ".tf", ".Dockerfile", ".js", ".ts", ".py", ".md", ".txt"]

def scan_repo(path):
    results = []
    for root, _, files in os.walk(path):
        for file in files:
            full_path = os.path.join(root, file)
            ext = os.path.splitext(file)[-1].lower()
            if ext in TARGET_EXTENSIONS or 'Dockerfile' in file:
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            for category, patterns in PATTERNS.items():
                                for pat in patterns:
                                    if re.search(pat, line):
                                        results.append({
                                            "category": category,
                                            "file": full_path,
                                            "line": i + 1,
                                            "content": line.strip()
                                        })
                except Exception as e:
                    print(f"[red]Error reading {full_path}: {e}[/red]")
    return results

if __name__ == "__main__":
    scan_path = input("🔍 Enter path to scan (local repo): ").strip()
    results = scan_repo(scan_path)
    if not results:
        print("[green]✅ No issues or patterns found.[/green]")
    else:
        print(f"[blue]\n📘 Found {len(results)} issues:[/blue]")
        for r in results:
            print(f"[yellow][{r['category']}][/yellow] {r['file']} (Line {r['line']}): {r['content']}")
        with open("ktgpt_output.json", "w") as f:
            json.dump(results, f, indent=2)
        print("\n📝 Output written to ktgpt_output.json")
