## Music Library Organization

Each primary genre should have its own directory within the root of this project, e.g. "House" or "Pop". There's also a special directory, "\_New", in which you can place newly downloaded tracks. The "\_Playlists" folder contains generated m3u files per genre.

## Features

The analysis script, *analyze.py*, roughly does the following for each track:

- Extract ID3 title & artist metadata from filename *(Please make sure all your tracks are named "Artist - Title")*
- Detect the track's key using [KeyFinder](http://www.ibrahimshaath.co.uk/keyfinder/). Depends on [keyfinder-cli](https://github.com/EvanPurkhiser/keyfinder-cli)!
- Open the track in your music player & spectrum analyzer for quick previewing
- Warn of files with low bitrate
- Edit (through user input) or clear several tags for newly downloaded files
- After cleaning/editing, move files from "\_New" to the specified genre/directory
- Edit the ID3 genre tag based on a file's directory
- Lots of other stuff, which can be turned on/off by commenting the lines in the *analyze* method. Most of the methods should be pretty self-explanatory.

## Usage

- Run: ```./analyze.py```
