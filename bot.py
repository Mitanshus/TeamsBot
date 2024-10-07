import base64
import os
import json
from botbuilder.core import TurnContext, ActivityHandler
from botbuilder.schema import Activity, Attachment
import aiohttp
from bs4 import BeautifulSoup
from auth import create_access_token
from dotenv import load_dotenv

load_dotenv()

USER_ID = os.getenv('INIT_USER_ID', None)
USER_EMAIL = os.getenv('INIT_USER_EMAIL', None)
USER_ROLE = os.getenv('INIT_USER_ROLE', None)
USER_NAME = os.getenv('INIT_USER_NAME', None)
BACKEND_URL = os.getenv('BACKEND_URL', None)
class MyTeamsBot(ActivityHandler):
    def __init__(self):
        self.pdf_uploaded = False
        self.backend_url = BACKEND_URL
        self.uploading_pdf = False
        self.user_data = {"user_id": USER_ID, "email": USER_EMAIL, "username": USER_NAME, "role": USER_ROLE}

    async def get_token_from_activity(self, turn_context: TurnContext):
        token = None
        if hasattr(turn_context.activity, "channel_data"):
            channel_data = turn_context.activity.channel_data
            if "teams" in channel_data:
                token = channel_data["teams"].get("token")
        return token 

    async def on_message_activity(self, turn_context: TurnContext):
        # token = await self.get_token_from_activity(turn_context=turn_context)
        
        await self.handle_question(turn_context.activity.text, turn_context)

    

    async def handle_question(self, question: str, turn_context: TurnContext):
    # Acknowledge the user's question
        await turn_context.send_activity("Processing your request...")

        # Send the question to the backend
        token = create_access_token(data=self.user_data)
        headers = {
            'Authorization': f'Bearer {token}'
        }
        timeout = aiohttp.ClientTimeout(total=60)  # Timeout of 60 seconds

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{self.backend_url}/api/users/{self.user_data['user_id']}/pdf-chats", headers=headers, json={"question": question}, timeout=timeout) as response:
                    if response.status == 201:
                        answer = await response.json()
                        soup = BeautifulSoup(answer['output'], features="html.parser").get_text('\n')
                        await turn_context.send_activity(f"Answer: {soup}")
                    else:
                        await turn_context.send_activity("Failed to get an answer. Please try again.")
            except Exception as e:
                await turn_context.send_activity(f"An error occurred: {str(e)}")
                print(f"Error: {str(e)}")


    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Welcome! You can start asking questions now")