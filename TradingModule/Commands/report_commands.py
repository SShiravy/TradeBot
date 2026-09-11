
import logging


logger = logging.getLogger("Commands")


class SendPositionSignal(Command):
    async def execution_report(self):
        await TelegramReporter().new_position(self.position)
        self.position.plot = None

    def command(self, time):
        self.position.sended = True
        self.position.last_update_timestamp = time
        return True


