from botbuilder.core import TurnContext, ActivityHandler, CardFactory, MessageFactory
from botbuilder.schema import Activity, ActivityTypes, Attachment, CardAction, HeroCard, ActionTypes
from botbuilder.core.teams import TeamsActivityHandler, TeamsInfo
from botbuilder.schema.teams import FileConsentCard, FileConsentCardResponse
import json

class EnhancedTeamsBot(TeamsActivityHandler):
    def __init__(self, conversation_state):
        self.conversation_state = conversation_state

    async def on_message_activity(self, turn_context: TurnContext):
        text = turn_context.activity.text.lower()
        if text == "upload":
            await self._send_file_consent_card(turn_context)
        elif text == "chart":
            await self._send_chart_card(turn_context)
        else:
            await turn_context.send_activity(f"You said: {turn_context.activity.text}")

    async def _send_file_consent_card(self, turn_context: TurnContext):
        consent_context = {"filename": "sample.txt"}
        file_card = FileConsentCard(
            description="This is a file consent card.",
            size_in_bytes=1024,
            accept_context=consent_context,
            decline_context=consent_context
        )
        attachment = Attachment(
            content=file_card.serialize(),
            content_type=FileConsentCard.content_type
        )
        await turn_context.send_activity(MessageFactory.attachment(attachment))

    async def _send_chart_card(self, turn_context: TurnContext):
        card = HeroCard(
            title="Sample Chart",
            images=[{"url": "https://example.com/sample-chart.png"}],
            buttons=[
                CardAction(
                    type=ActionTypes.im_back,
                    title="View Details",
                    value="chart details"
                )
            ]
        )
        await turn_context.send_activity(MessageFactory.attachment(CardFactory.hero_card(card)))

    async def on_teams_file_consent_accept(
        self, turn_context: TurnContext, file_consent_card_response: FileConsentCardResponse
    ):
        # Handle file upload logic here
        await turn_context.send_activity("File upload accepted. Processing...")

    async def on_teams_file_consent_decline(
        self, turn_context: TurnContext, file_consent_card_response: FileConsentCardResponse
    ):
        await turn_context.send_activity("File upload declined.")