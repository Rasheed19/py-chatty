import faicons as fa
from shiny import ui

from shared.defns import DocSplitterDefaultArgs, FileType


# TODO: move this to views.py??
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


def create_collection_button(message: str):
    return ui.card(
        ui.card_header(message),
        ui.row(
            ui.column(
                6,
                ui.input_action_button(
                    id="goto_create_collection",
                    label="Create a new collection",
                    # class_="btn btn-primary",
                ),
            ),
            ui.column(
                6,
                ui.input_task_button(
                    id="use_as_context",
                    label="Use collection for contex",
                    auto_reset=False,
                    # class_="btn btn-primary",
                ),
            ),
        ),
    )


def create_collection_modal() -> ui.Tag:
    return ui.modal(
        ui.input_text(
            id="collection_name",
            label="Collection name:",
            placeholder="Name your collection",
        ),
        ui.input_text_area(
            id="collection_description",
            label="Collection description:",
            placeholder="Describe your collection",
        ),
        title="Create a collection to hold your documents",
        easy_close=True,
        footer=ui.input_action_button(
            "create_collection",
            "Create",
            # class_="btn btn-primary",
        ),
        size="s",
        fade=True,
    )


def create_desc_value_box(desc_text_ui: ui.Tag) -> ui.Tag:
    gear_fill = ui.HTML(
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-gear-fill" viewBox="0 0 16 16"><path d="M9.405 1.05c-.413-1.4-2.397-1.4-2.81 0l-.1.34a1.464 1.464 0 0 1-2.105.872l-.31-.17c-1.283-.698-2.686.705-1.987 1.987l.169.311c.446.82.023 1.841-.872 2.105l-.34.1c-1.4.413-1.4 2.397 0 2.81l.34.1a1.464 1.464 0 0 1 .872 2.105l-.17.31c-.698 1.283.705 2.686 1.987 1.987l.311-.169a1.464 1.464 0 0 1 2.105.872l.1.34c.413 1.4 2.397 1.4 2.81 0l.1-.34a1.464 1.464 0 0 1 2.105-.872l.31.17c1.283.698 2.686-.705 1.987-1.987l-.169-.311a1.464 1.464 0 0 1 .872-2.105l.34-.1c1.4-.413 1.4-2.397 0-2.81l-.34-.1a1.464 1.464 0 0 1-.872-2.105l.17-.31c.698-1.283-.705-2.686-1.987-1.987l-.311.169a1.464 1.464 0 0 1-2.105-.872l-.1-.34zM8 10.93a2.929 2.929 0 1 1 0-5.86 2.929 2.929 0 0 1 0 5.858z"/></svg>'
    )
    action_buttons = [
        ui.input_action_button(
            id=f"goto_{id}",
            label=id.replace("_", " ").capitalize(),
            width="200px",
            # class_="btn btn-primary",
        )
        for id in ("add_document", "delete_document", "delete_collection")
    ]

    action_buttons_spaced = []
    for i, b in enumerate(action_buttons):
        action_buttons_spaced.append(b)
        if i in (0, 1):
            action_buttons_spaced.append(ui.p())

    return ui.card(
        ui.card_header(
            "Collection description",
            ui.popover(
                ui.span(gear_fill, style="position:absolute; top: 5px; right: 7px;"),
                action_buttons_spaced,
                title="Collection options",
                placement="right",
                id="collection_options_popover",
            ),
        ),
        ui.row(
            ui.column(
                10,
                desc_text_ui,
            ),
            ui.column(2, fa.icon_svg("book", height="50px", width="50px")),
        ),
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
        # class_="btn btn-primary",
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
