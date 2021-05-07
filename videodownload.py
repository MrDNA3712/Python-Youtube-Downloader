import requests
import logging
from urllib import parse
import json
from tqdm import tqdm
import argparse
import ffmpeg
import tempfile
import os

class Stream():
    
    def __init__(self, format_json):
        #self.json = format_json
        self.url = format_json['url']
        self.has_audio = 'audioQuality' in format_json
        if self.has_audio:
            if format_json['audioQuality'] == 'AUDIO_QUALITY_LOW':
                self.audio_quality = 0
            elif format_json['audioQuality'] == 'AUDIO_QUALITY_MEDIUM':
                self.audio_quality = 1
            self.audio_quality_str=format_json['audioQuality']
        else:
            self.audio_quality_str = 'NO_AUDIO'
        
        self.has_video = 'qualityLabel' in format_json
        if self.has_video:
            self.video_quality = int(format_json['qualityLabel'][:-1])
            self.video_quality_str = format_json['qualityLabel']
        else:
            self.video_quality_str = "NO_VIDEO"
        self.mime,codecs = format_json['mimeType'].split(';')
        self.codecs = codecs.strip().split(',')
        self.file_ending='.'+self.mime.split('/')[1]

    def __lt__(self,other):
        if self.has_video and other.has_video:
            if self.video_quality != other.video_quality:
                return self.video_quality < other.video_quality
        if self.has_audio and other.has_audio:
            if self.audio_quality != other.audio_quality:
                return self.audio_quality < other.audio_quality
        return False

    def __gt__(self,other):
        if self.has_video and other.has_video:
            if self.video_quality != other.video_quality:
                return self.video_quality > other.video_quality
        if self.has_audio and other.has_audio:
            if self.audio_quality != other.audio_quality:
                return self.audio_quality > other.audio_quality
        return False

    @staticmethod
    def string_header():
        return "{:13s} {:20s} {:10s} {}".format("Video Quality","Audio Quality","Mime Type","Codecs")

    def __str__(self):
        return "{:13s} {:20s} {:10s} {}".format(self.video_quality_str,self.audio_quality_str,self.mime,','.join(self.codecs))
        

class Video():
    
    def __init__(self,id):
        self.id = id
        self.video_info = get_video_info(self.id)
        self.title = self.video_info['videoDetails']['title']
        self.formats = []
        for fmt in self.video_info['streamingData']['formats']:
            self.formats.append(Stream(fmt))
        self.video_formats = []
        self.audio_formats = []
        for fmt in self.video_info['streamingData']['adaptiveFormats']:
            s = Stream(fmt)
            if s.has_video:
                self.video_formats.append(s)
            else:
                self.audio_formats.append(s)

    @property
    def all_formats(self):
        return self.formats+self.video_formats+self.audio_formats
        
    def get_best_streams(self, use_adaptive_formats=True):
        options = self.formats
        if use_adaptive_formats:
            options += self.video_formats
        selection = options[:1]
        for fmt in options:
            if fmt > selection[0]:
                selection[0]=fmt
        if not selection[0].has_audio and use_adaptive_formats:
            selection.append(self.audio_formats[0])
            for fmt in self.audio_formats:
                if fmt > selection[1]:
                    selection[1]=fmt
        return selection   


def parse_youtube_link(link):
    #https://youtu.be/ucbx9we6EHk
    #https://www.youtube.com/watch?v=ucbx9we6EHk    
    #https://www.youtube.com/v/ucbx9we6EHk
    split_result=parse.urlsplit(link)
    if split_result.netloc == 'youtu.be':
        return split_result.path[1:]
    elif split_result.netloc == 'www.youtube.com':
        if split_result.path == '/watch':
            return parse.parse_qs(split_result.query)['v'][0]
        elif split_result.path[:3] == '/v/':
            return split_result.path[3:]
    
    print("invalid link")

def get_video_info(id):
    video_info_link="https://www.youtube.com/get_video_info?video_id={}".format(id)
    video_info=requests.get(video_info_link)
    response = parse.parse_qs(video_info.text)
    return json.loads(response['player_response'][0])

def download(video_url,filename='download.mp4'):
    #print(filename)
    video = requests.get(video_url, stream=True)
    length = int(video.headers['Content-Length'])

    chunk_size=4096
    with tqdm(total=length,unit='B',unit_divisor=1024,unit_scale=True) as pb:
        with open(filename,'wb') as f:
            for data in video.iter_content(chunk_size=chunk_size):
                f.write(data)
                pb.update(chunk_size)

def select_best_streams(options):
    auswahl = options[:1]
    for option in options:
        if 'qualityLabel' in option:
            if int(option['qualityLabel'][:-1]) > int(auswahl[0]['qualityLabel'][:-1]):
                auswahl[0] = option
    if -1 == auswahl[0]['mimeType'].find(','):
        auswahl.append(None)
        for option in options:
            if 'audioQuality' in option:
                if None == auswahl[1]:
                    auswahl[1] = option
                elif auswahl[1]['audioQuality'] == 'AUDIO_QUALITY_LOW' and option['audioQuality'] == 'AUDIO_QUALITY_MEDIUM':
                    auswahl[1] = option
    num = 1
    for option in auswahl:
        if "qualityLabel" in option:
            print(str(num) +".\t"+ option['qualityLabel']+"\t"+option['mimeType'])
        elif 'audioQuality' in option:
            print(str(num) +".\t"+ option['audioQuality']+"\t"+option['mimeType'])
        num += 1
    return auswahl


def main(video,outputfile,interactive=False):
    youtube_video=Video(video)

    if interactive:
        num = 1
        print("{:2s}. {}".format("Nr.",Stream.string_header()))
        for option in youtube_video.all_formats:
            print("{:2d}. {}".format(num, str(option)))
        invalid = True
        while invalid:
            invalid = False
            i =input('Selection: ')
            selection = []
            auswahl = i.split('+')
            for a in auswahl:
                if int(a)-1 >= len(youtube_video.all_formats) or int(a)-1 < 0:
                    print("Not a vaild selection")
                    invalid = True
                else:
                    selection.append(youtube_video.all_formats[int(a)-1])
    else:
        selection = youtube_video.get_best_streams()
    print("The following streams will be downloaded")
    for stream in selection:
        print(stream)
    
    if outputfile == '':
        outputfile = youtube_video.title + '.mp4'
    elif len(args.video_filename) < 4 or not args.video_filename[-4:] == '.mp4':
        outputfile=outputfile + '.mp4'

    if len(selection) == 2 and selection[0].has_video and selection[1].has_audio:
        with tempfile.TemporaryDirectory() as tempdir:
            videofile = os.path.join(tempdir,'.videodownload.tmp')
            audiofile = os.path.join(tempdir,'.audiodownload.tmp')
            videostream, audiostream = selection
            download(videostream.url,videofile)
            download(audiostream.url,audiofile)
            
            video = ffmpeg.input(videofile)
            audio = ffmpeg.input(audiofile)
            ffmpeg.output(video['0'],audio['0'],outputfile,vcodec='copy',acodec='copy').run(quiet=True,overwrite_output=True)
    elif len(selection) >= 2:
        counter = 1
        for video in selection:
            video_url = video.url
            outputfile = outputfile[:-4]+str(counter)+'.mp4'
            download(video_url,outputfile)
            counter += 1
    else:
        video_url = selection[0].url
        
        download(video_url,outputfile)
    

if __name__=='__main__':
    parser = argparse.ArgumentParser(prog="Python Youtube Downloader", description="Simple Youtube Downloader")
    parser.add_argument("video_id", help="The youtube video id",nargs=1)
    parser.add_argument("video_filename", help="Where the downloaded video will be saved",nargs='?', default='')
    parser.add_argument("--chooseQuality", "-cq", help="Display all available video qualities and choose which to download", action='store_const',const=True,default=False)
    args = parser.parse_args()


    video_id=args.video_id[0]
    if video_id[:5]=='https':
        video_id = parse_youtube_link(video_id)
    
    main(video_id,args.video_filename,args.chooseQuality)
  