import datetime
import io

import feedparser

class RSSFeed:
    """
        The RSSFeed object represents an RSS feed.
    """
    def __init__(self, content : str) -> None:
        feed = feedparser.parse(
            io.BytesIO(content.encode('utf-8'))
        )

        self.title = feed.channel.title
        self.link  = feed.channel.link
        self.raw   = content

        if 'updated_parsed' not in feed.channel.keys():
            self.updated = None
        else:
            self.updated = datetime.datetime(
                *feed.channel['updated_parsed'][:6]
            )
    
        # Optional subtitle
        if 'subtitle' not in feed.channel.keys():
            self.subtitle = "Available at " + self.link
        else:
            self.subtitle = feed.channel['subtitle']

        # Published entries
        self.entries = []

        for entry in feed.entries:
            try:
                e = FeedEntry(entry)
            except Exception as e:
                pass
            else:
                self.entries.append(e)
    
    def __repr__(self) -> str:
        return f"<RSSFeed posts={len(self.entries)}>"

class FeedEntry:
    def __init__(self, entry : feedparser.util.FeedParserDict) -> None:
        self.title = entry['title']
        try:
            self.published = entry['published_parsed']
        except KeyError:
            self.published = entry['updated_parsed']
        self.published = datetime.datetime(*self.published[:6])
        
        if 'summary' in entry.keys():
            self.summary = entry['summary']
        else:
            self.summary = None

        if 'link' in entry.keys():
            self.link = entry['link']
        else:
            self.link = None
        
        self.content = None
        if 'content' in entry.keys():
            c = entry['content']
            if ( len(c) == 1 
             and 'type' in c[0].keys()
             and 'value' in c[0].keys()
             and c[0]['type'] == 'text/html'
               ):
                self.content = str(c[0]['value'])
    
    def m_json(self):
        return {
            'body'  :   ( self.title + '\n\n' 
                        + ( ('' if not self.summary else self.summary + '\n\n') 
                                if not self.content else self.content + '\n\n'
                          )
                        + ( '' if not self.link else self.link + '\n\n'
                          )
                        ),
            'msgtype'   :   'm.text',
            'format'    :   'org.matrix.custom.html',
            'formatted_body'    :   (
                '<h1>' + self.title + '</h1>' +
                ( ('' if not self.summary else self.summary + '\n\n')
                      if not self.content else self.content + '\n\n'
                ) +
                ( '' if not self.link else '<p>' + self.link + '</p>')
            )
        }
    
    def __repr__(self):
        return str(dict(
            title=self.title,
            published=self.published,
            summary=self.summary,
            link=self.link,
            content=self.content
        ))
    
    def __eq__(self, __o: object) -> bool:
        return (
            self.__repr__() == __o.__repr__() and 
            self.__class__ == __o.__class__
        )

if __name__ == '__main__':
    while True:
    	print(RSSFeed(input("Insert an RSS Feed: ")))