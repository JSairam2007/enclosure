"""M4: simple OTA update v1 -> v2 with health check and automatic rollback.
Layout: deploy/releases/<version>/  +  deploy/state.json {"current": "...", "previous": "...", "history": [...]}
Package = zip with manifest.json: {"version", "entry": [...], "health_cmd": [...], "files": {path: sha256}}
Commands:
  python m4/ota/ota.py pack --src m4/ota/example_app --version v1 --out pkgs/v1.zip
  python m4/ota/ota.py install pkgs/v1.zip          # verify hashes, unpack, switch, health check
  python m4/ota/ota.py install pkgs/v2.zip          # if v2's health check fails -> automatic rollback to v1
  python m4/ota/ota.py rollback                     # manual rollback to previous
  python m4/ota/ota.py status
  python m4/ota/ota.py run                          # run the current release's entry (use under the watchdog)
Integrity = SHA-256 per file. This is NOT a signature: anyone who can write the zip can write its manifest.
For a real device sign the manifest (see docs/threat_model.md).
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, time, zipfile

ROOT = "deploy"
REL = os.path.join(ROOT, "releases")
STATE = os.path.join(ROOT, "state.json")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def load_state():
    return json.load(open(STATE)) if os.path.exists(STATE) else {"current": None, "previous": None, "history": []}


def save_state(s):
    os.makedirs(ROOT, exist_ok=True)
    tmp = STATE + ".tmp"
    json.dump(s, open(tmp, "w"), indent=1)
    os.replace(tmp, STATE)  # atomic switch


def log(s, ev, ver):
    s["history"].append({"time": time.strftime("%Y-%m-%d %H:%M:%S"), "event": ev, "version": ver})
    print(f"[ota] {ev} {ver}")


def fix(cmd):
    return [sys.executable if c == "python" else c for c in cmd]


def pack(src, version, out, entry, health):
    files = {}
    for dp, _, fs in os.walk(src):
        for f in fs:
            full = os.path.join(dp, f)
            files[os.path.relpath(full, src).replace("\\", "/")] = sha(full)
    man = {"version": version, "entry": entry, "health_cmd": health, "files": files}
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in files:
            z.write(os.path.join(src, rel), rel)
        z.writestr("manifest.json", json.dumps(man, indent=1))
    print(f"packed {len(files)} files -> {out} ({version})")


def health(version, timeout):
    d = os.path.join(REL, version)
    man = json.load(open(os.path.join(d, "manifest.json")))
    try:
        r = subprocess.run(fix(man["health_cmd"]), cwd=d, timeout=timeout)
        return r.returncode == 0, f"exit {r.returncode}"
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except OSError as e:
        return False, repr(e)


def install(pkg, timeout):
    s = load_state()
    with zipfile.ZipFile(pkg) as z:
        man = json.loads(z.read("manifest.json"))
        ver = man["version"]
        for n in z.namelist():  # zip-slip guard
            if n.startswith("/") or ".." in n.replace("\\", "/").split("/"):
                sys.exit(f"refusing unsafe path in package: {n}")
        dst = os.path.join(REL, ver)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        z.extractall(dst)
    for rel, h in man["files"].items():
        if sha(os.path.join(dst, rel)) != h:
            shutil.rmtree(dst)
            log(s, "rejected_hash_mismatch", ver)
            save_state(s)
            sys.exit(f"hash mismatch on {rel}: package rejected, nothing changed")
    old, older = s["current"], s["previous"]
    s["previous"], s["current"] = old, ver
    log(s, "switched", ver)
    save_state(s)
    ok, why = health(ver, timeout)
    if ok:
        log(s, "health_ok", ver)
        save_state(s)
        return 0
    log(s, f"health_failed ({why})", ver)
    s["current"], s["previous"] = old, older  # restore exactly the state before this install
    log(s, "rolled_back_to", old)
    save_state(s)
    return 1


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    pk = sp.add_parser("pack")
    pk.add_argument("--src", required=True)
    pk.add_argument("--version", required=True)
    pk.add_argument("--out", required=True)
    pk.add_argument("--entry", nargs="+", default=["python", "app.py"])
    pk.add_argument("--health", nargs="+", default=["python", "health.py"])
    ins = sp.add_parser("install")
    ins.add_argument("pkg")
    ins.add_argument("--timeout", type=float, default=30)
    sp.add_parser("rollback")
    sp.add_parser("status")
    sp.add_parser("run")
    a = p.parse_args()
    if a.cmd == "pack":
        pack(a.src, a.version, a.out, a.entry, a.health)
    elif a.cmd == "install":
        sys.exit(install(a.pkg, a.timeout))
    elif a.cmd == "rollback":
        s = load_state()
        if not s["previous"]:
            sys.exit("no previous version to roll back to")
        s["current"], s["previous"] = s["previous"], s["current"]
        log(s, "manual_rollback_to", s["current"])
        save_state(s)
    elif a.cmd == "status":
        print(json.dumps(load_state(), indent=1))
    else:
        s = load_state()
        if not s["current"]:
            sys.exit("nothing installed")
        d = os.path.join(REL, s["current"])
        man = json.load(open(os.path.join(d, "manifest.json")))
        sys.exit(subprocess.call(fix(man["entry"]), cwd=d))


if __name__ == "__main__":
    main()
