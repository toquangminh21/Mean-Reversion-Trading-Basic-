# Mean-Reversion-Trading-Basic-
Barebone mean reversion trading algorithm, L/S Equity strategy

Signals:
# LONG Undervalued stocks:
# Signal 1: if returns from previous day's low to today's open < 1 sd of rolling 90 day close-to-close returns (gapdown: indicates short-term downward trend)
# Signal 2: open prices > rolling 20 day moving average (they have been moving down, now at the open they're moving up -> mean reversion is happening)

# SHORT Overvalued stocks: exact opposite

Things to improve on:
1) Entirely based on price, but I have been thinking I can add some volatility measures in it (MR when less vol, i.e when noise dies out) Right now, yahoofinance only has volume so I’ll play around with that, but if the IB API we’re gonna use have some other vol measures I’ll play with that too.
2) All positions are entered as soon as market opens and liquidated when market closes. Better if trade can be done throughout the day
3) Not accounted for transaction costs + short margin
4) Not compatible with Software Dev team's backtesting framework
