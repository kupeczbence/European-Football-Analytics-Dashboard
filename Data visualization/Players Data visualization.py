#Oldal: https://www.football-data.co.uk/data.php
#CSV Adatok: https://www.football-data.co.uk/spainm.php
#Notes (milyen adatok lehetnek a CSV fájlokban): https://www.football-data.co.uk/notes.txt)
#https://plotly.com/python
#Játékos adatok: https://www.kaggle.com/datasets/maso0dahmed/football-players-data

#Szükséges könyvtárak
import pandas as pd
import numpy as np
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import os
from dash import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots

#Adatok betöltése több ligához és szezonhoz 
LEAGUES = {
    "La Liga": {
        "2022/23": "laliga2022-2023.csv",
        "2023/24": "laliga2023-2024.csv",
        "2024/25": "laliga2024-2025.csv"
    },
    "Premier League": {
        "2022/23": "premier2022-2023.csv",
        "2023/24": "premier2023-2024.csv",
        "2024/25": "premier2024-2025.csv"
    },
    "Serie A": {
        "2022/23": "seriaA2022-2023.csv",
        "2023/24": "seriaA2023-2024.csv",
        "2024/25": "seriaA2024-2025.csv"
    }
}

def load_data(league, season):
    path = LEAGUES[league][season]
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} nem található! Töltsd le a football-data.co.uk-ról.")
    df = pd.read_csv(path)
    df["Season"] = season
    df["League"] = league
    return df

# Betöltjük egyszer az összes elérhető adatot
data_dict = {}
for league, seasons in LEAGUES.items():
    for season in seasons:
        data_dict[(league, season)] = load_data(league, season)

#Játékos adatok betöltése

df = pd.read_csv("fifa_players.csv")

#Euró értékének megfelelő beállítása
df["value_euro"] = df["value_euro"].apply(
    lambda x: f"{int(x):,}".replace(",", " ") + " €" if pd.notna(x) else "Ismeretlen"
)

# Egyedi pozíciók kigyűjtése 
all_positions = sorted(set(
    pos.strip() for positions in df["positions"].dropna()
    for pos in positions.split(",")
))

# Dash app
app = dash.Dash(__name__)
app.title = "Football Dashboard (Több liga és szezon)"

# Defaultok a kezdő állapothoz (ne legyen None)
DEFAULT_LEAGUE = list(LEAGUES.keys())[0]
DEFAULT_SEASON = list(LEAGUES[DEFAULT_LEAGUE].keys())[0]
DEFAULT_TEAMS = sorted(set(data_dict[(DEFAULT_LEAGUE, DEFAULT_SEASON)]["HomeTeam"]).union(
                       set(data_dict[(DEFAULT_LEAGUE, DEFAULT_SEASON)]["AwayTeam"])))
DEFAULT_TEAM = DEFAULT_TEAMS[0] if DEFAULT_TEAMS else None

#Ez a játékosok kiválasztásához kell
def make_radar(title, categories, players, colors):

    labels = {
        "acceleration": "Gyorsulás",
        "sprint_speed": "Sprintsebesség",
        "strength": "Erő",
        "stamina": "Állóképesség",
        "agility": "Agilitás",
        "jumping": "Ugrás",

        "interceptions": "Szerelés",
        "marking": "Emberfogás",
        "standing_tackle": "Álló szerelés",
        "sliding_tackle": "Csúszó szerelés",
        "aggression": "Agresszivitás",

        "finishing": "Befejezés",
        "shot_power": "Lövőerő",
        "long_shots": "Távoli lövés",
        "positioning": "Pozíciójáték",
        "vision": "Látás",
        "crossing": "Beadás",
        "dribbling": "Cselezés"
    }

    fig = go.Figure()

    for player, color in zip(players, colors):
        values = [player[c] for c in categories]
        values.append(values[0])

        theta = [labels.get(c, c) for c in categories]
        theta.append(theta[0])

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=theta,
            fill='toself',
            name=player["name"],
            line=dict(color=color, width=2),
            fillcolor=color.replace("rgb", "rgba").replace(")", ",0.25)")
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title=dict(text=title, x=0.5),
        template="plotly_white",
        height=420,
        margin=dict(l=70, r=70, t=80, b=70),
        legend=dict(orientation="h", x=0.5, xanchor="center")
    )

    return fig

# Layout
app.layout = html.Div([
    html.H1("⚽ Európai Ligák Dashboard", style={'textAlign': 'center'}),

    # Liga / Szezon / Csapat választás
    html.Div([
    html.Div([
        html.Label("Válassz ligát:", style={'marginRight': '5px'}),
        dcc.Dropdown(
            id="league-dropdown",
            options=[{"label": l, "value": l} for l in LEAGUES.keys()],
            value=DEFAULT_LEAGUE,
            clearable=False,
            style={'width': '200px', 'display': 'inline-block'}
        )
    ], style={'display': 'inline-flex', 'alignItems': 'center', 'marginRight': '25px'}),

    html.Div([
        html.Label("Válassz szezont:", style={'marginRight': '5px'}),
        dcc.Dropdown(
            id="season-dropdown",
            options=[{"label": s, "value": s} for s in LEAGUES[DEFAULT_LEAGUE].keys()],
            value=DEFAULT_SEASON,
            clearable=False,
            style={'width': '200px', 'display': 'inline-block'}
        )
    ], style={'display': 'inline-flex', 'alignItems': 'center', 'marginRight': '25px'}),

    html.Div([
        html.Label("Válassz csapatot:", style={'marginRight': '5px'}),
        dcc.Dropdown(
            id="team-dropdown",
            options=[{"label": t, "value": t} for t in DEFAULT_TEAMS],
            value=DEFAULT_TEAM,
            clearable=False,
            style={'width': '200px', 'display': 'inline-block'}
        )
    ], style={'display': 'inline-flex', 'alignItems': 'center'})
], style={'textAlign': 'center', 'marginBottom': '30px'}),

    # KPI-k
    html.Div(id='kpi-cards', style={
        'display': 'flex', 'justifyContent': 'center', 'gap': '40px', 'marginBottom': '40px'
    }),

    # Diagramok
    html.Div([
        html.Div([dcc.Graph(id="bar-goals")], style={'width': '48%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id="scatter-alt")], style={'width': '48%', 'display': 'inline-block'})
    ]),
    html.Div([dcc.Graph(id="time-goals")]),
    html.Div([dcc.Graph(id="discipline-stats")], style={'marginTop': '40px'}),

    #Meccsek és forma diagram szekció
html.Div([
    html.Hr(),
    html.H3("📊 Meccsek és csapatforma alakulása", 
            style={"textAlign": "center", "marginTop": "25px"}),

    html.Div([
        # Momentum chart (forma-idősor)
        html.Div([
            dcc.Graph(id="momentum-chart", style={
                "height": "450px", 
                "boxShadow": "0 4px 12px rgba(0,0,0,0.15)",
                "borderRadius": "10px",
                "backgroundColor": "white",
                "padding": "10px"
            })
        ], style={"flex": "1", "marginRight": "20px"}),

        # Meccsek táblázata
        html.Div([
            html.H4("🗓️ Lejátszott mérkőzések", style={"textAlign": "center", "marginBottom": "10px"}),
            dash_table.DataTable(
                id="match-table",
                columns=[
                    {"name": "Dátum", "id": "Date"},
                    {"name": "Hazai csapat", "id": "HomeTeam"},
                    {"name": "Idegen csapat", "id": "AwayTeam"},
                    {"name": "Hazai gól", "id": "FTHG"},
                    {"name": "Idegen gól", "id": "FTAG"},
                    {"name": "Eredmény", "id": "Result"},
                ],
                style_table={
                    "height": "400px",
                    'overflowY': 'auto',
                    'boxShadow': '0 4px 12px rgba(0,0,0,0.15)',
                    'borderRadius': '10px',
                    'backgroundColor': 'white'
                },
                style_header={
                    'backgroundColor': '#f0f0f0',
                    'fontWeight': 'bold',
                    'textAlign': 'center'
                },
                style_cell={
                    'textAlign': 'center',
                    'padding': '6px',
                    'whiteSpace': 'normal'
                },
                style_data_conditional=[
                    {'if': {'filter_query': '{Result} = "Win"'}, 'backgroundColor': '#d4edda'},
                    {'if': {'filter_query': '{Result} = "Draw"'}, 'backgroundColor': '#fff3cd'},
                    {'if': {'filter_query': '{Result} = "Loss"'}, 'backgroundColor': '#f8d7da'},
                ]
            )
        ], style={"flex": "1"})
    ], style={
        "display": "flex", 
        "justifyContent": "space-between", 
        "alignItems": "flex-start", 
        "width": "90%", 
        "margin": "auto",
        "gap": "20px"
    }),
    html.Div([
    html.H3("Legjobb és legrosszabb meccsek összehasonlítása", style={"textAlign": "center","marginBottom": "10px"}),

    dcc.Graph(
        id="update_radar",
        style={"height": "600px","marginTop": "30px"}
    )], 
    
    style={
    "padding": "20px",
    "border": "2px solid #ddd",
    "borderRadius": "15px",
    "marginTop": "20px",
    "backgroundColor": "white",
    "boxShadow": "0px 4px 10px rgba(0,0,0,0.1)"})
]),



# Meccs-kereső és összehasonlító (az oldal alján)
    
    html.Hr(),
    html.H2("📊 Meccs statisztikai összehasonlítás", style={'textAlign': 'center'}),

    html.Div([
        dcc.Input(
            id="match-search",
            type="text",
            placeholder="Írj be egy csapatnevet (kezd el gépelni)...",
            style={'width': '20%', 'marginBottom': '15px','padding': '8px'}
        ),
        dcc.Dropdown(
            id="match-dropdown",
            placeholder="Válassz mérkőzést...",
            style={'width': '45%','marginLeft': 'auto','marginRight': 'auto'}
        )
    ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center','justifyContent': 'center', 'marginBottom': '25px'}),


    html.Div([
        html.Small("Tipp: írj be legalább 2 karaktert. Ha ligát és szezont kiválasztottad, a keresés azt használja."),
    ], style={'textAlign': 'center', 'color': '#666', 'marginBottom': '20px'}),

    # Itt jelennek meg egymás mellett a két ábra: match-comparison és match-odds
    html.Div([
        html.Div([dcc.Graph(id="match-comparison")], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        html.Div([dcc.Graph(id="match-odds")], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'})
    ], style={'display': 'flex', 'justifyContent': 'space-between', 'gap': '10px', 'marginBottom': '40px'}),

    html.Hr(),
    html.H2("⚽ FIFA játékos statisztikai vizualizáció", style={"textAlign": "center", "color": "#000000"}),

    # JÁTÉKOS STATISZTIKA 
    html.H3("🎯 Játékos keresés és statisztikák", style={"textAlign": "center", "marginTop": "20px", "color": "#000000"}),
    html.Div(
    [
        html.Div(
            dcc.Dropdown(
                id="player-dropdown-1",
                options=[{"label": name, "value": name} for name in sorted(df["name"].unique())],
                placeholder="Kezdd el beírni az 1. játékos nevét...",
                searchable=True,
                style={"width": "65%"}
            ),
            style={
                "width": "50%",
                "display": "flex",
                "justifyContent": "center"
            }
        ),

        html.Div(
            dcc.Dropdown(
                id="player-dropdown-2",
                options=[{"label": name, "value": name} for name in sorted(df["name"].unique())],
                placeholder="Kezdd el beírni a 2. játékos nevét...",
                searchable=True,
                style={"width": "65%"}
            ),
            style={
                "width": "50%",
                "display": "flex",
                "justifyContent": "center"
            }
        )
    ],
    style={
        "display": "flex",
        "width": "80%",
        "margin": "20px auto"
    }
),

    dash_table.DataTable(
    id="player-info",
    columns=[
        {"name": "Név", "id": "full_name"},
        {"name": "Nemzetiség", "id": "nationality"},
        {"name": "Pozíciók", "id": "positions"},
        {"name": "Kor", "id": "age"},
        {"name": "Érékelés", "id": "overall_rating"},
        {"name": "Magasság (cm)", "id": "height_cm"},
        {"name": "Súly (kg)", "id": "weight_kgs"},
        {"name": "Érték (euró)", "id": "value_euro"},
    ],
    data=[],  # Kezdetben üres
    style_table={
        'width': '80%', 
        'margin': 'auto', 
        'marginBottom': '30px',
        'boxShadow': '0 2px 8px rgba(0,0,0,0.2)', 
        'borderRadius': '10px',
        'overflow': 'hidden',   
        'border': 'none',},
    style_cell={
        'textAlign': 'center', 
        'fontFamily': 'Arial', 
        'padding': '10px', 
        'fontSize': 14,
        #'border': 'none'
        },
    style_header={
        'backgroundColor': "#ffd89b", 
        #'background': 'linear-gradient(90deg, #FF512F, #F09819)',
        'color': 'white', 
        'fontWeight': 'bold',
        #'border': 'none'
        },
    style_data={
        #'border': 'none'
        },
    style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': '#F6F8FC'}]
),

    html.Div([
        dcc.Graph(id="radar-physical", style={"display": "inline-block", "width": "33%"}),
        dcc.Graph(id="radar-defense", style={"display": "inline-block", "width": "33%"}),
        dcc.Graph(id="radar-attack", style={"display": "inline-block", "width": "33%"})
    ], style={"textAlign": "center"}),

    html.Hr(style={"margin": "40px 0"}),

    # POZÍCIÓ STATISZTIKA 
    html.H3("📊 Pozíció szerinti elemzés", style={"textAlign": "center", "color": "#000000"}),

    html.Div([
        html.Label("Pozíció kiválasztása:", style={"fontWeight": "bold"}),
        dcc.Dropdown(
            id="position-dropdown",
            options=[{"label": p, "value": p} for p in all_positions],
            placeholder="Válassz egy pozíciót...",
            style={"width": "40%", "margin": "10px auto"}
        ),
    ], style={"textAlign": "center"}),

    dash_table.DataTable(
        id="players-table",
        columns=[
            {"name": "Név", "id": "name"},
            {"name": "Nemzetiség", "id": "nationality"},
            {"name": "Pozíciók", "id": "positions"},
            {"name": "Értékelés", "id": "overall_rating"},
            {"name": "Potencia", "id": "potential"},
            {"name": "Skill", "id": "skill_moves(1-5)"},
            {"name": "Gyengébbik láb", "id": "weak_foot(1-5)"},
        ],
        data=[],
        style_table={
            'width': '95%', 
            'margin': 'auto', 
            'marginBottom': '30px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.2)', 
            'borderRadius': '10px',
            'overflow': 'hidden',   
            'border': 'none',},
        style_cell={
            'textAlign': 'center', 
            'fontFamily': 'Arial', 
            'fontSize': 13, 
            'padding': '8px'},
        style_header={
            'backgroundColor': '#d9a7c7', 
            'color': 'white', 
            'fontWeight': 'bold'},
        style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': '#F3F6FA'}],
        page_size=15
    ),

    dcc.Graph(id="rating-heatmap", style={"width": "90%", "margin": "auto","boxShadow": "0 4px 12px rgba(0,0,0,0.15)", "borderRadius": "10px"}),

    html.Div([
        dcc.Graph(id="foot-pie", style={"display": "inline-block", "width": "45%"}),
        dcc.Graph(id="body-pie", style={"display": "inline-block", "width": "45%"})
    ], style={"textAlign": "center", "marginBottom": "50px"})
])

#Dropdown frissítések(liga, szezon, csapat)
@app.callback(
    Output("season-dropdown", "options"),
    Input("league-dropdown", "value")
)
def update_season_options(league):
    seasons = list(LEAGUES.get(league, {}).keys())
    return [{"label": s, "value": s} for s in seasons]

@app.callback(
    Output("team-dropdown", "options"),
    [Input("league-dropdown", "value"), Input("season-dropdown", "value")]
)
def update_team_options(league, season):
    if not league or not season or (league, season) not in data_dict:
        return []
    df = data_dict[(league, season)]
    teams = sorted(set(df["HomeTeam"]).union(set(df["AwayTeam"])))
    return [{"label": t, "value": t} for t in teams]

# Dashboard fő callback
@app.callback(
    [Output("bar-goals", "figure"),
     Output("scatter-alt", "figure"),
     Output("time-goals", "figure"),
     Output("kpi-cards", "children"),
     Output("discipline-stats", "figure")],
    [Input("league-dropdown", "value"),
     Input("season-dropdown", "value"),
     Input("team-dropdown", "value"),]
)
def update_dashboard(league, season, team,):
    # Védő ellenőrzés: ha nincs még adat, adjon helyőrzőt (ne legyen callback hiba)
    if not league or not season or (league, season) not in data_dict:
        empty_fig = px.line(title="Nincs adat: válassz ligát és szezont")
        placeholder_kpis = [html.Div("Válassz ligát / szezont", style={'padding':'10px'})]
        return empty_fig, empty_fig, empty_fig, placeholder_kpis, empty_fig

    df = data_dict[(league, season)]

    if not team:
        empty_fig = px.line(title="Nincs csapat kiválasztva")
        placeholder_kpis = [html.Div("Válassz csapatot", style={'padding':'10px'})]
        return empty_fig, empty_fig, empty_fig, placeholder_kpis, empty_fig

    # KPI számítások (kártyák az oldal tetején gólok, meccsek stb.)
    team_df = df[(df["HomeTeam"] == team) | (df["AwayTeam"] == team)].copy()
    total_matches = len(team_df)

    goals_for = team_df.apply(lambda r: r["FTHG"] if r["HomeTeam"] == team else r["FTAG"], axis=1).sum()
    goals_against = team_df.apply(lambda r: r["FTAG"] if r["HomeTeam"] == team else r["FTHG"], axis=1).sum()
    goal_diff = int(goals_for - goals_against)

    if "HS" in df.columns and "AS" in df.columns:
        shots_against = team_df.apply(lambda r: r["AS"] if r["HomeTeam"] == team else r["HS"], axis=1).sum()
    else:
        shots_against = 0
    shots_against_per_game = round(shots_against / total_matches, 2) if total_matches > 0 else 0

    avg_goals = round(goals_for / total_matches, 2) if total_matches > 0 else 0
    wins = int((((team_df["HomeTeam"] == team) & (team_df["FTR"] == "H")) |
                 ((team_df["AwayTeam"] == team) & (team_df["FTR"] == "A"))).sum())
    win_rate = round(wins / total_matches * 100, 1) if total_matches > 0 else 0

    #kártyák mérete hogy könnyebben lehessen változtatni
    card_width = "160px"   # szélesség
    card_height = "100px"  #magasság

    #kártyák stílusa
    card_base_style = {
    'padding': '10px',
    'borderRadius': '8px',
    'textAlign': 'center',
    'display': 'flex',
    'flexDirection': 'column',
    'justifyContent': 'center',
    'alignItems': 'center',
    'width': card_width,
    'height': card_height,
    'boxShadow': '0 4px 10px rgba(0,0,0,0.2)'}

    kpi_cards = html.Div(
        children=[
        html.Div([html.H4("Mérkőzések", style={'margin':'0'}), html.H2(total_matches, style={'margin':'0'})],
                 style={**card_base_style, **{'background': '#e6f2ff'}}),
        html.Div([html.H4("Összes gól", style={'margin':'0'}), html.H2(int(goals_for), style={'margin':'0'})],
                 style={**card_base_style, **{'background': '#d9f2d9'}}),
        html.Div([html.H4("⚽ Gólkülönbség", style={'margin':'0'}), html.H2(f"{goal_diff:+d}", style={'margin':'0'})],
                 style={**card_base_style, **{'background': '#fff2cc'}}),
        html.Div([html.H4("Átlag gól / meccs", style={'margin':'0'}), html.H2(f"{avg_goals:.2f}", style={'margin':'0'})],
                 style={**card_base_style, **{'background': '#fff2cc'}}),
        html.Div([html.H4("🛡️ Kapott lövések/meccs", style={'margin':'0'}), html.H2(f"{shots_against_per_game}", style={'margin':'0'})],
                 style={**card_base_style, **{'background': '#fff2cc'}}),
        html.Div([html.H4("Győzelmek", style={'margin':'0'}), html.H2(wins, style={'margin':'0'})],
                 style={**card_base_style, **{'background': '#ffd6cc'}}),
        html.Div([html.H4("🏆 Győzelmi arány", style={'margin':'0'}), html.H2(f"{win_rate}%", style={'margin':'0'})],
                 style={**card_base_style, **{'background': '#ffd6cc'}})
    ],
    style={
        'display': 'flex',
        'gap': '30px',
        'justifyContent': 'center',
        'alignItems': 'center',
        'flexWrap': 'nowrap',   
        'marginBottom': '30px'
    }
)

    # 1. Diagram : Gólok csapatonként (hazai/idegenbeli bontás) 
    home_goals = df.groupby("HomeTeam")["FTHG"].sum()
    away_goals = df.groupby("AwayTeam")["FTAG"].sum()
    
    team_stats = pd.DataFrame({"Team": sorted(set(df["HomeTeam"]).union(set(df["AwayTeam"])))})

    team_stats["Hazai gólok"] = team_stats["Team"].map(home_goals).fillna(0).astype(int)
    team_stats["Idegenbeli gólok"] = team_stats["Team"].map(away_goals).fillna(0).astype(int)
    team_stats["Összes gól"] = team_stats["Hazai gólok"] + team_stats["Idegenbeli gólok"]

    #ábrázolás
    fig_bar = px.bar(team_stats, x="Team", y=["Hazai gólok", "Idegenbeli gólok"],
                     title=f"{league} – {season} góljai (hazai/idegenbeli)",
                     labels={"value": "Gólok", "Team": "Csapat"},
                     barmode="group", color_discrete_map={ "Hazai gólok": "#1f77b4",  "Idegenbeli gólok": "#ff7f0e"  })
    fig_bar.update_layout(xaxis_tickangle=-45,legend_title_text="",template="plotly_white")

    # 2. Diagram: A/B változat helyett
    required_cols = {"FTHG", "FTAG"}
    if not required_cols.issubset(df.columns):
        fig_scatter = px.scatter(title="Nincs gól adat ebben a szezonban")
    else:
        df_scatter = df.copy()
        df_scatter["GoalDifference"] = df_scatter["FTHG"] - df_scatter["FTAG"]

        fig_scatter = px.scatter(
            df_scatter,
            x=df_scatter.index,
            y="GoalDifference",
            labels={
                "index": "Mérkőzés sorszáma",
                "GoalDifference": "Gólkülönbség"
            },
            title=f"Gólkülönbségek alakulása ({league} – {season})",
            template="plotly_white"
        )

        fig_scatter.update_traces(
            marker=dict(size=8, opacity=0.7, color="#1A759F")
        )

        fig_scatter.update_layout(
            height=500,
            title_x=0.5,
            yaxis=dict(
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor="gray"
            )
        )

    # 3. Diagram: Gólok időben 
    if "Date" in df.columns and "FTHG" in df.columns and "FTAG" in df.columns:
    # Dátum normalizálása és hibás értékek kezelése
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)
        df = df.dropna(subset=["Date"])

    # Gólok numerikus konverziója
        df["FTHG"] = pd.to_numeric(df["FTHG"], errors="coerce").fillna(0)
        df["FTAG"] = pd.to_numeric(df["FTAG"], errors="coerce").fillna(0)

    #  Hazai és idegenbeli meccsek szétválasztása
        home_goals = df.loc[df["HomeTeam"] == team, ["Date", "FTHG"]].copy()
        away_goals = df.loc[df["AwayTeam"] == team, ["Date", "FTAG"]].copy()

        home_goals["Típus"] = "Hazai meccs"
        away_goals["Típus"] = "Idegenbeli meccs"

        home_goals.rename(columns={"FTHG": "Gólok"}, inplace=True)
        away_goals.rename(columns={"FTAG": "Gólok"}, inplace=True)

        team_goals = pd.concat([home_goals, away_goals])
        team_goals = team_goals.sort_values("Date")

    # Diagram készítés
        if not team_goals.empty:
            fig_time = px.line(
                team_goals,
                x="Date",
                y="Gólok",
                color="Típus",
                title=f"{team} gólok időbeli alakulása ({season})",
                labels={"Date": "Dátum"},
                markers=True,
                color_discrete_map={
                    "Hazai meccs": "#2ca02c",     # zöld
                    "Idegenbeli meccs": "#da1b0d"  # piros
                }
            )
            fig_time.update_traces(mode="lines+markers")
            fig_time.update_layout(legend_title_text="Mérkőzés típusa",template="plotly_white")
        else:
            fig_time = px.line(title=f"Nincs adat gólokra ebben a szezonban ({season})")
    else:
        fig_time = px.line(title=f"Nincs elérhető adat ehhez a szezonhoz ({season})")

    # 4.Diagram: Fegyelmi statisztikák ('nincs adat' felirat a sávon)
    #az ilyeneknél lehet több adatott is hozzá adni és akkor kiegészíti a diagrammot
    stats_map = {
    "Sárga lapok": ("HY", "AY"),
    "Piros lapok": ("HR", "AR"),
    "Szögletek": ("HC", "AC"),
    "Szabálytalanságok": ("HF", "AF"),
    "Szabadrúgások": ("HFKC", "AFKC"),
    "Lesek": ("HO", "AO"),
    "Lövések": ("HS", "AS"),
    "Kaput eltaláló lövések": ("HST", "AST"),
    "Kapufa": ("HHW ", "AHW "),
    }

    #oszlopok színei
    STAT_COLOR_MAP = {
    "Sárga lapok": "#FFD700",     # arany
    "Piros lapok": "#FF0000",     # piros
    "Szögletek": "#1f77b4",       # kék
    "Szabálytalanságok": "#EB0FBF", # rózsaszín
    "Szabadrúgások": "#2ca02c",   # zöld
    "Lesek": "#9467bd",            # lila
    "Lövések": "#963264",
    "Kaput eltaláló lövések": "#51cdd1",
    "Kapufa": "#160ab8",
    }

# Ebben a listában gyűjtjük össze az adott csapat statisztikai adatait
    team_stats_data = []
    #kigyűjtjük az adatokat
    for label, (home_col, away_col) in stats_map.items():
        if home_col in df.columns and away_col in df.columns:
            total = int(df.loc[df["HomeTeam"] == team, home_col].sum() + df.loc[df["AwayTeam"] == team, away_col].sum())
            display_text = f"{total}"
            numeric_value = total
        # Ha nincs adat az adott statisztikára (pl. másik szezonban nem szerepelt)
        else:
            display_text = "0 (nincs adat erre a szezonra)"
            numeric_value = 0
        team_stats_data.append({"Statisztika": label, "Érték": numeric_value, "Felirat": display_text})

    #ábrázolás
    discipline_df = pd.DataFrame(team_stats_data)
    fig_discipline = px.bar(discipline_df, x="Statisztika", y="Érték",
                            title=f"{team} fegyelmi és játékmenet statisztikái ({league} – {season})",
                            color="Statisztika", text="Felirat", color_discrete_map=STAT_COLOR_MAP)
    fig_discipline.update_traces(textposition="outside")
    max_val = discipline_df["Érték"].max()
    fig_discipline.update_yaxes(range=[0, max_val * 1.2])
    fig_discipline.update_layout(yaxis=dict(showgrid=False),legend_title_text="",template="plotly_white")

    return fig_bar, fig_scatter, fig_time, kpi_cards, fig_discipline


#Momentum chartos rész (5. diagram)
@app.callback(
    [Output("momentum-chart", "figure"),
     Output("match-table", "data")],
    [Input("league-dropdown", "value"),
     Input("season-dropdown", "value"),
     Input("team-dropdown", "value")]
)

def update_team_performance(league, season, selected_team):
    # Ha nincs kiválasztva bajnokság, szezon vagy csapat, visszatér üres diagrammal és adattal
    if not selected_team or not league or not season:
        return go.Figure(), []
    
    # A kiválasztott bajnokság és szezon alapján betöltjük a megfelelő CSV-fájlt
    df_path = LEAGUES[league][season]
    df_filtered = pd.read_csv(df_path)

    # A CSV dátumait biztonságosan konvertáljuk (nap/hónap/év formátumból is)
    df_filtered["Date"] = pd.to_datetime(df_filtered["Date"], errors="coerce", dayfirst=True)
    # Eldobjuk azokat a sorokat, ahol a dátum átalakítása sikertelen volt
    df_filtered = df_filtered.dropna(subset=["Date"])  # eltávolítja a hibás dátumokat
    
    # Kiválogatjuk az összes olyan meccset, ahol a kiválasztott csapat szerepelt akár hazai, akár vendég oldalon
    team_matches = df_filtered[
        (df_filtered["HomeTeam"] == selected_team) | 
        (df_filtered["AwayTeam"] == selected_team)
    ].copy()

    # Ha a csapatnak nincs meccse az adott szezonban, visszatérünk üres adattal és üres ábrával
    if team_matches.empty:
        return go.Figure(), []

    # Eredmény meghatározása (győzelem/döntetlen/vereség)
    team_matches["Result"] = team_matches.apply(
        lambda row: (
            "Win" if (row["HomeTeam"] == selected_team and row["FTHG"] > row["FTAG"]) or
                       (row["AwayTeam"] == selected_team and row["FTAG"] > row["FTHG"])
            else "Draw" if row["FTHG"] == row["FTAG"]
            else "Loss"
        ),
        axis=1
    )

    # Pontszám hozzárendelése (Win=3, Draw=1, Loss=0)
    team_matches["Points"] = team_matches["Result"].map({"Win": 3, "Draw": 1, "Loss": 0})

    # folyamatos győzelmi forma — kumulált pontszám
    team_matches = team_matches.sort_values("Date")
    team_matches["CumulativePoints"] = team_matches["Points"].cumsum()

    #  Momentum chart 
    fig_momentum = go.Figure()

    # Színezés a meccs eredménye szerint
    colors = team_matches["Result"].map({"Win": "#28a745", "Draw": "#ffc107", "Loss": "#dc3545"})

    #ábrázolások
    fig_momentum.add_trace(go.Bar(
        x=team_matches["Date"],
        y=team_matches["Points"],
        marker_color=colors,
        name="Meccs eredmény",
        hovertemplate="Dátum: %{x|%Y-%m-%d}<br>Pont: %{y}<extra></extra>"
    ))

    # Folyamatos forma vonal (összesített pont)
    fig_momentum.add_trace(go.Scatter(
        x=team_matches["Date"],
        y=team_matches["CumulativePoints"],
        mode="lines+markers",
        line=dict(color="#007bff", width=3),
        name="Folyamatos forma"
    ))

    fig_momentum.update_layout(
        title=f"{selected_team} győzelmi széria ({season})",
        xaxis_title="Dátum",
        yaxis_title="Pont / Forma",
        template="plotly_white",
        hovermode="x unified",
        legend_title_text="Eredménytípus",
        xaxis=dict(
            type="date",  
            tickformat="%Y-%m-%d",  # év-hónap-nap
            tickangle=45
        )
    )

    # Táblázathoz adatok előkészítése
    team_matches["Date"] = team_matches["Date"].dt.strftime("%Y-%m-%d")
    table_data = team_matches[["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "Result"]].to_dict("records")

    return fig_momentum, table_data

#Radar Chartos rész legjobb 3 és legrosszabb 3 meccs kiválasztása (6-7. diagram)
@app.callback(
    Output("update_radar", "figure"),
    [Input("league-dropdown", "value"),
     Input("season-dropdown", "value"),
     Input("team-dropdown", "value")]
)

def update_radar(league, season, team):
    #ha nincs benne akkor üreset dobjon vissza
    if not league or not season or not team:
        return go.Figure()

    #adatok kiszedése
    df = pd.read_csv(LEAGUES[league][season])
    df_team = df[(df["HomeTeam"] == team) | (df["AwayTeam"] == team)].copy()

    top3, bottom3 = rank_matches(df_team, team)

    # max érték a radar tengelyekhez
    max_stat = np.max(df_team[["HS", "AS", "HST", "AST", "HC", "AC", "HF", "AF", "HY", "AY", "HR", "AR"]].max())

    fig = create_dual_radar(top3, bottom3, team, max_stat)
    return fig

def get_team_stats_for_match(row, team):
    if row["HomeTeam"] == team:
        stats = {
            "Lövések": row["HS"],
            "Kaput eltaláló": row["HST"],
            "Szögletek": row["HC"],
            "Szabálytalanságok": row["HF"],
            "Sárga lapok": row["HY"],
            "Piros lapok": row["HR"],
        }
    else:
        stats = {
            "Lövések": row["AS"],
            "Kaput eltaláló": row["AST"],
            "Szögletek": row["AC"],
            "Szabálytalanságok": row["AF"],
            "Sárga lapok": row["AY"],
            "Piros lapok": row["AR"],
        }

    return stats

def rank_matches(df_team, team):
    # Gólkülönbség a csapat szemszögéből
    df_team["GoalDiff"] = df_team.apply(
        lambda x: (x["FTHG"] - x["FTAG"]) if x["HomeTeam"] == team else (x["FTAG"] - x["FTHG"]),
        axis=1
    )

    # Lapok száma (sárga + piros)
    df_team["Cards"] = df_team.apply(
        lambda x: (x["HY"] + x["HR"]) if x["HomeTeam"] == team else (x["AY"] + x["AR"]),
        axis=1
    )

    # Meccs eredménye a csapat szemszögéből
    df_team["Result"] = df_team.apply(
        lambda x: (
            "Win" if (x["HomeTeam"] == team and x["FTHG"] > x["FTAG"]) or
                      (x["AwayTeam"] == team and x["FTAG"] > x["FTHG"])
            else "Loss" if (x["HomeTeam"] == team and x["FTHG"] < x["FTAG"]) or
                           (x["AwayTeam"] == team and x["FTAG"] < x["FTHG"])
            else "Draw"
        ),
        axis=1
    )

    # Csak nyert meccsek -> TOP 3
    wins = df_team[df_team["Result"] == "Win"].copy()
    top3 = wins.sort_values(
        by=["GoalDiff", "Cards"], 
        ascending=[False, True]  # nagyobb gólkülönbség előrébb, kevesebb lap előrébb
    ).head(3)

    # Csak vesztett meccsek -> BOTTOM 3
    losses = df_team[df_team["Result"] == "Loss"].copy()
    bottom3 = losses.sort_values(
        by=["GoalDiff", "Cards"],
        ascending=[True, False]  # kisebb (negatívabb) gólkülönbség előrébb, több lap előrébb
    ).head(3)

    return top3, bottom3


def create_dual_radar(top3, bottom3, team, max_stat):
    # A radar diagram tengelyeihez tartozó statisztikai kategóriák
    categories = ["Lövések", "Kaput eltaláló", "Szögletek", "Szabálytalanságok", ] #"Sárga lapok", "Piros lapok"
    
    # Két radar diagram (polar chart) egymás mellet
    fig = make_subplots(rows=1, cols=2,
                        specs=[[{'type': 'polar'}, {'type': 'polar'}]],
                        subplot_titles=("🏆 Legjobb 3 meccs", "💔 Legrosszabb 3 meccs"))
    
    for ann in fig.layout.annotations:
        ann.y = 1.15      # alapból ~1.0 körül van
        ann.font.size = 16

    green_shades = ["#006400", "#eadc17", "#ebee94"] #legjobb 3 meccshez a színek
    red_shades = ["#8b0000", "#0800ff", "#c766ff"]#legrosszabb 3 meccshez a színek

    # Legjobb 3 meccs kirajzolása (bal oldali radar)
    # Végigmegyünk a top3 DataFrame sorain
    for idx, row in enumerate(top3.itertuples()):
        
        # Az adott meccs statisztikáinak lekérése a csapat szemszögéből
        stats = get_team_stats_for_match(row._asdict(), team)
        
        # Az értékek listába rendezése, az első elem duplikálásával (a radar kör bezárásához)
        values = [stats[c] for c in categories]
        values = values + [values[0]]
        
        # A radar-görbe hozzáadása a bal oldali (1. oszlop) subplothoz
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories + [categories[0]],
            fill='toself',
            # cím: kivel játszott
            name=f"{row.Date} vs {row.AwayTeam if row.HomeTeam == team else row.HomeTeam}",
            line_color=green_shades[idx],
            opacity=0.6
        ), row=1, col=1)

    #Ugyan az mint az előző csak bottom 3 másik diagramra
    for idx, row in enumerate(bottom3.itertuples()):
        stats = get_team_stats_for_match(row._asdict(), team)

        values = [stats[c] for c in categories]
        values = values + [values[0]]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories + [categories[0]],
            fill='toself',
            name=f"{row.Date} vs {row.AwayTeam if row.HomeTeam == team else row.HomeTeam}",
            line_color=red_shades[idx],
            opacity=0.6
        ), row=1, col=2)

    #Általános elrendezés és tengelybeállítások
    fig.update_layout(
    title=dict(
        text=f"{team} – Legjobb és legrosszabb 3 meccs radar összehasonlítása",
        x=0.5,
        y=1.0,              # max érték
        xanchor="center",
        yanchor="top",
        pad=dict(t=40),
        font=dict(size=20)
    ),
    showlegend=True,
    template="plotly_white",

    polar=dict(radialaxis=dict(visible=True, range=[0, max_stat])),
    polar2=dict(radialaxis=dict(visible=True, range=[0, max_stat])),

    margin=dict(t=180)     #  EZ emeli meg valójában
)

    return fig

# Meccs-kereső callback (utolsó rész)
@app.callback(
    Output("match-dropdown", "options"),
    [Input("match-search", "value"),
     Input("league-dropdown", "value"),
     Input("season-dropdown", "value")]
)
def update_match_list(search_text, league, season):
    # ha nincs keresőszöveg, térj vissza üres listával
    if not search_text or len(search_text.strip()) < 2:
        return []

    search_text = search_text.strip().lower()
    options = []

    # ha liga és szezon meg van adva, keresünk csak abban
    if league and season and (league, season) in data_dict:
        df = data_dict[(league, season)]
        filtered = df[
            df["HomeTeam"].str.contains(search_text, case=False, na=False) |
            df["AwayTeam"].str.contains(search_text, case=False, na=False)
        ]
        for idx, row in filtered.iterrows():
            date_str = str(row.get("Date", ""))
            try:
                date_str = pd.to_datetime(date_str).strftime("%Y-%m-%d")
            except Exception:
                date_str = str(row.get("Date", ""))
            label = f"{row['HomeTeam']} vs {row['AwayTeam']} — {date_str}"
            value = f"{league}|||{season}|||{int(idx)}"
            options.append({"label": label, "value": value})
    else:
        # keresés minden betöltött szezon/liga kombinációban
        for (lg, ss), df in data_dict.items():
            filtered = df[
                df["HomeTeam"].str.contains(search_text, case=False, na=False) |
                df["AwayTeam"].str.contains(search_text, case=False, na=False)
            ]
            for idx, row in filtered.iterrows():
                date_str = str(row.get("Date", ""))
                try:
                    date_str = pd.to_datetime(date_str).strftime("%Y-%m-%d")
                except Exception:
                    date_str = str(row.get("Date", ""))
                label = f"{row['HomeTeam']} vs {row['AwayTeam']} — {date_str} ({lg} {ss})"
                value = f"{lg}|||{ss}|||{int(idx)}"
                options.append({"label": label, "value": value})

    return options


# 8-9. diagram Meccs összehasonlító callback (megrajzolja a tükördiagramot és az odds-ot)
@app.callback(
    [Output("match-comparison", "figure"),
     Output("match-odds", "figure")],
    Input("match-dropdown", "value")
)

def display_match_stats(match_value):
    import dash

    # Ha még nincs semmi kiválasztva (pl. oldalbetöltéskor), ne frissítsen
    if match_value is None:
        raise dash.exceptions.PreventUpdate

    # Ha nincs érvényes érték, mutassunk egy alap üzenetet
    if not match_value:
        empty_fig = px.bar(
            pd.DataFrame({"Üzenet": ["Válassz egy mérkőzést a listából"], "Érték": [0]}),
            x="Üzenet",
            y="Érték",
            title="Válassz egy mérkőzést a listából"
        )
        return empty_fig, empty_fig

    #A kiválasztott elem dekódolása (league|||season|||index)
    try:
        league, season, idx_str = match_value.split("|||")
        idx = int(idx_str)
    # Ha a formátum nem megfelelő
    except Exception:
        err_fig = px.bar(title="Érvénytelen mérkőzés kiválasztás")
        return err_fig, err_fig

    # Ellenőrzés, hogy a liga–szezon–meccs index megtalálható-e az adatforrásban
    if (league, season) not in data_dict or idx not in data_dict[(league, season)].index:
        err_fig = px.bar(title="Nem található adat a kiválasztott mérkőzéshez")
        return err_fig, err_fig

    # Adatsor kiválasztása
    df = data_dict[(league, season)]
    row = df.loc[idx]

    home_team = row["HomeTeam"]
    away_team = row["AwayTeam"]

    # Dátum formázása egységes YYYY-MM-DD formátumba
    date_str = str(row.get("Date", ""))
    try:
        date_str = pd.to_datetime(date_str).strftime("%Y-%m-%d")
    except Exception:
        pass

    # Meccs statisztikák definiálása(hozzá lehet többet adni)
    stats = {
        "Piros lapok": ("HR", "AR"),
        "Sárga lapok": ("HY", "AY"),
        "Szabálytalanságok": ("HF", "AF"),
        "Szögletek": ("HC", "AC"),
        "Kapura lövések": ("HST", "AST"),
        "Lövések": ("HS", "AS"),
        "Gólok": ("FTHG", "FTAG")
    }

    # Három lista az ábrázoláshoz: tengelyfelirat, hazai és vendég értékek
    labels, home_vals, away_vals = [], [], []
    for label, (hcol, acol) in stats.items():
        # Az adott mutató értéke hazai és vendég csapatra (NaN kezeléssel)
        if hcol in df.columns and acol in df.columns:
            h = int(row[hcol]) if pd.notna(row[hcol]) else 0
            a = int(row[acol]) if pd.notna(row[acol]) else 0
            labels.append(label)
            # A hazai értékeket negatívba tesszük, hogy szimmetrikusan ábrázolható legyen
            home_vals.append(-h)
            away_vals.append(a)

    # Ha nincs adat, visszaad egy alap figyelmeztetést
    if not labels:
        return px.bar(title="Ehhez a mérkőzéshez nincs statisztika"), px.bar(title="Nincs odds adat ehhez a mérkőzéshez")

    #Statisztikai oszlopdiagram (hazai vs vendég)
    comp_df = pd.DataFrame({
        "Statisztika": labels,
        f"{home_team} (hazai)": home_vals,
        f"{away_team} (vendég)": away_vals
    })

    fig_comp = px.bar(
        comp_df.melt(id_vars="Statisztika", var_name="Csapat", value_name="Érték"),
        x="Érték", y="Statisztika", color="Csapat",
        orientation="h", # vízszintes oszlopok
        title=f"{home_team} vs {away_team} – Meccs statisztikák ({date_str})",
        barmode="relative", # az értékek egymás mellé kerülnek közös tengelyen
        color_discrete_map={
        f"{home_team} (hazai)": "#2ca02c",  # zöld
        f"{away_team} (vendég)": "#da1b0d"  # piros
    }
    )

    # X tengely skálázása, hogy szimmetrikus legyen a két oldal
    max_val = max(max(map(abs, home_vals)), max(map(abs, away_vals)))
    fig_comp.update_xaxes(range=[-max_val * 1.1, max_val * 1.1])
    fig_comp.update_layout(xaxis_title="Érték", yaxis_title="", template="plotly_white", bargap=0.25)

    # Odds ábra, Odds adatok kinyerése több bukmékertől
    odds_cols = {
        "Avg": ("AvgH", "AvgD", "AvgA"),
        "Pinnacle": ("PSH", "PSD", "PSA"),
        "William Hill": ("WHH", "WHD", "WHA"),
        "Interwetten": ("IWH", "IWD", "IWA"),
        "VCBet": ("VCH", "VCD", "VCA"),
        "Max": ("MaxH", "MaxD", "MaxA"),
        "Bet365": ("B365H", "B365D", "B365A")
    }

    odds_data = []
    for book, (hcol, dcol, acol) in odds_cols.items():
        if hcol in df.columns and dcol in df.columns and acol in df.columns:
            hval, dval, aval = row.get(hcol), row.get(dcol), row.get(acol)

            # Csak akkor vesszük figyelembe, ha van bármilyen érték
            if pd.notna(hval) or pd.notna(dval) or pd.notna(aval):
                odds_data.extend([
                    {"Bukmeker": book, "Kimenetel": "Idegen", "Odds": aval},
                    {"Bukmeker": book, "Kimenetel": "Döntetlen", "Odds": dval},
                    {"Bukmeker": book, "Kimenetel": "Hazai", "Odds": hval},
                    
                ])

    # Odds adatokat DataFrame-be konvertáljuk
    odds_df = pd.DataFrame(odds_data).dropna(subset=["Odds"]) if odds_data else pd.DataFrame()

    # Odds ábra létrehozása
    if odds_df.empty:
        fig_odds = px.bar(title="⚠️ Nincs odds adat ehhez a mérkőzéshez")
    else:
        fig_odds = px.bar(
            odds_df, x="Odds", y="Bukmeker", color="Kimenetel",
            orientation="h", barmode="group",
            title=f"💰 Fogadási oddsok – {home_team} vs {away_team} ({date_str})",
            color_discrete_map={
                "Idegen": "#da1b0d",       # piros
                "Döntetlen": "#ff7f0e",   # narancs
                "Hazai": "#2ca02c",       # zöld
                }
        )
        fig_odds.update_layout(legend_title_text="",template="plotly_white")

    # Ábrák visszaadása: statisztikai összevetés és odds diagram
    return fig_comp, fig_odds

#CALLBACK: Játékos keresés és radar frissítés
@app.callback(
    [Output("player-info", "data"),
     Output("radar-physical", "figure"),
     Output("radar-defense", "figure"),
     Output("radar-attack", "figure")],
    [Input("player-dropdown-1", "value"),
     Input("player-dropdown-2", "value")]
)
def update_player(player1, player2):

    if not player1 and not player2:
        return [], go.Figure(), go.Figure(), go.Figure()

    selected_players = []
    table_data = []

    for name in [player1, player2]:
        if name:
            p = df[df["name"] == name].iloc[0]
            selected_players.append(p)
            table_data.append({
                "full_name": p["full_name"],
                "nationality": p["nationality"],
                "positions": p["positions"],
                "age": p["age"],
                "overall_rating": p["overall_rating"],
                "height_cm": p["height_cm"],
                "weight_kgs": p["weight_kgs"],
                "value_euro": p["value_euro"]
            })

    physical = ["acceleration", "sprint_speed", "strength", "stamina", "agility", "jumping"]
    defense = ["interceptions", "marking", "standing_tackle", "sliding_tackle", "aggression"]
    attack = ["finishing", "shot_power", "long_shots", "positioning", "vision", "crossing", "dribbling"]

    colors = ["rgb(31,119,180)", "rgb(214,39,40)"]  # kék + piros

    return (
        table_data,
        make_radar("Fizikai attribútumok", physical, selected_players, colors),
        make_radar("Védekezés", defense, selected_players, colors),
        make_radar("Támadás", attack, selected_players, colors)
    )


# CALLBACK: Pozíció nézet frissítése
@app.callback(
    [Output("players-table", "data"),
     Output("rating-heatmap", "figure"),
     Output("foot-pie", "figure"),
     Output("body-pie", "figure")],
    [Input("position-dropdown", "value")]
)
def update_position_view(selected_position):
    if not selected_position:
        return [], go.Figure(), go.Figure(), go.Figure()

    filtered = df[df["positions"].str.contains(selected_position, na=False)].copy()

    table_data = filtered[[
        "name", "nationality", "positions",
        "overall_rating", "potential",
        "skill_moves(1-5)", "weak_foot(1-5)"
    ]].sort_values(by="overall_rating", ascending=False).to_dict("records")

    fig = px.density_heatmap(
        filtered,
        x="overall_rating",
        y="potential",
        color_continuous_scale="Pinkyl",
        title=f"{selected_position} pozícióban játszó játékosok Értékelés-Potencia eloszlása",
        nbinsx=20,
        nbinsy=20,
        
    )
    fig.update_layout(
        xaxis_title="Értékelés",
        yaxis_title="Potencia",
        template="plotly_white",
        height=500,
        title_x=0.5,
        coloraxis_colorbar=dict(
        title="Intenzitás", )
    )

    # Preferred foot pie chart
    filtered["preferred_foot"] = filtered["preferred_foot"].replace({
    "Left": "Bal",
    "Right": "Jobb"
    })
    
    foot_counts = filtered["preferred_foot"].value_counts().reset_index()
    foot_counts.columns = ["Láb", "Darabszám"]
    foot_fig = go.Figure(go.Pie(
        labels=foot_counts["Láb"],
        values=foot_counts["Darabszám"],
        hole=0.3,
        pull=[0.05]*len(foot_counts),
    ))
    foot_fig.update_traces(
    textinfo='percent+label',
    textfont_size=14,
    marker=dict(
        line=dict(color='#FFFFFF', width=2),
        colors=['#9ecae1', '#fdae6b', '#a1d99b', '#bcbddc', '#fdd0a2']),
    hole=0.3)

    foot_fig.update_layout(
    title_text="Lábhasználat eloszlása",
    title_x=0.5,
    showlegend=False,
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    margin=dict(t=50, b=0, l=0, r=0))

    # --- Body type pie chart ---
    #body_map = {
    #"Messi": "Lean",
    #"C. Ronaldo": "Normal",
    #"Neymar": "Lean",
    #"Akinfenwa": "Stocky",
    #"Courtois": "Normal"
#}

# Alapérték, ha ismeretlen az érték
    #filtered["body_type"] = filtered["body_type"].replace(body_map)
    filtered["body_type"] = filtered["body_type"].apply(lambda x: x if x in ["Lean", "Normal", "Stocky", "Average"] else "Other")

    body_type_translation = {
        "Lean": "Vékony",
        "Normal": "Normál",
        "Stocky": "Izmos",
        "Average": "Átlagos",
        "Other": "Egyéb"
    }

    filtered["body_type"] = filtered["body_type"].replace(body_type_translation)

    body_counts = filtered["body_type"].value_counts().reset_index()
    body_counts.columns = ["Test alkat", "Darabszám"]
    body_fig = go.Figure(go.Pie(
        labels=body_counts["Test alkat"],
        values=body_counts["Darabszám"],
        hole=0.3,
        pull=[0.05]*len(body_counts),
    ))

    body_fig.update_traces(
    textinfo='percent+label',
    textfont_size=14,
    marker=dict(
        line=dict(color='#FFFFFF', width=2),
        colors=['#9ecae1', '#fdae6b', '#a1d99b', '#bcbddc', '#fdd0a2']),
    hole=0.3)

    body_fig.update_layout(
    title_text="Testalkat eloszlása",
    title_x=0.5,
    showlegend=False,
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    margin=dict(t=50, b=0, l=0, r=0))

    return table_data, fig, foot_fig, body_fig

#  Futtatás 
if __name__ == "__main__":
    app.run(debug=True)
