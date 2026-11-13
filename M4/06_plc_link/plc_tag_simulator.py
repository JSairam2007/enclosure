"""Local PLC-tag simulation; does not connect to a PLC."""
import argparse, json
from datetime import datetime, timezone

p=argparse.ArgumentParser()
p.add_argument("--class", dest="classification", choices=["SEALED","OPEN"], required=True)
args=p.parse_args()
tag={"CartonDetected":True,"SealStatus":args.classification,
     "RejectRequest":args.classification=="OPEN",
     "updated_at":datetime.now(timezone.utc).isoformat(),
     "source":"LOCAL_SIMULATOR_NOT_PLC"}
print(json.dumps(tag,indent=2))
