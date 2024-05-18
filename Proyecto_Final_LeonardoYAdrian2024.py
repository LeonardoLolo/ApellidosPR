# Importante descargar lo siguiente:
# !pip install -q dash
# !pip install -q plotly
# !pip install -q dash_bootstrap_components
# !pip install -q dash_daq
# !pip install -q fuzzywuzzy

# -*- coding: utf-8 -*-
"""
Created on Fri May 17 01:36:06 2024

@author: Leonardo Morales Casillas,
        leonardo.morales2@upr.edu
        
   Proyecto Final:Reimplementación de apellidosPR
   utilizando datos a escala de unidad electoral      

"""
#######################################################

#             Adrian R. Roldan Richards
#             Leonardo Morales Casillas
#                17 de mayo de 2024
#                     Web Apps
#    Proyecto Final: Reimplementación de apellidosPR
#      utilizando datos a escala de unidad electoral
#

######################################################

# Librerias
import pandas as pd
import plotly.express as px
import ssl
from dash import Dash, dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import dash
import json
import numpy as np
from shapely.geometry import Point, Polygon
import geopandas as gpd
from fuzzywuzzy import fuzz, process
import plotly.graph_objs as go
import requests
import json

ssl._create_default_https_context = ssl._create_unverified_context

app = dash.Dash(external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css"],
                meta_tags=[{'name' : 'viewport',
                            'content': 'width=device-width, initial-scale=1'}])


# Diccionario para eliminar los acentos
rep = str.maketrans("ÁÉÍÓÚáéíóú", "AEIOUaeiou")

df = pd.read_parquet('https://cdat.uprh.edu/~leonardo.morales2/Datos_ProyectFinal2024/info_poblacion.parquet', engine='pyarrow')
df['municipio'] = df['municipio'].str.upper().str.translate(rep)#.astype('category')
tabla_municipio = pd.read_parquet('https://cdat.uprh.edu/~adrian.roldan/datos_Proyecto3/tabla_municipio.parquet')
tabla_codigo = pd.read_parquet('https://cdat.uprh.edu/~adrian.roldan/datos_Proyecto3/tabla_codigo.parquet')
tabla_year = pd.read_parquet('https://cdat.uprh.edu/~adrian.roldan/datos_Proyecto3/tabla_year.parquet')
pobDict = dict(zip(df["municipio"], df["poblacion"]))
pobDict_code = dict(zip(df["codigo"].astype(str), df["poblacion"]))

# Cargar y modificar el GeoJSON con la codificación correcta
codigo_to_municipio = pd.Series(df['municipio'].values, index=df['codigo']).to_dict()
nombre_mun = pd.read_csv("https://cdat.uprh.edu/~adrian.roldan/datos_Proyecto3/nombre_municipios.csv", encoding="ISO-8859-1")

# URL del archivo GeoJSON
url = "https://cdat.uprh.edu/~adrian.roldan/datos_Proyecto3/unidades_4326.geojson"

# Solicitar el contenido del archivo
response = requests.get(url)
response.raise_for_status()  # Esto lanzará un error si la solicitud no fue exitosa

# Cargar el contenido JSON
mapaUnidades = json.loads(response.content)

# Guardar el GeoJSON modificado
with open("unidades_4326_filtrado.geojson", 'w', encoding='utf-8') as f:
    json.dump(mapaUnidades, f, ensure_ascii=False)    
    

for feature in mapaUnidades['features']:
    precinto_num = feature['properties']['precinto']
    unidad_num = feature['properties']['unidad']
    feature['properties']['codigo'] = (precinto_num * 100) + unidad_num

for feature in mapaUnidades['features']:
    codigo = feature['properties']['codigo']
    # Set the 'municipio' property if 'codigo' is in the mapping dictionary
    if codigo in codigo_to_municipio:
        feature['properties']['municipio'] = codigo_to_municipio[codigo].upper()
    else:
        # Optionally, handle features without a matching 'codigo'
        feature['properties']['municipio'] = None  # Or some default value or indicator

#==============================================================================
@callback(
    Output('analysis-output', 'children'),  # Update the output target
    Input('input-apellido', 'value')
)

def analisisApellido(miApellido):


    miApellido = miApellido.upper().strip().translate(rep)

    if miApellido in tabla_municipio.columns:
        df_apellido = tabla_municipio[miApellido]

        # Calculating ranking
        ranking = tabla_municipio.sum().sort_values(ascending=False)
        posicion = ranking.index.get_loc(miApellido)+1

        # Calculating count
        conteo = tabla_municipio[miApellido]
        conteo_apellido = conteo.sum()
        conteo_total = tabla_municipio.sum().sum()

        # Calculating frequency
        frecuencia = {}
        for key in pobDict:
            if str(key) in conteo:
                frecuencia[key] = 100 * conteo[str(key)] / pobDict[key]
            else:
                frecuencia[key] = 0

        df_frecuencia = pd.DataFrame.from_dict(frecuencia, orient='index', columns=['frecuencia']).reset_index()
        df_frecuencia.rename(columns={'index': 'municipio'}, inplace=True)
        df_frecuencia.sort_values("frecuencia", ascending=False, inplace=True)

        primeros_cinco = list(df_frecuencia['municipio'][:5])

        # Finding the unit with the most people
        conteo2 = tabla_codigo[miApellido].sort_values(ascending=False)
        primero = str(conteo2.index[0])
        precinto = primero[:-2]
        pueblo = nombre_mun[nombre_mun['precinto'] == int(precinto)]['municipio'].iloc[0].upper()

        # Constructing the message to be displayed
        output = html.Div([
            html.H5(f"Análisis del apellido {miApellido}", style={'color': 'lightblue', 'text-align': 'center'}),
            html.H5(f"Ocupa la posición número {posicion:,} entre {len(ranking):,} apellidos distintos.", style={'color': 'white','text-align': 'center'}),
            html.H5(f"Hay {conteo_apellido:,} personas con ese apellido de un total de {conteo_total:,}.", style={'color': 'white','text-align': 'center'}),
            html.H5(f"Es más frecuente en los siguientes municipios: {', '.join(primeros_cinco)}.", style={'color': 'white','text-align': 'center'}),
            html.H5(f"Hay mayor cantidad de personas en la unidad {primero} en el pueblo {pueblo}", style={'color': 'white','text-align': 'center'})
        ], style={'text-align': 'center', 'width': '100%'})

        return output

    else:
        output = html.Div([
            html.H5(f"Análisis del apellido {miApellido}", style={'color': 'lightblue', 'text-align': 'center'}),
            html.H5("Apellido no disponible", style={'color': 'white','text-align': 'center'}),
            html.H5("Apellido no disponible", style={'color': 'white','text-align': 'center'}),
            html.H5("Apellido no disponible", style={'color': 'white','text-align': 'center'})
        ], style={'text-align': 'center', 'width': '100%'})

        return output

    return html.Div(["Ingrese un apellido para analizar."], style={'color': 'white', 'text-align': 'center', 'width': '100%'})  # Default message if no input is given


@callback(
    Output("apellidos-similares", "children"),
    Input("input-apellido", "value")
)

def update_apellidoSimilares(miApellido):

    miApellido = miApellido.upper().translate(rep)

    if miApellido in tabla_municipio.columns:

        # Filtra apellidos con las mismas tres primeras letras
        tres_primeras_letras = miApellido[:3]
        apellidos_unicos = tabla_municipio.columns.tolist()
        apellidos_similares = [apellido for apellido in apellidos_unicos if apellido.startswith(tres_primeras_letras)]

        # Limita a los primeros 5 apellidos similares
        apellidos_similares = apellidos_similares[:5]

        apellidos_similares_format = ', '.join(apellidos_similares)


        return [

            html.P(f"Apellidos similares: {apellidos_similares_format}",
                   style={'font-weight': 'bold',
                          'margin-top': '20px',
                          'margin-bottom': '20px',
                          'color': 'white'
                          })
      ]

    else:
        return [
                html.P(" "),

            ]


#==============================================================================
app.layout = html.Div([
    html.Div(
        style={'backgroundColor': '#333333', 'height': '100vh'},
        children=[
                   dbc.Row(
                       dbc.Col(
                           [
                               html.H1("apellidosPR", style={'text-align': 'left', 'color': 'lightblue', 'margin-bottom': '10px'}),
                               html.H2("Una aplicación para el análisis y visualización espacial de los apellidos en Puerto Rico",
                                       style={'text-align': 'left', 'color': 'red'}),
                           ],
                           style={
                               'border': '3px solid black',
                               'padding': '20px',
                               'margin': '0 auto',
                               'backgroundColor':'#343d46',
                               'width': '97%',
                               'border-radius': '10px',
                               'marginTop': '10px',
                               'marginBottom': '20px'
                           },
                           width=12
                       )
                   ),

            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.I("Entre Apellido",style={'color': 'white'}),
                        dcc.Input(id="input-apellido", type="text", value="RIVERA", debounce=True,
                                  style={'margin': 'auto', 'display': 'block', 'width': '100%', 'float': 'left',
                                          'marginTop': '5px','paper_bgcolor':'#696969'}),
                        html.H5(
                            "No incluya acentos y puede utilizar letras mayúsculas o minúsculas",
                            style={'color': '#59C3E0', 'text-align': 'left', 'marginTop': '10px'}
                        )
                    ], style={'display': 'flex', 'flex-direction': 'column', 'align-items': 'left',
                              'margin-bottom': '20px', 'margin-top': '50px', 'padding': '10px',
                              'border': '3px solid #0e2f44', 'borderRadius': '5px',
                              "paper_bgcolor": '#333333', 'width': '30%','marginLeft':'20px'})
                ], md=6),

                dbc.Col([

                    html.Div([
                        html.Img(src='https://cdat.uprh.edu/~leonardo.morales2/Datos_ProyectFinal2024/apellidosPR_Logo.jpg',
                                  style={'height': 'auto', 'width': '100%'}),
                    ], style={'padding': '10px', 'float': 'right', 'display': 'flex',
                              'flex-direction': 'column',
                              'margin-left': '950px', 'align-items': 'right', 'margin-top': '-230px'}),

                ], md=6),

                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.P("Seleccione el rango de años:", style={'textAlign': 'center', 'marginTop': '20px'}),
                            dcc.RangeSlider(
                                id='year-slider',
                                min=1800,
                                max=2024,
                                value=[1800, 2024],
                                marks={str(year): str(year) for year in range(1800, 2025, 10)},
                                step=1,
                                allowCross=False
                            ),
                            html.Div(id="slider-output-container", style={'textAlign': 'center', 'marginTop': '10px'})
                        ], style={'padding': '20px', 'color':'white'})
                    ], md=12)
                ]),

                dbc.Row([
                    dbc.Col([
                        html.Div(id='analysis-output', style={'padding': '10px', 'fontSize': '16px',
                                                              'textAlign': 'center','backgroundColor':'#333333',
                                                              'border': '3px solid black', 'borderRadius': '5px',
                                                              'margin': '10px 0'})
                    ], width={'size': 10, 'offset': 1})  # Centering the column
                ]),

                dbc.Row([
                    dbc.Col(dcc.Graph(id='bar-graph', style={'height': 'auto', 'width': '49.5%',
                                                              'border': '3px solid black'}),
                            md=6, className="col-md-6", align='center'),
                    dbc.Col(dcc.Graph(id='pie-chart', style={'height': 'auto', 'width': '50%',
                                                              'float': 'right', 'margin-top': '-455px',
                                                              'border': '3px solid black'}),
                            md=6, className="col-md-6", align='right')
                ]),
                dbc.Row([
                    dbc.Col(dcc.Graph(id='bar2-graph', style={'height': 'auto', 'width': '49.5%',
                                                                'border': '3px solid black',
                                                                'float': 'left'}),
                            md=6, className="col-md-6", align='center'),
                    dbc.Col(dcc.Graph(id="pie2-chart",
                                      style={'height': 'auto', 'width': '50%', 'border': '3px solid black',
                                              'margin-top': '-455px', 'float': 'right'}
                                      ), md=6, className="col-md-6", align='center')
                ]),

                dbc.Row([

                    html.Div([
                        dcc.Graph(id='line-chart')
                    ], style={'height': 'auto', 'width': '99.5%', 'border': '3px solid black'})


                    ]),

                dbc.Row([
                    dcc.Graph(
                        id="cloropleth-graph",
                        style={'height': 'auto', 'width': '99.5%', 'border': '3px solid black'})
                ]),

                dbc.Row([
                    dbc.Col([

                    html.Div([

                    html.Div(id='apellidos-similares', style={'padding': '10px', 'fontSize': '14px',
                                                            'text-align': 'center',
                                                            'backgroundColor':'#333333'})


                    ], style={
                        'border': '1px solid black',
                        'borderRadius': '5px',
                        'margin-left': '30px',
                        'margin-right': '100px',
                        'margin-bottom': '30px',
                        'margin-top': '20px',
                        'backgroundColor':'#333333'
                    })

                    ],width=12)

                ])


            ]),
        ])
])


@callback(
    Output('slider-output-container', 'children'),
    Input('year-slider', 'value')
)
def update_output(value):
    return f'Selecciones el rango de años: {value[0]} a {value[1]}'


#==============================================================================
def graficoGenerico(miApellido):

    miApellido = miApellido.upper().strip().translate(rep)

    if miApellido not in tabla_codigo.columns:

        fig = go.Figure()

        fig.update_layout(
            xaxis=dict(showgrid=True, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=True, showticklabels=False, zeroline=False),
            paper_bgcolor="white",
            margin=dict(r= 50, t= 65, l= 50, b= 25)
        )

        fig.add_annotation(
            x=0.5,
            y=0.5,
            xref='paper',
            yref='paper',
            text=f"Apellido {miApellido} NO está disponible",
            showarrow=False,
            font=dict(
                size=20,
                color="black"
            ),
            align='center'
        )

        fig.update_layout(

            shapes=[
                dict(
                    type="rect",
                    xref="paper",
                    yref="paper",
                    x0=0,
                    y0=0,
                    x1=1,
                    y1=1,
                    line=dict(
                        color="white",
                        width=1,
                    ),
                    fillcolor="rgba(0,0,0,0)"
                )
              ]

            )

        fig.update_layout(
                paper_bgcolor="#333333",
                plot_bgcolor='#696969',

            )


    return fig


#==============================================================================
@callback(
    Output('bar-graph', 'figure'),
    [Input('input-apellido', 'value'),
    Input("year-slider", "value")]
)

def grafico_Barras(miApellido, year_range):

    miApellido = miApellido.upper().strip().translate(rep)

    if miApellido not in tabla_codigo.columns:
        return graficoGenerico(miApellido)

    filtered_df = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]

    # Convertir columnas a 'category' si aplicable
    df['municipio'] = df['municipio'].astype('category')
    df['Paterno'] = df['Paterno'].astype('category')

    tabla_municipio = pd.crosstab(index= filtered_df['municipio'], columns=  filtered_df ['Paterno'])

    if miApellido in tabla_municipio.columns:
        df_apellido = tabla_municipio[miApellido]


        # Calcula la frecuencia relativa basada en la población
        frecuencia = {}

        for municipio in df_apellido.index:
            poblacion_municipio = pobDict.get(municipio, 1)  # Evitar división por cero
            frecuencia[municipio] = 100 * (df_apellido[municipio] / poblacion_municipio)

        # Creando un DataFrame para el gráfico de barras
        df_frecuencia = pd.DataFrame(list(frecuencia.items()), columns=["municipio", "frecuencia"])
        df_frecuencia.sort_values("frecuencia", ascending=False, inplace=True)


        custom_palette = [
            '#FBE3E0 ',  # Rojo más claro
            '#fb8b79',  # Rojo claro
            '#fb4a46',  # Rojo medio
            '#ff3333',  # Rojo oscuro
            '#800000'   # Rojo más oscuro
        ]

        # Creando el bar graph
        fig = px.bar(df_frecuencia[0:10],
                     x="frecuencia",
                     y="municipio",
                     color="frecuencia",
                     labels={'municipio':'Municipio','frecuencia':'Frecuencia'},
                     color_continuous_scale=custom_palette,
                     orientation="h",
                     title=f'Histograma de frecuencia para el apellido <b>{miApellido}</b>'
                     )
        fig.update_layout(showlegend=False)
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(margin={"r": 50, "t": 60, "l": 30, "b": 50})

        fig.update_layout(title={
            'text': f'Histograma de frecuencia para el apellido <b>{miApellido}</b>' ,
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {
                'size': 14,
                'color':'white'
            }
        })

        fig.update_layout(

            shapes=[
                dict(
                    type="rect",
                    xref="paper",
                    yref="paper",
                    x0=0,
                    y0=0,
                    x1=1,
                    y1=1,
                    line=dict(
                        color="white",
                        width=1,
                    ),
                    fillcolor="rgba(0,0,0,0)"
                )
              ]

            )

        fig.update_layout(
                xaxis=dict(
                    tickfont=dict(color='white')
        ),
                yaxis=dict(
                    tickfont=dict(color='white')
        ))

        fig.update_layout(
                paper_bgcolor="#333333",
                plot_bgcolor='#696969',
                xaxis_title_font=dict(color='white'),  # Change the color of the x-axis title
                yaxis_title_font=dict(color='white'),  # Change the color of the y-axis title
                coloraxis_colorbar=dict(
                        tickfont=dict(color='white'),
                        title=dict(text='Frecuencia', font=dict(color='white'))
            ))

    return  fig


#==============================================================================
@callback(
    Output("pie-chart", "figure"),
    [Input("input-apellido", "value"),
     Input("year-slider", "value")]
)

def pie_chart(miApellido, year_range):

    miApellido = miApellido.upper().strip().translate(rep)

    if miApellido not in tabla_codigo.columns:
        return graficoGenerico(miApellido)

    filtered_df = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
    tabla_municipio = pd.crosstab(index= filtered_df ['municipio'], columns=  filtered_df ['Paterno'])

    if miApellido in tabla_municipio.columns:
        df_apellido = tabla_municipio[miApellido]

        # Calculate relative frequency based on population
        frecuencia = {municipio: 100 * (df_apellido[municipio] / pobDict.get(municipio, 1))
                      for municipio in df_apellido.index}

        # Creando un DataFrame para el gráfico de barras
        df_frecuencia = pd.DataFrame(list(frecuencia.items()), columns=["municipio", "frecuencia"])
        df_frecuencia.sort_values("frecuencia", ascending=False, inplace=True)

        # Define custom color scale
        custom_palette = ['#FBE3E0', '#fb8b79', '#fb4a46', '#ff3333', '#800000']  # Lightest to darkest
        # Escala de colores en función de la frecuencia
        freq_max = df_frecuencia['frecuencia'].max()
        freq_min = df_frecuencia['frecuencia'].min()
        df_frecuencia['color'] = df_frecuencia['frecuencia'].apply(
            lambda x: custom_palette[int((x - freq_min) / (freq_max - freq_min) * (len(custom_palette) - 1))]
        )

        fig = px.pie(df_frecuencia[0:10],
                     values='frecuencia',
                     names='municipio',
                     color='color',            
                     labels={'municipio':'Municipio','frecuencia':'Frecuencia',
                             'color':'Color'},
                     color_discrete_map={color: color for color in custom_palette})

        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(showlegend=False)
        fig.update_layout(margin={"r": 0, "t": 60, "l": 0, "b": 15})

        fig.update_layout(title={
            'text': f'Pie chart de frecuencia para el apellido <b>{miApellido}</b>' ,
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {
                'size': 14,
                'color':'white'
            }
        })

        fig.update_layout(
                xaxis=dict(
                    tickfont=dict(color='white')
        ),
                yaxis=dict(
                    tickfont=dict(color='white')
        ))

        fig.update_layout(
                paper_bgcolor="#333333",
                plot_bgcolor='#696969'
            )

    return  fig
#==============================================================================

custom_color_scale = [
    (0, "white"),                  # Start at the minimum value with white
    (1/6, "#ffcccc"),              # Lightest red
    (2/6, "#ff9999"),              # Light red
    (3/6, "#ff6666"),              # Medium light red
    (4/6, "#ff3333"),              # Medium dark red
    (5/6, "#ff0000"),              # Dark red
    (1, "#5E0B0B")                 # Darkest red at the maximum value
]


@callback(
    Output('cloropleth-graph', 'figure'),
    Input('input-apellido', 'value')
)

def update_map(miApellido):

    miApellido = miApellido.upper().strip().translate(rep)
    df_frecuencia_code = pd.DataFrame()

    if miApellido in tabla_codigo.columns:
        conteo = tabla_codigo[miApellido]
        conteo.index = conteo.index.astype(str)

        # Calculate the frequency percentage for each key in 'pobDict'
        frecuencia = {}
        for key in pobDict_code:
            if str(key) in conteo:
                frecuencia[key] = 100 * conteo[str(key)] / pobDict_code[key]
            else:
                frecuencia[key] = 0

        # Create a DataFrame for choropleth
        df_frecuencia_code = pd.DataFrame(list(frecuencia.items()), columns=["codigo", "frecuencia"])
        df_frecuencia_code.sort_values("frecuencia", ascending=False, inplace=True)

        # Apply logarithmic transformation and handle cases where value could be zero
        df_frecuencia_code['frecuencia'] = np.log1p(df_frecuencia_code['frecuencia'])

    # Ensure the DataFrame has data to plot
    if df_frecuencia_code.empty:
        return graficoGenerico(miApellido)

    else:
        # Ensure you have set up your Mapbox Access Token
        px.set_mapbox_access_token('pk.eyJ1IjoiYWRyLXJvbDIwMDMiLCJhIjoiY2wya2lsY2RhMHJydzNpbndoYzczeXZzZCJ9.zWN680-oRGm402AwkYenAQ')

        # Custom color scale from white to red
        white_to_red = [
            (0, 'white'),  # Start with white
            (1, 'red')     # End with red
        ]

        # Adjusted function to use choropleth_mapbox
        fig = px.choropleth_mapbox(
                df_frecuencia_code,
                geojson=mapaUnidades,
                locations='codigo',
                color='frecuencia',
                featureidkey="properties.codigo",
                color_continuous_scale=white_to_red,
                mapbox_style="dark",
                zoom=8,
                center={"lat": 18.2208, "lon": -66.5901},
                opacity=0.8
        )
        fig.update_layout(margin={"r": 50, "t": 65, "l": 50, "b": 20})
        fig.update_layout(coloraxis_showscale=False)
        fig.update_layout(clickmode='event')
        fig.update_layout(autosize=True)

        fig.update_layout(title={
            'text': f'Mapa Coroplético para el apellido <b>{miApellido}</b>',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {
                'size': 14,
                'color':'white'
            }
        })

        # El borde para el grafico
        fig.update_layout(

            shapes=[
                dict(
                    type="rect",
                    xref="paper",
                    yref="paper",
                    x0=0,
                    y0=0,
                    x1=1,
                    y1=1,
                    line=dict(
                        color="white",
                        width=3,
                    ),
                    fillcolor="rgba(0,0,0,0)"
                )
              ]

            )

        fig.update_layout(
                xaxis=dict(
                    tickfont=dict(color='white')
        ),
                yaxis=dict(
                    tickfont=dict(color='white')
        ))

        fig.update_layout(plot_bgcolor="#696969")
        fig.update_layout(paper_bgcolor="#333333")

    return fig

#==============================================================================
@callback(
    Output("bar2-graph", "figure"),
    [Input("input-apellido", "value"),
     Input("year-slider", "value")]
)

def generaciones_barGraph(miApellido, year_range):

    miApellido = miApellido.upper().strip().translate(rep)

    if miApellido not in tabla_codigo.columns:
        return graficoGenerico(miApellido)

    filtered_df = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
    tabla_gen = pd.crosstab(index= filtered_df['Generation'], columns=  filtered_df ['Paterno'])

    if miApellido in tabla_municipio.columns:
        df_apellido = tabla_gen[miApellido]

        apellido_data = tabla_gen[miApellido]

        apellido_percent = round(apellido_data / apellido_data.sum() * 100,2)

        # Creando el bar graph
        fig = px.bar(
                     x=apellido_percent.index,
                     y=apellido_data.values,
                     color=apellido_percent.index,
                     color_discrete_sequence=px.colors.qualitative.Plotly,
                     labels={'x':'Generacion','y':'Porcentaje'},
                     )
        fig.update_layout(showlegend=False)
        fig.update_layout(margin={"r": 50, "t": 60, "l": 30, "b": 50})

        fig.update_layout(title={
            'text': f'Histograma de la generacion perteneciente del apellido <b>{miApellido}</b>' ,
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {
                'size': 14,
                'color':'white'
            }
        })

        fig.update_layout(

            shapes=[
                dict(
                    type="rect",
                    xref="paper",
                    yref="paper",
                    x0=0,
                    y0=0,
                    x1=1,
                    y1=1,
                    line=dict(
                        color="white",
                        width=1,
                    ),
                    fillcolor="rgba(0,0,0,0)"
                )
              ]

            )

        fig.update_layout(
                xaxis=dict(
                    tickfont=dict(color='white')
        ),
                yaxis=dict(
                    tickfont=dict(color='white')
        ))

        fig.update_layout(
                paper_bgcolor="#333333",
                plot_bgcolor='#696969',
                xaxis_title_font=dict(color='white'),  # Change the color of the x-axis title
                yaxis_title_font=dict(color='white')  # Change the color of the y-axis title

            )

        return  fig

#==============================================================================
@callback(
    Output("pie2-chart", "figure"),
    [Input("input-apellido", "value"),
     Input("year-slider", "value")]
)

def pieChartGen(miApellido, year_range):

    miApellido = miApellido.upper().strip().translate(rep)

    if miApellido not in tabla_codigo.columns:
        return graficoGenerico(miApellido)

    filtered_df = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1])]
    tabla_gen = pd.crosstab(index= filtered_df ['Generation'], columns=  filtered_df ['Paterno'])

    apellido_data = tabla_gen[miApellido]
    apellido_percent = round(apellido_data / apellido_data.sum() * 100,2)

    # Create the pie chart
    fig = px.pie(
        names=apellido_percent.index,  
        values=apellido_percent.values,  
        title='Percentage of People by Generation',  
        color_discrete_sequence=px.colors.qualitative.Plotly
    )

    fig.update_layout(title={
        'text': f'Pie chart de la generacion del apellido <b>{miApellido}</b>' ,
        'y': 0.95,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top',
        'font': {
            'size': 14,
            'color':'white'
        }
    })

    fig.update_layout(margin={"r": 0, "t": 60, "l": 0, "b": 15})

    fig.update_layout(
            paper_bgcolor="#333333",
            plot_bgcolor='#696969',
            legend=dict(
                font=dict(
                    color='white'  # Cambia el color del texto de la leyenda a rojo
                )
            )

        )

    return fig

#==============================================================================
@callback(
    Output("line-chart", "figure"),
    Input("input-apellido", "value")
)

def lineChartGen(miApellido):

    miApellido = miApellido.upper().strip().translate(rep)

    if miApellido not in tabla_municipio.columns:
        return graficoGenerico(miApellido)

    apellido_data = tabla_year[miApellido]

    apellido_percent = round(apellido_data / apellido_data.sum() * 100,2)

    fig_line = go.Figure()

    fig_line.add_trace(
        go.Scatter(
            x=apellido_percent.index,
            y=apellido_data.values,
            mode='lines',
            marker=dict(color='red'),
            name='Datos'
        )
    )

    # Agregar anotaciones para las generaciones en el lado derecho
    annotations = [
        dict(
            x=1.20,
            y=1,
            xref="paper",
            yref="paper",
            text="Pre-Lost Generation (1800-1882)",
            showarrow=False,
            font=dict(color="white"),
            align="left",
            bgcolor="#333333"
        ),
        dict(
            x=1.20,
            y=0.9,
            xref="paper",
            yref="paper",
            text="Lost Generation (1883-1900)",
            showarrow=False,
            font=dict(color="white"),
            align="left",
            bgcolor="#333333"
        ),
        dict(
            x=1.20,
            y=0.8,
            xref="paper",
            yref="paper",
            text="Greatest Generation (1901-1927)",
            showarrow=False,
            font=dict(color="white"),
            align="left",
            bgcolor="#333333"
        ),
        dict(
            x=1.20,
            y=0.7,
            xref="paper",
            yref="paper",
            text="Silent Generation (1928-1945)",
            showarrow=False,
            font=dict(color="white"),
            align="left",
            bgcolor="#333333"
        ),
        dict(
            x=1.20,
            y=0.6,
            xref="paper",
            yref="paper",
            text="Baby Boomers (1946-1964)",
            showarrow=False,
            font=dict(color="white"),
            align="left",
            bgcolor="#333333"
        ),
        dict(
            x=1.20,
            y=0.5,
            xref="paper",
            yref="paper",
            text="Generation X (1965-1980)",
            showarrow=False,
            font=dict(color="white"),
            align="left",
            bgcolor="#333333"
        ),
        dict(
            x=1.20,
            y=0.4,
            xref="paper",
            yref="paper",
            text="Millennials (1981-1996)",
            showarrow=False,
            font=dict(color="white"),
            align="left",
            bgcolor="#333333"
        )
    ]

    fig_line.update_layout(
        shapes=[
            dict(
                type="rect",
                xref="paper",
                yref="paper",
                x0=0,
                y0=0,
                x1=1,
                y1=1,
                line=dict(
                    color="white",
                    width=1,
                ),
                fillcolor="rgba(0,0,0,0)"
            )
        ],
        margin={"r":250, "t":60, "l":40, "b":25},
        annotations=annotations
    )

    fig_line.update_layout(title={
        'text': f'Grafica de linea de las generaciones del apellido <b>{miApellido}</b>',
        'y': 0.95,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top',
        'font': {
            'size': 14,
            'color':'white'
        }
    })

    fig_line.update_layout(
        xaxis=dict(
            tickfont=dict(color='white'),
            range=[1800, 2024]  # Establece el rango del eje x desde el mínimo hasta el máximo valor
        ),
        yaxis=dict(
            tickfont=dict(color='white')
        ),
        plot_bgcolor="#696969",
        paper_bgcolor="#333333",
        xaxis_title='Años',
        yaxis_title='Cantidad',
        xaxis_title_font=dict(color='white'),  # Change the color of the x-axis title
        yaxis_title_font=dict(color='white'))


    return fig_line



if __name__ == '__main__':
    app.run_server(debug=True)

