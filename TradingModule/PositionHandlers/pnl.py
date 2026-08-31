



def update_pnl(
        self,
        executed_price: float,
        volume: float | None = None,
        pnl: float | None = None,
    ):
        """
        calculate pnl based on volume and closed price
        if argument volume is None, then whole volume will considered
        """
        if self.volume <= 0:
            return
        volume = self.volume if volume is None or self.volume - volume < 0 else volume
        direction = 1 if self.side is PositionSide.LONG else -1
        if self.in_forex:
            self.pnl_dollar += (
                pnl
                if pnl
                else (executed_price - self.entry_price)
                * direction
                * volume
                * self.chart.contract_size
            )
            self.pnl_in_pip += (executed_price - self.entry_price) * direction * 10
        else:
            self.pnl_percent += (
                (executed_price - self.entry_price)
                * direction
                / self.entry_price
                * 100
                * self.leverage
            )
            self.pnl_dollar += pnl if pnl else self.pnl_percent * volume / 100
        self.volume -= volume
