from models.movie import Movie
from utils.imdb import get_movie_details, search_movies as search_movies_api
import sqlite3

class MovieController:
    def __init__(self, db_path):
        self.movie_model = Movie(db_path)
        self.db_path = db_path

    def search_movies(self, query):
        # Llama a la función de búsqueda de la API
        results = search_movies_api(query)

        # Filtrar resultados para incluir solo películas
        if 'Search' in results:
            # Filtrar solo los resultados que son películas
            filtered_results = [movie for movie in results['Search'] if movie['Type'] == 'movie']

            # Verificar si las películas están disponibles en la base de datos
            available_movies = self.get_available_movie_ids()

            # Marcar las películas disponibles
            for movie in filtered_results:
                movie['is_available'] = movie['imdbID'] in available_movies

            results['Search'] = filtered_results

        return results

    def get_movie_details(self, movie_id):
        movie_details = get_movie_details(movie_id)  # Llamada a la API
        if 'errorMessage' in movie_details:
            return None  # Manejo de errores si no se obtienen detalles

        # Obtener el video_link de la base de datos
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT video_link FROM movies WHERE imdb_id = ?', (movie_id,))
            result = cursor.fetchone()
            is_available = result[0] if result else False
            video_link = result[0] if result else None

        return {
            'title': movie_details.get('Title', 'N/A'),
            'year': movie_details.get('Year', 'N/A'),
            'poster': movie_details.get('Poster', 'N/A'),
            'imdb_rating': movie_details.get('imdbRating', 'N/A'),
            'director': movie_details.get('Director', 'N/A'),
            'runtime': movie_details.get('Runtime', 'N/A'),
            'plot': movie_details.get('Plot', 'N/A'),
            'imdb_id': movie_id,
            'language': movie_details.get('Language', 'N/A'),
            'country': movie_details.get('Country', 'N/A'),
            'awards': movie_details.get('Awards', 'N/A'),
            'actors': movie_details.get('Actors', 'N/A'),
            'genre': movie_details.get('Genre', 'N/A'),
            'is_available': is_available,
            'video_link': video_link
        }

    def get_all_movies(self):
        return self.movie_model.get_all_movies()

    def get_available_movie_ids(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT imdb_id FROM movies WHERE available = 1')
            return [row[0] for row in cursor.fetchall()]

    def get_available_movies(self):
        available_movie_ids = self.get_available_movie_ids()
        available_movies = []
        for movie_id in available_movie_ids:
            movie_details = self.get_movie_details(movie_id)
            if movie_details:
                available_movies.append(movie_details)
        return available_movies

    def search_movies_realtime(self, query):
        results = self.search_movies(query)
        return results.get('Search', [])[:5]  # Limitamos a 5 resultados para la búsqueda en tiempo real

    def get_random_recommendations(self, count=6):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT imdb_id FROM movies WHERE available = 1 ORDER BY RANDOM() LIMIT ?', (count,))
            movie_ids = [row[0] for row in cursor.fetchall()]

        recommendations = []
        for movie_id in movie_ids:
            movie_details = self.get_movie_details(movie_id)
            if movie_details:
                recommendations.append(movie_details)
        return recommendations
