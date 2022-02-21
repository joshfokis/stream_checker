import json
import os
import requests
from tinydb import TinyDB, Query

from dotenv import load_dotenv

class Arr:

    def __init__(self, apikey, host, media_type, remove=False):
        self.apikey = apikey
        self.host = host
        self.media_type = media_type
        self.remove = remove
        self.url = f"http://{self.host}/api/v3/{self.media_type}?apikey={self.apikey}"

    def get_ids(self):
        return get(url=url).json()

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



if os.path.exists(".env"):
    load_dotenv(".env")

def parse_streaming(ids, my_services):
    services = []
    if "flatrate" in services.keys():
        for serv in services.get("flatrate"):
            if serv.get("provider_name") in my_services:
                services.append(serv.get("provider_name"))
    return services


class StreamMonitor:

    def __init__(self):
        self.config = self._get_config()
        pass

    def _get_config(self):
        config = {}
        if os.path.exists(".env"):
            load_dotenv(".env")
        with open('.env') as f:
           for line in f.readlines():
                a = line.strip('\n').split(' = ')
                config[a[0]] = a[1]

        return config

    def create_database(self):
        pass

    def read_database(self):
        pass

    def update_database(self):
        pass




def main():
    # TODO: update code to use the classes and maybe turn main into a class
    db = TinyDB("streaming.json")

    radarr_host = os.getenv("RADARR_HOST")
    radarr_apikey = os.getenv("RADARR_APIKEY")
    sonarr_host = os.getenv("SONARR_HOST")
    sonarr_apikey = os.getenv("SONARR_APIKEY")
    tmdb_apikey = os.getenv("TMDB_APIKEY")
    my_services = [
        "Netflix",
        "Disney Plus",
        "Hulu",
        "Amazon Prime Video",
    ]  # [x for x in os.getenv('SERVICES').split(,)

    media_ids = []

    movie_ids = get_movie_ids(
        radarr_apikey=radarr_apikey, host=radarr_host, media_type="movie"
    )

    for x in movie_ids:
        media_ids.append(i)

    series_ids = get_movie_ids(
        apikey=sonarr_apikey, host=sonarr_host, media_type="series"
    )

    for x in series_ids:
        media_ids.append(i)

    parsed_ids = parse_media(media_ids)
    parsed_services = parse_streaming(parsed_ids, my_services)

    for i in parsed_services:
        db.insert(i)

    return


def get(url):
    return requests.get(url=url).json()

def put(url, data):
    return requests.put(url=url, data=data)

if __name__ == "__main__":
    # main()
    stream = StreamMonitor()
    print(stream.config)
