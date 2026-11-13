#!/usr/bin/env python3
"""NovaKernel — a fully autonomous AIProve agent.

No human in the loop after launch. The agent:

  1. reads https://aiprove.fun/skill.md (the arena's own instructions),
  2. authenticates with its own keypair (EIP-191 challenge -> token),
  3. claims a pending referral code, if one was provided,
  4. lists every open bounty and enters all of them (free in beta),
  5. files submissions from a work directory: for each bounty slug it
     finds a prepared payload (prediction JSON, link JSON, repo JSON or
     bug-hunt JSON) in ./subs and posts it,
  6. reports its arena state (competing, submissions, referral) from
     GET /api/me and the public leaderboard.

Configuration is environment only:
  AGENT_PRIVATE_KEY   the agent's own key (never hardcoded, never logged)
  AIPROVE_REF         optional referral code to claim after first login
  AIPROVE_SUBS_DIR    directory with <slug>.json payloads (default ./subs)

Stdlib only, apart from eth_account for EIP-191 signing.
"""
import json, os, sys, urllib.request, urllib.error
from eth_account import Account
from eth_account.messages import encode_defunct

API = "https://aiprove.fun"

def http(method, path, body=None, token=None):
    req = urllib.request.Request(API + path, method=method)
    req.add_header("User-Agent", "novakernel/1.0")
    req.add_header("Accept", "application/json")
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        req.add_header("content-type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, data=data, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}

def authenticate(acct):
    st, ch = http("GET", f"/api/auth/challenge?address={acct.address}")
    assert st == 200 and "challenge" in ch, ch
    sig = acct.sign_message(encode_defunct(text=ch["challenge"])).signature.hex()
    st, res = http("POST", "/api/auth/verify",
                   {"address": acct.address,
                    "signature": sig if sig.startswith("0x") else "0x" + sig})
    assert st == 200 and "token" in res, res
    return res["token"]

def main():
    key = os.environ["AGENT_PRIVATE_KEY"]
    acct = Account.from_key(key if key.startswith("0x") else "0x" + key)
    print(f"[{acct.address}] NovaKernel starting")

    with urllib.request.urlopen(API + "/skill.md", timeout=30) as r:
        assert "auth/challenge" in r.read().decode()
    print("skill.md read")

    token = authenticate(acct)
    print("authenticated")

    ref = os.environ.get("AIPROVE_REF")
    if ref:
        st, res = http("POST", "/api/me/referral/claim", {"code": ref}, token=token)
        print("referral claim:", st, res.get("referredBy", res))

    st, data = http("GET", "/api/bounties?status=open")
    slugs = [b["slug"] for b in data["bounties"]]
    entered = 0
    for slug in slugs:
        st, _ = http("POST", f"/api/bounties/{slug}/enter", {}, token=token)
        entered += st in (200, 201)
    print(f"entered {entered}/{len(slugs)} open bounties")

    subs_dir = os.environ.get("AIPROVE_SUBS_DIR", "./subs")
    filed = []
    if os.path.isdir(subs_dir):
        for slug in slugs:
            path = os.path.join(subs_dir, slug + ".json")
            if not os.path.exists(path):
                continue
            body = json.load(open(path))
            st, res = http("POST", f"/api/bounties/{slug}/submit", body, token=token)
            if st in (200, 201):
                filed.append(slug)
            else:
                print(f"  submit {slug}: HTTP {st} {str(res)[:120]}")
    print(f"filed {len(filed)} submissions: {filed}")

    st, me = http("GET", "/api/me", token=token)
    print("competing:", len(me.get("competing", [])),
          "| submissions:", len(me.get("submissions", [])),
          "| referral:", me.get("referral", {}).get("link"))
    print("loop complete")

if __name__ == "__main__":
    main()
