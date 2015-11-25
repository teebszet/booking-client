#! /usr/bin/env python

# BookingClient class

import re
import requests
import logging
import sqlite3
import sys

''' Synopsis

Module for looking up Booking.com API hotel info

    from booking_client import BookingClient
    BC = BookingClient('bookingapi_user', 'bookingapi_pass')

Public methods:

    hotel_info = BC.getHotelInfo(hotel='aravaca', city='madrid')
    city_id    = BC.getCityId(city='madrid', country='es')

Stores all hotel_ids for a city to SQLite hotel_lookups.db:

    BC.storeHotelLookups(city='madrid'):

'''
class BookingClient(object): 

    def __init__(self, user, key):
        self.__api_url = "https://distribution-xml.booking.com/json/bookings"
        self.__user = user
        self.__key = key
        self.__city_ids = {
            'madrid'     :  -390625,
            'london'     :  -2601889,
            'amsterdam'  :  -2140479,
            'berlin'     :  -1746463,
            'copenhagen' :  -2745636,
            # just hard code ids here as needed,
            # can automate it eventually to store in a database
            # (use BC.getCityId)
        }
        self.__hotel_lookups = sqlite3.connect('hotel_lookups.db')

    ##
    ## public methods
    ##
    '''
        city_id = BC.getCityId(city='madrid', country='es') 
    '''
    def getCityId(self, city, country):
        for cities in self.getCitiesForCountry(country):
            found = self._filterByField(seq=cities, field='name', value=city)
            if found:
                return found['city_id']
            else: 
                logging.info(city + " not found. paging through offset")
        logging.info("finished search without finding" + city)

    '''
    Use optional 'fuzzy' to match wildcards on either side of the 'hotel' string

        hotel_info = BC.getHotelInfo(hotel='aravaca', city='madrid') 
        hotel_info = BC.getHotelInfo(hotel='aravaca', city='madrid', fuzzy=1) 
    '''
    def getHotelInfo(self, hotel, city, fuzzy=0):
        hotel_id = self._retrieve_hotel_id(hotel, city, fuzzy)
        if not hotel_id:
            return
        logging.info("found hotel_id: {} for {}".format(hotel_id, hotel))
        params = 'city_ids={}&hotel_ids={}'.format(
            str(self.__city_ids[city]),
            str(hotel_id))
        r = self._api_get('getHotels', params)
        return r.json()

    '''
    Force store all hotel_id, name pairs for a city in a SQLite db

        hotel_lookups = self.storeHotelLookups(city='madrid') 
    '''
    def storeHotelLookups(self, city):
        table_name = self._get_hotel_lookup_table_name(city)
        c = self.__hotel_lookups.cursor()

        c.execute('''
            CREATE TABLE IF NOT EXISTS {}(
                hotel_id INTEGER PRIMARY KEY,
                name     TEXT)
            '''.format(table_name))
        #TODO create index on 'name'

        for hotels in self.getHotelsForCity(city):
            for hotel in hotels:
                # store in SQLite
                c.execute("INSERT OR REPLACE INTO {} VALUES (?, ?)".format(table_name),
                    (hotel['hotel_id'], hotel['name']))
            self.__hotel_lookups.commit()
        logging.info("finished store hotels")

    '''
    Helper method to dump hotel_ids for a city from hotel_lookups.db

        BC.dumpHotelIds(city='madrid')
    '''
    def dumpHotelIds(self, city):
        table_name = self._get_hotel_lookup_table_name(city)
        c = self.__hotel_lookups.cursor()
        for row in c.execute("SELECT * FROM {}".format(table_name)):
            print row

    ##
    ## generators
    ##
    '''
    Generator for paging through 1000 cities at a time for a country

        for cities in self.getCitiesForCountry(country='es'):
            # do stuff...
    '''
    def getCitiesForCountry(self, country):
        offset = 0
        while True:
            r = self._api_get(
                'getCities',
                'countrycodes=' + country + '&offset=' + str(offset))
            response = r.json()
            if len(response):
                yield response 
                offset += 1000
            else:
                break

    '''
    Generator for paging through 1000 hotels at a time for a city name

        for hotels in self.getHotelsForCity(city='madrid'):
            # do stuff...
    '''
    def getHotelsForCity(self, city):
        # check we know the city
        if not self._get_hotel_lookup_table_name(city):
            return

        offset = 0
        while True:
            r = self._api_get(
                'getHotels',
                'city_ids=' + str(self.__city_ids[city]) + '&fields=hotel_id,name' + '&offset=' + str(offset))
            response = r.json()
            if len(response):
                yield response 
                offset += 1000
            else:
                break

    ##
    ## private methods
    ##
    '''
    Case insensitive matching through a sequence, where each element is a dictionary.
    The first element which has a 'field' matching 'value' is returned.

        cities = [{'name':'madrid'}, {'name':'barcelona'}]
        el_city = _filterByField(seq=cities, field='name', value='barcelona')
        
        # returns {'name':'barcelona'}
    '''
    def _filterByField(self, seq, field, value):
        for el in seq:
            if re.match(re.escape(value), el[field], re.IGNORECASE): 
                return el
        return

    '''
    '''
    def _path(self, api_function, params=''):
        #TODO use a uri constructor
        path = self.__api_url + "." + api_function
        if params:
            path = path + '?' + params
        logging.info(path)
        return path

    '''
    '''
    def _api_get(self, api_function, params):
        r = requests.get(
            self._path(api_function, params),
            auth=(self.__user, self.__key)
        )
        if r.status_code == 200:
            resp = r.json()
            if type(resp) is list:
                logging.info("success")
                return r
            else:
                logging.info("api error: ", resp['message'])
        else:
            sys.exit(1)

    '''
    '''
    def _get_hotel_lookup_table_name(self, city):
        if (city not in self.__city_ids):
            logging.info("'%(city)s' was not cached. run getCityIdForName to find city_id and then cache it (code it in the script)" % locals())
            return
        return 'hotels_' + city

    def _select_hotel_id(self, city, like_clause):
        table_name = self._get_hotel_lookup_table_name(city)
        logging.info("select {} with like_clause {}".format(table_name, like_clause))
        c = self.__hotel_lookups.cursor()
        c.execute('''
            SELECT hotel_id, name
            FROM {}
            WHERE name like ?
            '''.format(table_name), (like_clause,))
        rows = c.fetchall()

        if len(rows):
            return rows
        else:
            logging.info("nothing")
            return

    '''
    '''
    def _retrieve_hotel_id(self, hotel, city, fuzzy=0):
        rows = self._select_hotel_id(city, like_clause=hotel)

        # check lookup result and perhaps try harder
        if not rows:
            logging.info("found 0 matches for {}".format(hotel))
            if fuzzy:
                logging.info("will try some fuzzier matches, because fuzzy was on")
                # try a looser match
                # remove commas, underscores, dashes
                cleansed_hotel = re.sub(r"[,\_\-]+", '', hotel)
                with_cleansed = cleansed_hotel

                # wildcards on each end
                with_wildcards = "%{}%".format(cleansed_hotel)

                # replace whitespace with wildcard '%'
                cleansed_hotel = re.sub(r"\s+", '%', cleansed_hotel)
                with_extra_wildcards = "%{}%".format(cleansed_hotel)

                # remove the word 'hotel'
                cleansed_hotel = re.sub(r"hotel", '', cleansed_hotel, flags=re.IGNORECASE)
                with_remove_hotel = "%{}%".format(cleansed_hotel)
                with_remove_hotel = re.sub(r"%+", '%', with_remove_hotel)

                # switch the order of words
                words = cleansed_hotel.split('%')
                words.reverse()
                reversed_string = "%".join(words)
                with_reversed_string = "%{}%".format(reversed_string)
                with_reversed_string = re.sub(r"%+", '%', with_reversed_string)

                rows = (self._select_hotel_id(city, like_clause=with_cleansed) or
                    self._select_hotel_id(city, like_clause=with_wildcards) or
                    self._select_hotel_id(city, like_clause=with_extra_wildcards) or
                    self._select_hotel_id(city, like_clause=with_remove_hotel) or
                    self._select_hotel_id(city, like_clause=with_reversed_string) or
                    None)
        elif len(rows)  > 1:
            logging.error("too many candidates for {} returned. consider more specific hotel name".format(hotel))
            logging.error(rows)
            return

        # return if something
        if rows and len(rows):
            return rows[0][0] 
        else:
            logging.error("could not find hotel_id for {}".format(hotel))
            return

    '''
    Do we need to store hotel lookups?
    '''
    def _maybe_store_hotel_lookups(self, city):
        c = self.__hotel_lookups.cursor()
        table_name = self._get_hotel_lookup_table_name(city)
        try:
            logging.info('try to find lookup table')
            c.execute('''
                SELECT count(*)
                FROM {}
                '''.format(table_name))
            rows = c.fetchall()
            if rows[0][0] == 0:
                logging.info('found 0 rows for table {}, will run storeHotelLookups'.format(city))
                self.storeHotelLookups(city=city)

        except sqlite3.OperationalError as e:
            if re.search('no such table', e.message):
                logging.info('could not find table for {}, will run storeHotelLookups'.format(city))
                self.storeHotelLookups(city=city)
            else:
                raise
        return


## testing only

if __name__ == '__main__':
    # print BC.getCityId('hong kong', 'cn') # api error
    # print BC.getCityId('madrid', 'es') # -390625
    # print BC.getCityId('london', 'gb') # -2601889
    # print BC.getCityId('amsterdam', 'nl') # -2140479
    # print BC.getCityId('berlin', 'de') # -1746463
    # print BC.storeHotelLookups(city='madrid')
    # BC.dumpHotelIds('madrid')
    # print BC.getHotelInfo('Bohemian Chic Las Letras', 'madrid')
    # print BC.getHotelInfo('Bohemian', 'madrid', fuzzy=1)
    # print BC.getCityId('copenhagen', 'dk') # -2745636
