# DJANGO IMPORTS
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from dropbox.exceptions import AuthError
from django.db import connections

# OPERATIONAL IMPORTS
import json
import os

# DROPBOX SYSTEM IMPORTS
from dotenv import load_dotenv
from dropbox import Dropbox

# UTILITY FUNCTIONS
import utils


# —————————————————————————————————————
# ENDPOINTS
# —————————————————————————————————————

@login_required
def index(request):
    if DEBUG:
        print("index.html REQUESTED")
    return render(request, "index.html", {"plot_data": plot})


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


def logout_handler(request):
    logout(request)
    if DEBUG:
        print("LOGOUT CONFIRMED")
    return redirect("login")


# GETS CLICK ON GRAPH AND SEARCHES LATENT SPACE (IN data.sqlite3)
def click(request):
    if request.method == "POST":
        print("Received POST request to /click/")
        try:
            data = json.loads(request.body)
            x = data.get("x")
            y = data.get("y")
            print(f"Received coordinates: x={x}, y={y}")
            # X AND Y ARE RECEIVED CORRECTLY

            # GET TOP N MOST SIMILAR (USING data.sqlite3)
            N = 8
            top_N_filenames = utils.get_most_similar(x_input=x, y_input=y, N=N)

            # Initialize Dropbox with refresh capabilities
            dbx = Dropbox(
                app_secret=os.getenv('DROPBOX_APP_SECRET'),
                oauth2_refresh_token=os.getenv('DROPBOX_REFRESH_TOKEN'),
                app_key=os.getenv('DROPBOX_APP_KEY')
            )
            print("Dropbox initialized with refresh capability")

            # GET TEMP. LINKS FOR TOP N IMAGES
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


# CHANGES CATEGORY BASED ON DROPDOWN SELECTION
def dropdown(request):
    utils.change_category(request.GET.get('option'))
    return redirect("index")


# —————————————————————————————————————
# "MAIN" CODE
# —————————————————————————————————————

# DEBUG SETTING
DEBUG = True

# "CATEGORY" FOR DISPLAY, DEFAULTS TO mens_pants
CATEGORY = "mens_pants"
# CREATE plot FOR INITIAL LOAD...
plot = utils.create_plot(CATEGORY=CATEGORY)

# LOAD DROPBOX THING
load_dotenv()
