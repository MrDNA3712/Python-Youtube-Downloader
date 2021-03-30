import requests
from urllib import parse
import json
from tqdm import tqdm
import argparse

def get_video_info(id):
    video_info_link="https://www.youtube.com/get_video_info?video_id={}".format(id)
    video_info=requests.get(video_info_link)
    response = parse.parse_qs(video_info.text)
    return json.loads(response['player_response'][0])

def download(video_url,filename='download.mp4'):
    print(filename)
    video = requests.get(video_url, stream=True)
    length = int(video.headers['Content-Length'])

    chunk_size=1024
    with tqdm(total=length,unit='B',unit_divisor=1024,unit_scale=True) as pb:
        with open(filename,'wb') as f:
            for data in video.iter_content(chunk_size=chunk_size):
                f.write(data)
                pb.update(chunk_size)

if __name__=='__main__':
    parser = argparse.ArgumentParser(prog="Python Youtube Downloader", description="Simple Youtube Downloader")
    parser.add_argument("video_id", help="The youtube video id",nargs=1)
    parser.add_argument("video_filename", help="Where the downloaded video will be saved",nargs='?', default='')
    parser.add_argument("--chooseQuality", "-cq", help="Display all available video qualities and choose which to download", action='store_const',const=True,default=False)
    args = parser.parse_args()

    video_info = get_video_info(args.video_id[0])

    options = video_info['streamingData']['formats']
    if args.chooseQuality:
        num = 1
        for option in options:
            print(num +".\t"+ option['qualityLabel']+"\t"+option['mimeType'])
            num += 1
        
        auswahl = int(input('Selection: '))-1
        if auswahl >= len(options) or auswahl < 0:
            print("Not a vaild selection")
    else:
        print(options[-1]['qualityLabel']+"\t"+options[-1]['mimeType'])
        auswahl = -1

    video_url = options[auswahl]['url']
    if args.video_filename == '':
        outfile = video_info['videoDetails']['title'] + '.mp4'
    elif len(args.video_filename) < 4 or not args.video_filename[-4:] == '.mp4':
        outfile=args.video_filename + '.mp4'
    else:
        outfile=args.video_filename
    download(video_url,outfile)
