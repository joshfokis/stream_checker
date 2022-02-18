import json
import os
import requests
from tinydb import TinyDB, Query

from dotenv import load_dotenv


if os.path.exists('.env'):
    load_dotenv('.env')

def get_ids(apikey, host, media_type):
    url = f"http://{host}/api/v3/{media_type}?apikey={apikey}"
    ids = requests.get(url=url).json()
    media_ids = []
    for i in ids:
        media_ids.append({'id':i.get('tmdbId'), 'title':i.get('title')}) 

    return movie_ids

def get_providers(media_id, tmdb_apikey, media_type):
    url = f"https://api.themoviedb.org/3/{media_type}/{media_id}/watch/providers?api_key={tmdb_apikey}"
    providers = requests.get(url=url).json()
    return providers

def parse_media(ids, tmdb_apikey):
    stream_providers = []
    for mi in ids:
        providers = get_providers(mi.get('id'), tmdb_apikey)
        if providers and 'results' in providers:
            stream_providers.append({'id':mi.get('id'), 'title':mi.get('title'), 'streams':providers.get('results')})
        else:
            stream_providers.append({'id':mi.get('id'), 'title':mi.get('title'), 'streams':providers})
    return stream_providers

def parse_streaming(ids, my_services):
    media = []
    for i in ids:
        if "US" in i.get("streams").keys():
            services = []
            if 'flatrate' in i.get('streams').get('US').keys():
                for serv in i.get('streams').get('US').get('flatrate'):
                    if serv.get('provider_name') in my_services:
                        services.append(serv.get('provider_name'))
                if services:
                    i['streaming'] = services
                    media.append(i)
                else:
                    i['streaming'] = ['None']
                    media.append(i)
        else:
            i['streaming'] = ['None']
            media.append(i)
    return media


def main():
    db = TinyDB('streaming.json')

    radarr_host = os.getenv('RADARR_HOST')
    radarr_apikey = os.getenv('RADARR_APIKEY')
    sonarr_host = os.getenv('SONARR_HOST')
    sonarr_apikey = os.getenv('SONARR_APIKEY')
    tmdb_apikey = os.getenv('TMDB_APIKEY')
    my_services = ['Netflix', 'Disney Plus', 'Hulu', 'Amazon Prime Video'] # [x for x in os.getenv('SERVICES').split(,)

    media_ids = []

    movie_ids = get_movie_ids(radarr_apikey=radarr_apikey, host=radarr_host, media_type='movie')

    for x in movie_ids:
        media_ids.append(i)

    series_ids = get_movie_ids(apikey=sonarr_apikey, host=sonarr_host, media_type='series')

    for x in series_ids:
        media_ids.append(i)

    parsed_ids = parse_media(media_ids)
    parsed_services = parse_streaming(parsed_ids, my_services)

    for i in parsed_services:
        db.insert(i) 

    return

if __name__=="__main__":
    main()
