entry_p = 0.1075
highest_peak = 0.108704
trade_sl = 0.106586
trade = {'sl': 0.106586, 'trailing_sl': 0.106586}

if highest_peak >= entry_p * 1.0045:
    profit_above_045 = (highest_peak - entry_p * 1.0045) / entry_p
    smart_lock_pct = 0.0015 + (profit_above_045 * 0.70)
    smart_lock_sl = entry_p * (1 + smart_lock_pct)
    
    print(f"smart_lock_sl: {smart_lock_sl}")
    if smart_lock_sl > trade_sl:
        trade['trailing_sl'] = smart_lock_sl
        trade_sl = smart_lock_sl
        print("Updated trade_sl with smart_lock_sl!")

if trade_sl > trade.get('sl', 0) * 1.0015:
    print(f"Syncing! trade_sl: {trade_sl} > {trade.get('sl', 0) * 1.0015}")
    trade['sl'] = trade_sl
else:
    print(f"No sync. {trade_sl} is not > {trade.get('sl', 0) * 1.0015}")
