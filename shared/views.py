import faicons as fa
from shiny import ui

from shared.defns import (
    DEFAULT_LLM_TEMPERATURE,
    DocSplitterDefaultArgs,
    FileType,
    Model,
)


def restrict_width(
    *args,
    sm: int | None = None,
    md: int | None = None,
    lg: int | None = None,
    pad_y: int = 5,
    **kwargs,
) -> ui.Tag:
    cls = "mx-auto"
    if sm:
        cls += f" col-sm-{sm}"
    if md:
        cls += f" col-md-{md}"
    if lg:
        cls += f" col-lg-{lg}"

    return ui.div(*args, {"class": cls}, {"class": f"py-{pad_y}"}, **kwargs)


def no_selected_collection_message(duration: int) -> None:
    ui.notification_show(
        "No collection is selected. Please select or create a collection",
        duration=duration,
        type="error",
    )


def create_del_collection_modal(collection_name: str) -> ui.Tag:
    return ui.modal(
        title=f"Are you sure you want to delete {collection_name} collection? This action is irriversible!",
        easy_close=True,
        footer=ui.input_action_button(
            "delete_collection",
            "Yes, delete collection",
            class_="btn btn-primary",
        ),
        size="m",
        fade=True,
    )


def create_collection_modal() -> ui.Tag:
    return ui.modal(
        ui.input_text(
            id="collection_name",
            label="Collection name (must not contain space)",
            placeholder="Name your collection",
            width="500px",
        ),
        ui.input_text_area(
            id="collection_description",
            label="Collection description",
            placeholder="Describe your collection",
            width="500px",
        ),
        title="Create a collection to hold your documents",
        easy_close=True,
        footer=ui.input_action_button(
            "create_collection",
            "Create",
            class_="btn btn-primary",
        ),
        size="m",
        fade=True,
    )


def create_desc_value_box(desc_text_ui: ui.Tag) -> ui.Tag:
    action_buttons = [
        ui.column(
            4,
            ui.input_action_button(
                id=f"goto_{id}",
                label=id.replace("_", " ").capitalize(),
                class_="btn btn-primary",
            ),
        )
        for id in ("add_document", "delete_collection", "create_collection")
    ]

    return ui.card(
        ui.card_header("Collection description and action centre"),
        ui.row(
            ui.column(
                10,
                desc_text_ui,
            ),
            ui.column(2, fa.icon_svg("book", height="50px", width="50px")),
        ),
        ui.row(action_buttons),
    )


def create_doc_add_modal(collection_name: str):
    upload_ui = ui.input_file(
        "docs",
        f"Choose document(s) to add to collection. Chatty supports {', '.join(FileType)}",
        accept=[f".{f}" for f in FileType],
        multiple=True,
        width="500px",
    )

    options_ui = ui.row(
        ui.column(
            6,
            ui.input_numeric(
                id="splitter_chunk_size",
                label="Chunk size",
                value=DocSplitterDefaultArgs.CHUNK_SIZE,
                min=1,
            ),
        ),
        ui.column(
            6,
            ui.input_numeric(
                id="splitter_chunk_overlap",
                label="Chunk overlap",
                value=DocSplitterDefaultArgs.CHUNK_OVERLAP,
                min=1,
            ),
        ),
    )

    add_embed_ui = ui.input_task_button(
        id="add_document",
        label="Add and embed documents",
        auto_reset=False,
        class_="btn btn-primary",
    )

    return ui.modal(
        upload_ui,
        options_ui,
        title=f"Add documents to {collection_name} collection",
        easy_close=True,
        size="m",
        fade=True,
        footer=add_embed_ui,
    )


def create_help_pannel() -> ui.Tag:
    return ui.accordion(
        ui.accordion_panel(
            "Need help? Read how to use Ragapp",
            ui.markdown(f"""
                    Ragapp is an easy tool to chat with your various kinds of documents. It currently
                    supports {", ".join(FileType)}. Using Ragapp is very easy. It can be done in 3 steps:

                    - **Select a model**, this is the model that Ragapp will use for RAG.
                    - **Select a collection**, note that you will need to create a new collection if you are using
                    Ragapp for the first time. Then, you will need to add documents to this collection.
                    - Click on **Set parameters & start chatting** button.

                    That is it!

                    You can manage your collection from the **Collection description and action centre**.

                    Enjoy Ragapp!
                    """),
            icon=fa.icon_svg("lightbulb"),
        ),
        open=False,
    )


def create_temp_slider() -> ui.Tag:
    return ui.input_slider(
        id="llm_temp",
        label=(
            "LLM temperature",
            ui.br(),
            ui.help_text(
                "The temperature of the model. Increasing the temperature will make the model answer more creatively."
            ),
        ),
        min=0.0,
        max=1.0,
        value=DEFAULT_LLM_TEMPERATURE,
        ticks=False,
    )


def create_llm_select() -> ui.Tag:
    return ui.input_select(
        id="model",
        label=(
            "Choose a model to use",
            ui.br(),
            ui.help_text(
                "The model to use for generating responses. You can always change this on the fly."
            ),
        ),
        choices=[m for m in Model],
        selected=Model.LLAMA,
        multiple=False,
        selectize=True,
    )


def create_collection_select(choices: list[str]) -> ui.Tag:
    return ui.input_select(
        id="collection",
        label=(
            "Choose or search collection",
            ui.br(),
            ui.help_text(
                "The document collection to use for LLM context. You can always change this on the fly."
            ),
        ),
        choices=choices,
        multiple=False,
        selectize=True,
    )
