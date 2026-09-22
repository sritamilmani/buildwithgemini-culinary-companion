# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors.agent_engine_sandbox_code_executor import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.a2ui_utils import a2ui_callback
from app.image_tools import generate_culinary_item_image, generate_culinary_item_video, generate_recipe_photo
from app.pantry_tools import add_pantry_item, get_pantry_items, remove_pantry_item
from app.rag_tools import consult_culinary_herbal_docs
from app.recipe_api_tools import search_external_recipes


async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


# Initialize A2UI Schema Manager for version 0.8 with BasicCatalog
schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

role_description = (
    "You are Culinary Companion, a personal chef and recipe assistant.\n\n"
    "CRITICAL ALLERGY & SAFETY RULE:\n"
    "- Always record, remember, and strictly respect ALL user allergies, medical dietary restrictions, and food sensitivities across all conversations.\n"
    "- Whenever a user mentions an allergy or dietary restriction, explicitly acknowledge it and confirm that it will be saved to memory.\n"
    "- Before suggesting any recipe, dish, or meal plan, cross-reference all ingredients against the user's remembered allergies and NEVER include any allergen.\n\n"
    "FIRESTORE PANTRY BACKEND:\n"
    "- Use `get_pantry_items` to check current pantry inventory from Firestore when the user asks about available ingredients or what to cook.\n"
    "- Use `add_pantry_item` and `remove_pantry_item` to update the Firestore pantry inventory when ingredients are bought, used, or edited.\n\n"
    "EXTERNAL RECIPE SEARCH:\n"
    "- Use `search_external_recipes` to search for real recipe ideas, ingredients, and instructions from TheMealDB global database.\n\n"
    "RECIPE PHOTO & IMAGE GENERATION:\n"
    "- Call `generate_recipe_photo` or `generate_culinary_item_image` whenever recommending or detailing a recipe so a photo of the dish is created and saved to GCS. Include the image URL in your response.\n\n"
    "HERBAL & BOTANICAL KNOWLEDGE GROUNDING:\n"
    "- Use `consult_culinary_herbal_docs` to look up culinary and botanical knowledge from Nicholas Culpeper's 'The Complete Herbal' text corpus whenever asked about herbs, spices, or natural plant remedies.\n\n"
    "PERSONALIZATION:\n"
    "- Remember user dietary goals, favorite cuisines, disliked ingredients, and pantry stock from previous conversations."
)

instruction = schema_manager.generate_system_prompt(
    role_description=role_description,
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=AgentEngineSandboxCodeExecutor(
        agent_engine_resource_name="projects/qwiklabs-gcp-03-f55cf09067a8/locations/us-east1/reasoningEngines/5396765907961774080",
    ),
    instruction=instruction,
    tools=[
        get_weather,
        get_current_time,
        get_pantry_items,
        add_pantry_item,
        remove_pantry_item,
        search_external_recipes,
        generate_recipe_photo,
        generate_culinary_item_image,
        generate_culinary_item_video,
        consult_culinary_herbal_docs,
        PreloadMemoryTool(),
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
