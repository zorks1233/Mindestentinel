# generate_reports 
#!/usr/bin/env python3
"""
Generate a simple system report (JSON) including diagnostics and counts.
"""
import json
from src.admin.diagnostics import run_diagnostics
from src.core.knowledge_base import KnowledgeBase
from pathlib import Path
from datetime import datetime

def main(out="reports/report.json"):
    report = {}
    report["diagnostics"] = run_diagnostics()
    kb = KnowledgeBase()
    report["kb_count"] = kb.count_all()
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    data = {"generated_at": datetime.utcnow().isoformat(), "report": report}
    Path(out).write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print("Report written to", out)

if __name__ == "__main__":
    main()
