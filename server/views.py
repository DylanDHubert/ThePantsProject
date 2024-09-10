from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse


import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go

DEBUG = True


@login_required
def index(request):
    if DEBUG: print("index.html REQUESTED")
    return render(request, "index.html")


"""
HANDLES LOGIN FOR USERS...
MAIN PAGE (INDEX) REQUIRES VALID LOG IN
BUILD USING DJANGO SYSTEM
"""
def login_handler(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if DEBUG: print(f"LOGIN ATTEMPT FOR USER: {username}")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if DEBUG: print(f"AUTHORIZATION CONFIRMED FOR USER: {username}")
            login(request, user)
            if DEBUG: print(f"USER {username} LOGGED IN")
            return redirect("index")
        else:
            if DEBUG:
                print(f"AUTHORIZATION FAILED FOR USER: {username}")
                print(f"PROVIDED PASSWORD: {password}")
            return render(
                request, "login.html", {"error": "INVALID USERNAME OR PASSWORD"}
            )
    else:
        if DEBUG: print("login.html REQUESTED")
        return render(request, "login.html")

"""
HANDLES SIGNUP FOR NEW USERS...
BUILD USING DJANGO SYSTEM
"""
def signup_handler(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if DEBUG: print("SIGN UP FORM SUBMITTED")
        if form.is_valid():
            user = form.save()
            if DEBUG: print(f"FORM IS VALID FOR USER: {user}")
            login(request, user)
            if DEBUG: print(f"SUCCESSFUL SIGNUP & LOGIN FOR USER: {user}")
            return redirect('index')
    else:
        if DEBUG: print("INVALID SIGNUP FORM SUBMITTED, RE–PROMPTING THE USER")
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})


"""
HANDLES LOGOUT...
BUILD USING DJANGO SYSTEM
"""
def logout_handler(request):
    logout(request)
    if DEBUG: print("LOGOUT CONFIRMED")
    return redirect("login")


"""
SCATTER PLOT...
???
"""
df = pd.read_csv("data.csv")

heatmap_data = go.Histogram2d(
    x=df['x'],
    y=df['y'],
    colorscale=[[0, 'rgba(0,0,0,0)'], [1, '#55B059']],
    zsmooth=None,
    nbinsy=50,
    nbinsx=100,
    hovertemplate='<b>X:</b> %{x}<br><b>Y:</b> %{y}<br><b>Density:</b> %{z}<extra></extra>',
    showscale=False,
)

fig = go.Figure(data=heatmap_data)
fig.update_layout(
    title='VGG Latent Space of 1000 Pants',
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
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    )

def plot(request):
    plot_html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')
    return HttpResponse(plot_html, content_type='text/html')