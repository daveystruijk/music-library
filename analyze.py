#!/usr/local/bin/python
import readline
import glob2
import logging
import shutil
from os import listdir, getcwd
from os.path import splitext, basename, dirname, isdir, join
from mutagen.mp3 import MP3
from mutagen.id3 import TIT2, TOPE, TCON

NEW_TRACKS_DIRECTORY = 'New'

logging.basicConfig(format='%(levelname)s: %(message)s')
logging.getLogger().setLevel(logging.INFO)

def analyze(filepath):
    print "\n=> %s" % filepath
    file_handle = open(filepath)
    mp3 = MP3(filepath)
    extract_title_and_artist_from_filename(file_handle, mp3)
    file_handle, mp3 = move_to_folder_if_new(file_handle, mp3)
    extract_genre_from_directory_name(file_handle, mp3)

def extract_title_and_artist_from_filename(file_handle, mp3):
    filename = splitext(basename(file_handle.name))[0]
    tokens = filename.split(' - ')
    if (len(tokens) != 2):
        logging.warning("Cannot extract title and artist from filename")
        return
    mp3.tags.add(TIT2(encoding=3, text=tokens[1])) # title
    mp3.tags.add(TOPE(encoding=3, text=tokens[0])) # artist
    mp3.save()

def move_to_folder_if_new(file_handle, mp3):
    directory = dirname(file_handle.name)
    if (directory != NEW_TRACKS_DIRECTORY):
        return file_handle, mp3
    print "New file! Which genre should it be moved to?"
    possible_directories = [d for d in glob2.glob("*") if isdir(d)]
    new_directory = ''
    while (new_directory not in possible_directories):
        new_directory = raw_input("Genre: ")
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

tracks = glob2.glob("**/*.mp3")
for track in tracks:
    analyze(track)
