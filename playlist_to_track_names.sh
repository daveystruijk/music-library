#!/bin/bash

PLAYLIST=$1
tail -n +2 "_Playlists/$PLAYLIST.m3u" | sed "s/\'/\\\'/g" | sed "s/\.mp3$//g" | xargs -I '{}' basename '{}' | pbcopy
echo "Tracklist for '$PLAYLIST' copied to clipboard."

