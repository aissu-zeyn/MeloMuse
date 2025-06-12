import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import logging
from tqdm import tqdm
import time
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpotifyDataCollector:
    def __init__(self):
        load_dotenv()
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        self.redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')
        if not self.client_id or not self.client_secret:
            raise ValueError("Spotify API credentials not found in environment variables")
        logger.info("Initializing Spotify client...")
        try:
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope='user-read-private user-read-email playlist-read-private playlist-read-collaborative user-library-read user-top-read user-read-recently-played playlist-modify-public playlist-modify-private',
                cache_path='.spotify_cache',
                open_browser=True
            ))
            test_search = self.sp.search('test', limit=1)
            if test_search:
                logger.info("Successfully connected to Spotify API")
                token_info = self.sp._auth_manager.get_access_token()
                if token_info:
                    logger.info(f"Token type: {token_info.get('token_type', 'unknown')}")
                    logger.info(f"Token expires in: {token_info.get('expires_in', 'unknown')} seconds")
            else:
                raise Exception("Failed to connect to Spotify API")
        except Exception as e:
            logger.error(f"Error initializing Spotify client: {str(e)}")
            if hasattr(e, 'response'):
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response headers: {json.dumps(dict(e.response.headers), indent=2)}")
            raise

    def _handle_rate_limit(self, func, *args, **kwargs):
        max_retries = 3
        base_delay = 2
        for attempt in range(max_retries):
            try:
                time.sleep(1)
                return func(*args, **kwargs)
            except Exception as e:
                if '429' in str(e) or '403' in str(e):
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Rate limit hit, waiting {delay} seconds...")
                        if hasattr(e, 'response'):
                            logger.error(f"Response status: {e.response.status_code}")
                            logger.error(f"Response headers: {json.dumps(dict(e.response.headers), indent=2)}")
                            if hasattr(e.response, 'text'):
                                logger.error(f"Response body: {e.response.text}")
                        time.sleep(delay)
                        continue
                raise

    def get_track_info(self, track_id):
        try:
            logger.info(f"Fetching track info for {track_id}")
            track = self._handle_rate_limit(self.sp.track, track_id)
            if not track:
                logger.warning(f"No track info found for {track_id}")
                return None
            return {
                'id': track['id'],
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'popularity': track['popularity'],
                'duration_ms': track['duration_ms'],
                'album': track['album']['name'],
                'release_date': track['album']['release_date'],
                'explicit': track['explicit'],
                'track_number': track['track_number'],
                'disc_number': track['disc_number'],
                'available_markets': len(track['available_markets']),
                'is_local': track['is_local'],
                'album_type': track['album']['album_type'],
                'album_release_date': track['album']['release_date'],
                'album_total_tracks': track['album']['total_tracks'],
                'artist_popularity': track['artists'][0].get('popularity', 0),
                'artist_genres': track['artists'][0].get('genres', []),
                'artist_followers': track['artists'][0].get('followers', {}).get('total', 0)
            }
        except Exception as e:
            logger.error(f"Error fetching track info for {track_id}: {str(e)}")
            if hasattr(e, 'response'):
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response headers: {json.dumps(dict(e.response.headers), indent=2)}")
                if hasattr(e.response, 'text'):
                    logger.error(f"Response body: {e.response.text}")
            return None

    def search_playlists_by_mood(self, mood, limit=5):
        all_playlists = []
        seen_ids = set()
        queries = [
            f"mood {mood}",
            f"{mood} music",
            f"{mood} songs",
            f"{mood} playlist"
        ]
        for query in queries:
            try:
                logger.info(f"Searching with query: {query}")
                results = self._handle_rate_limit(self.sp.search, q=query, type='playlist', limit=limit)
                if not results or 'playlists' not in results or 'items' not in results['playlists']:
                    logger.warning(f"No results for query: {query}")
                    continue
                playlists = results['playlists']['items']
                logger.info(f"Found {len(playlists)} playlists for query: {query}")
                for playlist in playlists:
                    if playlist['id'] not in seen_ids:
                        seen_ids.add(playlist['id'])
                        all_playlists.append(playlist)
            except Exception as e:
                logger.error(f"Error processing query '{query}': {str(e)}")
                if hasattr(e, 'response'):
                    logger.error(f"Response status: {e.response.status_code}")
                    logger.error(f"Response headers: {json.dumps(dict(e.response.headers), indent=2)}")
                    if hasattr(e.response, 'text'):
                        logger.error(f"Response body: {e.response.text}")
                continue
        logger.info(f"Found {len(all_playlists)} unique playlists for mood: {mood}")
        return all_playlists[:limit]

    def get_playlist_tracks(self, playlist_id):
        try:
            logger.info(f"Fetching tracks from playlist {playlist_id}")
            results = self._handle_rate_limit(self.sp.playlist_tracks, playlist_id)
            if not results or 'items' not in results:
                logger.warning(f"No tracks found in playlist {playlist_id}")
                return []
            tracks = results['items']
            while results['next'] and len(tracks) < 50:
                time.sleep(1)
                results = self._handle_rate_limit(self.sp.next, results)
                if 'items' in results:
                    tracks.extend(results['items'])
            return tracks[:50]
        except Exception as e:
            logger.error(f"Error fetching tracks from playlist {playlist_id}: {str(e)}")
            if hasattr(e, 'response'):
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response headers: {json.dumps(dict(e.response.headers), indent=2)}")
                if hasattr(e.response, 'text'):
                    logger.error(f"Response body: {e.response.text}")
            return []

    def collect_mood_data(self, mood, num_tracks=20):
        tracks_data = []
        playlists = self.search_playlists_by_mood(mood)
        for playlist in tqdm(playlists, desc=f"Processing playlists for mood: {mood}"):
            playlist_tracks = self.get_playlist_tracks(playlist['id'])
            for track_item in playlist_tracks:
                if len(tracks_data) >= num_tracks:
                    break
                track = track_item['track']
                if not track or not track['id']:
                    continue
                track_info = self.get_track_info(track['id'])
                if not track_info:
                    continue
                track_data = {
                    'mood': mood,
                    **track_info
                }
                tracks_data.append(track_data)
                time.sleep(1.5)
        return tracks_data

    def collect_all_mood_data(self, moods=None):
        if moods is None:
            moods = ['happy', 'sad', 'energetic', 'calm', 'angry', 'romantic', 'melancholic']
        all_data = []
        for mood in tqdm(moods, desc="Processing moods"):
            mood_data = self.collect_mood_data(mood)
            all_data.extend(mood_data)
        return pd.DataFrame(all_data)

    def save_data(self, data, filename='spotify_mood_data.csv'):
        data.to_csv(filename, index=False)
        logger.info(f"Data saved to {filename}")

    def create_playlist(self, name, description, tracks_df):
        try:
            user = self.sp.current_user()
            user_id = user['id']
            playlist = self.sp.user_playlist_create(
                user=user_id,
                name=name,
                description=description,
                public=True
            )
            track_uris = [f"spotify:track:{track_id}" for track_id in tracks_df['id']]
            for i in range(0, len(track_uris), 100):
                chunk = track_uris[i:i + 100]
                self.sp.playlist_add_items(playlist['id'], chunk)
                time.sleep(1)
            logger.info(f"Created playlist: {playlist['name']}")
            logger.info(f"Playlist URL: {playlist['external_urls']['spotify']}")
            return playlist
        except Exception as e:
            logger.error(f"Error creating playlist: {str(e)}")
            if hasattr(e, 'response'):
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response headers: {json.dumps(dict(e.response.headers), indent=2)}")
                if hasattr(e.response, 'text'):
                    logger.error(f"Response body: {e.response.text}")
            raise

if __name__ == "__main__":
    collector = SpotifyDataCollector()
    moods = ['happy', 'sad', 'energetic', 'calm', 'melancholic']
    dataset = collector.collect_all_mood_data(moods)
    collector.save_data(dataset) 