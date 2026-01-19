#!/usr/bin/env python3
"""
Test script to verify swap day parsing works correctly.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

try:
    from src.orchestrator.edit_handler import get_edit_handler
    import json
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


def test_swap_parsing():
    """Test various swap day command formats."""
    handler = get_edit_handler()
    
    test_cases = [
        "I want to swap day 1 itinerary with day 2",
        "swap day 1 and day 2",
        "swap Day 1 itinerary to Day 2 and vice versa",
        "swap day 1 with day 2",
        "I want to swap day 1 with day 2",
    ]
    
    print("=" * 60)
    print("Testing Swap Day Parsing")
    print("=" * 60)
    print()
    
    for test_input in test_cases:
        print(f"Input: '{test_input}'")
        try:
            result = handler.parse_edit_command(test_input)
            print(f"  Edit Type: {result.get('edit_type')}")
            print(f"  Source Day: {result.get('source_day')}")
            print(f"  Target Day: {result.get('target_day')}")
            
            if result.get('edit_type') == 'SWAP_DAYS' and result.get('source_day') and result.get('target_day'):
                print("  ✅ PASS - Correctly identified as SWAP_DAYS")
            else:
                print("  ❌ FAIL - Not correctly identified")
            print()
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            print()


if __name__ == "__main__":
    test_swap_parsing()
