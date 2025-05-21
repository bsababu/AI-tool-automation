import panel as pn

from panel_chat import run_panel_interface

if __name__ == "__main__":
    app = run_panel_interface()
    pn.serve(app, port=1001, show=True, title="Results analysis chat")
