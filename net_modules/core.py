"""Summary
"""
import requests
import bs4
import sys
import logging
from more_itertools import chunked
import threading
import grequests


def get_url_contents(link, method="GET", headers=None,
                     params=None, proxy_config=None):
    """Summary
    
    Parameters
    ----------
    link : str
        link to web page
    method : str, optional
        type of request, valid methods are: POST, GET, PUT, PATCH, and DELETE
        if passed parameter not found in above list, GET will used
        default is GET
    headers : HTTP headers, optional
        HTTP header fields
    params : request parameters, optional
        parameters used for request
    proxy_config : dict
        proxies argument value
    
    Returns
    -------
    Tuple[bytes, str]
        web-page as a bytes and its encode
    """
    valid_methods = {"POST", "GET", "PUT", "PATCH", "DELETE"}
    if method not in valid_methods:
        method = "GET"

    if params is None:
        pass
    elif not isinstance(params, dict):
        print("params is of type {}, it will omitted.".format(type(headers)))
        params = None

    if headers is None:
        pass
    elif not isinstance(headers, dict):
        print("header is of type {}, it will omitted.".format(type(headers)))
        headers = {}
    # `headers` is dict
    elif "User-Agent" not in headers:
        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 "
        "Safari/537.36"

    if proxy_config is None:
        pass
    elif not isinstance(proxy_config, dict):
        print("proxy_config is of type {}, it will omitted.".format(
            type(proxy_config)))
        proxy_config = None

    try:
        result = requests.request(method, link, data=params,
                                  headers=headers, proxies=proxy_config)
        return result.content, result.encoding
    except Exception as ex:
        print(ex)


class ArticleCrawler:
    """A class to crawl news from various sites
    

    to start crawling you must initialize member variables, see `__init__` for more details
    
    Attributes
    ----------
    article_body_css : list or str
        CSS selector(s) used to extract body of article, if list passed it will
        aggregate inner text of matching elements
    article_link_css : list or str
        CSS selector(s) used to find articles link (direct link to this)
    base_url : str
        base url of website that contains article
    create_dir : str or bool
        if passed str a directory with same name created and all file will put on it
        it is recommended to pass existing directory
    current_page_url : str
        URL to web page containing articles links
    encode : str
        files encoding
    file_names_prefix : str
        prefix files name 
    internal_counter : int
        Description
    multi_thread : bool
        sun on single thread or multiple threads
    next_page_css : list or str
        CSS selector(s) used to determine next page that contain article links
        if this property equals None will be ignored
    number_of_articles : int
        number of articles to crawl from `base_url`, should be positive
    website_base_url_regexp : str
        regular expression to extract website from `self.base_url`
    """

    def __init__(self, base_url=None, number_of_articles: int = 20,
                 article_link_css=None, article_body_css=None,
                 next_page_css=None, file_names_prefix=None,
                 create_dir=False, encode="utf-8", multi_thread: bool = False):
        """Summary
        
        Parameters
        ----------
        base_url : None, optional
            refer to class attributes
        number_of_articles : int, optional
            refer to class attributes
        article_link_css : None, optional
            refer to class attributes
        article_body_css : None, optional
            refer to class attributes
        next_page_css : None, optional
            refer to class attributes
        file_names_prefix : None, optional
            refer to class attributes
        create_dir : bool or str, optional
            whether to put article files in a specified directory or not
            directory will be created if it doesn't exist
        encode : str, optional
            refer to class attributes
        multi_thread : bool, optional
            Description
        """
        self.base_url = base_url
        self.current_page_url = self.base_url
        self.number_of_articles = number_of_articles
        self.article_link_css = article_link_css
        self.article_body_css = article_body_css
        self.next_page_css = next_page_css
        self.file_names_prefix = file_names_prefix if isinstance(
            file_names_prefix, str) else ''
        self.encode = encode
        self.create_dir = create_dir
        self.multi_thread = multi_thread
        if isinstance(self.create_dir, str):
            self._create_output_dir()
        self.website_base_url_regexp = r'^(http(s)?:\/\/(www\.)?[a-z0-9]+\.(\w){2,3})'
        self.internal_counter = 1

    def run(self):
        """you should call this function to start crawling
        
        Raises
        ------
        ValueError
            in case any missing or invalid values for parameters
        """
        if not self._check_attributes():
            raise ValueError("some attribute values missing")
        if self.multi_thread:
            self._multi_thread()
        else:
            self._run_single_thread()
            # single threaded

    def _run_single_thread(self):
        """Summary
        """
        while True:
            articles_links, bs4_object = \
                self._extract_article_links(self.current_page_url)

            for link in articles_links:
                if self.internal_counter > self.number_of_articles:
                    break
                try:
                    temp = self._extract_article_body(link)
                    self.internal_counter = self.internal_counter + 1
                    self._save_to_file(temp)

                    if self.internal_counter % 500 == 0:
                        logging.info(
                            'stored files : {}.'.format(self.internal_counter))
                except Exception as ex:
                    self._exception_handler(ex)
                    continue
            if self.internal_counter >= self.number_of_articles:
                break
            # get next link
            self.current_page_url = \
                self._extract_elements(self.next_page_css,
                                       bs4_object=bs4_object,
                                       attributes=['href'])[0]
            if self.current_page_url[0] == '/':
                import re
                pattern = re.compile(self.website_base_url_regexp)
                match_obj = re.match(pattern=pattern, string=self.base_url)
                aux_url = match_obj.group()
                # check for urls now
                self.current_page_url = aux_url + self.current_page_url

    def _multi_thread(self):
        """
        """
        while True:
            articles_links, bs4_object = \
                self._extract_article_links(self.current_page_url)
            urls = (grequests.get(link) for link in articles_links)

            bodies = []
            for body in grequests.map(urls):
                bodies.append(str(body.content, encoding=body.encoding))
            chucked_list = chunked(bodies, 3)
            bodies = []
            threads = []
            lock_obj = threading.Lock()
            for chunk in chucked_list:
                threads.append(
                    threading.Thread(
                        target=self._mt_helper,
                        args=(chunk, bodies, lock_obj)
                    )
                )
                threads[-1].start()
            for th in threads:
                th.join()  # busy wait

            for body in bodies:
                self._save_to_file(body)
                self.internal_counter = self.internal_counter + 1
                if self.internal_counter > self.number_of_articles:
                    break
                elif self.internal_counter % 500 == 0:
                    logging.info(
                        'stored files : {}.'.format(self.internal_counter))

            if self.internal_counter >= self.number_of_articles:
                break
            # get next link
            self.current_page_url = \
                self._extract_elements(self.next_page_css,
                                       bs4_object=bs4_object,
                                       attributes=['href'])[0]
            if self.current_page_url[0] == '/':
                import re
                pattern = re.compile(self.website_base_url_regexp)
                match_obj = re.match(pattern=pattern, string=self.base_url)
                aux_url = match_obj.group()
                # check for urls now
                self.current_page_url = aux_url + self.current_page_url

    def _mt_helper(self, links: list, bodies: list, lock: threading.Lock):
        """Summary

        Parameters
        ----------
        links : list
            Description
        bodies : list
            Description
        lock : threading.Lock
            Description
        """
        for link in links:
            try:
                lock.acquire()
                bodies.append(self._extract_article_body(link))
                lock.release()
            except Exception as ex:
                lock.acquire()
                self._exception_handler(ex)
                lock.release()
        logging.debug('thread ended execute')

    def _check_attributes(self):
        """Summary

        Returns
        -------
        bool
            Description
        """
        # article_body_css
        if isinstance(self.article_body_css, list) or isinstance(self.article_body_css, str):
            pass
        else:
            raise ValueError('article_body_css must be either str or list')
        # article_link_css
        if isinstance(self.article_link_css, list) or isinstance(self.article_link_css, str):
            pass
        else:
            raise ValueError('article_link_css must be either str or list')
        # base_url
        if isinstance(self.base_url, str):
            self.current_page_url = self.base_url
            pass
        else:
            raise ValueError('article_link_css must be either str')
        # create_dir
        if isinstance(self.create_dir, str) or isinstance(self.create_dir, bool):
            pass
        else:
            raise ValueError('create_dir must be str or bool')
        # encode
        if isinstance(self.encode, str):
            pass
        else:
            raise ValueError('encode must be str')
        # file_names_prefix
        if isinstance(self.file_names_prefix, str) or self.file_names_prefix is None:
            pass
        else:
            raise ValueError('file_name_prefix must be either str or None')
        # multi_thread
        if isinstance(self.multi_thread, bool):
            pass
        else:
            raise ValueError('multi_thread must be bool')
        # next_page_css
        if isinstance(self.next_page_css, list) or isinstance(self.next_page_css, str):
            pass
        else:
            raise ValueError('next_page_css must be either str or list')
        # number_of_articles
        if isinstance(self.number_of_articles, int):
            pass
        else:
            raise ValueError('number_of_articles must be int')

        return True

    def _extract_elements(self, css_selectors,
                          html_doc="",
                          bs4_object=None,
                          attributes=None):
        """Summary

        Parameters
        ----------
        css_selectors : TYPE
            Description
        html_doc : TYPE
            Description
        bs4_object : None, optional
            Description
        attributes : list, optional
            if provided value of this attributes will returned

        Raises
        ------
        TypeError
            Description

        Returns
        -------
        list
            list of matched elements
        """
        if isinstance(css_selectors, str):
            css_selectors = [css_selectors]
        elif isinstance(css_selectors, list):
            pass

        else:
            tb = sys.exc_info()[2]
            raise TypeError(
                "css_selector must be either str or list of str"
            ).with_traceback(tb)

        if isinstance(bs4_object, bs4.BeautifulSoup):
            return self._extract_elements_from_bs4(css_selectors=css_selectors,
                                                   bs4_object=bs4_object,
                                                   attributes=attributes
                                                   )
        # check for html_doc
        elif isinstance(html_doc, str) and not html_doc == "":
            return self._extract_elements_from_str(css_selectors,
                                                   html_doc,
                                                   attributes
                                                   )
        else:
            tb = sys.exc_info()[2]
            raise TypeError(
                "html_doc must be either str or pass a "
                "bs4.BeautifulSoup object"
            ).with_traceback(tb)

    @staticmethod
    def _extract_elements_from_bs4(css_selectors: list,
                                   bs4_object: bs4.BeautifulSoup,
                                   attributes=None):
        """Summary

        Parameters
        ----------
        css_selectors : list
            list of selectors
        bs4_object : bs4.BeautifulSoup
            bs4 object used to search
        attributes : None, optional
            Description

        Returns
        -------
        TYPE
            Description

        Raises
        ------
        TypeError
            Description
        """
        ret = []
        if attributes is None:
            for css_selector in css_selectors:
                ret = ret + bs4_object.select(css_selector)
        elif not isinstance(attributes, list):
            tb = sys.exc_info()[2]
            raise TypeError(
                "attributes must be list object"
            ).with_traceback(tb)
        else:
            for css_selector in css_selectors:
                for elem in bs4_object.select(css_selector):
                    for attribute in attributes:
                        ret.append(elem[attribute])
        return ret

    def _extract_elements_from_str(self, css_selectors: list,
                                   html_doc: str, attributes):
        """Summary

        Parameters
        ----------
        css_selectors : list
            Description
        html_doc : str
            Description
        attributes : TYPE
            Description

        Returns
        -------
        TYPE
            Description
        """
        bs4_object = bs4.BeautifulSoup(html_doc, 'html.parser')
        return self._extract_elements_from_bs4(css_selectors=css_selectors,
                                               bs4_object=bs4_object,
                                               attributes=attributes)

    def _extract_article_links(self, url):
        """Summary

        Parameters
        ----------
        url : TYPE
            Description

        Returns
        -------
        TYPE
            Description

        Deleted Parameters
        ------------------
        css_selectors : TYPE
            Description
        """
        try:
            html_doc, encode = get_url_contents(url)
            bs4_object = bs4.BeautifulSoup(html_doc, 'html.parser')

            links = self._extract_elements(
                self.article_link_css, bs4_object=bs4_object, attributes=['href'])
            import re
            pattern = re.compile(self.website_base_url_regexp)
            match_obj = re.match(pattern=pattern, string=self.base_url)
            aux_url = match_obj.group()
            # check for urls now

            for (i, link) in enumerate(links):
                # if link is relative(!) modify it!
                if link[0] == '/':  # dummy check for now
                    links[i] = aux_url + links[i]
            return links, bs4_object
        except Exception as ex:
            self._exception_handler(ex)
            return []

    def _extract_article_body(self, article_link):
        """Summary

        Parameters
        ----------
        article_link : TYPE
            Description

        Deleted Parameters
        ------------------
        body_css : TYPE
            Description

        Returns
        -------
        TYPE
            Description
        """
        if not self.multi_thread:
            page_content, encode = get_url_contents(article_link)
            page_content = str(page_content, encoding=encode)
        else:
            page_content = article_link
        page_content = bs4.BeautifulSoup(page_content, 'html.parser')
        page_content = self._extract_elements(
            self.article_body_css, bs4_object=page_content)
        ret = ''
        for item in page_content:
            ret = ret + item.get_text()
        return ret

    def _save_to_file(self, content):
        """Summary

        Parameters
        ----------
        content : TYPE
            Description

        Deleted Parameters
        ------------------
        number : TYPE
            Description
        """
        pad_len = len(str(self.number_of_articles))
        if not self.create_dir == '':
            base_dir = self.create_dir + '/' + self.file_names_prefix
        else:
            base_dir = self.file_names_prefix

        file_name = f'{base_dir}_{self.internal_counter:0{pad_len}}.txt'
        # print(file_name)
        with open(file_name, mode='w+',
                  encoding=self.encode) as f:
            f.write(content)

    def _create_output_dir(self):
        """Summary
        """
        import os
        if not os.path.exists(self.create_dir):
            os.mkdir(self.create_dir)

    def dump(self):
        """dump attributes on disk
        """
        import pandas as pd
        dt = pd.Series()
        dt['multi_thread'] = self.multi_thread
        dt['article_body_css'] = self.article_body_css
        dt['article_link_css'] = self.article_link_css
        dt['base_url'] = self.base_url
        dt['create_dir'] = self.create_dir
        dt['next_page_css'] = self.next_page_css
        dt['encode'] = self.encode
        dt['file_names_prefix'] = self.file_names_prefix
        dt['website_base_url_regexp'] = self.website_base_url_regexp
        dt['current_page_url'] = self.current_page_url
        dt['internal_counter'] = self.internal_counter
        dt['number_of_articles'] = self.number_of_articles
        # storing on json file
        dt.to_json('ArticleCrawler.json')

    def create_from_dump(self, json_dump='ArticleCrawler.json'):
        """restore attributes from disk

        Parameters
        ----------
        json_dump : str, optional
            file name or path to file that contains dump file, must be json
        """
        import pandas as pd
        dt = pd.read_json(json_dump, orient='records', typ='series')
        self.multi_thread = dt['multi_thread']
        self.article_body_css = dt['article_body_css']
        self.article_link_css = dt['article_link_css']
        self.base_url = dt['base_url']
        self.create_dir = dt['create_dir']
        self.next_page_css = dt['next_page_css']
        self.encode = dt['encode']
        self.file_names_prefix = dt['file_names_prefix']
        self.website_base_url_regexp = dt['website_base_url_regexp']
        self.current_page_url = dt['current_page_url']
        self.internal_counter = dt['internal_counter']
        self.number_of_articles = dt['number_of_articles']

    def _exception_handler(self, exception: Exception):
        """Summary

        Parameters
        ----------
        exception : Exception
            Description
        """
        logging.exception(exception, exc_info=True)
        self.dump()
