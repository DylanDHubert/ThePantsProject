# DJANGO IMPORTS
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dropbox.exceptions import AuthError
from django.db import connections

# OPERATIONAL IMPORTS
import json
import os
import numpy as np
import base64

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
            N = 6
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
# GAN-RELATED VIEWS
# —————————————————————————————————————

@login_required
def gan_visualizer(request):
    """View for the GAN-based latent space visualization"""
    if DEBUG:
        print("gan_visualizer.html REQUESTED")
    
    # Check if StyleGAN is available
    stylegan_available = getattr(utils, 'STYLEGAN_AVAILABLE', False)
    print(f"StyleGAN available: {stylegan_available}")
    
    # Show a warning message if StyleGAN is not available
    gan_warning = None
    if not stylegan_available:
        gan_warning = "StyleGAN modules are not installed. You'll see a placeholder instead of generated images."
        print("Warning: StyleGAN modules not available")
    
    # Initialize GAN model and load vectors
    vectors = utils.load_latent_vectors()
    print(f"Loaded vectors shape: {vectors.shape if hasattr(vectors, 'shape') else 'unknown'}")
    
    # Default starting vectors (first 2 in our array)
    z1 = vectors[0].tolist() if len(vectors) > 0 else []
    z2 = vectors[1].tolist() if len(vectors) > 1 else []
    
    # Ensure z1 and z2 are not None
    if not z1 or not z2:
        print("Creating fallback random vectors")
        # Create fallback random vectors
        z1 = np.random.randn(1, 512).tolist()
        z2 = np.random.randn(1, 512).tolist()
    
    print(f"z1 shape: {len(z1)} x {len(z1[0]) if z1 and len(z1) > 0 else 0}")
    print(f"z2 shape: {len(z2)} x {len(z2[0]) if z2 and len(z2) > 0 else 0}")
    
    # Get a random initial pants image from Dropbox
    initial_image = None
    try:
        # Initialize Dropbox
        dbx = Dropbox(
            app_secret=os.getenv('DROPBOX_APP_SECRET'),
            oauth2_refresh_token=os.getenv('DROPBOX_REFRESH_TOKEN'),
            app_key=os.getenv('DROPBOX_APP_KEY')
        )
        
        # Get a random pants image
        with connections['data'].cursor() as cursor:
            cursor.execute("SELECT filename FROM mens_pants ORDER BY RANDOM() LIMIT 1")
            filename = cursor.fetchone()[0]
            
            temp_link = dbx.files_get_temporary_link(filename)
            initial_image = temp_link.link
            print(f"Got initial pants image: {initial_image[:50]}...")
            
    except Exception as e:
        print(f"Error getting initial image: {str(e)}")
        # Fallback to static placeholder
        initial_image = "/static/images/placeholder.png"
        print("Using static placeholder image instead")
    
    context = {
        "z1": json.dumps(z1),
        "z2": json.dumps(z2),
        "initial_image": initial_image,
        "stylegan_available": stylegan_available,
        "gan_warning": gan_warning,
        "num_features": len(z1[0]) if z1 and len(z1) > 0 else 512
    }
    return render(request, "gan_visualizer.html", context)

@csrf_exempt
def gan_generate(request):
    """API endpoint to generate pants images from latent vectors"""
    if request.method == "POST":
        if DEBUG:
            print("Received POST request to /gan-generate/")
        
        # Check if StyleGAN is available
        stylegan_available = getattr(utils, 'STYLEGAN_AVAILABLE', False)
        print(f"StyleGAN available in generate endpoint: {stylegan_available}")
        
        if not stylegan_available:
            # Return a placeholder image if StyleGAN is not available
            print("Warning: StyleGAN not available, returning placeholder")
            return JsonResponse({
                "status": "warning",
                "message": "StyleGAN modules not available. Using placeholder image.",
                "image": "/static/images/placeholder.png",
                "vector": None
            })
            
        try:
            # Read request body
            print("Parsing request body...")
            request_body = request.body.decode('utf-8')
            print(f"Request body: {request_body[:100]}...")
            
            data = json.loads(request_body)
            print(f"Parsed data: {str(data)[:100]}...")
            
            # Get parameters from request
            vector_type = data.get("vector_type", "interpolated")
            print(f"Vector type: {vector_type}")
            
            if vector_type == "interpolated":
                # Get the two endpoints and interpolation parameter
                z1 = np.array(data.get("z1"))
                z2 = np.array(data.get("z2"))
                alpha = float(data.get("alpha", 0.5))
                print(f"Interpolating between vectors, alpha={alpha}")
                
                # Interpolate between the vectors
                z = utils.interpolate_latent_vectors(z1, z2, alpha)
                
                # Apply any feature perturbations
                features = data.get("features", {})
                for idx, amount in features.items():
                    z = utils.perturb_latent_vector(z, int(idx), float(amount))
            
            elif vector_type == "custom":
                # Use a custom latent vector provided by the client
                latent_vector = data.get("latent_vector")
                print(f"Custom vector received, shape: {np.array(latent_vector).shape if latent_vector else 'None'}")
                
                if not latent_vector:
                    print("Error: No latent vector provided")
                    return JsonResponse({
                        "status": "error",
                        "message": "No latent vector provided",
                        "image": "/static/images/placeholder.png",
                        "vector": None
                    })
                
                z = np.array(latent_vector)
                
            elif vector_type == "random":
                # Generate a new random vector
                G = utils.load_gan_model()
                if G is None:
                    # If model couldn't be loaded
                    print("Error: Could not load GAN model")
                    return JsonResponse({
                        "status": "error",
                        "message": "Could not load GAN model.",
                        "image": "/static/images/placeholder.png",
                        "vector": None
                    })
                z = np.random.randn(1, G.z_dim)
                print(f"Generated random vector with shape {z.shape}")
            
            # Generate image from vector
            truncation = float(data.get("truncation", 0.7))
            print(f"Generating image with truncation {truncation}...")
            image_bytes = utils.generate_pants_image(z, truncation_psi=truncation)
            
            if image_bytes is None:
                # If image generation failed
                print("Error: Failed to generate image")
                return JsonResponse({
                    "status": "error",
                    "message": "Failed to generate image.",
                    "image": "/static/images/placeholder.png",
                    "vector": z.tolist() if 'z' in locals() else None
                })
                
            # Convert to base64 for sending to frontend
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            print("Successfully generated and encoded image")
            
            return JsonResponse({
                "status": "success", 
                "image": f"data:image/png;base64,{image_b64}",
                "vector": z.tolist()
            })
            
        except Exception as e:
            if DEBUG:
                print(f"Error in gan_generate view: {str(e)}")
                import traceback
                traceback.print_exc()
            return JsonResponse({
                "status": "error", 
                "message": str(e),
                "image": "/static/images/placeholder.png",
                "vector": None
            })
    else:
        if DEBUG:
            print("Received non-POST request to /gan-generate/")
        return JsonResponse({"status": "error", "message": "Invalid request method"})

@csrf_exempt
def gan_new_vectors(request):
    """API endpoint to generate new random vectors"""
    if request.method == "POST":
        if DEBUG:
            print("Received POST request to /gan_new_vectors/")
        
        # Check if StyleGAN is available
        stylegan_available = getattr(utils, 'STYLEGAN_AVAILABLE', False)
        
        try:
            # Generate new random vectors
            if stylegan_available:
                G = utils.load_gan_model()
                if G is not None:
                    z_dim = G.z_dim
                    z1 = np.random.randn(1, z_dim)
                    z2 = np.random.randn(1, z_dim)
                else:
                    # Default dimension if model can't be loaded
                    z_dim = 512
                    z1 = np.random.randn(1, z_dim)
                    z2 = np.random.randn(1, z_dim)
            else:
                # Default dimension if StyleGAN is not available
                z_dim = 512
                z1 = np.random.randn(1, z_dim)
                z2 = np.random.randn(1, z_dim)
            
            # Save in global array
            vectors = utils.load_latent_vectors()
            if len(vectors) >= 2:
                vectors[0] = z1
                vectors[1] = z2
            
            # Try to save to disk (might fail if directory doesn't exist)
            try:
                # Create GAN directory if it doesn't exist
                os.makedirs(os.path.join(settings.BASE_DIR, 'GAN'), exist_ok=True)
                latent_path = os.path.join(settings.BASE_DIR, 'GAN', 'latent_vectors.npy')
                np.save(latent_path, vectors)
            except Exception as e:
                if DEBUG:
                    print(f"Warning: Could not save vectors to disk: {str(e)}")
            
            return JsonResponse({
                "status": "success",
                "z1": z1.tolist(),
                "z2": z2.tolist()
            })
            
        except Exception as e:
            if DEBUG:
                print(f"Error in gan_new_vectors view: {str(e)}")
            # Return default vectors if there's an error
            z_dim = 512
            z1 = np.random.randn(1, z_dim)
            z2 = np.random.randn(1, z_dim)
            return JsonResponse({
                "status": "warning",
                "message": f"Using default random vectors due to error: {str(e)}",
                "z1": z1.tolist(),
                "z2": z2.tolist()
            })
    else:
        if DEBUG:
            print("Received non-POST request to /gan_new_vectors/")
        return JsonResponse({"status": "error", "message": "Invalid request method"})


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
