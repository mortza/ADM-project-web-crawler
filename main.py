from net_modules.core import ArticleCrawler


article_crawler = ArticleCrawler(create_dir='files')
# only for http://yjc.ir/fa
article_crawler.article_link_css = 'a.title4'
article_crawler.next_page_css = 'a.next'
article_crawler.article_body_css = 'div.body'
article_crawler.base_url = 'http://www.yjc.ir/fa/social'
article_crawler.number_of_articles = 200
article_crawler.file_names_prefix='prefix'
article_crawler.run()
