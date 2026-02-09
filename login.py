from dash import html, dcc


def login_layout():
    return html.Div(
        children=[
            html.H2("Login"),
            dcc.Input(
                id="username",
                type="text",
                placeholder="Username",
                style={"margin-bottom": "10px"},
            ),
            dcc.Input(
                id="password",
                type="password",
                placeholder="Password",
            ),
            html.Div(
                html.Button("Login", id="login-btn"), style={"margin-top": "10px"}
            ),
        ],
        style={"width": "300px", "margin": "100px auto"},
    )
