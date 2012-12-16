import re

def multiple_replace(dict, text): 
    regex = re.compile("|".join(map(re.escape, dict.keys())))
    return regex.sub(lambda mo: dict[mo.group(0)], text) 

def matches(keywords, content):
    keywords = [multiple_replace({"*": "[^ ]+"}, keyword) for keyword in keywords]
    keywords_regex = re.compile(ur"({0})".format("|".join([ur"\b{0}\b".format(keyword) for keyword in keywords])), re.IGNORECASE)
    keywords_matched = set(re.findall(keywords_regex, content))
    
    if len(keywords_matched) > 0: 
        content = re.sub(keywords_regex, ur'<span class="highlight">\1</span>', content)
    
    return (len(keywords_matched) > 0, content, keywords_matched)

def html2text(html):
    from libs import html2text as _html2text
    _html2text.BODY_WIDTH = 0
    return _html2text.HTML2Text().handle(html)
