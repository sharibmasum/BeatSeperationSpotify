import threading
import customtkinter
import os
import subprocess
import pygame
import time

app = customtkinter.CTk()
app.geometry("1000x450")

state = 0
audio_files = []

def playTrack():
    # Loop through all channels and soundsx
    print("Audio files to play:", audio_files)

    pygame.mixer.init()

    global channels, sounds
    channels = [pygame.mixer.Channel(i) for i in range(len(audio_files))]
    sounds = [pygame.mixer.Sound(file) for file in audio_files]

    global song_length
    song_length = sounds[0].get_length()

    global start_time
    start_time = time.time()

    for channel, sound in zip(channels, sounds):
        channel.set_volume(1.0)  # Set volume to maximum
        channel.play(sound)  # Play the sound on the channel

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
    # Channel 0 is to bass
    channels[0].set_volume(float(value) / 100)
    print(f"Bass volume set to {float(value) / 100}")


def changeDrums(value):
    # Channel 1 is to drums
    channels[1].set_volume(float(value) / 100)
    print(f"Drums volume set to {float(value) / 100}")


def changeOther(value):
    # Channel 2 is to "other"
    channels[2].set_volume(float(value) / 100)
    print(f"Other volume set to {float(value) / 100}")

def changeVocals(value):
    # Channel 3 is to "vocals"
    channels[3].set_volume(float(value) / 100)
    print(f"Vocals volume set to {float(value) / 100}")

def create_buttons_for_folders():
    base_path = "htdemucs"
    folders = [folder for folder in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, folder))]

    for i, folder in enumerate(folders):
        button = customtkinter.CTkButton(
            master=app,
            text=folder,
            command=lambda f=folder: on_folder_button_click(f)
        )

        button.place(x=20, y=100 + i * 50, anchor="w")

def on_folder_button_click(folder_name):
    base_path = "htdemucs"
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
        label = customtkinter.CTkLabel(master=app, text="Enter your song's absolute path")
        label.place(x=500, y=150, anchor="center")

        textbox = customtkinter.CTkTextbox(master=app, width=300, height=25)
        textbox.place(x=500, y=185, anchor="center")
        textbox.insert("0.0", "new text to insert")

        def showSaved():
            global state
            state = 1
            app.after(100, update_ui)  # Safely schedule UI update

        button1 = customtkinter.CTkButton(master=app, text="Pick from saved", fg_color="red", hover_color="darkred", command=showSaved)
        button1.place(x=500, y=300, anchor="center")

        def pressed():
            freevariable = textbox.get("1.0", "end-1c")
            print(freevariable)
            textbox.delete("1.0", "end-1c")
            textbox.insert("0.0", "Sent Path")

            loading_label = customtkinter.CTkLabel(master=app, text="Loading... 0%")
            loading_label.place(x=500, y=250, anchor="center")

            threading.Thread(
                target=separate_audio, args=(freevariable, loading_label), daemon=True
            ).start()

        button = customtkinter.CTkButton(master=app, command=pressed, text="Split Track")
        button.place(x=500, y=225, anchor="center")

    elif state == 1:
        play_button = customtkinter.CTkButton(app, text="Play Track", command=on_button_click, width = 300)
        play_button.place(x=750, y=100, anchor="center")

        # Sliders for controlling individual and master volumes
        bass_slider = customtkinter.CTkSlider(app, from_=0, to=100, command=changeBass, width = 300)
        bass_slider.place(x=750, y=150, anchor="center")
        bass_slider.set(100)

        drums_slider = customtkinter.CTkSlider(app, from_=0, to=100, command=changeDrums, width = 300)
        drums_slider.place(x=750, y=200, anchor="center")
        drums_slider.set(100)

        other_slider = customtkinter.CTkSlider(app, from_=0, to=100, command=changeOther, width = 300)
        other_slider.place(x=750, y=250, anchor="center")
        other_slider.set(100)

        vocals_slider = customtkinter.CTkSlider(app, from_=0, to=100, command=changeVocals, width = 300)
        vocals_slider.place(x=750, y=300, anchor="center")
        vocals_slider.set(100)

        global progress_slider
        progress_slider = customtkinter.CTkSlider(app, from_=0, to=100, width = 400, fg_color="red", progress_color="darkred", button_color = "darkred", button_hover_color = "darkred")
        progress_slider.place(x=750, y=350, anchor="center")

        def goBack():
            global state  # Access the global state variable
            state = 0  # Reset the state to 0
            if 'channels' in globals() and channels and any(channel.get_busy() for channel in channels): # channles could also not be defined at this point LOL
                stopAllTracks()
            app.after(100, update_ui)  # Safely update the UI

        buttonGoBack = customtkinter.CTkButton(master=app, text="Go Back", command=goBack, width = 150)
        buttonGoBack.place(x=20, y=415, anchor="w")

        label2 = customtkinter.CTkLabel(master=app, text="Saved Songs, Pick From:")
        label2.place(x=100, y=50, anchor="center")
        create_buttons_for_folders()

def separate_audio(audio_file_path, loading_label):
    global state
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

            # Define the path to the separated files
            separated_path = os.path.join(directory, "htdemucs", filename.rsplit('.', 1)[0])
            global audio_files
            audio_files = [
                f"{separated_path}/bass.wav",
                f"{separated_path}/drums.wav",
                f"{separated_path}/other.wav",
                f"{separated_path}/vocals.wav"
            ]

            # Update state and rebuild UI
            state = 1
            app.after(100, update_ui)  # Safely schedule UI update
        else:
            loading_label.configure(text="Error during processing.")
    except FileNotFoundError:
        loading_label.configure(text="Error: Demucs not found. Install using 'pip install demucs'.")
    except Exception as e:
        loading_label.configure(text=f"An error occurred: {str(e)}")


update_ui()
app.mainloop()