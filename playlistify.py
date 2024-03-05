# import libraries
import json

import requests
import pandas as pd
from pandas import json_normalize
import spotipy
import spotipy.util as util

from spotifysecrets import *


class SpotifyAnalyzer:
    # create SpotifyAnalyzer instance
    def __init__(self, username, redirect_uri='http://localhost:8888/callback', scope=["playlist-read-private"]):
        
        self.token = None
        self.sp = None
        self.username = username
        self.scope = scope
        self.redirect_uri = redirect_uri
        self.generate_token()
        
    # set/modify scope
    def set_scope(self, scope):
        self.scope = scope
        self.generate_token()
        
    
    def generate_token(self):
        token = util.prompt_for_user_token(
            self.username, 
            self.scope, 
            client_id=CLIENT_ID, 
            client_secret=CLIENT_SECRET, 
            redirect_uri=self.redirect_uri
        )
        if token:
            self.sp = spotipy.Spotify(auth=token)
            self.token = token
        else:
            print(f"Cant get token for {self.username}")

        
    # Print top artists
    def get_top_artists(self):
        # Get request for top artists
        headers = {
            'Authorization': 'Bearer ' + self.token
        }
        params = {
            "limit": 20,  # number of artists to retrieve
            "time_range": "medium_term"  # time range for top artists (short_term, medium_term, long_term)
        }
        response = requests.get('https://api.spotify.com/v1/me/top/artists', headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
        else:
            print(f"Error: {response.status_code}")

        # ANALYSIS
        data_str  = json.dumps(data, indent=2)
        data_dict = json.loads(data_str)


        top_artists = data['items']

        for artist in top_artists:
            artists = artist['name']
            print(f"{artist['name']} Popularity: {artist['popularity']} Genres: {artist['genres']}")

        return
    
    # Print available genre seeds
    def get_genre_seeds(self):
        headers = {
            'Authorization': 'Bearer ' + self.token
        }
        response2 = requests.get('https://api.spotify.com/v1/recommendations/available-genre-seeds', headers=headers)

        if response2.status_code == 200:
            data2 = response2.json()
        else:
            print(f"Error: {response2.status_code}")

        data2_str = json.dumps(data2, indent=2)
        print(data2_str)

    # Get playlist details
    def get_playlist_details(self, playlist_link):
        # get playlist ID from the provided link
        playlist_id = playlist_link.split('/')[-1]

        # get playlist details using the Spotify Web API
        headers = {
            'Authorization': 'Bearer ' + self.token
        }
        response = requests.get(f'https://api.spotify.com/v1/playlists/{playlist_id}', headers=headers)

        if response.status_code == 200:
            playlist_data = response.json()
        else:
            print(f"Error: {response.status_code}")
            return None

        # Extract relevant details from playlist data
        def extract_track_info(track):
            song_title = track['track']['name']
            artists = ', '.join([artist['name'] for artist in track['track']['artists']])
            uri = track['track']['uri']
            popularity = track['track']['popularity']
            return song_title, artists, uri, popularity

        playinfo = []
        for track in playlist_data['tracks']['items']:
            # song_title, artists, uri, popularity = extract_track_info(track)
            # print(f"{song_title} - {artists}")
            playlist_info = {
                'playlist_id': playlist_data['id'],
                'title': playlist_data['name'],
                'description': playlist_data['description'],
                'image_url': playlist_data['images'][0]['url'] if playlist_data['images'] else None,
                'song_title' : track['track']['name'],
                'artists' : ', '.join([artist['name'] for artist in track['track']['artists']]),
                'artist_uris' : ', '.join([artist['uri'] for artist in track['track']['artists']]),
                'popularity' : track['track']['popularity'],
                'uri' : track['track']['uri']
            }
            playinfo.append(playlist_info)
        
        df = pd.DataFrame(playinfo)

        songinfo = []
        for index, row in df.iterrows():
            song_uri = row['uri'].split(':')[-1]
            artists = row['artist_uris'].split(', ')

            # Get genres for each artist in song
            genres = []
            for artist in artists:
                artist_uri = artist.split(':')[-1]
                genre_response = requests.get(f'https://api.spotify.com/v1/artists/{artist_uri}', headers=headers)
                if genre_response.status_code == 200:
                    genre_data = genre_response.json()
                    genres.extend(genre_data['genres'])

            song_response = requests.get(f'https://api.spotify.com/v1/audio-features/{song_uri}', headers=headers)

            if song_response.status_code == 200 and genre_response.status_code == 200:
                song_data_json = song_response.json()
                song_data = {
                    'song_title': row['song_title'],
                    'song_id': song_data_json['id'],
                    'artists' : row['artists'],
                    'popularity' : row['popularity'],
                    'danceability': song_data_json['danceability'],
                    'energy': song_data_json['energy'],
                    'key': song_data_json['key'],
                    'loudness': song_data_json['loudness'],
                    'mode': song_data_json['mode'],
                    'speechiness': song_data_json['speechiness'],
                    'acousticness': song_data_json['acousticness'],
                    'instrumentalness': song_data_json['instrumentalness'],
                    'liveness': song_data_json['liveness'],
                    'valence': song_data_json['valence'],
                    'tempo': song_data_json['tempo'],
                    'duration_ms': song_data_json['duration_ms'],
                    'time_signature': song_data_json['time_signature'],
                    'genres': genres
                }
                genre_data = genre_response.json()

                songinfo.append(song_data)
            else:
                print(f"Error: {song_response.status_code}")
                return None
        
        songdf = pd.DataFrame(songinfo)
        # Return playlist details, list of song detail dataframes, list of song titles
        return df, songdf, playlist_data['name']


def main():

    # credentials
    username = 'nrkjbdqb3gwxlzypjce5vvqra'
    redirect_uri = 'http://localhost:8888/callback'

    # list of predefined scopes
    scope = [
        'user-top-read',
        'user-read-recently-played',
        'user-read-currently-playing', 
        'playlist-read-private', 
        'playlist-read-collaborative', 
        'playlist-modify-private', 
        'playlist-modify-public', 
        'user-library-read'
    ]

    sp = SpotifyAnalyzer(username, redirect_uri)
    # sp.get_top_artists()
    # sp.get_genre_seeds()
    df, songdf, playlist_name = sp.get_playlist_details('https://open.spotify.com/playlist/1W7ZTOHtVIcA3Js5sEzNZV?si=302c6798a03d4b07')
    df.to_csv(f'data/{playlist_name}.csv', index=False)
    songdf.to_csv(f'data/{playlist_name}_songs.csv', index=False)

if __name__ == "__main__":
    main()