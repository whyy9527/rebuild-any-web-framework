"""Candidate-specific storage acceptance, not an original Duolingo rule."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CASES = [
    ("invalid_json", "broken", "course_unavailable"),
    ("empty_object", "{}", "course_unavailable"),
    ("null_completed_courses", '{"completedCourses":null}', "course_unavailable"),
    ("negative_hearts", '{"completedCourses":[],"hearts":-1}', "course_unavailable"),
    ("legacy_empty", '{"completedCourses":[]}', "course_path"),
]

def main():
    build = subprocess.run(["swift", "build", "--package-path", "projects/education-swift", "--product", "LingoSeed"], cwd=ROOT, capture_output=True, text=True, timeout=120)
    if build.returncode:
        print(json.dumps({"status":"unavailable", "reason":"build failed", "output":(build.stdout+build.stderr).replace(str(ROOT),"<workspace>")}))
        return 2
    binary = ROOT / "projects/education-swift/.build/debug/LingoSeed"
    results = []
    with tempfile.TemporaryDirectory(prefix="lingoseed-progress-check-") as directory:
        directory = Path(directory)
        probe = directory / "probe"
        compile_probe = subprocess.run(["swiftc", str(ROOT / "projects/duolingo-web/progress-ui-probe.swift"), "-o", str(probe)], capture_output=True, text=True, timeout=60)
        if compile_probe.returncode:
            print(json.dumps({"status":"unavailable", "reason":"probe compilation failed", "output":compile_probe.stderr.replace(str(ROOT),"<workspace>")}))
            return 2
        for name, content, expected in CASES:
            progress = directory / (name + ".json")
            progress.write_text(content)
            child = subprocess.Popen([str(binary), "--fixture", str(ROOT / "projects/duolingo-web/fixture-v2.json"), "--progress", str(progress)], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                read = subprocess.run([str(probe), str(child.pid)], capture_output=True, text=True, timeout=25)
                observed = read.stdout.strip()
                unchanged = progress.read_bytes() == content.encode()
                status = "unavailable" if read.returncode else "pass" if observed == expected and unchanged else "fail"
                results.append({"case":name,"expected_screen":expected,"observed_screen":observed,"file_unchanged":unchanged,"status":status})
            finally:
                if child.poll() is None:
                    child.terminate()
                    try: child.wait(timeout=5)
                    except subprocess.TimeoutExpired: child.kill(); child.wait(timeout=5)
    report = {"kind":"candidate_progress_native_ui", "binary_sha256":hashlib.sha256(binary.read_bytes()).hexdigest(), "results":results}
    print(json.dumps(report, separators=(",", ":")))
    return 2 if any(r["status"] == "unavailable" for r in results) else 0 if all(r["status"] == "pass" for r in results) else 1

if __name__ == "__main__":
    raise SystemExit(main())
