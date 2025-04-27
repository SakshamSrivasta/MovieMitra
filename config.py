import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
 
# TMDB API Configuration
TMDB_API_KEY = os.getenv('TMDB_API_KEY', 'your_api_key_here')
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/w500'  # w500 is a good size for posters 