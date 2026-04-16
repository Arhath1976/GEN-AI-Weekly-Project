import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parent
    data_path = project_root / "data"
    artifacts_path = project_root / "artifacts_smoke"

    if not data_path.exists():
        print("[FAIL] Missing data folder:", data_path)
        return 1

    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_ollama = bool(os.getenv("OLLAMA_MODEL"))

    if not (has_openai or has_ollama):
        print("[FAIL] No LLM configured.")
        print("Set OPENAI_API_KEY or OLLAMA_MODEL, then rerun smoke_test.py")
        return 1

    cmd = [
        sys.executable,
        str(project_root / "knowledgegraph.py"),
        "--data-path",
        str(data_path),
        "--persist-path",
        str(artifacts_path),
        "--graph-max-chunks",
        "20",
        "--query",
        "Who did ACME acquire?",
    ]

    print("[RUN]", " ".join(cmd))
    completed = subprocess.run(cmd, text=True, capture_output=True)

    print("\n[STDOUT]\n" + completed.stdout)
    if completed.stderr.strip():
        print("[STDERR]\n" + completed.stderr)

    if completed.returncode != 0:
        print(f"[FAIL] Script exited with code {completed.returncode}")
        return completed.returncode

    graph_file = artifacts_path / "knowledge_graph.graphml"
    if not graph_file.exists():
        print("[FAIL] Graph artifact missing:", graph_file)
        return 1

    if "BetaLabs" not in completed.stdout:
        print("[WARN] Smoke test ran, but expected entity 'BetaLabs' not found in output.")
    else:
        print("[PASS] Smoke test succeeded and expected entity was found.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
