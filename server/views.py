from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from dropbox.exceptions import AuthError 

import json
import os

from dotenv import load_dotenv
from dropbox import Dropbox

import numpy as np
import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go

DEBUG = True

load_dotenv()
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
        zsmooth=False,
        nbinsy=200,
        nbinsx=200,
        hovertemplate="<b>X:</b> %{x}<br><b>Y:</b> %{y}<br><b>Density:</b> %{z}<extra></extra>",
        showscale=False,
    )

    fig = go.Figure(data=heatmap_data)
    fig.update_layout(
        title="VGG Latent Space of 5K Pants",
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


def whiten_data(df, columns):
    # Extract the data to be whitened
    data = df[columns].values

    # Standardize the data
    data_mean = np.mean(data, axis=0)
    data_std = np.std(data, axis=0, ddof=0)
    data_standardized = (data - data_mean) / data_std

    # Compute covariance matrix
    cov_matrix = np.cov(data_standardized, rowvar=False)

    # Perform eigen-decomposition
    eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)

    # Compute whitening matrix
    whitening_matrix = eigenvectors @ np.diag(1.0 / np.sqrt(eigenvalues)) @ eigenvectors.T

    # Apply whitening
    data_whitened = data_standardized @ whitening_matrix

    # Update DataFrame
    df[columns] = data_whitened
    return df


df = pd.read_csv("data.csv")
df = whiten_data(df, ['x', 'y'])
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
    return result[0:8]


def click(request):
    if request.method == "POST":
        print("Received POST request to /click/")
        try:
            data = json.loads(request.body)
            x = data.get("x")
            y = data.get("y")
            print(f"Received coordinates: x={x}, y={y}")

            df["distance"] = np.sqrt((df["x"] - x) ** 2 + (df["y"] - y) ** 2)
            N = 17
            top_N_filenames = df.nsmallest(N, "distance")["filename"].to_list()
            top_N_filenames = remove_duplicate_style(top_N_filenames)

            # Initialize Dropbox with refresh capabilities
            dbx = Dropbox(
                app_secret=os.getenv('DROPBOX_APP_SECRET'),
                oauth2_refresh_token=os.getenv('DROPBOX_REFRESH_TOKEN'),
                app_key=os.getenv('DROPBOX_APP_KEY')
            )
            print("Dropbox initialized with refresh capability")


            # Get temporary links for the top 3 images
            image_links = []
            for filename in top_N_filenames:
                try:
                    print(f"Attempting to get temporary link for: {filename}")
                    temp_link = dbx.files_get_temporary_link(filename)
                    image_links.append(temp_link.link)
                    print(f"Successfully got link for {filename}")
                except AuthError as auth_error:
                    print(f"Authentication error: {str(auth_error)}")
                    # If it's an expired access token, the SDK should automatically refresh it
                    # If it persists, there might be an issue with the refresh token
                    image_links.append(None)
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