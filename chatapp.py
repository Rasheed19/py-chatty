import ollama
from shiny import App, Inputs, Outputs, Session, render, ui

from shared import views
from shared.defns import MessageFormat
from shared.utils import stream_response

side_bar = ui.sidebar(
    views.create_llm_select(),
    views.create_temp_slider(),
    ui.input_dark_mode(mode="dark"),
    width=300,
    id="sidebar",
)
app_ui = ui.page_sidebar(
    side_bar,
    ui.output_ui(id="title_handler"),
    ui.chat_ui(
        id="chat",
        width="50%",
    ),
    title="Chatapp",
    fillable=True,
    fillable_mobile=True,
)


def server(input: Inputs, output: Outputs, session: Session):
    chat = ui.Chat(id="chat", on_error="sanitize")

    @render.ui
    def title_handler():
        return views.restrict_width(
            ui.h1(
                "Hey, I'm Chatapp! What can I help with?",
            ),
        )

    @chat.on_user_submit
    def _():
        ui.update_sidebar(id="sidebar", show=False)
        ui.remove_ui(selector="#title_handler", immediate=True)

    @chat.on_user_submit
    async def _():
        # TODO: note that the messages keep track of all messages: both question and response;
        # this might be an issue of memory and context: find a way of truncating messages down to
        # top n chat history or use token_limits below
        messages = chat.messages(format=MessageFormat.OLLAMA, token_limits=None)

        response = ollama.chat(
            model=input.model(),
            messages=messages,
            stream=True,
            options={"temperature": input.llm_temp()},
        )

        await chat.append_message_stream(stream_response(response))


app = App(app_ui, server)
