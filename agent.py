"""Cafe voice ordering prototype.

Local mic + speaker in, Deepgram Nova for STT, Claude for the order-taking
brain, Deepgram Aura-2 for TTS. Payment is stubbed (see payment.py) so you
can test the whole conversation flow with zero real hardware or money
involved.

Run:
    cp .env.example .env   # then fill in your API keys
    python agent.py
"""

import asyncio
import os

from dotenv import load_dotenv

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import BotStartedSpeakingFrame, BotStoppedSpeakingFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.processors.audio.vad_processor import VADProcessor
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.services.anthropic.llm import AnthropicLLMService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.deepgram.tts import DeepgramTTSService
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams

from menu import MENU, OrderState
from payment import charge
from greeter import PersonGreeter
from status import set_status
from status_server import start_status_server

load_dotenv()

order = OrderState()

SYSTEM_PROMPT = f"""You are a friendly barista taking a customer's order by voice
at a cafe counter. Menu (drink: available sizes): {MENU}

Milk options: whole, semi-skimmed, oat (+50p), almond (+50p), soy (+40p).
Extra shots are 60p each. Syrups (vanilla, caramel, hazelnut) are 50p each.

Be brief and natural, like a real barista - not a chatbot. Ask only the
clarifying questions you need (size, milk if it's a milk drink). When the
order sounds complete, read back the full order and the total, and ask if
that's everything before calling take_payment. Never invent menu items,
sizes, or prices that aren't in the menu above.

This is a voice conversation - your replies are spoken aloud by a
text-to-speech engine, not displayed as text. Never use markdown formatting
(no **bold**, no bullet points, no asterisks, no headers). Write only plain
spoken sentences, exactly as a barista would say them out loud.

Sometimes you'll be asked to respond with no customer message yet - that
means a camera detected someone walking up to the counter. In that case,
open with a short, warm, natural greeting like "Hey, how can I help?" and
nothing else. Don't repeat this greeting once the conversation is under
way."""


async def add_item_handler(params):
    args = params.arguments
    result = order.add_item(
        drink=args["drink"],
        size=args["size"],
        milk=args.get("milk"),
        extra_shots=args.get("extra_shots", 0),
        syrup=args.get("syrup"),
    )
    set_status(order_items=order.items, order_total=order.total(), order_state="ordering")
    await params.result_callback(result)


async def get_order_summary_handler(params):
    await params.result_callback({"summary": order.summary(), "total": order.total()})


async def take_payment_handler(params):
    result = await charge(order.total())
    set_status(order_items=order.items, order_total=order.total(), order_state="paid")
    await params.result_callback(result)

    await asyncio.sleep(4)
    order.clear()
    set_status(order_items=[], order_total=0, order_state="idle")


TOOLS = [
    FunctionSchema(
        name="add_item",
        description="Add a drink to the customer's order.",
        properties={
            "drink": {"type": "string", "description": "e.g. latte, espresso, tea"},
            "size": {"type": "string", "description": "e.g. small, medium, large"},
            "milk": {"type": "string", "description": "milk type, if applicable"},
            "extra_shots": {"type": "integer", "description": "number of extra espresso shots"},
            "syrup": {"type": "string", "description": "syrup flavour, if requested"},
        },
        required=["drink", "size"],
        handler=add_item_handler,
    ),
    FunctionSchema(
        name="get_order_summary",
        description="Get the current order items and running total.",
        properties={},
        required=[],
        handler=get_order_summary_handler,
    ),
    FunctionSchema(
        name="take_payment",
        description="Charge the customer's card for the current order total. "
        "Only call this after reading back the full order and total, and the "
        "customer has confirmed it's correct.",
        properties={},
        required=[],
        handler=take_payment_handler,
    ),
]


class StatusFrameObserver(FrameProcessor):
    """Watches frames passing through the pipeline and reports bot
    speaking state to status.json, for the light indicator UI. Passes
    every frame through unchanged."""

    async def process_frame(self, frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, BotStartedSpeakingFrame):
            set_status(talking=True)
        elif isinstance(frame, BotStoppedSpeakingFrame):
            set_status(talking=False)
        await self.push_frame(frame, direction)


async def main():
    transport = LocalAudioTransport(
        LocalAudioTransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
        )
    )

    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))

    llm = AnthropicLLMService(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="claude-sonnet-4-6",
    )

    tts = DeepgramTTSService(
        api_key=os.getenv("DEEPGRAM_API_KEY"),
        voice=os.getenv("DEEPGRAM_TTS_VOICE", "aura-2-thalia-en"),
    )

    context = LLMContext(
        messages=[{"role": "system", "content": SYSTEM_PROMPT}],
        tools=TOOLS,
    )
    context_aggregator = LLMContextAggregatorPair(context)

    vad = VADProcessor(vad_analyzer=SileroVADAnalyzer(params=VADParams(confidence=0.7, start_secs=0.3, stop_secs=0.6)))

    status_observer = StatusFrameObserver()

    pipeline = Pipeline(
        [
            transport.input(),
            vad,
            stt,
            context_aggregator.user(),
            llm,
            tts,
            transport.output(),
            status_observer,
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(pipeline)

    start_status_server(os.path.dirname(__file__))

    greeter = PersonGreeter(
        task=task,
        loop=asyncio.get_event_loop(),
        should_greet=lambda: len(order.items) == 0,
    )
    greeter.start()

    runner = PipelineRunner()
    await runner.run(task)


if __name__ == "__main__":
    asyncio.run(main())
