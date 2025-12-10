#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Alert 6 (FAAM Concentration Monitor)
Tests: configuration loading, rule parsing, and basic function availability
"""

import os
import sys
import io

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv

# Load environment from .env.example (for testing)
load_dotenv(".env.example")

# Import Alert 6 functions
from canton_monitor import (
    ALERT6_INSTANCES,
    ALERT6_FAAMVIEW_API_KEY,
    ALERT6_FAAMVIEW_API_URL,
    parse_concentration_rules,
    fetch_faam_stats,
    check_concentration_rules,
    format_concentration_alert,
    run_alert6_instance,
    run_alert6
)

def test_configuration_loading():
    """Test that Alert 6 configuration loads correctly"""
    print("=" * 60)
    print("TEST 1: Configuration Loading")
    print("=" * 60)

    print(f"\nAPI Key: {ALERT6_FAAMVIEW_API_KEY[:20]}... (truncated)")
    print(f"API URL: {ALERT6_FAAMVIEW_API_URL}")
    print(f"\nInstances loaded: {len(ALERT6_INSTANCES)}")

    for instance in ALERT6_INSTANCES:
        print(f"\n  Instance {instance['id']}: {instance['name']}")
        print(f"    Rules: {instance['rules']}")
        print(f"    Time Window: {instance['time_window_hours']}h")
        print(f"    Interval: {instance['interval_minutes']}min")
        print(f"    Exclude Pushover: {instance['exclude_pushover']}")

    assert len(ALERT6_INSTANCES) > 0, "No instances loaded!"
    print("\n[PASSED] Configuration loading")
    return True

def test_rule_parsing():
    """Test rule parsing function"""
    print("\n" + "=" * 60)
    print("TEST 2: Rule Parsing")
    print("=" * 60)

    test_cases = [
        ("2:50", [(2, 50.0)]),
        ("2:50,3:60", [(2, 50.0), (3, 60.0)]),
        ("2:50,3:60,5:75", [(2, 50.0), (3, 60.0), (5, 75.0)]),
        ("5:75,10:90", [(5, 75.0), (10, 90.0)]),
    ]

    for rules_string, expected in test_cases:
        result = parse_concentration_rules(rules_string)
        print(f"\n  Input: '{rules_string}'")
        print(f"  Expected: {expected}")
        print(f"  Got: {result}")
        assert result == expected, f"Rule parsing failed for '{rules_string}'"
        print("  ✓ PASSED")

    print("\n✓ Rule parsing: PASSED")
    return True

def test_check_concentration_logic():
    """Test concentration checking logic with mock data"""
    print("\n" + "=" * 60)
    print("TEST 3: Concentration Logic")
    print("=" * 60)

    # Mock FAAM data
    mock_data = {
        "providers": [
            {"provider": "provider1", "percent_of_total": 26.05},
            {"provider": "provider2", "percent_of_total": 14.19},
            {"provider": "provider3", "percent_of_total": 10.50},
            {"provider": "provider4", "percent_of_total": 8.20},
            {"provider": "provider5", "percent_of_total": 7.15},
        ],
        "network_total": 9449838.10,
        "time_window": {
            "from": "2025-12-09T11:00:00Z",
            "to": "2025-12-10T11:00:00Z"
        }
    }

    # Test rules: top 2 > 50%, top 3 > 60%
    rules = [(2, 50.0), (3, 60.0)]

    results = check_concentration_rules(mock_data, rules)

    print(f"\n  Mock data: 5 providers")
    print(f"  Rules: {rules}")
    print(f"\n  Results:")

    for result in results:
        top_x = result['top_x']
        threshold = result['threshold']
        concentration = result['concentration']
        triggered = result['triggered']

        print(f"    Top {top_x}: {concentration:.2f}% vs {threshold}% threshold")
        print(f"    Triggered: {triggered}")

        # Verify calculations
        if top_x == 2:
            expected_concentration = 26.05 + 14.19  # 40.24%
            assert abs(concentration - expected_concentration) < 0.01
            assert triggered == False  # 40.24% < 50%
        elif top_x == 3:
            expected_concentration = 26.05 + 14.19 + 10.50  # 50.74%
            assert abs(concentration - expected_concentration) < 0.01
            assert triggered == False  # 50.74% < 60%

    print("\n✓ Concentration logic: PASSED")
    return True

def test_message_formatting():
    """Test multi-rule message formatting"""
    print("\n" + "=" * 60)
    print("TEST 4: Message Formatting")
    print("=" * 60)

    # Mock rule results
    rule_results = [
        {
            "top_x": 2,
            "threshold": 50.0,
            "concentration": 52.40,
            "triggered": True,
            "providers": [
                {"provider": "provider1", "percent_of_total": 26.05, "total_amount": 2460654},
                {"provider": "provider2", "percent_of_total": 26.35, "total_amount": 2489832},
            ],
            "network_total": 9449838.10,
            "time_window": {"from": "2025-12-09T11:00:00Z", "to": "2025-12-10T11:00:00Z"}
        },
        {
            "top_x": 3,
            "threshold": 60.0,
            "concentration": 58.20,
            "triggered": False,
            "providers": [
                {"provider": "provider1", "percent_of_total": 26.05, "total_amount": 2460654},
                {"provider": "provider2", "percent_of_total": 26.35, "total_amount": 2489832},
                {"provider": "provider3", "percent_of_total": 5.80, "total_amount": 548091},
            ],
            "network_total": 9449838.10,
            "time_window": {"from": "2025-12-09T11:00:00Z", "to": "2025-12-10T11:00:00Z"}
        }
    ]

    message = format_concentration_alert("Test Instance", rule_results, any_triggered=True)

    print(f"\n  Generated message:\n")
    print("  " + "\n  ".join(message.split("\n")))

    # Verify message contains key elements
    assert "Test Instance" in message
    assert "⚠️" in message  # Triggered indicator
    assert "✓" in message   # OK indicator
    assert "52.40%" in message  # Concentration
    assert "58.20%" in message

    print("\n✓ Message formatting: PASSED")
    return True

def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("ALERT 6 (FAAM CONCENTRATION MONITOR) - TEST SUITE")
    print("=" * 60)

    tests = [
        test_configuration_loading,
        test_rule_parsing,
        test_check_concentration_logic,
        test_message_formatting
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"\n✗ {test.__name__}: FAILED")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"  Passed: {passed}/{len(tests)}")
    print(f"  Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n✓ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n✗ {failed} TEST(S) FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
