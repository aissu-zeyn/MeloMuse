import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import networkx as nx
import logging

logger = logging.getLogger(__name__)

class TransitionModel:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=5, random_state=42)
        self.feature_columns = [
            'popularity',
            'duration_ms',
            'explicit',
            'track_number',
            'disc_number',
            'available_markets',
            'album_total_tracks',
            'artist_popularity',
            'artist_followers'
        ]

    def train(self, dataset):
        """Train the transition model using the collected dataset."""
        logger.info("Training transition model...")
        
        # Prepare features for clustering
        features = dataset[self.feature_columns].copy()
        
        # Handle categorical features
        features['explicit'] = features['explicit'].astype(int)
        
        # Scale features
        scaled_features = self.scaler.fit_transform(features)
        
        # Cluster songs
        dataset['cluster'] = self.kmeans.fit_predict(scaled_features)
        
        # Build transition graph
        self._build_transition_graph(dataset)
        
        logger.info("Model training complete")

    def _build_transition_graph(self, dataset):
        """Build a graph representing possible transitions between songs."""
        # Group songs by mood and cluster
        mood_clusters = dataset.groupby(['mood', 'cluster'])
        
        # Add nodes for each mood-cluster combination
        for (mood, cluster), songs in mood_clusters:
            node_id = f"{mood}_{cluster}"
            self.graph.add_node(node_id, 
                              mood=mood,
                              cluster=cluster,
                              songs=songs.to_dict('records'))
        
        # Add edges between nodes
        for node1 in self.graph.nodes():
            mood1, cluster1 = node1.split('_')
            for node2 in self.graph.nodes():
                mood2, cluster2 = node2.split('_')
                
                # Calculate transition weight based on mood and cluster similarity
                weight = self._calculate_transition_weight(
                    self.graph.nodes[node1]['songs'][0],
                    self.graph.nodes[node2]['songs'][0]
                )
                
                if weight > 0:
                    self.graph.add_edge(node1, node2, weight=weight)

    def _calculate_transition_weight(self, song1, song2):
        """Calculate the weight of a transition between two songs."""
        # Base weight on mood transition
        mood_weights = {
            ('sad', 'happy'): 0.8,
            ('happy', 'sad'): 0.6,
            ('calm', 'energetic'): 0.7,
            ('energetic', 'calm'): 0.7,
            ('angry', 'calm'): 0.8,
            ('calm', 'angry'): 0.5,
            ('romantic', 'happy'): 0.7,
            ('happy', 'romantic'): 0.7,
            ('melancholic', 'happy'): 0.6,
            ('happy', 'melancholic'): 0.5
        }
        
        # Get base weight from mood transition
        mood_pair = (song1['mood'], song2['mood'])
        base_weight = mood_weights.get(mood_pair, 0.3)
        
        # Adjust weight based on feature similarity
        feature_similarity = self._calculate_feature_similarity(song1, song2)
        
        return base_weight * feature_similarity

    def _calculate_feature_similarity(self, song1, song2):
        """Calculate similarity between songs based on available features."""
        # Normalize numerical features
        features = ['popularity', 'duration_ms', 'artist_popularity', 'artist_followers']
        similarities = []
        
        for feature in features:
            max_val = max(song1[feature], song2[feature])
            if max_val > 0:
                similarity = 1 - abs(song1[feature] - song2[feature]) / max_val
                similarities.append(similarity)
        
        # Add similarity for categorical features
        if song1['explicit'] == song2['explicit']:
            similarities.append(1.0)
        else:
            similarities.append(0.0)
            
        if song1['album_type'] == song2['album_type']:
            similarities.append(1.0)
        else:
            similarities.append(0.0)
        
        return np.mean(similarities)

    def generate_playlist(self, start_emotion, end_emotion, duration_minutes):
        """Generate a playlist that transitions from start_emotion to end_emotion."""
        logger.info(f"Generating playlist from {start_emotion} to {end_emotion}")
        
        # Convert duration to milliseconds
        target_duration = duration_minutes * 60 * 1000
        
        # Find start and end nodes
        start_nodes = [n for n in self.graph.nodes() if n.startswith(start_emotion)]
        end_nodes = [n for n in self.graph.nodes() if n.startswith(end_emotion)]
        
        if not start_nodes or not end_nodes:
            raise ValueError(f"Could not find nodes for emotions: {start_emotion} or {end_emotion}")
        
        # Find shortest path
        best_path = None
        best_duration = float('inf')
        
        for start in start_nodes:
            for end in end_nodes:
                try:
                    path = nx.shortest_path(self.graph, start, end, weight='weight')
                    path_duration = self._calculate_path_duration(path)
                    
                    if abs(path_duration - target_duration) < abs(best_duration - target_duration):
                        best_path = path
                        best_duration = path_duration
                except nx.NetworkXNoPath:
                    continue
        
        if not best_path:
            raise ValueError(f"No valid path found from {start_emotion} to {end_emotion}")
        
        # Generate playlist from path
        playlist = []
        current_duration = 0
        
        for node in best_path:
            songs = self.graph.nodes[node]['songs']
            if songs:
                # Select a random song from the node
                song = np.random.choice(songs)
                playlist.append(song)
                current_duration += song['duration_ms']
                
                if current_duration >= target_duration:
                    break
        
        return pd.DataFrame(playlist)

    def _calculate_path_duration(self, path):
        """Calculate the total duration of a path in milliseconds."""
        total_duration = 0
        for node in path:
            songs = self.graph.nodes[node]['songs']
            if songs:
                # Use average duration of songs in the node
                avg_duration = np.mean([s['duration_ms'] for s in songs])
                total_duration += avg_duration
        return total_duration

if __name__ == "__main__":
    # Example usage
    import pandas as pd
    
    # Load dataset
    songs_df = pd.read_csv('data/emotional_music_dataset.csv')
    
    # Create and train model
    model = TransitionModel()
    model.train(songs_df)
    
    # Generate emotional journey
    path = model.generate_playlist(
        start_emotion='sad',
        end_emotion='happy',
        duration_minutes=30
    )
    
    # Get song details
    journey = model.get_song_details(path)
    print(f"Generated journey with {len(journey)} songs:")
    for song in journey:
        print(f"{song['name']} by {song['artist']} ({song['mood']})") 