# optimize_ai 
#!/usr/bin/env python3
"""
Run simple optimization suggestions via src.core.optimization.
"""
from src.core.optimization import Optimization
from src.core.knowledge_base import KnowledgeBase

def main():
    kb = KnowledgeBase()
    opt = Optimization()
    # example: record a fake metric and get suggestion
    opt.record("latency_ms", 120.0)
    cur = {"batch_size": 8, "lr": 0.001}
    suggestion = opt.suggest_parameter_adjustment(cur, "latency_ms", 100.0)
    print("Suggested params:", suggestion)

if __name__ == "__main__":
    main()
