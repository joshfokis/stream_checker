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
        self.url = f"http://{self.host}/api/v3/"

    # get media from *arr service
    def get_media(self):
        return get(url=f'{self.url}{self.media_type}?apikey={self.apikey}')

    # set monitor status for media in *arr
    def start_monitor(self, ids):
        data = {
          "movieIds": ids,
          "monitored": true,
        }
        return put(url=f'{self.url}movie/editor?apikey={self.apikey}', data=data)

    # set monitor status for media in *arr
    def stop_monitor(self, data):
        data = {
          "movieIds": ids,
          "monitored": false,
        }
        return put(url=f'{self.url}movie/editor?apikey={self.apikey}', data=data)

    # remove media files if remove_media=True
    def remove_media(self):
        if self.remove:
            pass
        pass


class TMDB:

    def __init__(self, apikey, country):
        self.apikey = apikey
        self.country = country

    # get all rent, buy, streaming providers for the media
    def get_services(self, media_type, media_id):
        url = f"https://api.themoviedb.org/3/{media_type}/{media_id}/watch/providers?api_key={self.apikey}"
        return self._parse_country(get(url=url))

    # Parse out all the selected country
    def _parse_country(self, services):

        if "results" in services:
           if self.country in services.get('results').keys(): 
               #return contry results if the country is found
               return services.get('results').get(self.country)
           else:
               # return results if the country isn't found
               # will not have key value to indicate it is 
               # on a streaming service
               # TODO: find a better way to resolve issue
               return services.get('results')
        else:
            # if media is not found return error
            # TODO: find a better way to resolve issue
            return services


class Config:

    def __init__(self):
        self.config = self._get_config()
        self.user_services = self._get_user_services()
        self.country = self._get_country()

    # get the config from .env file
    # TODO: look at changing to .conf
    def _get_config(self):
        config = {}

        # read .env in and create a dict based on key = value
        with open('.env') as f:
           for line in f.readlines():
                a = line.strip().split('=')
                config[a[0].strip()] = a[1].strip()
        return config

    # get user subscriptions from config as a list
    def _get_user_services(self):
        return [s.strip() for s in self.config.get('MY_SERVICES').split(',')]

    # get user country (US, UK, DE)
    def _get_country(self):
        return self.config.get('COUNTRY')

    # return api key for *arr service
    def apikey(self, service):
        return self.config.get(f"{service.upper()}_APIKEY")

    # return host:port of *arr service
    def host(self, service):
        return self.config.get(f"{service.upper()}_HOST")

# Parsing function to see if a flatrate provider is streaming
def parse_streaming(streaming_services, user_services):
    streaming_on = []

    # parse streaming providers excluding rent and buy for services
    # Flatrate means its on a subscription service (Netflix, Hulu)
    if "flatrate" in streaming_services.keys():
        for serv in streaming_services.get("flatrate"):
            if serv.get("provider_name") in user_services:
                streaming_on.append(serv.get("provider_name"))
    return streaming_on

# Sort through providers and media for streaming vs not while updating DB
def compare_streaming(service, subscriptions, media_type):

    # List for IDs for *arr service monitor status
    stop_monitor = []
    start_monitor = []

    # loop through media in *arr service and get streaming providers
    # and update *arr monitor status and DB
    for x in service.get_media():

        # get streaming providers
        streaming = parse_streaming(
            tmdb.get_services(media_type, x.get('tmdbId')), subscriptions
        )

        # if provider is found update media dict
        if streaming:
            stop_monitor.append(x.get('id'))
            x['streaming_on'] = streaming
        else:
            start_monitor.append(x.get('id'))

        # insert/update entry into database
        insert(x)

    return stop_monitor, start_monitor 

# Main function to init config and *arr services
def main():

    # TODO: Might change this to use args when running
    # init the config to get api keys
    c = Config()
    tmdb = TMDB(c.apikey('tmdb'), c.country)
    #sonarr = Arr(c.apikey('sonarr'), c.host('sonarr'), 'series')
    radarr = Arr(c.apikey('radarr'), c.host('radarr'), 'movie') 

    # parse stream providers vs user services to find if on streaming service
    stop_radarr, start_radarr = compare_streaming(radarr, c.user_services, 'movie')
    stop_sonarr, start_sonarr = compare_streaming(sonarr, c.user_services, 'series')

    # set Movies in Radarr monitor status
    radarr.stop_monitor(ids=stop_monitor)
    radarr.start_monitor(ids=start_monitor)

    # set Series in Sonarr monitor status
    sonarr.stop_monitor(ids=stop_monitor)
    sonarr.start_monitor(ids=start_monitor)

    return

### Request functions ###

def get(url):
    return requests.get(url=url).json()

def put(url, data):
    return requests.put(url=url, data=data)


### Database functions ###

def insert(media):
    Media = Query()
    return db.upsert(media, Media.tmdbId == media.get('tmdbId'))
     
if __name__ == "__main__":
    main()
