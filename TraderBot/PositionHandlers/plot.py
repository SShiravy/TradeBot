from ChartModule.plot import ChartPane, ObjectPlotter
from Settings.timing import TimeHandler
from TraderBot.models import Position,Trigger, TriggerType

class PositionPlotter(ObjectPlotter):

    def __call__(self, pane: ChartPane, position: Position) -> None:
        start_time = position.open_timestamp or position.defined_timestamp
        tp_price = position.steps[-1].price if position.steps else position.stoploss.price

        if position.closed_timestamp:
            end_of_line = position.closed_timestamp
            start_of_line = position.last_check_timestamp or start_time
            pane.draw_line(start_time, position.entry_price, start_of_line,
                           position.stoploss.price, "#FFD562")
            pane.draw_line(start_time, position.entry_price, start_of_line,
                           tp_price, "#7fff86")
            start_of_step = start_time
        else:
            end_of_line = TimeHandler.now()
            start_of_line = end_of_line - position.chart.timeframe.minutes * 60 * 10
            start_of_step = start_of_line

        pane.draw_horizontal_line(start_of_line, end_of_line, tp_price, "#09ff00b5")
        pane.draw_horizontal_line(start_of_line, end_of_line, position.stoploss.price, "#ff0000d5")

        for step in position.steps:
            step_end = step.triggered_timestamp or end_of_line
            pane.draw_line(start_of_step, step.price, step_end, step.price, "#00B957" if step.type is TriggerType.TP else "#5C00B9", width=2)

        pane.draw_horizontal_line(start_of_step, end_of_line, position.initial_stoploss.price,
                       "#FF2200", width=2)

        pane.extend_y_range(position.stoploss.price, tp_price)
        
      