"""Generate anonymized trial sheets from fixed prompts. Does not generate scores."""
import argparse
import json
import random
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--model", required=True)
parser.add_argument("--host", required=True)
parser.add_argument("--seed", type=int, required=True)
parser.add_argument("--runs", type=int, choices=(1, 2, 3), default=3)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
scenarios = json.loads(Path(__file__).with_name("scenarios.json").read_text())
trials = [{"model":args.model, "host":args.host, "split":split, "case":case["id"], "prompt":case["brief"],
           "domain":case["domain"], "arm":arm, "repeat":index+1, "status":"unverified",
           "score":None, "reviewer":None, "artifacts":[], "inputTokens":None, "outputTokens":None,
           "durationMs":None, "toolCalls":None, "cost":None}
          for split, cases in scenarios.items() for case in cases for arm in "ABCD"
          for index in range(args.runs)]
random.Random(args.seed).shuffle(trials)
args.output.mkdir(parents=True, exist_ok=True)
for i, trial in enumerate(trials, 1):
    trial["runId"] = f"trial-{i:04}"
for name, rows in (("operator.json", trials), ("reviewer.json", [
    {k:v for k,v in row.items() if k not in {"arm","repeat"}} for row in trials
])):
    (args.output/name).write_text(json.dumps(rows, ensure_ascii=False, indent=2)+"\n")
print(f"Prepared {len(trials)} unscored trials with arm labels removed from reviewer sheet")
