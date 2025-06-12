import argparse
import logging
from data.spotify_collector import SpotifyDataCollector
from models.transition_model import TransitionModel
import pandas as pd
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Generate a mood transition playlist')
    parser.add_argument('--start_emotion', type=str, required=True, help='Starting emotion')
    parser.add_argument('--end_emotion', type=str, required=True, help='Ending emotion')
    parser.add_argument('--duration', type=int, required=True, help='Playlist duration in minutes')
    parser.add_argument('--update_data', action='store_true', help='Update the dataset')
    args = parser.parse_args()

    collector = SpotifyDataCollector()
    moods = ['happy', 'sad', 'energetic', 'calm', 'angry', 'romantic', 'melancholic']

    if args.update_data:
        logger.info("Collecting music data...")
        dataset = collector.collect_all_mood_data(moods)
        collector.save_data(dataset, 'data/emotional_music_dataset.csv')
    else:
        if not os.path.exists('data/emotional_music_dataset.csv'):
            raise FileNotFoundError("Dataset not found. Please run with --update_data first.")
        dataset = pd.read_csv('data/emotional_music_dataset.csv')

    model = TransitionModel()
    model.train(dataset)

    playlist = model.generate_playlist(
        start_emotion=args.start_emotion,
        end_emotion=args.end_emotion,
        duration_minutes=args.duration
    )

    playlist.to_csv('generated_playlist.csv', index=False)
    logger.info(f"Playlist saved to generated_playlist.csv")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    playlist_name = f"Emotional Journey: {args.start_emotion.title()} to {args.end_emotion.title()}"
    playlist_description = f"An emotional journey from {args.start_emotion} to {args.end_emotion}, generated on {timestamp}"
    try:
        spotify_playlist = collector.create_playlist(playlist_name, playlist_description, playlist)
        logger.info(f"Playlist created in your Spotify account!")
        logger.info(f"Playlist URL: {spotify_playlist['external_urls']['spotify']}")
    except Exception as e:
        logger.error(f"Failed to create playlist in Spotify: {str(e)}")
        logger.info("You can still find the playlist in generated_playlist.csv")

if __name__ == "__main__":
    exit(main()) 