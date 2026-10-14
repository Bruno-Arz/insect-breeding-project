"""
Test runner that executes all test functions without external dependencies.
Can be run via: python run_tests.py
"""
import sys
import traceback
from tests.test_population import test_founder_population_structure, test_trait_assignment
from tests.test_heritability import test_heritability_recovery_multi_trial
from tests.test_selection import test_truncation_selection

def run_all():
    tests = [
        ("test_founder_population_structure", test_founder_population_structure),
        ("test_trait_assignment", test_trait_assignment),
        ("test_truncation_selection", test_truncation_selection),
        ("test_heritability_recovery_multi_trial", test_heritability_recovery_multi_trial),
    ]
    
    passed = 0
    failed = 0
    print("=" * 60)
    print("RUNNING AUTOMATED TEST SUITE")
    print("=" * 60)
    
    for name, fn in tests:
        print(f"[RUNNING] {name} ...", end=" ", flush=True)
        try:
            fn()
            print("PASS")
            passed += 1
        except Exception as e:
            print("FAIL")
            traceback.print_exc()
            failed += 1
            
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_all()
