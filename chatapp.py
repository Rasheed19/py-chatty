import ollama
from shiny import App, Inputs, Outputs, Session, render, ui

from shared.defns import Model
from shared.utils import stream_response
from shared.views import restrict_width

side_bar = ui.sidebar(
    ui.input_select(
        id="model",
        label="Choose a model to use:",
        choices=[m for m in Model],
        selected=Model.LLAMA,
        multiple=False,
        selectize=True,
    ),
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
        return restrict_width(
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
        messages = chat.messages(format="ollama")

        response = ollama.chat(
            model=input.model(),
            messages=messages,
            stream=True,
        )

        await chat.append_message_stream(stream_response(response))


app = App(app_ui, server)
