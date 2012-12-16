import re

from datetime import datetime

from django.db import models
from django.utils.html import escape

from helpers import multiple_replace, matches, html2text

class Config(models.Model):
    key = models.TextField(primary_key=True, blank=True)
    value = models.TextField(blank=True)
    
    class Meta:
        db_table = u'config'

class Assembly(models.Model):
    id = models.IntegerField(primary_key=True, blank=True)
    url = models.TextField(blank=True)
    house = models.TextField(blank=True)
    track = models.IntegerField(null=True, blank=True)
    ignore = models.IntegerField(null=True, blank=True)
    type = models.TextField(blank=True)
    missing = models.IntegerField(null=True, blank=True)
    latest_revision_id = models.IntegerField(null=True, blank=True)
    
    latest_revision = models.OneToOneField("Revision")
    
    class Meta:
        db_table = u'assemblies'

class Revision(models.Model):
    id = models.IntegerField(null=True, blank=True)
    date = models.IntegerField(null=True, blank=True)
    parlisnumber = models.TextField(blank=True)
    status = models.IntegerField(null=True, blank=True)
    is_public = models.IntegerField(null=True, blank=True)
    location = models.TextField(blank=True)
    variety = models.TextField(blank=True)
    committee = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    details_raw = models.TextField(blank=True)
    start_time = models.IntegerField(null=True, blank=True)
    end_time = models.IntegerField(null=True, blank=True)
    time_period = models.TextField(blank=True)
    revision_id = models.IntegerField(primary_key=True, blank=True)
    
    class Meta:
        db_table = u'revisions'
        
    def date_str(self):
        if self.date:
            return datetime.fromtimestamp(self.date).strftime("%d %B %Y")
        return None
    
    def start_time_str(self):
        if self.start_time:
            return datetime.fromtimestamp(self.start_time).strftime("%H:%M") 
        return None
    
    def end_time_str(self):
        if self.end_time:
            return datetime.fromtimestamp(self.end_time).strftime("%H:%M") 
        return None
        
    def is_match(self):
        content = html2text(self.details_raw) + " " + escape(self.summary)
        keywords_raw = Config.objects.get(key="keywords").value
        keywords = [keyword.strip() for keyword in keywords_raw.split(u",")]
        does_match, content, keywords_matched = matches(keywords, content)
        return does_match
        
    def details_text_highlighted(self):
        content = html2text(self.details_raw)
        keywords_raw = Config.objects.get(key="keywords").value
        keywords = [keyword.strip() for keyword in keywords_raw.split(u",")]
        does_match, content, keywords_matched = matches(keywords, content)
        return content
        
    def summary_highlighted(self):
        content = escape(self.summary)
        keywords_raw = Config.objects.get(key="keywords").value
        keywords = [keyword.strip() for keyword in keywords_raw.split(u",")]
        does_match, content, keywords_matched = matches(keywords, content)
        return content
        
    def keywords_matched(self):
        content = html2text(self.details_raw) + " " + escape(self.summary)
        keywords_raw = Config.objects.get(key="keywords").value
        keywords = [keyword.strip() for keyword in keywords_raw.split(u",")]
        does_match, content, keywords_matched = matches(keywords, content)
        return keywords_matched

class LogEntry(models.Model):
    id = models.IntegerField(primary_key=True, blank=True)
    datetime = models.IntegerField(null=True, blank=True)
    content = models.TextField(blank=True)
    type = models.TextField(blank=True)
    
    class Meta:
        db_table = u'log'
