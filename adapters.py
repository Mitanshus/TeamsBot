import sys
from datetime import datetime
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings, TurnContext
from botbuilder.schema import ActivityTypes, Activity

class AdapterWithErrorHandler(BotFrameworkAdapter):
    async def on_turn_error(self, turn_context: TurnContext, error: Exception):
        # Log the error
        print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)

        # Send a message to the user
        await turn_context.send_activity("The bot encountered an error or bug.")
        await turn_context.send_activity("To continue to run this bot, please fix the bot source code.")

        # Send a trace activity if we're talking to the Bot Framework Emulator
        if turn_context.activity.channel_id.lower() == "emulator":
            # Create a trace activity that contains the error object
            trace_activity = Activity(
                label="TurnError",
                name="on_turn_error Trace",
                timestamp=datetime.utcnow(),
                type=ActivityTypes.trace,
                value=f"{error}",
                value_type="https://www.botframework.com/schemas/error",
            )
            # Send a trace activity, which will be displayed in Bot Framework Emulator
            await turn_context.send_activity(trace_activity)