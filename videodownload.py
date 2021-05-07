import requests
import logging
from urllib import parse
import json
from tqdm import tqdm
import argparse
import ffmpeg

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


    video_id=args.video_id[0]
    if video_id[:5]=='https':
        video_id = parse_youtube_link(video_id)
    print("id: "+video_id)
    video_info = get_video_info(video_id)
    with open('video_info.json','w') as f:
        json.dump(video_info,f)


    formats = video_info['streamingData']['formats']
    adaptive = video_info['streamingData']['adaptiveFormats']
    options = formats + adaptive
    if args.chooseQuality:
        num = 1
        for option in options:
            if "qualityLabel" in option:
                print(str(num) +".\t"+ option['qualityLabel']+"\t"+option['mimeType'])
            elif 'audioQuality' in option:
                print(str(num) +".\t"+ option['audioQuality']+"\t"+option['mimeType'])
            num += 1
        invalid = True
        while invalid:
            invalid = False
            i =input('Selection: ')
            streams = []
            auswahl = i.split('+')
            for a in auswahl:
                if int(a)-1 >= len(options) or int(a)-1 < 0:
                    print("Not a vaild selection")
                    invalid = True
                else:
                    streams.append(options[int(a)-1])

    else:
        #print("auto selection")
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


    if args.video_filename == '':
        outfile = video_info['videoDetails']['title'] + '.mp4'
    elif len(args.video_filename) < 4 or not args.video_filename[-4:] == '.mp4':
        outfile=args.video_filename + '.mp4'
    else:
        outfile=args.video_filename

    if len(auswahl) == 2:
        videofile = '.videodownload.tmp'
        audiofile = '.audiodownload.tmp'
        video, audio = auswahl
        download(video['url'],videofile)
        download(audio['url'],audiofile)
        
        video = ffmpeg.input(videofile)
        audio = ffmpeg.input(audiofile)
        ffmpeg.output(video['0'],audio['0'],outfile,vcodec='copy',acodec='copy').run(overwrite_output=True)
    elif len(auswahl) > 2:
        counter = 1
        for video in auswahl:
            video_url = video['url']
            outfile = outfile[:-4]+str(counter)+'.mp4'
            download(video_url,outfile)
            counter += 1
    else:
        video_url = auswahl[0]['url']
        
        download(video_url,outfile)

    # vcounter = 0
    # acounter = 0
    # for adapt in video_info['streamingData']['adaptiveFormats']:
    #     if 'qualityLabel' in adapt  and adapt['qualityLabel'] == '1080p':
    #         vcounter += 1
    #         download(adapt['url'],outfile+'1080p_'+str(vcounter)+".mp4")
    #     elif 'audioQuality' in adapt and adapt['audioQuality'] == 'AUDIO_QUALITY_MEDIUM':
    #         acounter += 1
    #         download(adapt['url'],outfile+'audio'+str(acounter)+".aac")
