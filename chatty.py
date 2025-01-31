import ollama
from shiny import App, Inputs, Outputs, Session, reactive, render, ui
from shiny.types import FileInfo

from shared.defns import ChatMode, Embedding, Model
from shared.rag import (
    create_chain,
    create_database,
    create_embedding,
    create_retrieval,
    load_pdf,
    split_text,
)
from shared.utils import restrict_width

side_bar = ui.sidebar(
    ui.input_select(
        id="mode",
        label="Choose a chat mode:",
        choices=[cm for cm in ChatMode],
        selected=ChatMode.ORDINARY,
        multiple=False,
        selectize=True,
    ),
    ui.input_select(
        id="model",
        label="Choose a model to use:",
        choices=[m for m in Model],
        selected=Model.LLAMA,
        multiple=False,
        selectize=True,
    ),
    ui.output_ui("upload_handler"),
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
    title="CHATTY",
    fillable=True,
    fillable_mobile=True,
)


def server(input: Inputs, output: Outputs, session: Session):
    # Create and display empty chat
    chat = ui.Chat(id="chat", on_error="sanitize")

    # create a reactive value to store chain
    chain = reactive.Value()

    @render.ui
    def title_handler():
        return restrict_width(
            ui.h1(
                "Hey, I'm Chatty! What can I help with?",
                # class_="text-lg-center text-left",
            ),
            # sm=10,
            # md=10,
            # lg=8,
        )

    @render.ui
    def upload_handler():
        if input.mode() == ChatMode.RAG:
            return (
                ui.input_file(
                    "pdfs",
                    "Choose PDF file(s) to chat with",
                    accept=[".pdf"],
                    multiple=True,
                ),
                ui.input_task_button(
                    id="process", label="Process and embed PDF(s)", auto_reset=False
                ),
            )

    @reactive.effect
    @reactive.event(input.process)
    def _():
        files: list[FileInfo] | None = input.pdfs()
        if files is None:
            ui.modal_show(
                ui.modal("No files chosen", title="Oops! Something went wrong")
            )
            ui.update_task_button("process", state="ready")

        else:
            paths = [file["datapath"] for file in files]

            text = load_pdf(paths=paths)

            chunks = split_text(text=text)

            embedding = create_embedding(model=Embedding.NOMIC)

            db = create_database(chunks=chunks, embedding=embedding)

            llm, retriever = create_retrieval(model=input.model(), db=db)

            chain.set(create_chain(llm=llm, retriever=retriever))

            ui.notification_show(
                "Files processed and embedded. You can start chatting with them!",
                duration=5,
            )

            ui.update_task_button("process", state="ready")

    @reactive.calc
    def update_chain():
        return chain()

    @chat.on_user_submit
    def _():
        # collapse sidebar and remove title
        ui.update_sidebar(id="sidebar", show=False)
        ui.remove_ui(selector="#title_handler", immediate=True)

    # Define a callback to run when the user submits a message
    @chat.on_user_submit
    async def _():
        # Get messages currently in the chat
        messages = chat.messages(format="ollama")

        if input.mode() == ChatMode.ORDINARY:
            response = ollama.chat(
                model=input.model(),
                messages=messages,
                stream=True,
            )
            response = [chunk.message.content for chunk in response]
        elif input.mode() == ChatMode.RAG:
            curr_chain = update_chain()
            response = curr_chain.invoke(messages[0].content)

        # Append the response stream into the chat
        await chat.append_message_stream(response)


app = App(app_ui, server)
