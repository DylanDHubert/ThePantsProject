import os
import torch
import numpy as np
from django.core.management.base import BaseCommand
from django.conf import settings
import dnnlib
import legacy
from server.models import FileCoordinate

class Command(BaseCommand):
    help = 'Load the GAN model and generate latent space vectors'

    def add_arguments(self, parser):
        parser.add_argument('--checkpoint', type=str, 
                           default='pantsGAN_checkpoint_180.pkl',
                           help='Path to the GAN checkpoint file')
        parser.add_argument('--num_samples', type=int, 
                           default=100,
                           help='Number of sample points to generate')
        
    def handle(self, *args, **options):
        checkpoint_path = os.path.join(settings.BASE_DIR, 'GAN', options['checkpoint'])
        num_samples = options['num_samples']
        
        self.stdout.write(f"Loading GAN model from {checkpoint_path}")
        
        # Load the model
        try:
            with dnnlib.util.open_url(checkpoint_path) as f:
                G = legacy.load_network_pkl(f)['G_ema']
                # Move to CPU for server environment
                G = G.to('cpu')
                
            self.stdout.write(self.style.SUCCESS("GAN model loaded successfully"))
            
            # Generate random vectors
            self.stdout.write(f"Generating {num_samples} latent vectors")
            z_vectors = []
            
            for i in range(num_samples):
                # Generate a random latent vector
                z = np.random.randn(1, G.z_dim)
                z_vectors.append(z)
                
                # Store in the database with normalized coordinates 
                # (we'll use first 2 dimensions for x,y)
                normalized_x = z[0][0]  # First dimension
                normalized_y = z[0][1]  # Second dimension
                
                # Create a filename for this generated point
                filename = f"gan_sample_{i}.png"
                
                # Save to database
                FileCoordinate.objects.create(
                    filename=filename,
                    x=normalized_x,
                    y=normalized_y
                )
                
                if i % 10 == 0:
                    self.stdout.write(f"Generated {i} vectors")
            
            self.stdout.write(self.style.SUCCESS(f"Successfully generated {num_samples} latent vectors"))
            
            # Save the latent vectors for future use
            np.save(os.path.join(settings.BASE_DIR, 'GAN', 'latent_vectors.npy'), 
                   np.array(z_vectors))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error loading GAN model: {str(e)}"))