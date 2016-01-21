## Music Library Organization

Each primary genre should have its own directory within the root of this project, e.g. "House" or "Pop". There's also a special directory, "\_New", in which you can place newly downloaded tracks.

## Features

The analysis script, *analyze.py*, does the following:

- Extract ID3 title & artist metadata from filename *(Please make sure all your tracks are named "Artist - Title")*
- Detect the track's key using [KeyFinder](http://www.ibrahimshaath.co.uk/keyfinder/). Depends on [keyfinder-cli](https://github.com/EvanPurkhiser/keyfinder-cli)!
- Edit the rating for newly downloaded files
- Edit the remixer tag for newly downloaded files
- Edit the comment tag for newly downloaded files
- Move files from "\_New" to a user-specified genre/directory
- Edit the ID3 genre tag based on a file's directory

## Usage

- Run: ```./analyze.py```
