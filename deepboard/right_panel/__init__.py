from .template import RightPanel, fill_panel


def build_right_panel_routes(rt):
    rt("/fillpanel")(fill_panel)
