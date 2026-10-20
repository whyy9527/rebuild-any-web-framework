"""Run an explicit evaluator and retain its evidence; never assigns an aesthetic score."""
import hashlib
import math
import os
import signal
import subprocess
import tempfile
import time
from pathlib import Path
from capabilities.exploration.storage import digest


IGNORED = {'.git', '.codex', '.build', '.venv', 'venv', 'node_modules', '__pycache__',
           'artifacts', 'test-results', 'playwright-report', 'dist', 'build', '.pytest_cache', '.mypy_cache', '.ruff_cache'}
SOURCE_SUFFIXES = {'.py', '.swift', '.ts', '.tsx', '.js', '.mjs', '.cjs', '.toml', '.html', '.css'}


def input_manifest(root, paths):
    """Hash declared files/directories, including fixtures; never follow outside links."""
    root = Path(root).resolve()
    if not isinstance(paths, list) or not paths or any(not isinstance(p, str) or not p for p in paths):
        raise ValueError('nonempty relative acceptance paths required')
    files = {}
    for name in paths:
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts or name == '.':
            raise ValueError('acceptance paths must be relative and inside workspace')
        selected = root / relative
        if not selected.resolve().is_relative_to(root):
            raise ValueError('acceptance link escapes workspace')
        if selected.is_symlink() and selected.is_dir():
            raise ValueError('declare the real acceptance directory instead of a directory link')
        if not selected.exists():
            files[relative.as_posix()] = None  # Detect later creation/deletion too.
            continue
        candidates = selected.rglob('*') if selected.is_dir() else [selected]
        for path in sorted(candidates):
            if '__pycache__' in path.relative_to(root).parts or path.suffix in {'.pyc', '.pyo'} or path.name == '.DS_Store':
                continue
            if not path.resolve().is_relative_to(root):
                raise ValueError('acceptance link escapes workspace')
            if path.is_symlink() and path.is_dir():
                raise ValueError('declare the real acceptance directory instead of a directory link')
            if path.is_file():
                files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files


def manifest(root):
    root = Path(root).resolve()
    files = {}
    for directory, subdirs, names in os.walk(root, followlinks=False):
        subdirs[:] = sorted(name for name in subdirs if name not in IGNORED and not (Path(directory) / name).is_symlink())
        for name in sorted(names):
            path = Path(directory) / name
            if (path.suffix in SOURCE_SUFFIXES or name in {'package.json', 'package-lock.json'}) and path.resolve().is_relative_to(root):
                files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files


def evaluate(root, command, timeout=30, environment=None, input_text=None):
    if not command or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("explicit command and positive finite timeout required")
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError("workspace must be an existing directory")
    files = manifest(root)
    started = time.monotonic()
    exit_code, status = None, "unavailable"
    with tempfile.TemporaryFile() as stream, tempfile.TemporaryFile() as input_stream:
        if input_text is not None:
            input_stream.write(input_text.encode())
            input_stream.seek(0)
        process = None
        try:
            process = subprocess.Popen(command, cwd=root, stdin=input_stream if input_text is not None else subprocess.DEVNULL,
                                       stdout=stream, stderr=stream, start_new_session=True,
                                       env=None if environment is None else {**os.environ,**environment})
            try:
                exit_code = process.wait(timeout=timeout)
                status = "pass" if exit_code == 0 else "fail"
            except subprocess.TimeoutExpired:
                status = "timeout"
        except OSError as error:
            stream.write(str(error).encode())
        finally:
            if process is not None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
        stream.seek(0, 2)
        output_bytes = stream.tell()
        stream.seek(0)
        output = stream.read(65536).decode(errors="replace").replace(str(root), "<workspace>")
    integrity = "verified" if manifest(root) == files else "source_changed"
    if integrity != "verified":
        status = "invalid"
    return {
        "command": command,
        "source_files": files,
        "source_digest": digest(files),
        "integrity": integrity,
        "evaluator_digest": digest({"command": command, "tests": {k: v for k, v in files.items() if k.startswith("tests/")}}),
        "exit_code": exit_code,
        "status": status,
        "output": output,
        "output_bytes": output_bytes,
        "output_truncated": output_bytes > 65536,
        "output_sha256": hashlib.sha256(output.encode()).hexdigest(),
        "wall_seconds": round(time.monotonic() - started, 6),
    }
