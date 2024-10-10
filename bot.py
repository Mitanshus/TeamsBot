import asyncio
from botbuilder.core import TurnContext, ActivityHandler
from botbuilder.schema import Activity, ActivityTypes
import aiohttp
from html import escape
import html2text
import re
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
            await turn_context.send_activity(Activity(
                    type=ActivityTypes.message,
                    text=answer,
                ))
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
                    print(answer_data)
                    
                    main_answer = answer_data['output'].strip()
                    
                    # Convert HTML to Markdown
                    marked_text = html2text.HTML2Text()
                    marked_text.ignore_links = False
                    marked_text.body_width = 0
                    markdown_answer = marked_text.handle(main_answer)
                    
                    # Remove any remaining HTML tags
                    soup = BeautifulSoup(markdown_answer, features="html.parser")
                    clean_markdown = soup.get_text('\n')
                    
                    if 'citations' in answer_data:
                        citations_text = "**References:**\n\n"
                        for citation in answer_data['citations']:
                            citation_text = (f"[{citation['superscript']}] {citation['quote'].strip()} "
                                            f"Filename: **{citation['filename']}**, page number: {citation['page_number']}")
                            citations_text += citation_text + "\n\n"
                        
                        return f'{clean_markdown}\n\n{citations_text}'
                    return clean_markdown
                else:
                    raise Exception(f"There seems to be an issue. Please try again later")

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Welcome! You can start asking questions now")