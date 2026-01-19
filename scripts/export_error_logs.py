#!/usr/bin/env python3
"""
Script to export and analyze error logs for automated fixing.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from collections import Counter


def load_backend_logs(log_file: Path) -> List[Dict[str, Any]]:
    """Load backend error logs from JSONL file."""
    logs = []
    if log_file.exists():
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    return logs


def analyze_errors(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze error logs and provide insights."""
    if not logs:
        return {"message": "No errors found"}
    
    # Count by category
    categories = Counter(log["category"] for log in logs)
    
    # Count auto-fixable errors
    auto_fixable = [log for log in logs if log.get("auto_fixable", False)]
    
    # Group by error type
    error_types = Counter(log["error_type"] for log in logs)
    
    # Get recent errors (last 10)
    recent_errors = logs[-10:]
    
    return {
        "total_errors": len(logs),
        "categories": dict(categories),
        "error_types": dict(error_types),
        "auto_fixable_count": len(auto_fixable),
        "auto_fixable_errors": auto_fixable[-10:],  # Last 10 auto-fixable
        "recent_errors": recent_errors,
    }


def main():
    """Main function."""
    backend_log_file = Path("backend/logs/errors/error_log.jsonl")
    
    print("=" * 60)
    print("ERROR LOG ANALYSIS")
    print("=" * 60)
    print()
    
    # Load and analyze backend logs
    backend_logs = load_backend_logs(backend_log_file)
    if backend_logs:
        print(f"Backend Errors: {len(backend_logs)}")
        analysis = analyze_errors(backend_logs)
        print(f"  Total: {analysis['total_errors']}")
        print(f"  Categories: {analysis['categories']}")
        print(f"  Auto-fixable: {analysis['auto_fixable_count']}")
        print()
        
        if analysis['auto_fixable_errors']:
            print("Auto-fixable Errors:")
            for error in analysis['auto_fixable_errors']:
                print(f"  - [{error['category']}] {error['error_type']}: {error['error_message'][:80]}")
                if error.get('fix_suggestion'):
                    print(f"    Fix: {error['fix_suggestion']}")
            print()
    else:
        print("No backend errors found.")
        print()
    
    print("=" * 60)
    print("To view frontend errors, check browser console or localStorage")
    print("Frontend error key: 'frontend_error_logs'")
    print("=" * 60)


if __name__ == "__main__":
    main()
