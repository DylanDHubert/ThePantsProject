from django.db import connections
import plotly.io as pio
import plotly.graph_objects as go
import numpy as np
import io
from PIL import Image
import torch
import os

# Import StyleGAN modules
STYLEGAN_AVAILABLE = False
try:
    import dnnlib
    import legacy
    import sys
    
    # Make sure torch_utils is in the path
    sys.path.append('/Users/LukeHeitman/Desktop/ThePantsProject')
    
    # Testing actual StyleGAN availability
    import torch
    test_tensor = torch.randn(1, 512)
    print("Torch test successful")
    
    # Test that dnnlib works
    from dnnlib import EasyDict
    test_dict = EasyDict(test=True)
    print("dnnlib test successful")
    
    # If we got here, StyleGAN should be available
    STYLEGAN_AVAILABLE = True
    print("StyleGAN modules imported successfully")
except Exception as e:
    print(f"Error importing StyleGAN modules: {str(e)}")
    STYLEGAN_AVAILABLE = False

from django.conf import settings

# Cache for the GAN model to avoid reloading
GAN_MODEL_CACHE = None
# Cache for latent vectors
LATENT_VECTORS = None

# CREATE PLOT OBJECT FROM DATA OF data.sqlite TABLE: "CATEGORY"
def create_plot(CATEGORY):
    # SEARCH DATABASE data, AND GET RESULTS FOR X, Y COORDS
    with connections['data'].cursor() as cursor:
        query = f"SELECT x, y FROM {CATEGORY}"
        cursor.execute(query)
        results = cursor.fetchall()

    x, y = zip(*results)

    # GENERATE PLOTLY "HEATMAP"
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
    # ADDITIONAL MODIFICATIONS TO DISPLAY
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
    # RETURN AS JSON
    return pio.to_json(fig)


# SEARCH DATA OF data.sqlite TABLE: "CATEGORY" TO FIND NEAREST N ENTRIES
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
    
# GAN-RELATED FUNCTIONS

def load_gan_model():
    """Load the GAN model from the checkpoint"""
    global GAN_MODEL_CACHE
    
    if GAN_MODEL_CACHE is None:
        try:
            checkpoint_path = os.path.join(settings.BASE_DIR, 'GAN', 'pantsGAN_checkpoint_180.pkl')
            
            print(f"Loading GAN model from: {checkpoint_path}")
            with open(checkpoint_path, 'rb') as f:
                G = legacy.load_network_pkl(f)['G_ema']
                # Move to CPU for server environment
                G = G.to('cpu')
                GAN_MODEL_CACHE = G
            print("GAN model loaded successfully")
            return G
        except Exception as e:
            print(f"Error loading GAN model: {str(e)}")
            return None
    return GAN_MODEL_CACHE

def load_latent_vectors():
    """Load cached latent vectors or create new ones"""
    global LATENT_VECTORS
    
    if not STYLEGAN_AVAILABLE:
        print("StyleGAN modules not available. Cannot load latent vectors.")
        # Return mock vectors for development without StyleGAN
        return np.array([
            np.random.randn(1, 512),  # Typical StyleGAN z dimension is 512
            np.random.randn(1, 512)
        ])
    
    if LATENT_VECTORS is None:
        latent_path = os.path.join(settings.BASE_DIR, 'GAN', 'latent_vectors.npy')
        
        if os.path.exists(latent_path):
            LATENT_VECTORS = np.load(latent_path)
        else:
            # If no cached vectors, create 2 random ones
            G = load_gan_model()
            if G is not None:
                LATENT_VECTORS = np.array([
                    np.random.randn(1, G.z_dim),
                    np.random.randn(1, G.z_dim)
                ])
                np.save(latent_path, LATENT_VECTORS)
            else:
                # Default to standard size if model can't be loaded
                LATENT_VECTORS = np.array([
                    np.random.randn(1, 512),
                    np.random.randn(1, 512)
                ])
    
    return LATENT_VECTORS

def generate_pants_image(latent_vector, truncation_psi=0.7):
    """Generate a pants image from a latent vector using the GAN model"""
    
    # If StyleGAN modules are not available, just return the placeholder image
    if not STYLEGAN_AVAILABLE:
        print("StyleGAN modules not available - returning placeholder")
        try:
            placeholder_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'placeholder.png')
            with open(placeholder_path, 'rb') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading placeholder: {str(e)}")
            return None
    
    try:
        G = load_gan_model()
        
        if G is None:
            print("Failed to load GAN model")
            return None
        
        # Process input
        if isinstance(latent_vector, list):
            latent_vector = np.array(latent_vector)
        
        # Ensure correct shape
        if len(latent_vector.shape) == 1:
            latent_vector = latent_vector.reshape(1, -1)
        
        # Convert numpy array to torch tensor
        z = torch.from_numpy(latent_vector).float().to('cpu')
        
        print(f"Generating image with tensor shape: {z.shape}")
        
        # Apply the StyleGAN mapping and synthesis
        with torch.no_grad():
            print("Running mapping network...")
            w = G.mapping(z, None)
            print("Applying truncation trick...")
            w = G.mapping.w_avg + (w - G.mapping.w_avg) * truncation_psi
            print("Running synthesis network...")
            img = G.synthesis(w, noise_mode='const')
        
        print(f"Generated image with shape: {img.shape}")
        
        # Convert to PIL Image
        img = (img.permute(0, 2, 3, 1) * 127.5 + 128).clamp(0, 255).to(torch.uint8)
        pil_img = Image.fromarray(img[0].cpu().numpy(), 'RGB')
        
        # Return the image as bytes
        img_byte_arr = io.BytesIO()
        pil_img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        print("Successfully generated pants image")
        return img_byte_arr.getvalue()
    except Exception as e:
        print(f"Error generating pants image: {str(e)}")
        # Read and return the placeholder image as fallback
        try:
            placeholder_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'placeholder.png')
            with open(placeholder_path, 'rb') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading placeholder: {str(e)}")
            return None

def interpolate_latent_vectors(z1, z2, alpha):
    """Interpolate between two latent vectors"""
    return z1 * (1 - alpha) + z2 * alpha

def perturb_latent_vector(z, feature_idx, amount):
    """Perturb a specific feature dimension of a latent vector"""
    z_perturbed = z.copy()
    z_perturbed[0, feature_idx] += amount
    return z_perturbed