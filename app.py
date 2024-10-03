from aiohttp import web
from botbuilder.core import BotFrameworkAdapterSettings, ConversationState, MemoryStorage
from botbuilder.schema import Activity
from botbuilder.core.integration import aiohttp_error_middleware
from config import DefaultConfig
from bot import EnhancedTeamsBot
from adapters import AdapterWithErrorHandler

CONFIG = DefaultConfig()

# Create adapter.
SETTINGS = BotFrameworkAdapterSettings(CONFIG.APP_ID, CONFIG.APP_PASSWORD)
ADAPTER = AdapterWithErrorHandler(SETTINGS)

# Create MemoryStorage and ConversationState
MEMORY = MemoryStorage()
CONVERSATION_STATE = ConversationState(MEMORY)

# Create the Bot
BOT = EnhancedTeamsBot(CONVERSATION_STATE)

# Listen for incoming requests on /api/messages.
# async def messages(req: web.Request) -> web.Response:
#     # Main bot message handler.
#     if "application/json" in req.headers["Content-Type"]:
#         body = await req.json()
#     else:
#         return web.Response(status=415)

#     activity = Activity().deserialize(body)
#     auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""

#     try:
#         await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
#         return web.Response(status=200)
#     except Exception as e:
#         print(f"Exception: {e}")
#         return web.Response(status=500)
# Listen for incoming requests on /api/messages.
async def messages(req: web.Request) -> web.Response:
    # Main bot message handler.
    if "application/json" in req.headers["Content-Type"]:
        body = await req.json()
    else:
        return web.Response(status=415)

    activity = Activity().deserialize(body)
    auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""

    try:
        context = await ADAPTER.create_context(activity, auth_header)
        await BOT.on_turn(context)
        return web.Response(status=200)
    except Exception as e:
        print(f"Exception: {e}")
        return web.Response(status=500)

APP = web.Application(middlewares=[aiohttp_error_middleware])
APP.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    try:
        web.run_app(APP, host="localhost", port=CONFIG.PORT)
    except Exception as error:
        raise error