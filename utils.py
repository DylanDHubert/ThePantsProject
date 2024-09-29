from django.db import connections
import plotly.io as pio
import plotly.graph_objects as go

def create_plot_helper(CATEGORY):
    with connections['data'].cursor() as cursor:
        query = f"SELECT x, y FROM {CATEGORY}"
        cursor.execute(query)
        results = cursor.fetchall()

    x, y = zip(*results)

    heatmap_data = go.Histogram2d(
        x=x,
        y=y,
        colorscale=[[0, "rgba(0,0,0,0)"], [1, "#89764a "]],
        zsmooth=False,
        nbinsy=200,
        nbinsx=200,
        hovertemplate="<b>X:</b> %{x}<br><b>Y:</b> %{y}<br><b>Density:</b> %{z}<extra></extra>",
        showscale=False,
    )
    fig = go.Figure(data=heatmap_data)
    fig.update_layout(
        title="VGG Latent Space of ~2K Pants",
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            showline=False,
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            showline=False,
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        modebar=dict(
            orientation='v',
            bgcolor='rgba(0,0,0,0)',  # Set modebar background color to transparent
            activecolor='rgba(0,0,0,0)',  # Set modebar active color to transparent
        ),
    )

    return pio.to_json(fig)

def get_most_similar(x_input, y_input, N=5):
    x_input = float(x_input)
    y_input = float(y_input)
    N = int(N)

    # USE SQL TO GET DATA
    with connections['data'].cursor() as cursor:
        query = """
        SELECT filename
        FROM mens_pants
        ORDER BY (x - %s) * (x - %s) + (y - %s) * (y - %s)
        LIMIT %s
        """
        cursor.execute(query, [x_input, x_input, y_input, y_input, N])
        rows = cursor.fetchall()

    filenames = [row[0] for row in rows]

    return filenames

# CHANGES GLOBAL CATEGORY VARIABLE AND UPDATES GLOBAL plot VARIABLE TO CORRESPOND
def change_category(new_catagory):
    global CATEGORY, plot
    CATEGORY = new_catagory
    plot = create_plot(CATEGORY=new_catagory)

def create_plot(CATEGORY):
    plot = create_plot_helper(CATEGORY=CATEGORY)
    return plot