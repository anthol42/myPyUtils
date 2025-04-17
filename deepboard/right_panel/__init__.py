from .template import RightPanel, fill_panel
from .scalars import build_scalar_routes

def build_right_panel_routes(rt):
    rt("/fillpanel")(fill_panel)
    build_scalar_routes(rt)
