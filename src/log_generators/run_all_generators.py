import subprocess
import sys
from pathlib import Path

# Run all generators concurrently and wait for completion

def main():
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent.parent

    generators = [
        "basic_log_generator.py",
        "crash_log_generator.py",
        "error_spike_generator.py",
        "k8s_log_generator.py",
        "post_recovery_failure.py",
    ]

    procs = []
    for g in generators:
        path = script_dir / g
        if not path.exists():
            print(f"Generator not found: {path}")
            continue
        print(f"Starting {g}...")
        p = subprocess.Popen([sys.executable, str(path)], cwd=str(repo_root))
        procs.append((g, p))

    # Wait for all to finish
    for name, p in procs:
        rc = p.wait()
        print(f"{name} exited with return code {rc}")


if __name__ == "__main__":
    main()
