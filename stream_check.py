import json
import os
import requests
from tinydb import TinyDB, Query
from dotenv import load_dotenv

# Init Database document
db = TinyDB('streaming.json')


class Arr:

    def __init__(self, apikey, host, media_type, remove=False):
        self.apikey = apikey
        self.host = host
        self.media_type = media_type
        self.remove = remove
        self.url = f"http://{self.host}/api/v3/{self.media_type}?apikey={self.apikey}"

    def get_media(self):
        return get(url=self.url).json()

    def start_monitor(self):
        pass

    def stop_monitor(self):
        pass

    def remove_media(self):
        if self.remove:
            pass
        pass


class TMDB:

    def __init__(self, apikey, country):
        self.apikey = apikey
        self.country = country

    def get_services(self, media_type, media_id):
        url = f"https://api.themoviedb.org/3/{media_type}/{media_id}/watch/providers?api_key={self.apikey}"
        return self._parse_country(get(url=url))

    def _parse_country(self, services):
        if "results" in services:
           if self.country in services.get('results').keys(): 
               return services.get('results').get(self.country)
        else:
            print("error")


class Config:

    def __init__(self):
        self.config = self._get_config()
        self.user_services = self._get_user_services()
        self.country = self._get_country()

    def _get_config(self):
        config = {}

        if os.path.exists(".env"):
            load_dotenv(".env")

        with open('.env') as f:
           for line in f.readlines():
                a = line.strip().split('=')
                config[a[0].strip()] = a[1].strip()
        return config

    def _get_user_services(self):
        return [s.strip() for s in self.config.get('MY_SERVICES').split(',')]

    def _get_country(self):
        return self.config.get('COUNTRY')

    def apikey(self, service):
        return self.config.get(f"{service.upper()}_APIKEY")

    def host(self, service):
        return self.config.get(f"{service.upper()}_HOST")


def parse_streaming(streaming_services, user_services):
    streaming_on = []
    if "flatrate" in services.keys():
        for serv in services.get("flatrate"):
            if serv.get("provider_name") in my_services:
                streaming_on.append(serv.get("provider_name"))
    return streaming_on

def main():
    c = Config()
    tmdb = TMDB(c.apikey('tmdb'), c.country)
    #sonarr = Arr(c.apikey('sonarr'), c.host('sonarr'), 'series')
    radarr = Arr(c.apikey('radarr'), c.host('radarr'), 'movie') 

    #for x in sonarr.get_media():
    #    continue

    for x in radarr.get_media():
        streaming = parse_streaming(
            tmdb.get_services('movie', x.get('tmdbId'), c.user_services)
        )
        if streaming:
            x['streaming_on'] = streaming
            radarr.stop_monitor()
            radarr.remove_media()
        insert(x)

    #parsed_ids = parse_media(media_ids)
    #parsed_services = parse_streaming(parsed_ids, my_services)

    return


def get(url):
    return requests.get(url=url).json()

def put(url, data):
    return requests.put(url=url, data=data)

def insert(media):
    Media = Query()
    return db.upsert(media, Media.tmdbId == media.get('tmdbId'))
     
if __name__ == "__main__":
    main()
