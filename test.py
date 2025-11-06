# TODO: Check all attr which will get obj or list or dict ...
# TODO: check round with chart in creating position
# TODO: add if not self.check_market_open(position.chart) on begining of bot

import numpy as np

ticks = np.array([10, 11, 18, 24, 30, 50, 60]) * -1
print(ticks)
cross = np.logical_or(ticks <= -32, ticks >= -12)
print(cross)
idx = np.argmax(cross)
print(idx)

if not cross.any():
    result = None
else:
    result = "SL" if ticks[idx] <= -32 else "TP"
print(result)

print(1 - -1)
