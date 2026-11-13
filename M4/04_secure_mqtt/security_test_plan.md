# MQTT security test plan

| Test | Expected result | Evidence |
|---|---|---|
| Connect without username/password | Rejected | Broker log + client output |
| Connect with wrong password | Rejected | Broker log + client output |
| Connect with valid credentials, no TLS | Rejected if listener policy requires TLS | Client output |
| Connect with valid credentials over TLS | Accepted | Client output + broker log |
| Validate server certificate | Trusted CA and hostname | Client verification output |

Record broker/client versions, TLS version, certificate issuer/expiry, and date. Do not store secrets in Git.
