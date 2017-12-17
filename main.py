from net_modules.core import ArticleCrawler


article_crawler = ArticleCrawler()
# only for http://farsnews.com
article_crawler.article_link_css = '.ctgnewsinfo > a'
article_crawler.next_page_css = 'div#currPage + div>a'
article_crawler.article_body_css = 'div.nwstxtmainpane'
article_crawler.base_url = 'http://www.farsnews.com/social'
article_crawler.number_of_articles = 20
article_crawler.run()
