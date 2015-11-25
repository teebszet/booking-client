#! /usr/bin/env python

import argparse
import json
import logging
import sys

from booking_client import BookingClient

""" Synopsis

Script to look up hotel info from Booking.com API

To print a single hotel's info: 

    ./find_hotel_info.py --user USER --pass PASS --city madrid --hotel "Bohemian Hotel" 

Iterate through a file of one hotel name per line:

    cat copenhagen_hotels.txt | xargs --replace="HOTEL" ./find_hotel_info.py --user USER --pass PASS --city copenhagen --hotel "HOTEL" > copenhagen_hotel_info.json

"""

if __name__ == '__main__':

    # parse arguments
    ap = argparse.ArgumentParser(
        description="Script to retrieve hotel info from Booking.com API")

    ap.add_argument('-u', '--user', dest='user', required=True,
        help='username for Booking API')
    ap.add_argument('-p', '--pass', dest='password', required=True,
        help='password for Booking API')
    ap.add_argument('-c', '--city', dest='city', required=True,
        help='city for to look in (case insensitive)')
    ap.add_argument('--hotel', dest='hotel',
        help='hotel to look up (case insensitive)')
    ap.add_argument("-v", "--verbose", action="store_true",
        help="more vebose output (debug)")


    args = ap.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    BC = BookingClient(args.user, args.password)

    hotel_info = BC.getHotelInfo(hotel=args.hotel, city=args.city, fuzzy=1)
    print json.dumps(hotel_info)
