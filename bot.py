import asyncio
from botbuilder.core import TurnContext, ActivityHandler
from botbuilder.schema import Activity, ActivityTypes
import aiohttp
from bs4 import BeautifulSoup
from auth import create_access_token
from dotenv import load_dotenv
import os

load_dotenv()

USER_ID = os.getenv('INIT_USER_ID', None)
USER_EMAIL = os.getenv('INIT_USER_EMAIL', None)
USER_ROLE = os.getenv('INIT_USER_ROLE', None)
USER_NAME = os.getenv('INIT_USER_NAME', None)
BACKEND_URL = os.getenv('BACKEND_URL', None)

class MyTeamsBot(ActivityHandler):
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.user_data = {"user_id": USER_ID, "email": USER_EMAIL, "username": USER_NAME, "role": USER_ROLE}

    async def on_message_activity(self, turn_context: TurnContext):
        # Immediately acknowledge receipt of the message
        await turn_context.send_activity(Activity(
            type=ActivityTypes.typing
        ))
        
        # Process the question asynchronously
        asyncio.create_task(self.process_question(turn_context))

    async def process_question(self, turn_context: TurnContext):
        question = turn_context.activity.text
        try:
            answer = await self.get_answer_from_backend(question)
            await turn_context.send_activity(f"Answer: {answer}")
        except Exception as e:
            await turn_context.send_activity(f"An error occurred: {str(e)}")

    async def get_answer_from_backend(self, question: str) -> str:
        token = create_access_token(data=self.user_data)
        headers = {
            'Authorization': f'Bearer {token}'
        }
        timeout = aiohttp.ClientTimeout(total=60)  # Timeout of 60 seconds

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.backend_url}/api/users/{self.user_data['user_id']}/pdf-chats",
                headers=headers,
                json={"question": question},
                timeout=timeout
            ) as response:
                if response.status == 201:
                    answer_data = await response.json()
                    soup = BeautifulSoup(answer_data['output'], features="html.parser").get_text('\n')
                    return soup
                else:
                    raise Exception(f"Failed to get an answer. Status code: {response.status}")

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Welcome! You can start asking questions now")