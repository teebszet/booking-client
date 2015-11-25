#! /usr/bin/env python

import argparse
import logging

from booking_client import BookingClient

""" Synopsis

Script to dump hotel info from hotel_lookups.db

    ./dump_hotel_lookups.py --city madrid 

Try
    ./dump_hotel_lookups.py --city copenhagen | grep -i Avenue

"""

if __name__ == '__main__':

    # parse arguments
    ap = argparse.ArgumentParser(
        description="Script to dump hotel info from hotel_lookups.db")

    ap.add_argument('-c', '--city', dest='city', required=True,
        help='city for to look in (case insensitive)')
    ap.add_argument("-v", "--verbose", action="store_true",
        help="more vebose output (debug)")

    args = ap.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    BC = BookingClient('', '')
    BC.dumpHotelIds(city=args.city)
