


def draw(self):
        if not self.plot:
            return
        plot = self.plot.chart_plot
        if self.closed_timestamp:
            end_of_line = self.closed_timestamp
            start_of_line = (
                self.last_update_timestamp
                if self.last_update_timestamp
                else self.start_time
            )
            plot.draw_line(
                self.start_time,
                self.entry_price,
                start_of_line,
                self.stoploss,
                "#FFD562",
            )
            plot.draw_line(
                self.start_time,
                self.entry_price,
                start_of_line,
                self.takeprofit,
                "#7fff86",
            )
        else:
            end_of_line = self.plot.give_chartdata()[-1].timestamp
            start_of_line = end_of_line - self.chart.timeframe.minutes * 60 * 10

        plot.draw_sl_tp_lines(
            start_of_line,
            end_of_line,
            self.takeprofit,
            self.stoploss,
        )
        if not self.closed_timestamp:
            start_of_step = end_of_line - self.chart.timeframe.minutes * 60 * 10
        else:
            start_of_step = self.start_time

        for step in self.steps[1:]:
            plot.draw_line(
                start_of_step,
                step.price,
                step.triggered_timestamp if step.triggered_timestamp else end_of_line,
                step.price,
                "#00B957",
                width=2,
            )
        plot.draw_line(
            start_of_step,
            self.initial_stoploss,
            end_of_line,
            self.initial_stoploss,
            "#FF2200",
            width=2,
        )
        plot.set_y_range((self.stoploss, self.takeprofit))
