from tabulate import tabulate
import tkinter as tk
import customtkinter
import tkinter.messagebox as messagebox
import sys


def load_tracklist(tracklist_var):
    """
    Process the tracklist data and return a list of dictionaries representing rows of data.
    """
    # Split the data into rows
    rows = tracklist_var.strip().split('\n')
    # Split each row into columns based on tabs
    rows = [row.split('\t') for row in rows]
    # Extract the headers
    headers = rows[0]
    # Create dictionaries for each row
    dict_rows = [create_dict(row, headers) for row in rows[1:]]
    
    # Convert 'Start' and 'End' times to the desired format
    for row in dict_rows:
        row['Start'] = seconds_to_time(int(row['Start']))
        row['End'] = seconds_to_time(int(row['End']))
    
    return dict_rows

def create_dict(row, headers):
    """
    Create a dictionary for a row using the provided headers.
    """
    return {header: value.strip() for header, value in zip(headers, row)}

def seconds_to_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def merge_consecutive_rows(rows):
    """
    Merge consecutive rows with the same values for specified keys.
    """
    merged_rows = []
    i = 0
    while i < len(rows):
        current_row = rows[i].copy()
        # No need to convert 'Start' and 'End' times to integers
        start = current_row.get('Start', '00:00:00')
        end = current_row.get('End', '00:00:00')
        # Find consecutive rows with the same values for specified keys
        while i + 1 < len(rows) and \
              all(rows[i + 1].get(key) == current_row.get(key) for key in ['Artists', 'Track', 'Id', 'Albums']):
            end = rows[i + 1].get('End', '00:00:00')
            i += 1
        current_row['Start'] = start
        current_row['End'] = end
        merged_rows.append(current_row)
        i += 1
    return merged_rows

def get_track_counts(rows):
    """
    Calculate track counts for each artist and album.
    """
    artist_tracks = {}
    album_tracks = {}
    for row_dict in rows:
        artist = row_dict['Artists']
        title = row_dict['Track Title']
        if artist in artist_tracks:
            artist_tracks[artist].append(title)
        else:
            artist_tracks[artist] = [title]
        album = row_dict['Albums']
        if album in album_tracks:
            album_tracks[album].append(title)
        else:
            album_tracks[album] = [title]
    return artist_tracks, album_tracks

def get_exceeding_artists(artist_tracks):
    """
    Identify artists with 5 or more tracks.
    """
    exceeding_artists = {}
    for artist, tracks in artist_tracks.items():
        if len(tracks) >= 5:
            exceeding_artists[artist] = {'count': len(tracks), 'tracks': tracks}
    return exceeding_artists

def get_exceeding_albums(album_tracks):
    """
    Identify albums with 4 or more tracks.
    """
    exceeding_albums = {}
    for album, tracks in album_tracks.items():
        if len(tracks) >= 4:
            exceeding_albums[album] = {'count': len(tracks), 'tracks': tracks}
    return exceeding_albums

def get_consecutive_artist_tracks(merged_rows):
    """
    Identify consecutive tracks by the same artist.
    """
    consecutive_artist_tracks = {}
    current_artist = None
    current_count = 0
    current_tracks = []
    for row in merged_rows:
        artist = row['Artists']
        track = row['Track Title']
        if artist == current_artist:
            current_count += 1
            current_tracks.append(track)
        else:
            if current_artist is not None and current_count > 3:
                consecutive_artist_tracks[current_artist] = {'count': current_count, 'tracks': current_tracks}
            current_artist = artist
            current_count = 1
            current_tracks = [track]
    return consecutive_artist_tracks

def get_consecutive_album_tracks(merged_rows):
    """
    Identify consecutive tracks from the same album.
    """
    consecutive_album_tracks = {}
    current_album = None
    current_count = 0
    current_tracks = []
    for row in merged_rows:
        album = row['Albums']
        track = row['Track Title']
        if album == current_album:
            current_count += 1
            current_tracks.append(track)
        else:
            if current_album is not None and current_count > 2:
                consecutive_album_tracks[current_album] = {'count': current_count, 'tracks': current_tracks}
            current_album = album
            current_count = 1
            current_tracks = [track]
    return consecutive_album_tracks

def format_tracklist(merged_rows):
    """
    Format the tracklist for display.
    """
    headers = merged_rows[0].keys()

    # Convert the data into a tabulated format with line breaks for the text
    table_data = []
    for row in merged_rows:
        formatted_row = []
        for key in headers:
            # Add line breaks to long text
            value = row[key]
            if len(value) > 60:  # Adjust the threshold as needed
                split_value = [value[i:i+50] for i in range(0, len(value), 50)]
                formatted_value = '\n'.join(split_value)
                formatted_row.append(formatted_value)
            else:
                formatted_row.append(value)
        table_data.append(formatted_row)

    return tabulate(table_data, headers=headers)

def format_reason_for_restriction(exceeding_artists, exceeding_albums, consecutive_artist_tracks, consecutive_album_tracks):
    """
    Format the reasons for restriction for display.
    """
    result_text = ""
    if exceeding_artists:
        result_text += "Max Tracks By Artist:\n"
        for artist, data in exceeding_artists.items():
            result_text += f"{artist}: {data['count']} tracks\n"
            for track in data['tracks']:
                result_text += f"\t- {track}\n"
        result_text += f"\n"

    if consecutive_artist_tracks:
        result_text += "Max Consecutive Tracks By Artist:\n"
        for artist, data in consecutive_artist_tracks.items():
            result_text += f"{artist}: {data['count']} tracks\n"
            for track in data['tracks']:
                result_text += f"\t- {track}\n"
        result_text += f"\n"

    if exceeding_albums:
        result_text += "Max Tracks From Album:\n"
        for album, data in exceeding_albums.items():
            result_text += f"{album}: {data['count']} tracks\n"
            for track in data['tracks']:
                result_text += f"\t- {track}\n"
        result_text += f"\n"

    if consecutive_album_tracks:
        result_text += "Max Consecutive Tracks From Album:\n"
        for album, data in consecutive_album_tracks.items():
            result_text += f"{album}: {data['count']} tracks\n"
            for track in data['tracks']:
                result_text += f"\t- {track}\n"
        result_text += f"\n"

    return result_text

def format_macro_info(exceeding_artists, consecutive_artist_tracks, exceeding_albums, consecutive_album_tracks):
    """
    Format macro info for display.
    """
    macro_info = f"Our audio fingerprinter has detected that this show contains:\n\n"
    if exceeding_artists:
        for artist, data in exceeding_artists.items():
            macro_info += f"\t\t- {data['count']} tracks by {artist}:\n"
            for track in data['tracks']:
                macro_info += f"\t\t\t\t- {track}\n"
        macro_info += f"\t\tThis exceeds the limit set for the number of total tracks by one recording artist.\n\n"
    if consecutive_artist_tracks:
        for artist, data in consecutive_artist_tracks.items():
            macro_info += f"\t\t -{data['count']} consecutive tracks by {artist}:\n"
            for track in data['tracks']:
                macro_info += f"\t\t\t\t- {track}\n"
        macro_info += f"\t\tThis exceeds the limit set for the number of consecutive tracks by one recording artist.\n\n"
    if exceeding_albums:
        for album, data in exceeding_albums.items():
            macro_info += f"\t\t- {data['count']} tracks from the album \"{album}\":\n"
            for track in data['tracks']:
                macro_info += f"\t\t\t\t- {track}\n"
        macro_info += f"\t\tThis exceeds the limit set for the number of total tracks from the same album.\n\n"
    if consecutive_album_tracks:
        for album, data in consecutive_album_tracks.items():
            macro_info += f"\t\t- {data['count']} consecutive tracks from the album \"{album}\":\n"
            for track in data['tracks']:
                macro_info += f"\t\t\t\t- {track}\n"
        macro_info += f"\t\tThis exceeds the limit set for the number of consecutive tracks from the same album.\n\n"
    return macro_info

# Global exception handler for any error messages within application
def display_error_message(exc_type, exc_value, exc_traceback):
    error_message = "An error occurred."
    messagebox.showerror("Error", error_message)

    # traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)

# Set the global exception handler
sys.excepthook = display_error_message

# Button functions
# Function to display the tracklist
def display_tracklist():
    global tracklist_var
    tracklist_data = tracklist_var.get()
    if tracklist_data:
        try:
            rows = load_tracklist(tracklist_data)
            merged_rows = merge_consecutive_rows(rows)
            formatted_tracklist = format_tracklist(merged_rows)
            tracklist_text.config(state="normal")  # Enable editing
            tracklist_text.delete(1.0, tk.END)  # Clear previous content
            tracklist_text.insert(tk.END, formatted_tracklist)
            tracklist_text.config(state="disabled")  # Disable editing again
        except Exception as e:
            error_message = "Error: Incorrect format. Please check your input."
            tracklist_text.config(state="normal")  # Enable editing
            tracklist_text.delete(1.0, tk.END)  # Clear previous content
            tracklist_text.insert(tk.END, error_message)
            tracklist_text.config(state="disabled")  # Disable editing again
    else:
        tracklist_text.config(state="normal")
        tracklist_text.delete(1.0, tk.END)
        tracklist_text.insert(tk.END, "Please paste the tracklist before displaying.")
        tracklist_text.config(state="disabled")

# Function to see reasons for restriction
def see_reason_for_restriction():
    global tracklist_var
    tracklist_data = tracklist_var.get()
    if tracklist_data:
        rows = load_tracklist(tracklist_data)
        merged_rows = merge_consecutive_rows(rows)
        artist_tracks, album_tracks = get_track_counts(merged_rows)
        exceeding_artists = get_exceeding_artists(artist_tracks)
        exceeding_albums = get_exceeding_albums(album_tracks)
        consecutive_artist_tracks = get_consecutive_artist_tracks(merged_rows)
        consecutive_album_tracks = get_consecutive_album_tracks(merged_rows)
        
        # Check if any restrictions are found
        if not (exceeding_artists or exceeding_albums or consecutive_artist_tracks or consecutive_album_tracks):
            reason_text = "No restrictions found."
        else:
            reason_text = format_reason_for_restriction(exceeding_artists, exceeding_albums, consecutive_artist_tracks, consecutive_album_tracks)
            
        tracklist_text.config(state="normal")  # Enable editing
        tracklist_text.delete(1.0, tk.END)  # Clear previous content
        tracklist_text.insert(tk.END, reason_text)
        tracklist_text.config(state="disabled")  # Disable editing again
    else:
        tracklist_text.config(state="normal")
        tracklist_text.delete(1.0, tk.END)
        tracklist_text.insert(tk.END, "Please paste the tracklist before checking reasons for restriction.")
        tracklist_text.config(state="disabled")

# Function to see macro info
def see_macro_info():
    global tracklist_var
    tracklist_data = tracklist_var.get()
    if tracklist_data:
        rows = load_tracklist(tracklist_data)
        merged_rows = merge_consecutive_rows(rows)
        artist_tracks, album_tracks = get_track_counts(merged_rows)
        exceeding_artists = get_exceeding_artists(artist_tracks)
        exceeding_albums = get_exceeding_albums(album_tracks)
        consecutive_artist_tracks = get_consecutive_artist_tracks(merged_rows)
        consecutive_album_tracks = get_consecutive_album_tracks(merged_rows)
        
        # Check if any restrictions are found
        if not (exceeding_artists or exceeding_albums or consecutive_artist_tracks or consecutive_album_tracks):
            macro_info_text = "Our audio fingerprinter has detected that this show contains: No restrictions."
        else:
            macro_info_text = format_macro_info(exceeding_artists, consecutive_artist_tracks, exceeding_albums, consecutive_album_tracks)
            
        tracklist_text.config(state="normal")  # Enable editing
        tracklist_text.delete(1.0, tk.END)  # Clear previous content
        tracklist_text.insert(tk.END, macro_info_text)
        tracklist_text.config(state="disabled")  # Disable editing again
    else:
        tracklist_text.config(state="normal")
        tracklist_text.delete(1.0, tk.END)
        tracklist_text.insert(tk.END, "Please paste the tracklist before checking macro info.")
        tracklist_text.config(state="disabled")

# Function to start a new show
def new_show():
    tracklist_text.delete(1.0, tk.END)
    tracklist_var.set("")

    see_example()

# Function to copy output in text field
def copy():
    content = tracklist_text.get("1.0", tk.END)
    if content.strip():
        app.clipboard_clear()
        app.clipboard_append(content)

# Showing example of input function
def see_example():
    example_text = '''Use the following format that includes the header:\n
    Start	End	Artists	Track Title	Id	Albums
0	30	Mack Fields	Bowling Ball Blues	3530145	Cults Hits Novelty Classics, Vol. 1
30	60	Mack Fields	Bowling Ball Blues	3530145	Cults Hits Novelty Classics, Vol. 1
60	90	Mack Fields	Bowling Ball Blues	3530145	Cults Hits Novelty Classics, Vol. 1
90	120	Mack Fields	Bowling Ball Blues	3530145	Cults Hits Novelty Classics, Vol. 1
120	150	Hank Locklin	I m Tired Of Bummin Around	4838751	Queen Of Hearts
150	180	Hank Locklin	I m Tired Of Bummin Around	4838751	Queen Of Hearts
180	210	Hank Locklin	I m Tired Of Bummin Around	4838751	Queen Of Hearts
210	240	Hank Locklin	I m Tired Of Bummin Around	4838751	Queen Of Hearts
240	270	Hank Locklin	I m Tired Of Bummin Around	4838751	Queen Of Hearts
390	420	Hank Thompson	Hangover Tavern	2964975	A Six Pack To Go
420	450	Hank Thompson	Hangover Tavern	2964975	A Six Pack To Go
450	480	Hank Thompson	Hangover Tavern	2964975	A Six Pack To Go
480	510	Hank Thompson	Hangover Tavern	2964975	A Six Pack To Go
510	540	Hank Thompson	Hangover Tavern	2964975	A Six Pack To Go
540	570	Hank Thompson	Hangover Tavern	2964975	A Six Pack To Go\n ...'''
    # Clear previous content and set state to normal
    tracklist_text.config(state="normal")
    tracklist_text.delete(1.0, tk.END)
    tracklist_text.insert(tk.END, example_text)
    # Disable editing again
    tracklist_text.config(state="disabled")


# System settings
customtkinter.set_appearance_mode("system")
customtkinter.set_default_color_theme("dark-blue")

# App frame
app = customtkinter.CTk()
app.geometry("1600x800")
app.title("Tracklist Combiner")

# Adding UI elements
title = customtkinter.CTkLabel(app, text = "Paste the tracklist here (including the headers): ")
title.pack(padx = 10, pady = 10)

# Tracklist input
tracklist_var = tk.StringVar()
tracklist = customtkinter.CTkEntry(app, width = 600, height = 40, textvariable = tracklist_var)
tracklist.pack()

# Display tracklist button
display_button = customtkinter.CTkButton(app, text="Display Tracklist", command=display_tracklist, height=30, width=180)
display_button.pack(pady = 5)

# See reason for restriction button
reason_button = customtkinter.CTkButton(app, text="See Reason for Restriction", command=see_reason_for_restriction, height=30, width=180)
reason_button.pack(pady = 5)

# See macro info button
macro_info_button = customtkinter.CTkButton(app, text="See Macro Info", command=see_macro_info, height=30, width=180)
macro_info_button.pack(pady = 5)

# New show button
new_show_button = customtkinter.CTkButton(app, text="New Show", command=new_show, height=30, width=180)
new_show_button.pack(pady = 5)

# Text widget to display tracklist
tracklist_text = tk.Text(app, width=600, height=30, state="disabled")
tracklist_text.pack(padx=10, pady=10)
see_example()
# font=("TkDefaultFont", 14)

# Copy button of the output
copy_button = customtkinter.CTkButton(app, text="Copy", command=copy, height=30, width=180)
copy_button.pack(pady=5)

# Run app
#see_example()
app.mainloop()