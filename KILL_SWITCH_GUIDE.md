# Kill Switch Usage Guide

## Emergency Kill Switch for Binance Testnet

This tool allows you to quickly close all open positions and cancel all orders on your Binance testnet account.

### Files Created:
1. `emergency_kill_switch.py` - Main kill switch tool (recommended)
2. `simple_kill_switch.py` - Alternative version
3. `kill_switch.py` - Async version

### Usage:

#### 1. Check Current Status
```bash
cd /home/caretaker/Desktop/hedge
source trading_bot_env/bin/activate
python emergency_kill_switch.py --status
```

#### 2. Execute Kill Switch (Interactive)
```bash
python emergency_kill_switch.py --kill
```
- Will show current positions/orders
- Requires typing 'KILL' to confirm
- Safest option

#### 3. Execute Kill Switch (Auto-confirm)
```bash
python emergency_kill_switch.py --kill --confirm
```
- Immediately executes without confirmation
- Use only in emergencies

### What the Kill Switch Does:

1. **Cancels ALL open orders** - Stops any pending buy/sell orders
2. **Closes ALL open positions** - Creates market orders to exit all positions
3. **Uses reduceOnly=True** - Ensures orders only close positions, don't open new ones
4. **Uses isolated margin** - Maintains your margin mode settings
5. **Generates a report** - Saves execution details to `kill_switch_report.json`

### Current Account Status (as of last check):
- **Balance**: $14,962.15 USDT
- **Open Orders**: 1
- **Open Positions**: 2 (AIOT/USDT, API3/USDT)
- **Total PnL**: +$9.78

### Safety Features:
- ✅ Works only on testnet (sandbox=True)
- ✅ Requires explicit confirmation 
- ✅ Shows positions before executing
- ✅ Creates detailed execution reports
- ✅ Uses reduceOnly to prevent new positions
- ✅ Handles errors gracefully

### Emergency Usage:
If you need to stop all trading immediately:
```bash
python emergency_kill_switch.py --kill
# Type 'KILL' when prompted
```

### Log Files:
- `kill_switch_report.json` - Execution summary
- Console output shows real-time progress

### Notes:
- The tool is designed to be safe and reliable
- It will not open new positions, only close existing ones
- Works with the same API keys as your trading bot
- Can be run while the trading bot is running (though not recommended)

### Troubleshooting:
If the kill switch fails to close some positions:
1. Check the report file for specific errors
2. Try running it again (some orders may need time to settle)
3. Manually check your Binance testnet account
4. Contact support if issues persist
