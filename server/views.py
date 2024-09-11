from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
import json

import numpy as np
import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go

DEBUG = True

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
def create_plot(df):
    heatmap_data = go.Histogram2d(
        x=df['x'],
        y=df['y'],
        colorscale=[[0, 'rgba(0,0,0,0)'], [1, '#89764a ']],
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

    return pio.to_json(fig)

df = pd.read_csv("data.csv")
plot_data = create_plot(df)

@login_required
def index(request):
    if DEBUG: print("index.html REQUESTED")
    return render(request, 'index.html', {'plot_data': plot_data})


def click(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            x = data.get('x')
            y = data.get('y')

            df['distance'] = np.sqrt((df['x'] - x) ** 2 + (df['y'] - y) ** 2)

            top_4_filenames = df.nsmallest(4, 'distance')['filename'].to_list()
            B = False
            for i in range(3):
                if B: break
                for j in range(i,4):
                    print(top_4_filenames[i])
                    if top_4_filenames[i][-20:] == top_4_filenames[j][-20:]:
                        del top_4_filenames[j]
                        B = True
                        break
            if len(top_4_filenames) == 4: top_3_filenames = top_4_filenames[:-1]
            else: top_3_filenames = top_4_filenames
            print(top_3_filenames)

            return render(request, 'index.html', {'top_3_filenames': top_3_filenames})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})