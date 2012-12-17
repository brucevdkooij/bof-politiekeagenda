import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import re
import urllib2
import urlparse
import posixpath
import time

import lxml.html

from datetime import datetime

import config

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "politiekeagenda.settings")

import politiekeagenda.models as models

from helpers import retrieve_if_not_exists, date_string_to_datetime

#===============================================================================
# Helper functions
#===============================================================================

def update_or_create_assembly(assembly_dict):
    try:
        assembly = models.Assembly.objects.get(url=assembly_dict["url"])
    except models.Assembly.DoesNotExist:
        assembly = models.Assembly()
    
    # Set basic assembly properties
    for key, value in assembly_dict.items():
        if hasattr(assembly, key): setattr(assembly, key, value)
    
    # Compare revisions
    try:
        latest_revision = assembly.latest_revision
    except models.Revision.DoesNotExist:
        latest_revision = None
        
    revision = models.Revision(id=assembly.id)
    changes = False
    for key, value in assembly_dict.items():
        if hasattr(revision, key): 
            setattr(revision, key, value)
            if latest_revision and value != getattr(latest_revision, key) and key not in ["committee"]:
                changes = True

    if latest_revision == None or changes:
        assembly.latest_revision = revision
        
    assembly.save()
    assembly.latest_revision.save()
    
    # FIXME: assemmbly.latest_revision_id is not updated (hence there is no relation between assembly and revision)

#===============================================================================
# Main
#===============================================================================

def scrape(bypass_cache=False):
    assembly_urls = []
    error_on_retrieval = []
    
    #===============================================================================
    # Senate
    #===============================================================================

    #-------------------------------------------------------------------------------
    # Plenaire vergaderingen
    #-------------------------------------------------------------------------------
    def scrape_senate_plenary():
        index_url = "http://www.eerstekamer.nl/planning_plenaire_vergaderingen"
        
        try:
            document = lxml.html.parse(retrieve_if_not_exists(index_url, bypass_cache=bypass_cache)).getroot()
            document.make_links_absolute(index_url)
        except urllib2.HTTPError:
            error_on_retrieval.append(index_url)
            return
            
        for element in document.xpath("//a[contains(@href, '/plenaire_vergadering/')]"):
            date_string = element.text.strip()
            date, start_date, end_date = date_string_to_datetime(date_string)

            assembly_detail_url = element.get("href")
            
            try:
                document = lxml.html.parse(retrieve_if_not_exists(assembly_detail_url, bypass_cache=bypass_cache)).getroot()
                document.make_links_absolute(assembly_detail_url)
            except urllib2.HTTPError:
                error_on_retrieval.append(assembly_detail_url)
                continue
                
            # Remove the footer and various other irrelevant elements
            map(lambda element: element.getparent().remove(element), document.cssselect("#footer_menu")[0].getprevious().itersiblings())
            details_raw = "".join([lxml.etree.tostring(element) for element in document.cssselect("h1")[0].itersiblings()])
            
            # Add to database
            update_or_create_assembly({
                "type": "plenary",
                "url": assembly_detail_url,
                "date": int(time.mktime(date.timetuple())),
                "start_time": int(time.mktime(start_date.timetuple())) if start_date else None,
                "end_time": int(time.mktime(end_date.timetuple())) if end_date else None,
                "parlisnumber": None,
                "house": "senate",
                "status": None,
                "is_public": None,
                "location": None,
                "variety": None,
                "committee": None,
                "summary": None,
                "details_raw": details_raw,
            })
            assembly_urls.append(assembly_detail_url)
            
                
    #-------------------------------------------------------------------------------
    # Commissievergaderingen
    #-------------------------------------------------------------------------------
    def scrape_senate_committee():
        committees_index_url = "http://www.eerstekamer.nl/commissies"
        
        try:
            document = lxml.html.parse(retrieve_if_not_exists(committees_index_url, bypass_cache=bypass_cache)).getroot()
            document.make_links_absolute(committees_index_url)
        except urllib2.HTTPError:
            error_on_retrieval.append(committees_index_url)
            return
        
        for element in document.xpath(".//a[contains(@href, '/commissies/')]"):
            committee_name = element.text
            
            # Retrieve the individual page for each committee
            committee_page_url =  element.get("href")
            
            try:
                document = lxml.html.parse(retrieve_if_not_exists(committee_page_url, bypass_cache=bypass_cache)).getroot()
                document.make_links_absolute(committee_page_url)
            except urllib2.HTTPError:
                error_on_retrieval.append(committee_page_url)
                continue
            
            committee_code = posixpath.basename(urlparse.urlparse(committee_page_url).path)
            
            # Find the link pointing to the events listing for this committee
            committee_activities_url = document.xpath("//a[contains(@href, '/planning_activiteiten_commissie')]/@href")[0]
            committee_key = urlparse.parse_qs(urlparse.urlparse(committee_activities_url).query)["key"][0]
            
            # Scrape the events listing
            document = lxml.html.parse(retrieve_if_not_exists(committee_activities_url, bypass_cache=bypass_cache)).getroot()
            document.make_links_absolute(committee_activities_url)
            
            for element in document.xpath("//a[contains(@href, '/commissievergadering/')]"):
                date_string = element.text.strip()
                date, start_date, end_date = date_string_to_datetime(date_string)
                
                # Retrieve the details for this meeting
                assembly_detail_url = element.get("href")
                
                try:
                    document = lxml.html.parse(retrieve_if_not_exists(assembly_detail_url, bypass_cache=bypass_cache)).getroot()
                    document.make_links_absolute(assembly_detail_url)
                except urllib2.HTTPError:
                    error_on_retrieval.append(assembly_detail_url)
                    continue
                
                # Clean up the details (remove the footer etc.) and grab the details
                map(lambda element: element.getparent().remove(element), document.cssselect("#footer_menu")[0].getprevious().itersiblings())
                details_raw = "".join([lxml.etree.tostring(element) for element in document.cssselect("h1")[0].itersiblings()])
                
                # Store the entry in the database
                update_or_create_assembly({
                    "url": assembly_detail_url,
                    "type": "committee",
                    "date": int(time.mktime(date.timetuple())),
                    "start_time": int(time.mktime(start_date.timetuple())) if start_date else None,
                    "end_time": int(time.mktime(end_date.timetuple())) if end_date else None,
                    "parlisnumber": None,
                    "house": "senate",
                    "status": None,
                    "is_public": None,
                    "location": None,
                    "variety": None,
                    "committee": committee_page_url,
                    "summary": None,
                    "details_raw": details_raw,
                })
                assembly_urls.append(assembly_detail_url)
                
                    
    #===============================================================================
    # House of Represenatives
    #===============================================================================

    #-------------------------------------------------------------------------------
    # Plenaire vergaderingen
    #-------------------------------------------------------------------------------
    def scrape_house_plenary():
        # This week
        
        url = "http://www.tweedekamer.nl/vergaderingen/plenaire_vergaderingen/deze_week/index.jsp"
        document = lxml.html.parse(retrieve_if_not_exists(url, bypass_cache=bypass_cache)).getroot()
        document.make_links_absolute(url)
        
        for element in document.cssselect("#columntwo")[0].xpath(".//h3"):
            date_string = "".join(element.xpath(".//text()")).strip()
            date = datetime.strptime(date_string, "%A %d %B").replace(year=datetime.now().year)
            details_raw = lxml.etree.tostring(list(element.itersiblings())[0])
            
            assembly_detail_url = "http://www.tweedekamer.nl/vergaderingen/plenaire_vergaderingen/{0}".format(date.strftime("%Y%m%d"))
            
            update_or_create_assembly({
                "url": assembly_detail_url,
                "date": int(time.mktime(date.timetuple())),
                "house": "house",
                "type": "plenary",
                "details_raw": details_raw,
            })
            assembly_urls.append(assembly_detail_url)
            
            
        # Next week
        
        url = "http://www.tweedekamer.nl/vergaderingen/plenaire_vergaderingen/volgende_weken/index.jsp"
        document = lxml.html.parse(retrieve_if_not_exists(url, bypass_cache=bypass_cache)).getroot()
        document.make_links_absolute(url)
        
        for element in document.cssselect("#columntwo")[0].xpath(".//h3"):
            date_string = "".join(element.xpath(".//text()")).strip()
            details_raw = lxml.etree.tostring(list(element.itersiblings())[0])
            
            try:
                week = re.findall("week ([0-9]+)", date_string)[0]
            except IndexError: 
                continue
            
            date = datetime.strptime('{0} {1} 1'.format(datetime.now().year, week), '%Y %W %w')
            
            assembly_detail_url = "http://www.tweedekamer.nl/vergaderingen/plenaire_vergaderingen/week/{0}{1}".format(datetime.now().year, week)
            
            
            update_or_create_assembly({
                "url": assembly_detail_url,
                "date": int(time.mktime(date.timetuple())),
                "house": "house",
                "type": "plenary",
                "time_period": "week",
                "details_raw": details_raw,
            })
            assembly_urls.append(assembly_detail_url)
            
    #-------------------------------------------------------------------------------
    # Commissievergaderingen
    #-------------------------------------------------------------------------------
    def scrape_house_committee():
        committees_index_url = "http://www.tweedekamer.nl/vergaderingen/commissievergaderingen/per_commissie/index.jsp"
        document = lxml.html.parse(retrieve_if_not_exists(committees_index_url, bypass_cache=bypass_cache)).getroot()
        document.make_links_absolute(committees_index_url)

        for committee_activities_url in document.xpath("//a[contains(@href, 'commissieoverzicht.jsp')]/@href"):
            committee_activities_url = committee_activities_url
            document = lxml.html.parse(retrieve_if_not_exists(committee_activities_url, bypass_cache=bypass_cache)).getroot()
            document.make_links_absolute(committee_activities_url)
            
            # Check if the page contains any events
            if len(document.cssselect("#vergaderGroep")) == 0: continue
            if len(document.cssselect("#vergaderGroep")[0].getchildren()) == 0: continue
            
            # Extract the data from the event elements
            for foldout_element in document.cssselect("#vergaderGroep .foldout"):
                date = foldout_element.cssselect(".mocca-header .left-space strong")[0].text
                
                for meeting_element in foldout_element.xpath(".//*[contains(@id, 'fold')]")[0].iterchildren():
                    is_public = meeting_element.getchildren()[0].text == "Openbaar"
                    # Convert the table containing various event details to a key/value dict
                    properties = dict([("".join(row[0].xpath(".//text()")).strip(), "".join(row[1].xpath(".//text()")).strip()) 
                        for row in [row.getchildren() 
                        for row in meeting_element.cssselect("tr")]])
                    
                    # Scrape the date and time into a datetime object
                    time_string = re.sub(r"[\s]+", "", properties["Tijd:"])
                    time_segments = re.match("(?P<start_time>[0-9]{2}:[0-9]{2})(?:-(?P<end_time>[0-9]{2}:[0-9]{2}))?", time_string).groupdict()
                    start_date = datetime.strptime("{0} {1}".format(date, time_segments["start_time"]), "%A %d %B %Y %H:%M")
                    end_date = (datetime.strptime("{0} {1}".format(date, time_segments["end_time"]), "%A %d %B %Y %H:%M") 
                        if time_segments["end_time"] != None else None) 
                    
                    summary_element = meeting_element.xpath(".//a[contains(@href, 'details.jsp')]")[0]
                    summary = "".join(summary_element.xpath(".//text()")).strip()
                    assembly_detail_url = summary_element.get("href")
                    parlisnumber = urlparse.parse_qs(urlparse.urlparse(assembly_detail_url).query)["parlisnummer"][0]

                    # Scrape the details page (contains full agenda)
                    try:
                        document = lxml.html.parse(retrieve_if_not_exists(assembly_detail_url, bypass_cache=bypass_cache)).getroot()
                        document.make_links_absolute(assembly_detail_url)
                    except urllib2.HTTPError:
                        error_on_retrieval.append(assembly_detail_url)
                    
                    details_raw = None
                    
                    try:
                        foldout_element = document.xpath(".//*[contains(@id, 'fold')]")[0]
                        details_raw = "".join([lxml.etree.tostring(element) for element in foldout_element.xpath(".//hr")[0].itersiblings()])
                    except IndexError:
                        # No details available for this meeting at all (completely blank page)
                        pass
                        
                    # Store the entry in the database
                    update_or_create_assembly({
                        "url": assembly_detail_url,
                        "type": "committee",
                        "date": int(time.mktime(start_date.timetuple())),
                        "start_time": int(time.mktime(start_date.timetuple())),
                        "end_time": int(time.mktime(end_date.timetuple())) if end_date else None,
                        "parlisnumber": parlisnumber,
                        "house": "house",
                        "status": properties["Status:"].lower() if "Status:" in properties else None,
                        "is_public": is_public,
                        "location": properties["Plaats:"] if "Plaats:" in properties else None,
                        "variety": properties["Soort:"],
                        "committee": properties["Voortouwcommissie:"],
                        "summary": summary,
                        "details_raw": details_raw,
                    })
                    assembly_urls.append(assembly_detail_url)
    
    #-------------------------------------------------------------------------------
    # Mark missing
    #-------------------------------------------------------------------------------
    def mark_missing():
        from django.db.models import Q
        
        if len(error_on_retrieval) > 0: 
            print error_on_retrieval
            return
            
        assemblies = (models.Assembly.objects
            .filter(Q(missing=0) | Q(missing=None))
            .all())

        for assembly in assemblies:
            if assembly.url not in assembly_urls: assembly.missing = 1
        
        assembly.save()
    
    # Execute
    scrape_senate_plenary()
    scrape_senate_committee()
    scrape_house_plenary()
    scrape_house_committee()
    
    assembly_urls = set(assembly_urls)
    mark_missing()
    
def main(bypass_cache=False):
    bypass_cache = config.bypass_cache == True or bypass_cache
    scrape(bypass_cache)
    
if __name__ == "__main__":
    main()
