"""M4: OTA demo - builds three tiny releases and walks through v1 install, v2 good update,
v3 bad update (health check fails -> automatic rollback to v2), then a manual rollback to v1.
Usage: python M4/ota/demo_ota.py        (works in a temp folder; your deploy/ is untouched)
The 'app' in each release just prints its version; the bad one's health check exits 1.
"""
import os, subprocess, sys, tempfile, textwrap

OTA = os.path.abspath(os.path.join(os.path.dirname(__file__), "ota.py"))
work = tempfile.mkdtemp(prefix="ota_demo_")


def make(ver, healthy):
    d = os.path.join(work, "src_" + ver)
    os.makedirs(d)
    open(os.path.join(d, "app.py"), "w").write(f"print('edge app {ver} running')\n")
    open(os.path.join(d, "health.py"), "w").write(textwrap.dedent(f"""
        import sys
        print('health check {ver}:', {'"ok"' if healthy else '"FAILED (simulated broken model file)"'})
        sys.exit({0 if healthy else 1})
    """))
    return d


def ota(*args):
    print("\n$ ota", " ".join(args))
    return subprocess.call([sys.executable, OTA, *args], cwd=work)


for v, ok in (("v1", True), ("v2", True), ("v3", False)):
    ota("pack", "--src", make(v, ok), "--version", v, "--out", f"pkgs/{v}.zip")
ota("install", "pkgs/v1.zip"); ota("run")
ota("install", "pkgs/v2.zip"); ota("run")
rc = ota("install", "pkgs/v3.zip")
print("install v3 exit code:", rc, "(1 = rolled back)")
ota("run")
ota("rollback"); ota("run")
ota("status")
print("\ndemo folder:", work)
