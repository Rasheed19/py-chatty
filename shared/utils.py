from shiny import ui


def restrict_width(
    *args,
    sm: int | None = None,
    md: int | None = None,
    lg: int | None = None,
    pad_y: int = 5,
    **kwargs,
):
    cls = "mx-auto"
    if sm:
        cls += f" col-sm-{sm}"
    if md:
        cls += f" col-md-{md}"
    if lg:
        cls += f" col-lg-{lg}"

    return ui.div(*args, {"class": cls}, {"class": f"py-{pad_y}"}, **kwargs)
