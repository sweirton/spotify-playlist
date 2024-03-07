import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import tkinter as tk
from tkinter import messagebox, ttk  # adds additional features such as progress bars and buttons with more options.
from tkcalendar import Calendar, DateEntry
import webbrowser
from datetime import datetime
import threading

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), 'api_info.env')
load_dotenv(dotenv_path=dotenv_path)

# Spotify API credentials
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")

# Absolute path to cache file
cache_path = os.path.join(os.path.dirname(__file__), 'token.txt')

# Creates a Spotify playlist based on the Billboard Top 100 chart for a given date.
class PlaylistCreator:
    # initializes the Spotify API client and sets the initial values for the playlist name and URL
    def __init__(self):
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope="playlist-modify-private",
                cache_path=cache_path,
                show_dialog=True
            )
        )
        self.playlist_name = ""
        self.playlist_url = ""

    # retrieves the Billboard chart for the specified date, extracts the song names, creates a playlist on Spotify, searches for each song on Spotify, and adds the matching tracks to the playlist.
    def create_playlist(self, user_date, progress_bar):
        # takes a user_date parameter (representing the date for which the playlist should be created) and a progress_bar parameter (representing a progress bar widget). It retrieves the Billboard chart for the specified date, extracts the song names, formats the playlist name, creates the playlist on Spotify, searches for each song on Spotify, and adds the matching tracks to the playlist. Finally, it returns the URL of the created playlist.
        user_date_str = user_date.strftime('%Y-%m-%d')
        time_travel_link = f"https://www.billboard.com/charts/hot-100/{user_date_str}"
        response = requests.get(time_travel_link)
        text_response = response.text
        soup = BeautifulSoup(text_response, "html.parser")

        song_names_spans = soup.select("li ul li h3")
        song_names_list = [song.getText().strip() for song in song_names_spans]
        song_artist_spans = soup.select("li ul li:nth-of-type(1) span")
        song_artists_list = [artist.getText().strip() for artist in song_artist_spans]
        print(song_names_list)
        print(song_artists_list)

        # Format the date for the playlist name
        self.playlist_name = f"Billboard Top 100 {user_date.strftime('%B %Y')}"
        playlist_description = "Playlist created from Billboard Top 100 chart"
        playlist = self.sp.user_playlist_create(self.sp.current_user()["id"], self.playlist_name, public=False, description=playlist_description)

        # Playlist creation
        for idx, (song_name, artist_name) in enumerate(zip(song_names_list, song_artists_list), start=1):
            results = self.sp.search(q=f"{song_name} artist:{artist_name}", type="track")
            if results['tracks']['items']:
                track_uri = results['tracks']['items'][0]['uri']
                self.sp.playlist_add_items(playlist['id'], [track_uri])
                progress_bar["value"] = int((idx / len(song_names_list)) * 100)

        self.playlist_url = playlist['external_urls']['spotify']
        return self.playlist_url

class GUI(tk.Tk):
    # provides a date selection widget and a button to create a Billboard Top 100 playlist based on the selected date. The playlist creation process runs in a separate thread to avoid blocking the GUI, and a progress bar is updated during the creation process. Once the playlist is created, a button is enabled to open the playlist link in a web browser.
    def __init__(self):
        super().__init__()
        self.title("Billboard Top 100 Playlist Creator")
        self.geometry("220x300")
        self.configure(padx=10)

        self.playlist_creator = PlaylistCreator()

        self.create_button()

        self.welcome_label = tk.Label(self, text="THE TOP 100 PLAYLIST GENERATOR\n\n", wrap=150, font=("Oswald", 16, "bold"))
        self.welcome_label.grid(row=1, column=0, columnspan=3, pady=(30, 0))        

        self.cal = DateEntry(self, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.cal.grid(row=3, column=1, padx=10, pady=(0, 10))

        self.btn = ttk.Button(self, text="Submit Date", command=self.get_selected_date)
        self.btn.grid(row=3, column=2, pady=(0, 10))

        self.progress_bar = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=200, mode='determinate')
        self.progress_bar.grid(row=4, column=1, columnspan=3, pady=0)

        self.playlist_link_btn = ttk.Button(self, text="Playlist Link", command=self.open_playlist_link, state=tk.DISABLED)
        self.playlist_link_btn.grid(row=5, column=1, columnspan=3, pady=(10, 0))

    def create_button(self):
        def show_instructions():
            message = ("To create a Billboard Top 100 playlist, select a date from the dropdown menu below.\n\n"
                       "The Playlist Link button will become available once your playlist is ready.")
            messagebox.showinfo("Instructions", message)

        self.button = tk.Button(self, text="Help", command=show_instructions)
        self.button.grid(row=0, column=2, sticky="e", pady=0)

    def get_selected_date(self):
        # retrieves the selected date from the date selection widget, adjusts the year if necessary, and starts a new thread to create the playlist using the PlaylistCreator class.
        user_date_str = self.cal.get_date().strftime('%Y-%m-%d')
        user_date = datetime.strptime(user_date_str, '%Y-%m-%d')

        # Adjust the year if it's greater than the current year
        current_year = datetime.now().year
        if user_date.year > current_year:
            user_date = user_date.replace(year=user_date.year - 100)
        
        print("Selected date:", user_date)

        # Create a new thread for playlist creation
        threading.Thread(target=self.create_playlist_in_thread, args=(user_date,)).start()

    def create_playlist_in_thread(self, user_date):
        # calls the create_playlist method of PlaylistCreator in a separate thread, updates the progress bar and playlist URL, and enables the playlist link button.
        playlist_url = self.playlist_creator.create_playlist(user_date, self.progress_bar)
        self.playlist_creator.playlist_url = playlist_url  # Update the playlist URL in the PlaylistCreator
        self.progress_bar["value"] = 100
        self.playlist_link_btn["state"] = tk.NORMAL

    def open_playlist_link(self):
        # opens the playlist URL in a web browser.
        webbrowser.open(self.playlist_creator.playlist_url)

if __name__ == "__main__":
    app = GUI()
    app.mainloop()
