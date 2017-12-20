from net_modules.core import ArticleCrawler
import logging

logging.basicConfig(filename='log.txt',
                    filemode='w+',
                    format='%(asctime)s : %(levelname)s : %(message)s',
                    level=logging.INFO)

article_crawler = ArticleCrawler(create_dir='yjc_ir_social')
# only for http://yjc.ir/fa
article_crawler.article_link_css = 'a.title4'
article_crawler.next_page_css = 'a.next'
article_crawler.article_body_css = 'div.body'
article_crawler.base_url = 'http://www.yjc.ir/fa/social'
article_crawler.number_of_articles = 10000
article_crawler.file_names_prefix = 'social'
article_crawler.multi_thread = True
article_crawler.run()
