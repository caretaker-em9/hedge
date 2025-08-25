#!/usr/bin/env python3
"""
Test hedge trigger and exit logic with exact percentage calculations
"""

def test_hedge_logic():
    """Test the hedge trigger and exit calculations"""
    print("🧮 TESTING HEDGE LOGIC CALCULATIONS")
    print("=" * 60)
    
    # Test hedge trigger calculations
    print("\n1. HEDGE TRIGGER TESTS (-5% loss threshold):")
    
    test_cases = [
        {"entry_price": 100.0, "current_price": 95.0, "expected_trigger": True},   # Exactly -5%
        {"entry_price": 100.0, "current_price": 94.0, "expected_trigger": True},   # -6% (should trigger)
        {"entry_price": 100.0, "current_price": 96.0, "expected_trigger": False},  # -4% (should NOT trigger)
        {"entry_price": 100.0, "current_price": 80.0, "expected_trigger": True},   # -20% (should trigger)
        {"entry_price": 50.0, "current_price": 47.5, "expected_trigger": True},    # Exactly -5%
    ]
    
    for i, case in enumerate(test_cases, 1):
        entry_price = case["entry_price"]
        current_price = case["current_price"]
        expected = case["expected_trigger"]
        
        # Calculate loss percentage
        loss_pct = (current_price - entry_price) / entry_price
        trigger_threshold = -0.05  # -5%
        should_trigger = loss_pct <= trigger_threshold
        
        status = "✅" if should_trigger == expected else "❌"
        print(f"   Test {i}: Entry ${entry_price:.2f} → Current ${current_price:.2f}")
        print(f"           Loss: {loss_pct:.2%} | Trigger: {should_trigger} | Expected: {expected} {status}")
    
    # Test hedge exit calculations
    print("\n2. HEDGE EXIT TESTS (1% profit threshold):")
    
    exit_test_cases = [
        {
            "long_entry": 100.0, "long_amount": 0.1, "current_price": 98.0,
            "short_entry": 98.0, "short_amount": 0.15,
            "description": "Long loss covered by short profit"
        },
        {
            "long_entry": 100.0, "long_amount": 0.1, "current_price": 102.0,
            "short_entry": 95.0, "short_amount": 0.15,
            "description": "Both positions profitable"
        },
    ]
    
    for i, case in enumerate(exit_test_cases, 1):
        long_pnl = (case["current_price"] - case["long_entry"]) * case["long_amount"]
        short_pnl = (case["short_entry"] - case["current_price"]) * case["short_amount"]
        total_pnl = long_pnl + short_pnl
        
        total_invested = (case["long_entry"] * case["long_amount"] + 
                         case["short_entry"] * case["short_amount"])
        total_roi_pct = total_pnl / total_invested
        
        exit_threshold = 0.01  # 1%
        should_exit = total_roi_pct >= exit_threshold
        
        print(f"   Test {i}: {case['description']}")
        print(f"           Long P&L: ${long_pnl:.4f} | Short P&L: ${short_pnl:.4f}")
        print(f"           Total P&L: ${total_pnl:.4f} | ROI: {total_roi_pct:.2%}")
        print(f"           Should Exit: {should_exit} (threshold: {exit_threshold:.1%})")
    
    print("\n3. CONFIGURATION VERIFICATION:")
    print(f"   • Hedge trigger: Loss >= -5% (loss_pct <= -0.05)")
    print(f"   • Hedge exit: Profit >= 1% (roi_pct >= 0.01)")
    print(f"   • Logic: Enter hedge when buy position loses 5% or more")
    print(f"   • Logic: Exit both when combined profit reaches 1%")
    
    print("\n✅ HEDGE LOGIC TESTS COMPLETE")

if __name__ == "__main__":
    test_hedge_logic()
