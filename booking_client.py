#! /usr/bin/env python

# BookingClient class

import re
import requests
import sys

class BookingClient(object): 

    def __init__(self, user, key):
        self.__api_url = "https://distribution-xml.booking.com/json/bookings"
        self.__user = user
        self.__key = key
        self.__city_ids = {
            'madrid'    :  -390625,
            'london'    :  -2601889,
            'amsterdam' :  -2140479,
            'berlin'    :  -1746463,
            # just hard code ids here as needed,
            # can automate it eventually to store in a database
        }

    ##
    ## public methods
    ##
    def getHotelsForCity(self, city):
        '''
            hotels_json = self.getHotelsForCityId('madrid');
        '''
        if (city not in self.__city_ids):
            print "'%(city)s' was not cached. run getCityIdForName to find city_id and then cache it (code it in the script)" % locals()
            return

        r = self._api_get(
            'getHotels',
            'city_ids=' + str(self.__city_ids[city])
        )
        return r.json()

    def getCityIdForName(self, name, country):
        '''
            city_id = self.getCityIdForName('madrid', 'es') 
        '''
        for cities in self._getCities(country):
            city = self._filterByName(cities, name)
            if city:
                return city['city_id']
            else: 
                print name + " not found. paging through offset"

    def getCountries(self):
        '''
            countries = self.getCountries() 
        '''
        if hasattr(self, '__countries'):
            return self.__countries
        else:
            r = self._api_get('getCountries')
            self.__countries = r.json()
            return self.__countries

    ##
    ## private methods
    ##
    def _path(self, api_function, params=''):
        #TODO use a uri constructor
        path = self.__api_url + "." + api_function
        if params:
            path = path + '?' + params
        print path
        return path

    def _api_get(self, api_function, params):
        r = requests.get(
            self._path(api_function, params),
            auth=(self.__user, self.__key)
        )
        if r.status_code == 200:
            resp = r.json()
            if type(resp) is list:
                print "success"
                return r
            else:
                print "api error: ", resp['message']
        sys.exit()

    def _getCities(self, country):
        '''
            generator for paging through 1000 cities at a time for a country
        '''
        if not country: return

        offset = 0
        while True:
            r = self._api_get(
                'getCities',
                'countrycodes=' + country + '&offset=' + str(offset))
            yield r.json()
            offset += 1000

    def _filterByName(self, seq, name):
        for city in seq:
            if re.match(re.escape(name), city['name'], re.IGNORECASE): 
                return city
        return

## testing only

if __name__ == '__main__':
    BC = BookingClient('user', 'pass')

    # print BC.getCityIdForName('hong kong', 'cn') # api error
    # print BC.getCityIdForName('madrid', 'es') # -390625
    # print BC.getCityIdForName('london', 'gb') # -2601889
    # print BC.getCityIdForName('amsterdam', 'nl') # -2140479
    # print BC.getCityIdForName('berlin', 'de') # -1746463
    print BC.getHotelsForCity('sevilla')
