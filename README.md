# Emotional Music Journey Generator

A Python application that generates Spotify playlists that transition between different emotional states. The system uses machine learning to create smooth emotional transitions in music, taking you from one mood to another through carefully selected songs.

## Features

- Generates playlists that transition between different emotional states (e.g., sad to happy)
- Uses machine learning to analyze and group songs by mood
- Creates playlists directly in your Spotify account
- Supports multiple emotional states: happy, sad, energetic, calm, angry, romantic, melancholic
- Customizable playlist duration
- Saves generated playlists as CSV files

## Prerequisites

- Python 3.8 or higher
- Spotify Developer Account
- Spotify Premium Account (for full API access)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/emotional-music-journey.git
cd emotional-music-journey
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your Spotify API credentials:
     ```
     SPOTIFY_CLIENT_ID=your_client_id_here
     SPOTIFY_CLIENT_SECRET=your_client_secret_here
     SPOTIFY_REDIRECT_URI=your_redirect_uri_here
     ```

## Setting up Spotify API

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new application
3. Get your Client ID and Client Secret
4. Add your redirect URI to the app settings

## Usage

Generate a playlist that transitions from one emotion to another:

```bash
python generate_playlist.py --start_emotion sad --end_emotion happy --duration 30 --update_data
```

Arguments:
- `--start_emotion`: Starting emotional state (required)
- `--end_emotion`: Ending emotional state (required)
- `--duration`: Playlist duration in minutes (required)
- `--update_data`: Update the music dataset (optional)

Available emotions:
- happy
- sad
- energetic
- calm
- angry
- romantic
- melancholic

## Project Structure

```
emotional-music-journey/
├── data/
│   └── spotify_collector.py
├── models/
│   └── transition_model.py
├── generate_playlist.py
├── requirements.txt
├── README.md
├── .env.example
└── .env (not tracked by git)
```

## How It Works

1. **Data Collection**: The system collects music data from Spotify playlists tagged with different emotions.
2. **Feature Analysis**: Songs are analyzed based on available metadata like popularity, duration, and artist information.
3. **Clustering**: Songs are grouped into clusters based on their features.
4. **Transition Model**: A graph-based model creates smooth transitions between emotional states.
5. **Playlist Generation**: The system generates a playlist that gradually transitions from the start emotion to the end emotion.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Spotify Web API for providing the music data
- The Python community for the excellent libraries used in this project

## Disclaimer

This project is not affiliated with Spotify. Use of the Spotify API is subject to Spotify's terms of service. 