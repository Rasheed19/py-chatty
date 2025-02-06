import ollama
from shiny import App, Inputs, Outputs, Session, reactive, render, ui
from shiny.types import FileInfo

from shared import views
from shared.defns import NOTIFICATION_DURATION, ChatMode, FileType, Model
from shared.rag import (
    load_docs,
    split_docs,
    validate_splitter_args,
)
from shared.utils import CollectionClient

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
    # ui.output_ui("upload_handler"),
    ui.output_ui("collection_handler"),
    ui.output_ui("collection_desc_handler"),
    ui.input_dark_mode(mode="dark"),
    width=500,
    id="sidebar",
)
app_ui = ui.page_sidebar(
    side_bar,
    ui.output_ui(id="title_handler"),
    ui.chat_ui(
        id="chat",
        width="50%",
    ),
    title="Chatty",
    fillable=True,
    fillable_mobile=True,
)


def server(input: Inputs, output: Outputs, session: Session):
    # Create and display empty chat
    chat = ui.Chat(id="chat", on_error="sanitize")

    # create a reactive value to store chain
    chain = reactive.Value()

    client_obj = CollectionClient()
    collection_list = reactive.Value(
        client_obj.list_collections()
    )  # initialize collection list with the current list
    # collection_desc = reactive.Value()  # initialize collection description

    @render.ui
    def collection_handler():
        if input.mode() == ChatMode.RAG:
            temp_ui = []
            if collection_list():
                temp_ui.append(
                    ui.input_select(
                        id="collection",
                        label="Choose or search collection",
                        choices=collection_list(),
                        selected=collection_list()[0],
                        multiple=False,
                        selectize=True,
                    )
                )

            temp_ui.append(
                views.create_collection_button(
                    message="You don't have any collection yet. Please create one by clicking on the button below.",
                )
            )

            return temp_ui

    @render.ui
    def title_handler():
        return views.restrict_width(
            ui.h1(
                "Hey, I'm Chatty! What can I help with?",
                # class_="text-lg-center text-left",
            ),
            # sm=10,
            # md=10,
            # lg=8,
        )

    @render.ui
    def collection_desc_handler():
        if input.mode() == ChatMode.RAG:
            # ui.remove_ui(selector="#collection_desc_handler", immediate=True)
            # desc, _ = client_obj.describe_collection(input.collection())
            # collection_desc.set(desc)
            desc = extract_collection_desc()
            return views.create_desc_value_box(
                desc.name,
                f"""
                - *Description*: {desc.description}
                - *Date created*: {desc.date_created}
                - *Tag*: {desc.tag}
                - *Number of documents or chunks*: {desc.num_chunks}
                """,
            )

    # @reactive.effect
    # @reactive.event(input.collection)
    # def _():
    #     desc = extract_collection_desc()

    #     u(
    #         views.create_desc_value_box(
    #             desc.name,
    #             f"""
    #         - *Description*: {desc.description}
    #         - *Date created*: {desc.date_created}
    #         - *Tag*: {desc.tag}
    #         - *Number of documents or chunks*: {desc.num_chunks}
    #         """,
    #         )
    #     )

    @reactive.effect
    @reactive.event(input.goto_add_document)
    def _():
        ui.modal_show(views.create_doc_add_modal(input.collection()))

    @reactive.effect
    @reactive.event(input.goto_create_collection)
    def _():
        ui.modal_show(views.create_collection_modal())

    @reactive.effect
    @reactive.event(
        input.goto_add_document,
        input.goto_delete_document,
        input.goto_delete_collection,
    )  # TODO: add other collection options' triggers
    def _():
        ui.update_popover(id="collection_options_popover", show=False)

    @reactive.effect
    @reactive.event(input.create_collection)
    def _():
        # only collection name is compulsory
        if input.collection_name() == "":
            ui.notification_show(
                "Collection name must be given.",
                type="error",
                duration=NOTIFICATION_DURATION,
            )
        else:
            err = client_obj.create_collection(
                name=input.collection_name(), description=input.collection_description()
            )

            if err is not None:
                ui.notification_show(
                    f"Error in creating collection. Details: {err}",
                    type="error",
                    duration=NOTIFICATION_DURATION,
                )
            else:
                ui.notification_show(
                    f"Created collection with name: {input.collection_name()}",
                    type="message",
                    duration=NOTIFICATION_DURATION,
                )
                ui.modal_remove()

    @reactive.effect
    @reactive.event(input.add_document)
    def _():
        files: list[FileInfo] | None = input.docs()
        if files is None:
            ui.notification_show(
                "No files chosen",
                type="error",
                duration=NOTIFICATION_DURATION,
            )
            ui.update_task_button("add_document", state="ready")

        elif not validate_splitter_args(
            input.splitter_chunk_size()
        ) or not validate_splitter_args(input.splitter_chunk_overlap()):
            ui.notification_show(
                "Either chunk size or chunk overlap is invalid. Inputs must be positive integer",
                type="error",
                duration=NOTIFICATION_DURATION,
            )
            ui.update_task_button("add_document", state="ready")

        else:
            invalid_docs = []
            for file in files:
                ftype = file["name"].split(".")[-1]
                if ftype not in FileType:
                    invalid_docs.append(file["name"])

            if invalid_docs:
                ui.notification_show(
                    f"Wrong file(s) chosen. {', '.join(invalid_docs)} is/are not supported. "
                    f"Supported doc types are {', '.join(FileType)}.",
                    title="Oops! Something went wrong",
                    type="error",
                    duration=NOTIFICATION_DURATION,
                )

                ui.update_task_button("add_document", state="ready")
            else:
                paths = [file["datapath"] for file in files]

                docs, _ = load_docs(paths=paths)

                chunks = split_docs(
                    docs=docs,
                    chunk_size=input.splitter_chunk_size(),
                    chunk_overlap=input.splitter_chunk_overlap(),
                )

                # TODO: for now, skip doc description
                err = client_obj.add_documents(
                    collection_name=input.collection(),
                    documents=chunks,
                    ollama_embedding_name=input.ollama_embedding_name(),
                    description=None,
                )

                if err is None:
                    ui.notification_show(
                        "Files processed and embedded. You can start chatting with them!",
                        duration=NOTIFICATION_DURATION,
                    )

                    ui.update_task_button("add_document", state="ready")
                    ui.modal_remove()

                else:
                    ui.notification_show(
                        f"Error in adding documents to collection. Details: {err}",
                        duration=None,
                    )
                    ui.update_task_button("add_document", state="ready")

                # db = create_database(chunks=chunks, embedding=embedding)

                # llm, retriever = create_retrieval(model=input.model(), db=db)

                # llm, retriever = create_retrieval(
                #     model=input.model(),
                #     embedding=embedding,
                #     client=client_obj.client,
                #     collection_name="test",
                # )

                # chain.set(create_chain(llm=llm, retriever=retriever))

    # reactively update the collection list when new collection is created
    @reactive.effect
    @reactive.event(input.create_collection)
    def _():
        collection_list.set(client_obj.list_collections())

    # as a side effect of adding more documents to
    # the current selected collection; recalculate
    # the description: num of chunks would be increased
    # @reactive.effect
    # @reactive.event(input.add_document)
    # def _():
    #     desc, _ = client_obj.describe_collection(input.collection())
    #     collection_desc.set(desc)

    @reactive.effect
    @reactive.event(input.goto_delete_collection)
    def _():
        err = client_obj.delete_collection(input.collection())
        if err is not None:
            ui.notification_show(
                err,
                type="error",
                duration=NOTIFICATION_DURATION,
            )
        else:
            import time

            time.sleep(2)
            collection_list.set(client_obj.list_collections())

    # reactively extract collection description;
    # recalculates either when new documents are
    # added or a new collection is selected
    @reactive.calc
    # @reactive.event(input.collection)
    def extract_collection_desc():
        collection_desc, _ = client_obj.describe_collection(input.collection())
        return collection_desc

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
