import os
from requests import get, put, delete
from tinydb import TinyDB, Query
import logging

logging.basicConfig(
    filename='Stream_check.log',
    format='%(asctime)s %(message)s',
    filemode='w'
)

logger = logging.getLogger()

logger.setLevel(logging.DEBUG)
# Init Database document
db = TinyDB('streaming.json')


class Arr:

    def __init__(self, apikey, host, media_type, remove=False):
        self.apikey = apikey
        self.host = host
        self.media_type = media_type
        self.remove = remove
        self.url = f"http://{self.host}/api/v3/"

    def get_media(self):
        """Get media from *arr service

        Returns:
            dict: returns dictionary from url request
        """
        return get(url=f'{self.url}{self.media_type}?apikey={self.apikey}')

    def start_monitor(self, ids):
        """Sets the monitor status to True

        Args:
            ids (list): Receives a list of media IDs from the *arr service

        Returns:
            tuple: Currently returns the tuple from the requests module
        """
        data = {
          "movieIds": ids,
          "monitored": 'true',
        }
        return put(url=f'{self.url}movie/editor?apikey={self.apikey}', data=data)

    def stop_monitor(self, ids):
        """Sets the monitor status to False

        Args:
            data (list): Receives a list of media IDs from the *arr service

        Returns:
            tuple: Currently returns the tuple from the requests module
        """
        data = {
          "movieIds": ids,
          "monitored": 'false',
        }
        return put(url=f'{self.url}movie/editor?apikey={self.apikey}', data=data)

    def remove_media(self, ids, media_type):
        """Removes media files and folder when config remove is True

        Args:
            ids (list): Receives a list of media IDs from the *arr service
        """
        if self.remove:
            if media_type == 'movie':
                for i in ids:
                   delete(url=f'{self.url}/moviefile/{i}?apikey={self.apikey}') 
            elif media_type == 'series':
                for i in ids:
                    episodes = get(url=f'{self.url}episodeFile?seriesId={i}&apikey={self.apikey}')
                    for e in episodes.get('id'):
                        delete(url=f'{self.url}/episodeFile/{e}?apikey={self.apikey}') 
        return

class TMDB:

    def __init__(self, apikey, country):
        self.apikey = apikey
        self.country = country

    def get_services(self, media_type, media_id):
        """Gets rent,buy, and flatrate streaming providers for the media

        Args:
            media_type (str): Receives a string of movie or series
            media_id (int): Receives an int of the media id for The Movie Database

        Returns:
            dict: Returns dictionary of the streaming options
        """
        url = f"https://api.themoviedb.org/3/{media_type}/{media_id}/watch/providers?api_key={self.apikey}"
        return self._parse_country(get(url=url))

    def _parse_country(self, services):
        """Parses the services of the users country

        Args:
            services (dict): Receives a dict of the services for a media

        Returns:
            dict: Returns a dict of the users country streaming options
        """
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

    # TODO: look at changing to .conf
    def _get_config(self):
        """Opens and reads the config file

        Returns:
            dict: Returns a dict of all the key = value pairs
        """
        config = {}

        # read .env in and create a dict based on key = value
        with open('.env') as f:
           for line in f.readlines():
                a = line.strip().split('=')
                config[a[0].strip()] = a[1].strip()
        return config

    def _get_user_services(self):
        """Get user's streaming subscriptions in config dict

        Returns:
            list: Returns a list of the users streaming subscriptions
        """
        return [s.strip() for s in self.config.get('MY_SERVICES').split(',')]

    def _get_country(self):
        """ Get user's country in two letter format (US, UK, DE, etc)

        Returns:
            str: Returns string of country
        """
        return self.config.get('COUNTRY')

    def apikey(self, service):
        """Gets the API key for the service from the config

        Args:
            service (str): Receives the string of sonarr or radarr

        Returns:
            str: Returns string of API key
        """
        return self.config.get(f"{service.upper()}_APIKEY")

    def host(self, service):
        """Gets the host:port of the *arr service

        Args:
            service (str): Receives the string of sonarr or radarr

        Returns:
            str: Returns string of host:port for *arr service
        """
        return self.config.get(f"{service.upper()}_HOST")


def parse_streaming(streaming_services, user_services):
    """Parse to find flatrate in streaming services and match on users subscriptions

    Args:
        streaming_services (dict): Dict of the media streaming options
        user_services (list): List of user's streaming subscriptions

    Returns:
        list: Returns a list of all the streaming service matches for the users subscriptions
    """
    streaming_on = []

    # parse streaming providers excluding rent and buy for services
    # Flatrate means its on a subscription service (Netflix, Hulu)
    if "flatrate" in streaming_services.keys():
        for serv in streaming_services.get("flatrate"):
            if serv.get("provider_name") in user_services:
                streaming_on.append(serv.get("provider_name"))
    return streaming_on

def compare_streaming(service, subscriptions, media_type):
    """Sort through all the media and the streaming options matched with the users
       streaming subscriptions and puts them into a list of IDs to set the monitor 
       status in the *arr service.

    Args:
        service (str): String of sonarr or radarr
        subscriptions (list): List of user's streaming subscriptions
        media_type (str): String of movie or series

    Returns:
        tuple: Returns a tuple of lists, one of IDs for matched streams and one without
    """
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
    sonarr = Arr(c.apikey('sonarr'), c.host('sonarr'), 'series')
    radarr = Arr(c.apikey('radarr'), c.host('radarr'), 'movie') 

    # parse stream providers vs user services to find if on streaming service
    stop_radarr, start_radarr = compare_streaming(radarr, c.user_services, 'movie')
    stop_sonarr, start_sonarr = compare_streaming(sonarr, c.user_services, 'series')

    # set Movies in Radarr monitor status
    radarr.stop_monitor(ids=stop_radarr)
    radarr.start_monitor(ids=start_radarr)

    # set Series in Sonarr monitor status
    sonarr.stop_monitor(ids=stop_sonarr)
    sonarr.start_monitor(ids=start_sonarr)
    
    # remove media file from radarr 
    radarr.remove_media(ids=stop_radarr)

    # remove media file from sonarr 
    sonarr.remove_media(ids=stop_sonarr)

    return

### Database functions ###

def insert(media):
    Media = Query()
    return db.upsert(media, Media.tmdbId == media.get('tmdbId'))
     
if __name__ == "__main__":
    main()
