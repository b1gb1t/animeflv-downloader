from animeflv import AnimeFLV
from mega import Mega
import argparse
import re
from os import path, mkdir
from concurrent.futures import ThreadPoolExecutor

# Naruto
# relleno = [26,97,99,101,102,103,104,105,106,136,137,138,139,140,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,
#    161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,
#    201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219]

# Naruto Shippuden
relleno = [91,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,170,171,177,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,
            223,224,225,226,227,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,257,258,259,260,290,291,292,293,294,295,347,349,376,377,
            389,390,394,395,396,397,398,399,400,401,402,403,404,405,406,407,408,409,410,411,412,413,416,422,423,430,431,432,433,434,435,436,437,438,439,
            440,441,442,443,444,445,446,447,448,449]

def printMenu(options):
    count = 1
    menu = {}
    print('Selecciona el anime para descargar:')
    for opt in options:
        title = opt['title']
        menu[count] = (title, opt['id'])
        print(f'[{count}] {title}')
        count += 1
    return menu


def rangeEpisodes(arg_value, pat=re.compile(r"^[0-9]+-[0-9]+$")):
    if not pat.match(arg_value):
        raise argparse.ArgumentTypeError
    return arg_value

# TODO: threading
def megaDownload(api, episodes, wanted, outdir):
    notFound = []
    downloaded = []
    m = Mega()
    mega = m.login()
    with ThreadPoolExecutor(max_workers=5) as executor:
        for e in episodes:
            num = int(e['id'].split('-')[-1])
            if len(wanted) > 0 and num not in wanted:
                continue
            if num in relleno:
                continue
            urlEpisode = e['id']
            downLinks = api.downloadLinksByEpisodeID(urlEpisode)
            print(f'Episode: {urlEpisode}')
            for link in downLinks:
                if link['server'] == "MEGA":
                    print(f'\t- Link: {link["url"]}')
                    fname = f'{urlEpisode.split("/")[1]}.mp4'
                    executor.submit(threadDownload, mega, link['url'], outdir, fname)
                    downloaded.append(num)
            if num not in downloaded:
                notFound.append(num)
    
    print(f'[x] Not found episodes: {notFound}')


def threadDownload(api, url, outdir, fname):
    try:
        api.download_url(url, dest_path=outdir, dest_filename=fname)
    except Exception as e:
        print(f'[!] Error Mega API: {e}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AnimeFLV downloader')
    parser.add_argument('-a','--anime', help="Anime", required=True)
    parser.add_argument('-e', '--episodes', default='0-0', type=rangeEpisodes, required=False, help='Episode number to download or list of episodes. Examples:\nDownload from 1 to 10: 1-10\nDownload: 1,5,9')
    parser.add_argument('-o', '--outputdir', help='Directory to save episodes', required=True)
    args = parser.parse_args()

    if not path.exists(args.outputdir):
        answer = ''
        print(f'\nDirectory {args.outputdir} does not exists')
        while not answer == 's':
            answer = input('Do you want to create it? [s|n]')
            if answer == 'n':
                exit()
        mkdir(args.outputdir)

    wanted = []
    if args.episodes != '0-0':
        start = int(args.episodes.split('-')[0])
        stop = int(args.episodes.split('-')[1])
        for i in range(start,stop+1):
            wanted.append(i)
        #print(f'Episodes to download: {wanted}')

    api = AnimeFLV()
    options = api.search(args.anime)
    if len(options) > 1:
        menu = printMenu(options)
        choice = int(input('Introduzca el número: '))
        anime = menu[choice][1]
    elif len(options) == 0:
        print('AnimeFLV API failed. Try again.')
        exit(-1)
    else:
        anime = options[0]['id']

    #print(anime)   
    episodes =  api.getAnimeInfo(anime)['episodes']

    megaDownload(api, episodes, wanted, args.outputdir)
    