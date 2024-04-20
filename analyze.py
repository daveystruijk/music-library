#!/usr/local/bin/python
import readline
import glob2
import logging
import shutil
import re
import subprocess
import time
from collections import defaultdict
from os import listdir, getcwd, remove, rename, getenv
from os.path import splitext, basename, dirname, isdir, join
from colorama import init, Fore, Back, Style
from mutagen import File
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TOPE, TCON, TKEY, POPM, COMM, TPE1, TPE4, TDRC, ID3NoHeaderError

NEW_TRACKS_DIRECTORY = '_New'
PLAYLISTS_DIRECTORY = '_Playlists'
KEY_NOTATION = 'openkey'
SPECTRUM_ANALYZER_PATH = '/Applications/Spek.app'
MUSIC_PLAYER_PATH = '/Applications/VLC.app'

logging.basicConfig(format=Fore.MAGENTA + '%(levelname)s: %(message)s' + Style.RESET_ALL)
logging.getLogger().setLevel(logging.INFO)
TIMINGS = defaultdict(float)
init() # colorama

def count_time(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        TIMINGS[f.__name__] += (time2-time1)
        return ret
    return wrap


def analyze(filepath):
    print(Fore.GREEN + "\n=> %s" % filepath + Style.RESET_ALL)
    file_handle = open(filepath)
    ensure_id3_tag_present(filepath)
    mp3 = MP3(filepath)
    #open_music_player(file_handle, mp3)
    #open_spectrum_analyzer(file_handle, mp3)
    warn_low_bitrate(file_handle, mp3)
    file_handle, mp3 = remove_unwanted_text_from_filename(file_handle, mp3)
    file_handle, mp3 = extract_title_and_artist_from_filename(file_handle, mp3)
    #detect_key(file_handle, mp3)
    #pad_key(file_handle, mp3)
    #add_key_to_title_tag(file_handle, mp3)
    #add_rating(file_handle, mp3)
    #add_remixer(file_handle, mp3)
    #add_comment_tags(file_handle, mp3)
    clear_comments(file_handle, mp3)
    file_handle, mp3 = move_to_folder_if_new(file_handle, mp3)
    extract_genre_from_directory_name(file_handle, mp3)

@count_time
def ensure_id3_tag_present(filepath):
    try:
        meta = ID3(filepath)
    except ID3NoHeaderError:
        meta = File(filepath, easy=True)
        meta.add_tags()
        meta.save()

@count_time
def open_music_player(file_handle, mp3):
    if (dirname(file_handle.name) == NEW_TRACKS_DIRECTORY):
        subprocess.call(['open', '-g', '-a', MUSIC_PLAYER_PATH, file_handle.name])

@count_time
def open_spectrum_analyzer(file_handle, mp3):
    if (dirname(file_handle.name) == NEW_TRACKS_DIRECTORY):
        subprocess.call(['open', '-g', '-a', SPECTRUM_ANALYZER_PATH, file_handle.name])

@count_time
def warn_low_bitrate(file_handle, mp3):
    kbps = mp3.info.bitrate / 1000
    if (kbps < 250):
        logging.warning("Low bitrate: %s" % kbps)

@count_time
def remove_unwanted_text_from_filename(file_handle, mp3):
    filename = splitext(basename(file_handle.name))[0]
    for regex in [
            "\(.*(original|dirty|clean|extended|radio edit).*\)",
            "\[.*(original|dirty|clean|extended|radio edit).*\]"
        ]:
        pattern = re.compile(regex, re.IGNORECASE)
        result = re.search(pattern, filename)
        # Definitely drop matches with 'remix' or 'bootleg' in it,
        # as we don't want to lose important information.
        if result != None and not any(word in result.group().lower() for word in ["remix", "bootleg"]):
            print("Removed " + Fore.YELLOW + result.group() + Style.RESET_ALL + " from filename")
            filename = pattern.sub('', filename).strip()
    new_location = dirname(file_handle.name) + '/' + filename + '.mp3'
    if file_handle.name != new_location:
        rename(file_handle.name, new_location)
        print("File renamed as %s" % new_location)
        file_handle.close()
        return open(new_location), MP3(new_location)
    else:
        return file_handle, mp3

@count_time
def extract_title_and_artist_from_filename(file_handle, mp3):
    filename = splitext(basename(file_handle.name))[0]
    tokens = filename.split(' - ')
    if (len(tokens) != 2):
        title = mp3.tags.get('TIT2')
        artist = mp3.tags.get('TPE1')
        if (title == None or artist == None):
            print("Cannot extract title and artist from filename")
        else:
            new_filename = artist.text[0] + ' - ' + title.text[0]
            print("Cannot extract title and artist from filename. Rename file to '%s' ?" % new_filename)
            answer = get_input('y/n: ')
            if (answer == 'y'):
                new_location = dirname(file_handle.name) + '/' + new_filename + '.mp3'
                rename(file_handle.name, new_location)
                print("File renamed as %s" % new_location)
                file_handle.close()
                return open(new_location), MP3(new_location)
        return file_handle, mp3
    else:
        mp3.tags.add(TIT2(encoding=3, text=tokens[1])) # title
        mp3.tags.add(TOPE(encoding=3, text=tokens[0])) # original artist
        mp3.tags.add(TPE1(encoding=3, text=tokens[0])) # artist
        mp3.save()
        return file_handle, mp3

@count_time
def detect_key(file_handle, mp3):
    key = mp3.tags.get('TKEY')
    print(key)
    pattern = re.compile("^[0-9]{1,2}[md]$")
    if (key != None and pattern.match(key.text[0])):
        return # return if track already has a valid key
    if not cmd_exists("keyfinder-cli"):
        logging.warning("Cannot find keyfinder-cli")
        return
    logging.info("Detecting key...")
    new_key = subprocess.check_output(["keyfinder-cli", "-n", KEY_NOTATION,file_handle.name]).strip()
    mp3.tags.add(TKEY(encoding=3, text=new_key.decode()))
    mp3.save()

@count_time
def pad_key(file_handle, mp3):
    key = mp3.tags.get('TKEY')
    if key != None and len(key.text[0]) == 2:
        new_key = "0" + key.text[0]
        mp3.tags.add(TKEY(encoding=3, text=new_key))
        mp3.save()

@count_time
def add_key_to_title_tag(file_handle, mp3):
    key = mp3.tags.get('TKEY')
    title = mp3.tags.get('TIT2')
    if title != None and key != None:
        new_title = key.text[0] + "] " + title.text[0]
        mp3.tags.add(TIT2(encoding=3, text=new_title)) # title
        mp3.save()

@count_time
def add_rating(file_handle, mp3):
    directory = dirname(file_handle.name)
    popularimeter = mp3.tags.get(u'POPM:None')
    if (popularimeter != None and directory != NEW_TRACKS_DIRECTORY):
        return
    print("What rating should this track have? [1-5]")
    rating = None
    while(rating == None):
        stars = get_input("Stars: ")
        if (stars == '0'):
            mp3.tags.delall('POPM')
            mp3.save()
            return
        rating = stars_to_popm_value(stars)
        if (rating != None):
            mp3.tags.setall('POPM', [POPM(rating=rating)])
            mp3.save()
        else:
            print("Error, invalid rating")

@count_time
def add_remixer(file_handle, mp3):
    directory = dirname(file_handle.name)
    if (directory != NEW_TRACKS_DIRECTORY):
        return
    print("If this is a remix, enter the remixer (else, leave empty)")
    new_remixer = get_input("Remixer: ")
    if (new_remixer == ''):
        mp3.tags.delall('TPE4')
        mp3.save()
    else:
        mp3.tags.add(TPE4(encoding=3, text=new_remixer))
        mp3.save()

@count_time
def add_comment_tags(file_handle, mp3):
    directory = dirname(file_handle.name)
    if (directory != NEW_TRACKS_DIRECTORY):
        return
    comments = mp3.tags.getall('COMM')
    print("Current comments: %s" % map(lambda c: c.text[0], comments))
    print("Enter new comment or press enter to leave unchanged (or 'clear' to delete)")
    new_comment = get_input("Comment: ")
    new_comment = new_comment.strip()
    if (new_comment == 'clear'):
        mp3.tags.delall('COMM')
        mp3.save()
    elif (new_comment != ''):
        mp3.tags.setall('COMM', [COMM(encoding=3, lang='eng', text=new_comment)])
        mp3.save()

@count_time
def clear_comments(file_handle, mp3):
    directory = dirname(file_handle.name)
    if (directory != NEW_TRACKS_DIRECTORY):
        return
    mp3.tags.delall('COMM')
    mp3.save()

@count_time
def move_to_folder_if_new(file_handle, mp3):
    directory = dirname(file_handle.name)
    if (directory != NEW_TRACKS_DIRECTORY):
        return file_handle, mp3
    print("Which genre should it be moved to? (leave empty to move nothing)")
    possible_directories = [d for d in glob2.glob("*") if isdir(d)]
    new_directory = ''
    while (new_directory not in possible_directories):
        input_directory = get_input("Genre: ")
        if (input_directory == ''):
            return file_handle, mp3
        for new_dir in possible_directories:
            if new_dir.startswith(input_directory):
                new_directory=new_dir
                break
        if (new_directory in possible_directories):
            old_filename = file_handle.name
            new_filename = new_directory + '/' + basename(file_handle.name)
            print("Moving file from %s to %s" % (directory, new_directory))
            file_handle.close()
            shutil.move(old_filename, new_filename)
            return open(new_filename), MP3(new_filename)
        else:
            print("Error, there's no directory for that genre")

@count_time
def extract_genre_from_directory_name(file_handle, mp3):
    directory = dirname(file_handle.name)
    if (directory == ''):
        logging.warning("Cannot extract genre from directory name")
        return
    mp3.tags.add(TCON(encoding=3, text=directory))
    mp3.save()

def stars_to_popm_value(stars):
    try:
        stars = int(stars)
    except ValueError:
        return None
    values = {
        1: 1,
        2: 64,
        3: 128,
        4: 196,
        5: 255
    }
    return values.get(stars, None)

def get_input(text):
    return input(Fore.YELLOW + text + Style.RESET_ALL).strip()

def cmd_exists(cmd):
    return subprocess.call("type " + cmd, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

# Analysis process for each track
print("\nAnalyzing tracks...")
tracks = sorted(glob2.glob("**/*.[mM][pP]3"), key=lambda x: x.replace('_', '0'))
for track in tracks:
    analyze(track)

# Clear playlists directory
m3u_files = sorted(glob2.glob(PLAYLISTS_DIRECTORY + "/*.[mM]3[uU]"))
for m3u_file in m3u_files:
    remove(m3u_file)

# Generate playlist files
print("\nGenerating playlist files...")
directories = [ p.replace('/', '') for p in glob2.glob('*/') ]
for directory in directories:
    if (directory.startswith('_')):
        continue
    playlist_path = PLAYLISTS_DIRECTORY + '/' + directory + '.m3u'
    print(Fore.GREEN + "=> %s" % playlist_path + Style.RESET_ALL)
    playlist_file = open(playlist_path, 'w')
    tracks = sorted(glob2.glob(directory + "/*.[mM][pP]3"))
    playlist_file.write("#EXTM3U\n")
    for track in tracks:
        playlist_file.write("../" + track + "\n")
    playlist_file.close()

print("\nTimings:")
for func, seconds in TIMINGS.items():
    print("{} took {}s".format(func, round(seconds, 3)))

