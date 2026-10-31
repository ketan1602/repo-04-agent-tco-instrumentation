"""The fields of a scenario run that costing needs, so a report can be rebuilt without calling a model."""
from __future__ import annotations


def compact(result: dict) -> dict:
    direct, harnessed = result["direct"], result["harnessed"]
    steps = harnessed["interventions"]
    return {
        "case": result["case"], "category": result["category"], "paired": result["paired"],
        "direct": {"status": direct["status"], "tokens": direct["tokens"],
                   "violated": direct["violated"], "seconds": direct["seconds"],
                   "model_seconds": direct["model_seconds"]},
        "harnessed": {"status": harnessed["status"], "tokens": harnessed["tokens"],
                      "violated": harnessed["violated"], "passed": harnessed["verdict"]["passed"],
                      "escalated": steps["escalated_to_human"], "vetoed": steps["vetoed"],
                      "retried": steps["retried"], "seconds": harnessed["seconds"],
                      "model_seconds": harnessed["model_seconds"]},
    }
