"""
Test script for Phase 6: Evaluation System
Run this to verify all Phase 6 components work correctly.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Set dummy API key for testing (if not set)
if not os.getenv('GROK_API_KEY'):
    os.environ['GROK_API_KEY'] = 'test_key_for_testing_only'

try:
    from src.evaluation.feasibility_eval import get_feasibility_evaluator
    from src.evaluation.edit_correctness_eval import get_edit_correctness_evaluator
    from src.evaluation.grounding_eval import get_grounding_evaluator
except Exception as e:
    print(f"Error importing evaluation modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def test_feasibility_evaluator():
    """Test Feasibility Evaluator."""
    print("\n=== Testing Feasibility Evaluator ===")
    try:
        evaluator = get_feasibility_evaluator()
        
        # Create a sample itinerary
        sample_itinerary = {
            "city": "Jaipur",
            "duration_days": 2,
            "pace": "moderate",
            "day_1": {
                "morning": {
                    "activities": [
                        {
                            "activity": "Hawa Mahal",
                            "time": "09:00 - 10:30",
                            "duration_minutes": 90,
                            "travel_time_from_previous": 0
                        }
                    ]
                },
                "afternoon": {
                    "activities": [
                        {
                            "activity": "City Palace",
                            "time": "14:00 - 16:00",
                            "duration_minutes": 120,
                            "travel_time_from_previous": 15
                        }
                    ]
                },
                "evening": {"activities": []}
            },
            "day_2": {
                "morning": {"activities": []},
                "afternoon": {"activities": []},
                "evening": {"activities": []}
            }
        }
        
        # Test feasibility evaluation
        result = evaluator.evaluate_feasibility(sample_itinerary)
        
        if "is_feasible" in result and "score" in result:
            print(f"[PASS] Feasibility evaluation works: feasible={result.get('is_feasible')}, score={result.get('score')}")
            return True
        else:
            print(f"[FAIL] Feasibility evaluation returned invalid result: {result}")
            return False
        
    except Exception as e:
        print(f"[FAIL] Feasibility evaluator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_edit_correctness_evaluator():
    """Test Edit Correctness Evaluator."""
    print("\n=== Testing Edit Correctness Evaluator ===")
    try:
        evaluator = get_edit_correctness_evaluator()
        
        # Create old and new itineraries
        old_itinerary = {
            "city": "Jaipur",
            "duration_days": 2,
            "pace": "moderate",
            "day_1": {
                "morning": {"activities": [{"activity": "Hawa Mahal"}]},
                "afternoon": {"activities": []},
                "evening": {"activities": []}
            },
            "day_2": {
                "morning": {"activities": []},
                "afternoon": {"activities": []},
                "evening": {"activities": []}
            }
        }
        
        new_itinerary = {
            "city": "Jaipur",
            "duration_days": 2,
            "pace": "relaxed",  # Changed
            "day_1": {
                "morning": {"activities": [{"activity": "Hawa Mahal"}]},
                "afternoon": {"activities": []},
                "evening": {"activities": []}
            },
            "day_2": {
                "morning": {"activities": [{"activity": "New Activity"}]},  # Changed
                "afternoon": {"activities": []},
                "evening": {"activities": []}
            }
        }
        
        edit_intent = {
            "target_day": 2,
            "edit_type": "ADD_ACTIVITY"
        }
        
        # Test edit correctness evaluation
        result = evaluator.evaluate_edit_correctness(
            old_itinerary=old_itinerary,
            new_itinerary=new_itinerary,
            edit_intent=edit_intent
        )
        
        if "is_correct" in result and "modified_sections" in result:
            print(f"[PASS] Edit correctness evaluation works: correct={result.get('is_correct')}")
            print(f"   Modified sections: {result.get('modified_sections')}")
            return True
        else:
            print(f"[FAIL] Edit correctness evaluation returned invalid result: {result}")
            return False
        
    except Exception as e:
        print(f"[FAIL] Edit correctness evaluator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_grounding_evaluator():
    """Test Grounding Evaluator."""
    print("\n=== Testing Grounding Evaluator ===")
    try:
        evaluator = get_grounding_evaluator()
        
        # Create sample itinerary with POIs
        sample_itinerary = {
            "city": "Jaipur",
            "duration_days": 1,
            "day_1": {
                "morning": {
                    "activities": [
                        {
                            "activity": "Hawa Mahal",
                            "source_id": "way:123456",  # Valid source
                            "duration_minutes": 90
                        }
                    ]
                },
                "afternoon": {
                    "activities": [
                        {
                            "activity": "City Palace",
                            "source_id": None,  # Missing source
                            "duration_minutes": 120
                        }
                    ]
                },
                "evening": {"activities": []}
            }
        }
        
        # Test grounding evaluation
        result = evaluator.evaluate_grounding(
            itinerary=sample_itinerary,
            sources=[
                {"type": "wikivoyage", "url": "https://en.wikivoyage.org/wiki/Jaipur", "topic": "Jaipur"}
            ]
        )
        
        if "is_grounded" in result and "all_pois_have_sources" in result:
            print(f"[PASS] Grounding evaluation works: grounded={result.get('is_grounded')}, score={result.get('score')}")
            print(f"   All POIs have sources: {result.get('all_pois_have_sources')}")
            return True
        else:
            print(f"[FAIL] Grounding evaluation returned invalid result: {result}")
            return False
        
    except Exception as e:
        print(f"[FAIL] Grounding evaluator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_evaluator_integration():
    """Test evaluators integrated with orchestrator."""
    print("\n=== Testing Evaluator Integration ===")
    try:
        # Set API key before importing orchestrator
        if not os.getenv('GROK_API_KEY'):
            os.environ['GROK_API_KEY'] = 'test_key_for_testing_only'
        
        from src.orchestrator.orchestrator import get_orchestrator
        from src.orchestrator.conversation_manager import get_conversation_manager
        
        orchestrator = get_orchestrator()
        manager = get_conversation_manager()
        
        # Create session
        session_id = manager.create_session()
        manager.update_preferences(session_id, {
            "city": "Jaipur",
            "duration_days": 2,
            "pace": "moderate"
        })
        
        # Set a sample itinerary
        sample_itinerary = {
            "city": "Jaipur",
            "duration_days": 2,
            "pace": "moderate",
            "day_1": {
                "morning": {"activities": [{"activity": "Hawa Mahal", "source_id": "way:123456", "duration_minutes": 90}]},
                "afternoon": {"activities": []},
                "evening": {"activities": []}
            },
            "day_2": {
                "morning": {"activities": []},
                "afternoon": {"activities": []},
                "evening": {"activities": []}
            }
        }
        manager.set_itinerary(session_id, sample_itinerary)
        
        # Test that evaluators are accessible
        if orchestrator.feasibility_evaluator and orchestrator.grounding_evaluator:
            print("[PASS] Evaluators integrated with orchestrator")
            return True
        else:
            print("[FAIL] Evaluators not properly integrated")
            return False
        
    except Exception as e:
        print(f"[FAIL] Evaluator integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase 6 tests."""
    print("=" * 50)
    print("Phase 6: Evaluation System - Test Suite")
    print("=" * 50)
    
    results = []
    
    results.append(("Feasibility Evaluator", test_feasibility_evaluator()))
    results.append(("Edit Correctness Evaluator", test_edit_correctness_evaluator()))
    results.append(("Grounding Evaluator", test_grounding_evaluator()))
    results.append(("Evaluator Integration", test_evaluator_integration()))
    
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All Phase 6 tests passed!")
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed. Check errors above.")


if __name__ == "__main__":
    main()
