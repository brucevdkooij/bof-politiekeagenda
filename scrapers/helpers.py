import re
import urlparse
import hashlib
import urllib
import urllib2

from datetime import datetime, timedelta

from config import *

def retrieve_if_not_exists(url, headers={}, data=None, bypass_cache=False):
    hash_url = url
    url_object = urlparse.urlparse(url)
    
    base_url = url_object.scheme + "://" + url_object.netloc + url_object.path
    params = {}
    params.update(dict(urlparse.parse_qsl(url_object.query)))
    if data: params.update(dict(urlparse.parse_qsl(data)))
    
    if url_object.query or data:
        hash_url = base_url + "?" + "&".join([key + "=" + value for key, value in sorted(params.items())])
    
    filename = hashlib.md5(urllib.quote_plus(hash_url)).hexdigest()
    target_path = os.path.join(cache_directory, filename)
    
    if bypass_cache or not os.path.exists(target_path):
        print "Retrieving {0}...".format(url)
        if data:
            request = urllib2.Request(url, data=data, headers=headers)
        else:
            request = urllib2.Request(url, headers=headers)
        try:
            response = urllib2.urlopen(request)
            content = response.read()
            with open(target_path, "wb") as output_file:
                output_file.write(content)
        except urllib2.URLError, ex:
            print "Error while retrieving {0}".format(url)
            raise ex
    
    return target_path

def date_string_to_datetime(date_string):
    pattern = re.compile("""
        (?P<date>[0-9]+[ ][^ ]+[ ][0-9]{4})
        (?:
            .*
            (?:
                (?:circa)?[ ]
                (?P<start_time>[0-9]+\.[0-9]+)
                (?:[ ]-[ ](?P<end_time>[0-9]+\.[0-9]+))?
            )
        )?
    """, re.VERBOSE)
    #~ print date_string
    
    matches = re.match(pattern, date_string).groupdict()
    date = start_date = end_date = None
    
    date = datetime.strptime(matches["date"], "%d %B %Y")
    if matches["start_time"] != None: 
        hours, minutes = map(int, matches["start_time"].split("."))
        date = start_date = date + timedelta(hours=int(hours), minutes=int(minutes))
    if matches["end_time"] != None: 
        hours, minutes = map(int, matches["end_time"].split("."))
        end_date = date + timedelta(hours=int(hours), minutes=int(minutes))
        
    return (date, start_date, end_date)
