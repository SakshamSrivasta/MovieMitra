import requests
from config import TMDB_API_KEY, TMDB_BASE_URL, TMDB_IMAGE_BASE_URL
import logging

logger = logging.getLogger(__name__)

def search_movie(title):
    """Search for a movie by title and return its details including poster path."""
    try:
        url = f"{TMDB_BASE_URL}/search/movie"
        params = {
            'api_key': TMDB_API_KEY,
            'query': title,
            'language': 'en-US',
            'page': 1
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        if data['results']:
            movie = data['results'][0]  # Get the first result
            return {
                'id': movie['id'],
                'title': movie['title'],
                'poster_path': movie['poster_path'],
                'overview': movie['overview'],
                'release_date': movie['release_date']
            }
        return None
    except Exception as e:
        logger.error(f"Error searching movie {title}: {str(e)}")
        return None

def get_poster_url(poster_path):
    """Get the full URL for a movie poster."""
    if poster_path:
        return f"{TMDB_IMAGE_BASE_URL}{poster_path}"
    return None

def get_movie_details(movie_id):
    """Get detailed information about a movie."""
    try:
        url = f"{TMDB_BASE_URL}/movie/{movie_id}"
        params = {
            'api_key': TMDB_API_KEY,
            'language': 'en-US'
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        logger.error(f"Error getting movie details for ID {movie_id}: {str(e)}")
        return None 