"""Compare observable MCP contracts without judging their design output."""
import argparse
import json
from pathlib import Path
import statistics
import subprocess
from time import perf_counter

parser = argparse.ArgumentParser()
parser.add_argument("--baseline", type=Path, required=True)
parser.add_argument("--competitors", type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
requests = [("landing-mintlify", "landing-mintlify"), ("Vercel infrastructure developer landing page", "landing-vercel"),
            ("landing-page fintech carte banque", "landing-x-money"), ("landing page productivité adhd", "landing-fixa"),
            ("landing page agent marketing analytics", "landing-profound")]

def probe(command, callback):
    with subprocess.Popen(command, cwd=root, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True) as process:
        def rpc(method, params, notification=False):
            message = {"jsonrpc":"2.0", "method":method, "params":params}
            if not notification:
                message["id"] = 1
            start = perf_counter()
            process.stdin.write(json.dumps(message) + "\n")
            process.stdin.flush()
            if notification:
                return
            while line := process.stdout.readline():
                response = json.loads(line)
                if response.get("id") == 1:
                    return response["result"], round((perf_counter()-start)*1000, 2), len(line.encode())
            raise RuntimeError("MCP closed before responding")
        try:
            info = rpc("initialize", {"protocolVersion":"2025-11-25", "capabilities":{},
                                      "clientInfo":{"name":"cosmos-eval", "version":"1"}})[0]
            rpc("notifications/initialized", {}, True)
            listing = rpc("tools/list", {})[0]
            return {**info["serverInfo"], "tools":[x["name"] for x in listing["tools"]], **callback(rpc)}
        finally:
            process.terminate()
            process.wait(timeout=8)

def reference_probe(rpc):
    rows = []
    for query, expected in requests:
        result, latency, size = rpc("tools/call", {"name":"search_patterns","arguments":
            {"query":query,"platform":"web","category":"Landing-page"}})
        hits = [x["id"] for x in result["structuredContent"]["matches"]]
        rows.append(dict(query=query, expected=expected, hits=hits, inTopFive=expected in hits,
                         latencyMs=latency, responseBytes=size))
    return {"cases":rows, "recallAtFive":sum(row["inTopFive"] for row in rows)/len(rows),
            "medianMs":statistics.median(row["latencyMs"] for row in rows)}

result = {"scope":"Retrieval and MCP discovery only. Fixtures target the newly supplied assets.",
          "baseline":probe(["python3","-B",str(args.baseline.resolve())],reference_probe),
          "current":probe(["python3","-B",str(root/"skills/get-started/scripts/server.py")],reference_probe)}
if args.competitors:
    binaries = args.competitors.resolve()/".bin"
    for name, arguments in (("shadcn", ["mcp"]), ("playwright-mcp", ["--headless"])):
        try:
            result[name] = probe([str(binaries/name), *arguments], lambda rpc: {
                "verified":"MCP initialization and tools/list"})
        except (KeyError, OSError, RuntimeError, subprocess.SubprocessError) as error:
            result[name] = {"unverified":str(error)}
(root/"benchmarks/results/mcp-comparison.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
print(json.dumps({name:row.get("recallAtFive", row.get("verified", row.get("unverified")))
                  for name,row in result.items() if isinstance(row,dict)}, ensure_ascii=False))
