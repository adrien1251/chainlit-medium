import os
import chainlit as cl
from openai import OpenAI

@cl.on_chat_start 
async def on_chat_start():
    runner = OpenAI(
      api_key=os.getenv("OPENAI_API_KEY"),
      max_retries=3,
      organization=os.getenv("ORGANIZATION_ID"),
    )
    cl.user_session.set("runner", runner)

    thread = runner.beta.threads.create(
        messages=[]
    )

    cl.user_session.set("thread", thread)

    assistant = runner.beta.assistants.create(
        instructions="Tu es un assistant qui va répondre uniquement avec des rimes",
        model="gpt-4o-mini",
    )

    cl.user_session.set("assistant", assistant)


@cl.on_message
async def on_message(message: cl.Message):
    runner = cl.user_session.get("runner")
    thread = cl.user_session.get("thread")
    assistant = cl.user_session.get("assistant")

    runner.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message.content,
        )
    
    msg = cl.Message(content="")
    with runner.beta.threads.runs.stream(
        thread_id=thread.id,
        assistant_id=assistant.id,
    ) as stream:
        for event in stream:
            if event.event == "thread.message.delta" and event.data.delta.content:
                await msg.stream_token(event.data.delta.content[0].text.value)

    await msg.send()
