# Python Youtube Downloader

A simple python youtube video downloader.
Uses ffmpeg to merge video and audio streams.

## usage

Pass the Youtube Video ID or a youtube link as a commandline argument. 
```
$ python videodownload.py https://www.youtube.com/watch?v=ucbx9we6EHk 
```
You can specify the name of the downloaded video file. Default is the video title.
```
$ python videodownload.py https://www.youtube.com/watch?v=ucbx9we6EHk my_file_name.mp4
```
The `-mp3` option allows to just download the audio and convert it to mp3.
```
$ python videodownload.py https://www.youtube.com/watch?v=ucbx9we6EHk -mp3
```
The `-cq` option allows to choose the desired quality for the download. Default is the best quality availibe, though this creates larger files and therefore slower downloads.
```
$ python videodownload.py https://www.youtube.com/watch?v=ucbx9we6EHk -cq
```