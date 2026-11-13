"""M4: create a self-signed CA + server certificate for Mosquitto TLS, and render mosquitto.conf.
Usage: python m4/mosquitto/gen_certs.py [--host localhost] [--days 365]
Writes m4/mosquitto/certs/{ca.crt,ca.key,server.crt,server.key} and m4/mosquitto/mosquitto.conf
(absolute paths, so mosquitto can be started from any folder). Keys never leave this machine:
certs/ is in .gitignore. Then create the password file (you choose the password, it is not stored here):
  mosquitto_passwd -c m4/mosquitto/passwd edgeai
"""
import argparse, datetime, ipaddress, os
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

p = argparse.ArgumentParser()
p.add_argument("--host", default="localhost", help="name clients use to reach the broker")
p.add_argument("--ip", action="append", default=["127.0.0.1"], help="extra IP SANs (repeatable)")
p.add_argument("--days", type=int, default=365)
a = p.parse_args()
here = os.path.dirname(os.path.abspath(__file__))
cd = os.path.join(here, "certs")
os.makedirs(cd, exist_ok=True)
now = datetime.datetime.now(datetime.timezone.utc)


def key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def save(obj, name, private=False):
    path = os.path.join(cd, name)
    data = obj.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL,
                             serialization.NoEncryption()) if private else obj.public_bytes(serialization.Encoding.PEM)
    open(path, "wb").write(data)


ca_key = key()
ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "edgeai-local-ca")])
ca = (x509.CertificateBuilder().subject_name(ca_name).issuer_name(ca_name).public_key(ca_key.public_key())
      .serial_number(x509.random_serial_number()).not_valid_before(now)
      .not_valid_after(now + datetime.timedelta(days=a.days))
      .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
      .add_extension(x509.KeyUsage(digital_signature=True, key_cert_sign=True, crl_sign=True, content_commitment=False,
                                   key_encipherment=False, data_encipherment=False, key_agreement=False,
                                   encipher_only=False, decipher_only=False), critical=True)
      .sign(ca_key, hashes.SHA256()))
srv_key = key()
sans = [x509.DNSName(a.host)] + [x509.IPAddress(ipaddress.ip_address(i)) for i in a.ip]
srv = (x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, a.host)]))
       .issuer_name(ca_name).public_key(srv_key.public_key()).serial_number(x509.random_serial_number())
       .not_valid_before(now).not_valid_after(now + datetime.timedelta(days=a.days))
       .add_extension(x509.SubjectAlternativeName(sans), critical=False)
       .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
       .add_extension(x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
       .sign(ca_key, hashes.SHA256()))
save(ca, "ca.crt"); save(ca_key, "ca.key", True); save(srv, "server.crt"); save(srv_key, "server.key", True)

tpl = open(os.path.join(here, "mosquitto.conf.template")).read()
conf = tpl.replace("{{DIR}}", here.replace("\\", "/"))
open(os.path.join(here, "mosquitto.conf"), "w").write(conf)
print("wrote certs to", cd)
print("wrote", os.path.join(here, "mosquitto.conf"))
print("next: mosquitto_passwd -c m4/mosquitto/passwd edgeai   (choose a password)")
