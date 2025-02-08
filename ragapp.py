import time

from shiny import App, Inputs, Outputs, Session, reactive, render, ui
from shiny.types import FileInfo

from shared import views
from shared.defns import NOTIFICATION_DURATION, FileType, Model
from shared.rag import (
    create_chain,
    create_retrieval,
    load_docs,
    split_docs,
    validate_splitter_args,
)
from shared.utils import CollectionClient, CollectionDescription

side_bar = ui.sidebar(
    ui.input_select(
        id="model",
        label="Choose a model to use:",
        choices=[m for m in Model],
        selected=Model.LLAMA,
        multiple=False,
        selectize=True,
    ),
    ui.output_ui("collection_handler"),
    views.create_desc_value_box(ui.output_ui("desc_text_handler")),
    views.create_collection_button(
        message="You don't have any collection yet. Please create one by clicking on the button below.",
    ),
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
    chat = ui.Chat(id="chat", on_error="sanitize")

    chain = reactive.Value()

    client_obj = CollectionClient()

    collection_list = reactive.Value(client_obj.list_collections())

    collection_desc = reactive.Value(CollectionDescription)

    @render.ui
    def collection_handler():
        return ui.input_select(
            id="collection",
            label="Choose or search collection",
            choices=collection_list(),
            multiple=False,
            selectize=True,
        )

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
    def desc_text_handler():
        if collection_list():
            desc = collection_desc()
            return ui.markdown(f"""
                    # {desc.name}
                    - *Description*: {desc.description}
                    - *Date created*: {desc.date_created}
                    - *Tag*: {desc.tag}
                    - *Number of documents or chunks*: {desc.num_chunks}
                    """)

        return "You don't have any collection yet. Please create one by clicking on the button below."

    @reactive.effect
    @reactive.event(input.goto_add_document)
    def _():
        if collection_list():
            ui.modal_show(views.create_doc_add_modal(input.collection()))
            ui.update_popover(id="collection_options_popover", show=False)

        else:
            views.no_selected_collection_message(duration=NOTIFICATION_DURATION)

    @reactive.effect
    @reactive.event(input.goto_delete_collection)
    def _():
        if collection_list():
            err = client_obj.delete_collection(input.collection())
            if err is not None:
                ui.notification_show(
                    err,
                    type="error",
                    duration=NOTIFICATION_DURATION,
                )
            else:
                time.sleep(2)
                collection_list.set(client_obj.list_collections())
                ui.update_select(id="collection", choices=collection_list())
        else:
            views.no_selected_collection_message(duration=NOTIFICATION_DURATION)

    @reactive.effect
    @reactive.event(input.goto_create_collection)
    def _():
        ui.modal_show(views.create_collection_modal())

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

                collection_list.set(client_obj.list_collections())
                ui.update_select(id="collection", choices=collection_list())

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
                    description=None,
                )

                if err is None:
                    ui.notification_show(
                        "Files processed and embedded. You can start chatting with them!",
                        duration=NOTIFICATION_DURATION,
                    )

                    ui.update_task_button("add_document", state="ready")

                    desc, _ = client_obj.describe_collection(input.collection())
                    collection_desc.set(desc)

                    ui.modal_remove()

                else:
                    ui.notification_show(
                        f"Error in adding documents to collection. Details: {err}",
                        duration=NOTIFICATION_DURATION,
                        type="error",
                    )
                    ui.update_task_button("add_document", state="ready")

    @reactive.effect
    @reactive.event(input.use_as_context)
    def _():
        if collection_list():
            desc = collection_desc()
            if desc.num_chunks == 0:
                ui.notification_show(
                    "No documents added yet. Please documents to this collection",
                    duration=NOTIFICATION_DURATION,
                    type="error",
                )
                ui.update_task_button("use_as_context", state="ready")

            else:
                llm, retriever = create_retrieval(
                    model=input.model(),
                    client=client_obj.client,
                    collection_name=input.collection(),
                )
                chain.set(create_chain(llm=llm, retriever=retriever))

                time.sleep(2)
                ui.notification_show(
                    f"Collection {desc.name} is set as context. Enjoy chatting with chatty!",
                    duration=NOTIFICATION_DURATION,
                )
                ui.update_task_button("use_as_context", state="ready")

        else:
            views.no_selected_collection_message(duration=NOTIFICATION_DURATION)
            ui.update_task_button("use_as_context", state="ready")

    @reactive.effect
    def _():
        desc, _ = client_obj.describe_collection(input.collection())
        collection_desc.set(desc)

    @chat.on_user_submit
    def _():
        ui.update_sidebar(id="sidebar", show=False)
        ui.remove_ui(selector="#title_handler", immediate=True)

    @chat.on_user_submit
    async def _():
        messages = chat.messages(format="ollama")

        curr_chain = chain()
        response = curr_chain.stream(messages[0].content)

        response = (chunk for chunk in response)

        await chat.append_message_stream(response)


app = App(app_ui, server)
