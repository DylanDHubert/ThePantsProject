from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse, JsonResponse
import json
import os


from dropbox import Dropbox

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

        if DEBUG:
            print(f"LOGIN ATTEMPT FOR USER: {username}")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if DEBUG:
                print(f"AUTHORIZATION CONFIRMED FOR USER: {username}")
            login(request, user)
            if DEBUG:
                print(f"USER {username} LOGGED IN")
            return redirect("index")
        else:
            if DEBUG:
                print(f"AUTHORIZATION FAILED FOR USER: {username}")
                print(f"PROVIDED PASSWORD: {password}")
            return render(
                request, "login.html", {"error": "INVALID USERNAME OR PASSWORD"}
            )
    else:
        if DEBUG:
            print("login.html REQUESTED")
        return render(request, "login.html")


"""
HANDLES SIGNUP FOR NEW USERS...
BUILD USING DJANGO SYSTEM
"""


def signup_handler(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if DEBUG:
            print("SIGN UP FORM SUBMITTED")
        if form.is_valid():
            user = form.save()
            if DEBUG:
                print(f"FORM IS VALID FOR USER: {user}")
            login(request, user)
            if DEBUG:
                print(f"SUCCESSFUL SIGNUP & LOGIN FOR USER: {user}")
            return redirect("index")
    else:
        if DEBUG:
            print("INVALID SIGNUP FORM SUBMITTED, RE–PROMPTING THE USER")
        form = UserCreationForm()
    return render(request, "signup.html", {"form": form})


"""
HANDLES LOGOUT...
BUILD USING DJANGO SYSTEM
"""


def logout_handler(request):
    logout(request)
    if DEBUG:
        print("LOGOUT CONFIRMED")
    return redirect("login")


"""
SCATTER PLOT...
???
"""


def create_plot(df):
    heatmap_data = go.Histogram2d(
        x=df["x"],
        y=df["y"],
        colorscale=[[0, "rgba(0,0,0,0)"], [1, "#89764a "]],
        zsmooth=None,
        nbinsy=50,
        nbinsx=100,
        hovertemplate="<b>X:</b> %{x}<br><b>Y:</b> %{y}<br><b>Density:</b> %{z}<extra></extra>",
        showscale=False,
    )

    fig = go.Figure(data=heatmap_data)
    fig.update_layout(
        title="VGG Latent Space of 1000 Pants",
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
    )

    return pio.to_json(fig)


df = pd.read_csv("data.csv")
plot_data = create_plot(df)


@login_required
def index(request):
    if DEBUG:
        print("index.html REQUESTED")
    return render(request, "index.html", {"plot_data": plot_data})


"""
FUNCTION USED IN --> click()

"""
def remove_duplicate_style(filenames):
    result = []
    for filename in filenames:
        if not any(filename[-20:] == f[-20:] for f in result):
            result.append(filename)
        if len(result) == 3:
            break
    return result


def click(request):
    if request.method == "POST":
        print("Received POST request to /click/")
        try:
            data = json.loads(request.body)
            x = data.get("x")
            y = data.get("y")
            print(f"Received coordinates: x={x}, y={y}")

            df["distance"] = np.sqrt((df["x"] - x) ** 2 + (df["y"] - y) ** 2)
            top_4_filenames = df.nsmallest(4, "distance")["filename"].to_list()
            top_3_filenames = remove_duplicate_style(top_4_filenames)
            print(f"Top 3 filenames: {top_3_filenames}")

            # Initialize Dropbox
            dbx = Dropbox(settings.DROPBOX_ACCESS_TOKEN)
            print("Dropbox initialized")

            # Get temporary links for the top 3 images
            image_links = []
            for filename in top_3_filenames:
                try:
                    # Ensure the file path is correctly formatted
                    
                    print(f"Attempting to get temporary link for: {filename}")
                    temp_link = dbx.files_get_temporary_link(filename)
                    image_links.append(temp_link.link)
                    print(f"Successfully got link for {filename}")
                except Exception as e:
                    print(f"Error getting Dropbox link for {filename}: {str(e)}")
                    image_links.append(None)

            print(f"Returning image links: {image_links}")
            return JsonResponse({"status": "success", "image_links": image_links})
        except Exception as e:
            print(f"Error in click view: {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)})
    else:
        print("Received non-POST request to /click/")
        return JsonResponse({"status": "error", "message": "Invalid request method"})