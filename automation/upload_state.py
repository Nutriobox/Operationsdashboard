"""
Upload secrets/pp_storage_state.json to S3 so the AWS browser Lambdas pick up a
freshly-exported login session. Pure stdlib SigV4 PUT — no boto3/awscli needed.
Credentials come from secrets/aws-refresh.env (git-ignored), a scoped IAM user
that can ONLY PutObject this one object.

    python upload_state.py
"""
import sys, hashlib, hmac, datetime, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
ENVF = ROOT / "secrets" / "aws-refresh.env"
STATE = ROOT / "secrets" / "pp_storage_state.json"


def _env():
    d = {}
    for line in ENVF.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def _sign(key, msg):
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()


def main() -> int:
    e = _env()
    ak = e["AWS_REFRESH_ACCESS_KEY_ID"]
    sk = e["AWS_REFRESH_SECRET_ACCESS_KEY"]
    region = e["AWS_REFRESH_REGION"]
    bucket = e["AWS_REFRESH_BUCKET"]
    key = e["AWS_REFRESH_KEY"]
    if not STATE.exists():
        print("ERROR: secrets/pp_storage_state.json not found — run EXPORT first.")
        return 1
    body = STATE.read_bytes()
    host = f"{bucket}.s3.{region}.amazonaws.com"
    service = "s3"
    now = datetime.datetime.now(datetime.timezone.utc)
    amzdate = now.strftime("%Y%m%dT%H%M%SZ")
    datestamp = now.strftime("%Y%m%d")
    payload_hash = hashlib.sha256(body).hexdigest()
    canonical_uri = "/" + key
    canonical_headers = (f"host:{host}\n"
                         f"x-amz-content-sha256:{payload_hash}\n"
                         f"x-amz-date:{amzdate}\n")
    signed_headers = "host;x-amz-content-sha256;x-amz-date"
    canonical_request = "\n".join(["PUT", canonical_uri, "",
                                   canonical_headers, signed_headers, payload_hash])
    scope = f"{datestamp}/{region}/{service}/aws4_request"
    string_to_sign = "\n".join(["AWS4-HMAC-SHA256", amzdate, scope,
                                hashlib.sha256(canonical_request.encode()).hexdigest()])
    kdate = _sign(("AWS4" + sk).encode(), datestamp)
    kregion = _sign(kdate, region)
    kservice = _sign(kregion, service)
    ksigning = _sign(kservice, "aws4_request")
    signature = hmac.new(ksigning, string_to_sign.encode(), hashlib.sha256).hexdigest()
    auth = (f"AWS4-HMAC-SHA256 Credential={ak}/{scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}")
    req = urllib.request.Request(f"https://{host}{canonical_uri}", data=body, method="PUT",
                                 headers={"Host": host, "x-amz-date": amzdate,
                                          "x-amz-content-sha256": payload_hash,
                                          "Authorization": auth,
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            print(f"uploaded {len(body)} bytes -> s3://{bucket}/{key}  (HTTP {r.status})")
        return 0
    except Exception as ex:
        print(f"UPLOAD FAILED: {ex}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
