#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Alert 7 (FAAM Status Reports)
Tests: configuration loading, report formatting
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

# Import Alert 7 functions
from canton_monitor import (
    ALERT7_ENABLED,
    ALERT7_INTERVAL_MINUTES,
    ALERT7_TIME_WINDOW_HOURS,
    ALERT7_SHOW_TOP_X,
    ALERT7_BREAKDOWN_COUNT,
    format_faam_status_report
)

def test_configuration_loading():
    """Test that Alert 7 configuration loads correctly"""
    print("=" * 60)
    print("TEST 1: Configuration Loading")
    print("=" * 60)

    print(f"\nAlert 7 Enabled: {ALERT7_ENABLED}")
    print(f"Interval: {ALERT7_INTERVAL_MINUTES} minutes")
    print(f"Time Window: {ALERT7_TIME_WINDOW_HOURS} hours")
    print(f"Show Top X: {ALERT7_SHOW_TOP_X}")
    print(f"Breakdown Count: {ALERT7_BREAKDOWN_COUNT}")

    assert ALERT7_ENABLED == True, "Alert 7 should be enabled"
    assert ALERT7_INTERVAL_MINUTES == 60, "Interval should be 60 minutes"
    assert ALERT7_SHOW_TOP_X == [5, 10, 20], "Should show top 5, 10, 20"

    print("\n[PASSED] Configuration loading")
    return True

def test_report_formatting():
    """Test report formatting function"""
    print("\n" + "=" * 60)
    print("TEST 2: Report Formatting")
    print("=" * 60)

    # Mock FAAM data
    mock_data = {
        "providers": [
            {"provider": "cantonloop-mainnet-1", "percent_of_total": 14.20, "total_amount": 176908},
            {"provider": "cbtc-network", "percent_of_total": 12.85, "total_amount": 160090},
            {"provider": "provider-xyz", "percent_of_total": 8.91, "total_amount": 110998},
            {"provider": "node-fortress", "percent_of_total": 3.61, "total_amount": 44979},
            {"provider": "canton-pool", "percent_of_total": 2.58, "total_amount": 32139},
            {"provider": "provider-6", "percent_of_total": 2.10, "total_amount": 26182},
            {"provider": "provider-7", "percent_of_total": 1.95, "total_amount": 24303},
            {"provider": "provider-8", "percent_of_total": 1.80, "total_amount": 22425},
            {"provider": "provider-9", "percent_of_total": 1.65, "total_amount": 20561},
            {"provider": "provider-10", "percent_of_total": 1.50, "total_amount": 18688},
            {"provider": "provider-11", "percent_of_total": 1.35, "total_amount": 16815},
            {"provider": "provider-12", "percent_of_total": 1.20, "total_amount": 14952},
        ],
        "network_total": 1245832.0,
        "time_window": {
            "from": "2025-12-10T18:00:00Z",
            "to": "2025-12-10T19:00:00Z"
        }
    }

    # Test report formatting
    show_top_x = [5, 10, 20]
    breakdown_count = 5
    time_window_hours = 1

    message = format_faam_status_report(
        faam_data=mock_data,
        show_top_x=show_top_x,
        breakdown_count=breakdown_count,
        time_window_hours=time_window_hours
    )

    print(f"\n  Generated report:\n")
    print("  " + "\n  ".join(message.split("\n")))

    # Verify message contains key elements
    assert "FAAM Concentration Report" in message
    assert "Top  5:" in message
    assert "Top 10:" in message
    assert "Top 20:" in message or "Top 20: N/A" in message  # May not have 20 providers
    assert "Breakdown (Top 5)" in message
    assert "cantonloop-mainnet-1" in message
    assert "14.20%" in message
    assert "$176,908" in message

    # Verify concentrations are calculated correctly
    top_5_concentration = sum(p["percent_of_total"] for p in mock_data["providers"][:5])
    assert f"{top_5_concentration:6.2f}%" in message

    print("\n[PASSED] Report formatting")
    return True

def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("ALERT 7 (FAAM STATUS REPORTS) - TEST SUITE")
    print("=" * 60)

    tests = [
        test_configuration_loading,
        test_report_formatting
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"\n[FAILED] {test.__name__}")
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
        print("\n[OK] ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n[X] {failed} TEST(S) FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
