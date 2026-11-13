"""Make independent Git snapshots and export scope-checked review patches."""

import os
import re
import subprocess
from pathlib import Path, PurePosixPath

MAX_BYTES = 64 * 1024 * 1024
PRIVATE_SUFFIXES = {".key", ".pem", ".p12", ".pfx", ".jks", ".kdbx"}
PRIVATE_NAMES = {
    ".netrc", ".npmrc", ".pypirc", "credentials.json", "id_rsa", "id_ed25519",
    ".gitattributes", "agents.md", "gemini.md",
}


def git(cwd, *args, data=None, allowed=(0,)):
    env = {
        "PATH": os.defpath,
        "HOME": str(Path.home()),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "LC_ALL": "C",
    }
    result = subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false",
         "-c", "core.autocrlf=false", "-C", str(cwd), *args],
        input=data, capture_output=True, env=env, timeout=60, check=False,
    )
    if result.returncode not in allowed:
        raise ValueError(f"Git {args[0]} failed in {cwd.name} (exit {result.returncode})")
    return result.stdout


def path_name(value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("Expected a literal repository-relative path")
    path = PurePosixPath(value)
    if (path.is_absolute() or str(path) != value or ".." in path.parts
            or not path.parts or any(ord(c) < 32 or ord(c) == 127 for c in value)):
        raise ValueError("Expected a normalized repository-relative path")
    return value


def shareable(name):
    path = PurePosixPath(name)
    parts = [part.casefold() for part in path.parts]
    return (not any(p in {".git", ".agents", ".agent", "_agents", "_agent",
                         ".gemini", ".ssh", ".aws"}
                    or p == ".env" or p.startswith(".env.") for p in parts)
            and parts[-1] not in PRIVATE_NAMES
            and path.suffix.lower() not in PRIVATE_SUFFIXES)


def source_tree(cwd):
    root = Path(os.fsdecode(git(cwd, "rev-parse", "--show-toplevel").rstrip(b"\n")))
    commit = git(root, "rev-parse", "--verify", "HEAD^{commit}").decode().strip()
    tree = {}
    for entry in git(root, "ls-tree", "-rlz", commit).split(b"\0"):
        if not entry:
            continue
        header, name = entry.split(b"\t", 1)
        mode, kind, oid, size = header.decode().split()
        tree[os.fsdecode(name)] = (mode, kind, oid, size)
    return root, commit, tree


def choose(tree, requested):
    selected = set()
    for prefix in requested:
        matches = {name for name in tree if name == prefix or name.startswith(prefix + "/")}
        if not matches:
            raise ValueError(f"Share path is absent from the committed tree: {prefix}")
        selected.update(matches)
    safe = []
    for name in sorted(selected):
        mode, kind, oid, size = tree[name]
        if shareable(name) and kind == "blob" and mode in {"100644", "100755"}:
            try:
                path_name(name)
            except ValueError:
                continue
            safe.append((name, mode, oid, int(size)))
    if requested and not safe:
        raise ValueError("None of the selected files are regular, shareable tracked files")
    if sum(size for _, _, _, size in safe) > MAX_BYTES:
        raise ValueError("Selected committed files exceed 64 MiB per worker. Narrow share paths.")
    return safe, len(selected) - len(safe)


def prepare(cwd, root, selected):
    cwd.mkdir(mode=0o700)
    if root is None:
        return
    # Each worker gets its own index, object store, and refs, with no origin.
    git(cwd, "init", "-q", "--template=")
    if selected:
        objects = b"".join((oid + "\n").encode() for _, _, oid, _ in selected)
        stream = git(root, "cat-file", "--batch", data=objects)
        offset = 0
        for name, mode, oid, size in selected:
            header_end = stream.index(b"\n", offset)
            expected = f"{oid} blob {size}".encode()
            if stream[offset:header_end] != expected:
                raise ValueError("Git blob header did not match the committed tree")
            start = header_end + 1
            offset = start + size + 1
            path = cwd / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as handle:
                handle.write(stream[start:start + size])
            path.chmod(0o755 if mode == "100755" else 0o644)
    # Commit raw blob bytes without working-tree attribute filters.
    paths = [name for name, _, _, _ in selected]
    if paths:
        git(cwd, "-c", "core.attributesFile=/dev/null", "--literal-pathspecs",
            "add", "--force", "--pathspec-from-file=-", "--pathspec-file-nul",
            data=b"\0".join(os.fsencode(p) for p in paths) + b"\0")
    git(cwd, "-c", "user.name=delegateH", "-c", "user.email=delegateh@localhost",
        "commit", "-q", "--allow-empty", "-m", "delegateH snapshot")


def collect(cwd, base, writable):
    if base is None:
        if any(cwd.iterdir()):
            return "out_of_scope_changes", []
        return None, []
    if git(cwd, "rev-parse", "HEAD").decode().strip() != base:
        return "worker_committed", []
    changed = git(cwd, "diff", "--no-renames", "--name-only", "-z", "HEAD", "--")
    untracked = git(cwd, "ls-files", "--others", "-z")
    new_paths = {os.fsdecode(p) for p in untracked.split(b"\0") if p}
    paths = sorted({os.fsdecode(p) for p in changed.split(b"\0") if p} | new_paths)
    if set(paths) - set(writable):
        return "out_of_scope_changes", paths
    for name in paths:
        path = cwd / name
        if (path.is_symlink() or any(p.is_symlink() for p in path.parents if p != cwd)
                or (path.exists() and not path.is_file())):
            return "unsupported_change", paths
    return None, paths


def export_patch(cwd, paths):
    for name in paths:
        if (cwd / name).exists():
            git(cwd, "--literal-pathspecs", "add", "-N", "-f", "--", name)
    return git(cwd, "diff", "--binary", "--full-index", "--no-ext-diff",
               "--no-textconv", "--no-renames", "HEAD", "--")
