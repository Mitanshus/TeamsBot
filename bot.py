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
        if self.uploading_pdf:  # Check if the bot is currently uploading a PDF
            await turn_context.send_activity("Please wait! The PDF is being uploaded. You can't ask questions right now.")
            return
        
        if not self.pdf_uploaded:
            if turn_context.activity.attachments and len(turn_context.activity.attachments) > 0:
                attachment = turn_context.activity.attachments[0]
                if attachment.content_type == "application/pdf":
                    self.uploading_pdf = True
                    await self.handle_pdf_upload(attachment, turn_context)
                else:
                    await turn_context.send_activity("Please upload a PDF file.")
            else:
                await turn_context.send_activity("Please upload a PDF file to begin.")
        else:
            await self.handle_question(turn_context.activity.text, turn_context)

    async def handle_pdf_upload(self, attachment: Attachment, turn_context: TurnContext):
        # Get the PDF content as bytes
        token = create_access_token(self.user_data)
        pdf_content, file_name = await self.get_attachment_content(attachment)
        conversation_id = turn_context.activity.conversation.id

        # Send the PDF to the backend
        async with aiohttp.ClientSession() as session:
            pdf_metadata = {
                'filename': file_name,
                'text_only': False,
            }
            data = aiohttp.FormData()
            data.add_field('files',
                pdf_content,
                filename=file_name,
                content_type='application/pdf')
            data.add_field('request', json.dumps({"pdfs_metadata" : [pdf_metadata]}))
            headers = {
            'Authorization': f'Bearer {token}'
            }
            async with session.post(f"{self.backend_url}/api/users/{self.user_data['user_id']}/pdf-upload", data=data, headers=headers) as response:
                if response.status == 201:
                    await turn_context.send_activity("PDF is being proceesed please wait.")
                    self.pdf_uploaded = True
                    while self.uploading_pdf == True:
                        async with session.get(f"{self.backend_url}/api/user/{self.user_data['user_id']}", headers=headers) as response:
                            resp = await response.json()
                            self.uploading_pdf = not resp['files_processed']
                            print(self.uploading_pdf)
                            if resp['files_processed']:
                                await turn_context.send_activity("PDF is processed. You can now ask questions about the document.")
                    
                else:
                    await turn_context.send_activity("Failed to upload PDF. Please try again.")

    async def get_attachment_content(self, attachment: Attachment) -> bytes:
        # If the attachment has raw content, return it directly
        if hasattr(attachment, 'content') and attachment.content:
            return base64.b64decode(attachment.content)
        # If there's a content URL, download the content
        if attachment.content_url:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.content_url) as response:
                    return await response.read(), attachment.name

        raise ValueError("Attachment has no content or content URL")

    async def handle_question(self, question: str, turn_context: TurnContext):
        # Send the question to the backend
        token = create_access_token(data=self.user_data)
        headers = {
            'Authorization': f'Bearer {token}'
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.backend_url}/api/users/{self.user_data['user_id']}/pdf-chats", headers=headers,json={"question": question}) as response:
                if response.status == 201:
                    answer = await response.json()
                    soup = BeautifulSoup(answer['output']).get_text('\n')
                    await turn_context.send_activity(f"Answer: {soup}")
                else:
                    await turn_context.send_activity("Failed to get an answer. Please try again.")

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Welcome! Please upload a PDF file to begin.")