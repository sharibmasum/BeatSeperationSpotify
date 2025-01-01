import threading
import customtkinter
import subprocess
import pygame
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv
import yt_dlp


def configure():
    load_dotenv()

configure()
app = customtkinter.CTk()
app.title("Spotify and Beat Seperator Prototype")
app.geometry("1000x450")

state = 0
audio_files = []

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
SCOPE = os.getenv('SCOPE')

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE
))

api_key = os.getenv('api_key')
youtube = build('youtube', 'v3', developerKey=api_key)
DOWNLOAD_DIR = "spotify_songs"
def download_wav_with_ytdlp(youtube_url, filename):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f"{DOWNLOAD_DIR}/{filename}.%(ext)s",
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        wav_file_path = os.path.join(DOWNLOAD_DIR, f"{filename}.wav")
        print(f"Downloaded: {wav_file_path}")
        return wav_file_path
    except Exception as e:
        print(f"Error downloading {youtube_url}: {e}")
        return None
def search_youtube_video(query):
    try:
        search_response = youtube.search().list(
            q=query,
            part='snippet',
            maxResults=1
        ).execute()

        if 'items' in search_response and len(search_response['items']) > 0:
            video_id = search_response['items'][0]['id']['videoId']
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
            return youtube_url
        else:
            print(f"Cant find the video {query}")
            return None
    except Exception as e:
        print(f"There was an erorr searching for the vid: {e}")
        return None

def populateScreenWithLikedSongs():
    try:
        #Getting the users liked songs from spotify
        results = sp.current_user_saved_tracks(limit=50)  # getting 50 song (more burns out the api)

        #Removing other songs that may not be ther anymore
        widgets = app.winfo_children()
        for widget in widgets:
            try:
                widget.destroy()
            except Exception as e:
                print(f"Cant destroy the widget for reason: {widget}: {e}")


        # Show the liked songs
        for i, item in enumerate(results['items']):
            track = item['track']
            song_name = track['name']
            artist_name = track['artists'][0]['name']
            query = f"{song_name} {artist_name}"

            # function for each button press
            def download_and_convert(song_name=song_name, query=query):
                print(f"Searching and downloading: {song_name}")
                wav_file_path = download_wav_with_ytdlp(search_youtube_video(query), song_name)

                threading.Thread(
                    target=separate_audio, args=(wav_file_path,), daemon=True
                ).start()

            # Creating a button for each song
            button = customtkinter.CTkButton(
                master=app,
                text=song_name,
                command=download_and_convert,
                width = 300
            )
            button.place(x=20, y=100 + i * 40, anchor="w")

    except Exception as e:
        print(f"Error populating screen with liked songs: {e}")

def playTrack():
    print("Audio files to play:", audio_files)

    pygame.mixer.init()

    #Sound hold the actual file, channel holds volume
    global channels, sounds
    channels = [pygame.mixer.Channel(i) for i in range(len(audio_files))]
    sounds = [pygame.mixer.Sound(file) for file in audio_files]

    global song_length
    song_length = sounds[0].get_length()

    global start_time
    start_time = time.time()

    for channel, sound in zip(channels, sounds):
        channel.set_volume(1.0)
        channel.play(sound)

    update_timeline()

def update_timeline():
    global progress_slider, song_length, start_time

    if channels and channels[0].get_busy():
        elapsed_time = time.time() - start_time
        print(elapsed_time)
        progress_percentage = (elapsed_time / song_length) * 100
        progress_slider.set(progress_percentage)
        app.after(100, update_timeline)  # Update every 100ms


def on_button_click():
    threading.Thread(target=playTrack).start()

def stopAllTracks():
    for channel in channels:
        channel.stop()

def changeBass(value):
    channels[0].set_volume(float(value) / 100)
    print(f"Bass volume set to {float(value) / 100}")


def changeDrums(value):
    channels[1].set_volume(float(value) / 100)
    print(f"Drums volume set to {float(value) / 100}")


def changeOther(value):
    channels[2].set_volume(float(value) / 100)
    print(f"Other volume set to {float(value) / 100}")

def changeVocals(value):
    channels[3].set_volume(float(value) / 100)
    print(f"Vocals volume set to {float(value) / 100}")

def create_buttons_for_folders():
    base_path = "spotify_songs/htdemucs"
    folders = [folder for folder in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, folder))]
    for i, folder in enumerate(folders):
        button = customtkinter.CTkButton(
            master=app,
            text=folder,
            command=lambda f=folder: on_folder_button_click(f)
        )
        button.place(x=20, y=100 + i * 50, anchor="w")

def on_folder_button_click(folder_name):
    base_path = "spotify_songs/htdemucs"
    separated_path = os.path.join(base_path, folder_name)
    global audio_files
    global state
    audio_files = [
        os.path.join(separated_path, "bass.wav"),
        os.path.join(separated_path, "drums.wav"),
        os.path.join(separated_path, "other.wav"),
        os.path.join(separated_path, "vocals.wav"),
    ]
    state = 1
    app.after(100, update_ui)  # Safely schedule UI update
    print(f"Updated audio_files: {audio_files}")

def update_ui():
    widgets = app.winfo_children()
    for widget in widgets:
        try:
            widget.destroy()
        except Exception as e:
            print(f"Error destroying widget {widget}: {e}")

    if state == 0:
        populateScreenWithLikedSongs()
        label = customtkinter.CTkLabel(master=app, text="Enter your song's absolute path")
        label.place(x=750, y=150, anchor="center")

        textbox = customtkinter.CTkTextbox(master=app, width=300, height=25)
        textbox.place(x=750, y=185, anchor="center")
        textbox.insert("0.0", "new text to insert")

        def showSaved():
            global state
            state = 1
            app.after(100, update_ui)

        button1 = customtkinter.CTkButton(master=app, text="Pick from saved", fg_color="red", hover_color="darkred", command=showSaved)
        button1.place(x=750, y=300, anchor="center")

        def pressed():
            freevariable = textbox.get("1.0", "end-1c")
            print(freevariable)
            textbox.delete("1.0", "end-1c")
            textbox.insert("0.0", "Sent Path")



            threading.Thread(
                target=separate_audio, args=(freevariable,), daemon=True
            ).start()

        button = customtkinter.CTkButton(master=app, command=pressed, text="Split Track")
        button.place(x=750, y=225, anchor="center")

    elif state == 1:
        play_button = customtkinter.CTkButton(app, text="Play Track", command=on_button_click, width = 300)
        play_button.place(x=750, y=100, anchor="center")


        bass_slider = customtkinter.CTkSlider(app, from_=0, to=100, command=changeBass, width = 250)
        bass_label = customtkinter.CTkLabel(app, text="Bass")
        bass_label.place(x=625,y=148, anchor="center")
        bass_slider.place(x=770, y=150, anchor="center")
        bass_slider.set(100)

        drums_slider = customtkinter.CTkSlider(app, from_=0, to=100, command=changeDrums, width = 250)
        drums_slider.place(x=770, y=200, anchor="center")
        drums_label = customtkinter.CTkLabel(app, text="Drums")
        drums_label.place(x=625, y=198, anchor="center")
        drums_slider.set(100)

        other_slider = customtkinter.CTkSlider(app, from_=0, to=100, command=changeOther, width = 250)
        other_slider.place(x=770, y=250, anchor="center")
        other_label = customtkinter.CTkLabel(app, text="Other")
        other_label.place(x=625, y=248, anchor="center")
        other_slider.set(100)

        vocals_slider = customtkinter.CTkSlider(app, from_=0, to=100, command=changeVocals, width = 250)
        vocals_slider.place(x=770, y=300, anchor="center")
        vocals_label = customtkinter.CTkLabel(app, text="Vocals")
        vocals_label.place(x=625, y=298, anchor="center")
        vocals_slider.set(100)

        global progress_slider
        progress_slider = customtkinter.CTkSlider(app, from_=0, to=100, width = 400, fg_color="red", progress_color="darkred", button_color = "darkred", button_hover_color = "darkred")
        progress_slider.place(x=750, y=350, anchor="center")

        def goBack():
            global state
            state = 0
            if 'channels' in globals() and channels and any(channel.get_busy() for channel in channels): # channles could also not be defined at this point LOL
                stopAllTracks()
            app.after(100, update_ui)

        buttonGoBack = customtkinter.CTkButton(master=app, text="Go Back", command=goBack, width = 150)
        buttonGoBack.place(x=20, y=415, anchor="w")

        label2 = customtkinter.CTkLabel(master=app, text="Saved Songs, Pick From:")
        label2.place(x=100, y=50, anchor="center")
        create_buttons_for_folders()

def separate_audio(audio_file_path):
    global state

    loading_label = customtkinter.CTkLabel(master=app, text="Loading... 0%")
    loading_label.place(x=750, y=260, anchor="center")

    if not os.path.isfile(audio_file_path):
        loading_label.configure(text="Error: File not found.")
        return

    directory, filename = os.path.split(audio_file_path)

    try:
        process = subprocess.Popen(
            [
                "demucs",
                "-n",
                "htdemucs",
                "--out",
                directory,
                audio_file_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        # Display loading progress
        for line in process.stdout:
            print(line.strip())
            if "%" in line:
                progress = line.split("%")[0].strip()[-3:].strip()
                try:
                    loading_label.configure(text=f"Loading... {progress}%")
                except Exception:
                    pass

        process.wait()

        if process.returncode == 0:
            loading_label.configure(text="Audio separated successfully!")
            separated_path = os.path.join(directory, "htdemucs", filename.rsplit('.', 1)[0])
            global audio_files
            audio_files = [
                f"{separated_path}/bass.wav",
                f"{separated_path}/drums.wav",
                f"{separated_path}/other.wav",
                f"{separated_path}/vocals.wav"
            ]
            state = 1
            app.after(100, update_ui)
        else:
            loading_label.configure(text="Error during processing.")
    except FileNotFoundError:
        loading_label.configure(text="Error: Demucs is being weird.")
    except Exception as e:
        loading_label.configure(text=f"error: {str(e)}")



update_ui()
app.mainloop()