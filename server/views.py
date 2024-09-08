from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required



@login_required
def index(request):
    return render(request, "index.html")


def login_handler(request):
    print("!!!!!!!", request.method)
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        print(f"Login attempt for user: {username}")
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            print(f"Authentication successful for user: {username}")
            login(request, user)
            print(f"User {username} logged in successfully")
            return redirect("index")
        else:
            print(f"Authentication failed for user: {username}")
            print(f"Password provided: {password}") 
            return render(
                request, "login.html", {"error": "Invalid username or password"}
            )
    else:
        print("GET request to login page")
        return render(request, "login.html")
    
def signup_handler(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')  # Redirect to home page after signup
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

def logout_handler(request):
    logout(request)
    return redirect("login")
