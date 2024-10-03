from botbuilder.core import TurnContext, ActivityHandler
from botbuilder.schema import Activity

class MyTeamsBot(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        if turn_context.activity.text:
            await turn_context.send_activity(f"You said: {turn_context.activity.text}")

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Welcome to the bot!")