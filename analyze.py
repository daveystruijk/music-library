#!/usr/local/bin/python
import readline
import glob2
import logging
import shutil
import re
import subprocess
from os import listdir, getcwd
from os.path import splitext, basename, dirname, isdir, join
from colorama import init, Fore, Back, Style
from mutagen import File
from mutagen.mp3 import MP3
from mutagen.id3 import TIT2, TOPE, TCON, TKEY, POPM, COMM, TPE4, ID3NoHeaderError
from mutagen.easyid3 import EasyID3

NEW_TRACKS_DIRECTORY = '_New'
KEY_NOTATION = 'openkey'
SPECTRUM_ANALYZER_PATH = '/opt/homebrew-cask/Caskroom/spek/0.8.3/Spek.app'
MUSIC_PLAYER_PATH = '/Applications/iTunes.app'

logging.basicConfig(format='%(levelname)s: %(message)s')
logging.getLogger().setLevel(logging.INFO)
init() # colorama

def analyze(filepath):
    print Fore.GREEN + "\n=> %s" % filepath + Style.RESET_ALL
    file_handle = open(filepath)
    ensure_id3_tag_present(filepath)
    mp3 = MP3(filepath)
    open_music_player(file_handle, mp3)
    open_spectrum_analyzer(file_handle, mp3)
    warn_low_bitrate(file_handle, mp3)
    extract_title_and_artist_from_filename(file_handle, mp3)
    detect_key(file_handle, mp3)
    #add_rating(file_handle, mp3)
    #add_remixer(file_handle, mp3)
    #add_comment_tags(file_handle, mp3)
    clear_comments(file_handle, mp3)
    file_handle, mp3 = move_to_folder_if_new(file_handle, mp3)
    extract_genre_from_directory_name(file_handle, mp3)

def ensure_id3_tag_present(filepath):
    try:
        meta = EasyID3(filepath)
    except ID3NoHeaderError:
        meta = File(filepath, easy=True)
        meta.add_tags()
        meta.save()

def open_music_player(file_handle, mp3):
    if (dirname(file_handle.name) == NEW_TRACKS_DIRECTORY):
        subprocess.call(['open', '-g', '-a', MUSIC_PLAYER_PATH, file_handle.name])

def open_spectrum_analyzer(file_handle, mp3):
    if (dirname(file_handle.name) == NEW_TRACKS_DIRECTORY):
        subprocess.call(['open', '-g', '-a', SPECTRUM_ANALYZER_PATH, file_handle.name])

def warn_low_bitrate(file_handle, mp3):
    kbps = mp3.info.bitrate / 1000
    if (kbps < 250):
        logging.warning("Low bitrate: %s" % kbps)

def extract_title_and_artist_from_filename(file_handle, mp3):
    filename = splitext(basename(file_handle.name))[0]
    tokens = filename.split(' - ')
    if (len(tokens) != 2):
        logging.warning("Cannot extract title and artist from filename")
        return
    mp3.tags.add(TIT2(encoding=3, text=tokens[1])) # title
    mp3.tags.add(TOPE(encoding=3, text=tokens[0])) # artist
    mp3.save()

def detect_key(file_handle, mp3):
    key = mp3.tags.get('TKEY')
    pattern = re.compile("^[0-9]{1,2}[md]$")
    if (key != None and pattern.match(key.text[0])):
        return # return if track already has a valid key
    if not cmd_exists("keyfinder-cli"):
        logging.warning("Cannot find keyfinder-cli")
        return
    logging.info("Detecting key...")
    new_key = subprocess.check_output(["keyfinder-cli", "-n", KEY_NOTATION,file_handle.name]).strip()
    mp3.tags.add(TKEY(encoding=3, text=new_key))
    mp3.save()

def add_rating(file_handle, mp3):
    directory = dirname(file_handle.name)
    popularimeter = mp3.tags.get(u'POPM:None')
    if (popularimeter != None and directory != NEW_TRACKS_DIRECTORY):
        return
    print "What rating should this track have? [1-5]"
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
            print "Error, invalid rating"

def add_remixer(file_handle, mp3):
    directory = dirname(file_handle.name)
    if (directory != NEW_TRACKS_DIRECTORY):
        return
    print "If this is a remix, enter the remixer (else, leave empty)"
    new_remixer = get_input("Remixer: ")
    if (new_remixer == ''):
        mp3.tags.delall('TPE4')
        mp3.save()
    else:
        mp3.tags.add(TPE4(encoding=3, text=new_remixer))
        mp3.save()

def add_comment_tags(file_handle, mp3):
    directory = dirname(file_handle.name)
    if (directory != NEW_TRACKS_DIRECTORY):
        return
    comments = mp3.tags.getall('COMM')
    print "Current comments: %s" % map(lambda c: c.text[0], comments)
    print "Enter new comment or press enter to leave unchanged (or 'clear' to delete)"
    new_comment = get_input("Comment: ")
    new_comment = new_comment.strip()
    if (new_comment == 'clear'):
        mp3.tags.delall('COMM')
        mp3.save()
    elif (new_comment != ''):
        mp3.tags.setall('COMM', [COMM(encoding=3, lang='eng', text=new_comment)])
        mp3.save()

def clear_comments(file_handle, mp3):
    directory = dirname(file_handle.name)
    if (directory != NEW_TRACKS_DIRECTORY):
        return
    mp3.tags.delall('COMM')
    mp3.save()

def move_to_folder_if_new(file_handle, mp3):
    directory = dirname(file_handle.name)
    if (directory != NEW_TRACKS_DIRECTORY):
        return file_handle, mp3
    print "Which genre should it be moved to? (leave empty to move nothing)"
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
            print "Moving file from %s to %s" % (directory, new_directory)
            file_handle.close()
            shutil.move(old_filename, new_filename)
            return open(new_filename), MP3(new_filename)
        else:
            print "Error, there's no directory for that genre"

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
    return raw_input(Fore.YELLOW + text + Style.RESET_ALL).strip()

def cmd_exists(cmd):
    return subprocess.call("type " + cmd, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

tracks = glob2.glob("**/*.mp3")
for track in tracks:
    analyze(track)
