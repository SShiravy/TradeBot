from TraderBot.models import Position


def plot_position(plot, position: Position):
    if position.closed_timestamp:
        end_of_line = position.closed_timestamp
        start_of_line = (
            position.last_update_timestamp
            if position.last_update_timestamp
            else position.start_time
        )
        plot.draw_line(
            position.start_time,
            position.entry_price,
            start_of_line,
            position.stoploss,
            "#FFD562",
        )
        plot.draw_line(
            position.start_time,
            position.entry_price,
            start_of_line,
            position.takeprofit,
            "#7fff86",
        )
    else:
        end_of_line = position.plot.give_chartdata()[-1].timestamp
        start_of_line = end_of_line - position.chart.timeframe.minutes * 60 * 10

    plot.draw_sl_tp_lines(
        start_of_line,
        end_of_line,
        position.takeprofit,
        position.stoploss,
    )
    if not position.closed_timestamp:
        start_of_step = end_of_line - position.chart.timeframe.minutes * 60 * 10
    else:
        start_of_step = position.start_time

    for step in position.steps[1:]:
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
        position.initial_stoploss,
        end_of_line,
        position.initial_stoploss,
        "#FF2200",
        width=2,
    )
    plot.set_y_range((position.stoploss, position.takeprofit))
