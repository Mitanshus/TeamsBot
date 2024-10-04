import base64
import os
from botbuilder.core import TurnContext, ActivityHandler
from botbuilder.schema import Activity, Attachment
import aiohttp

class MyTeamsBot(ActivityHandler):
    def __init__(self):
        self.pdf_uploaded = False
        self.backend_url = "http://your-backend-url.com"  # To be replaced 

    async def on_message_activity(self, turn_context: TurnContext):
        if not self.pdf_uploaded:
            if turn_context.activity.attachments and len(turn_context.activity.attachments) > 0:
                attachment = turn_context.activity.attachments[0]
                if attachment.content_type == "application/pdf":
                    await self.handle_pdf_upload(attachment, turn_context)
                else:
                    await turn_context.send_activity("Please upload a PDF file.")
            else:
                await turn_context.send_activity("Please upload a PDF file to begin.")
        else:
            await self.handle_question(turn_context.activity.text, turn_context)

    async def handle_pdf_upload(self, attachment: Attachment, turn_context: TurnContext):
        # Get the PDF content as bytes
        pdf_content = await self.get_attachment_content(attachment)
        conversation_id = turn_context.activity.conversation.id
        print(conversation_id)



        # Send the PDF to the backend
        async with aiohttp.ClientSession() as session:
            files = {'file': ('document.pdf', pdf_content, 'application/pdf')}
            async with session.post(f"{self.backend_url}/upload_pdf", data=files) as response:
                if response.status == 200:
                    self.pdf_uploaded = True
                    await turn_context.send_activity("PDF uploaded successfully. You can now ask questions about the document.")
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
                    return await response.read()

        raise ValueError("Attachment has no content or content URL")

    async def handle_question(self, question: str, turn_context: TurnContext):
        # Send the question to the backend
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.backend_url}/ask", json={"question": question}) as response:
                if response.status == 200:
                    answer = await response.json()
                    await turn_context.send_activity(f"Answer: {answer['response']}")
                else:
                    await turn_context.send_activity("Failed to get an answer. Please try again.")

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Welcome! Please upload a PDF file to begin.")