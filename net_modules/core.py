"""Summary
"""
import requests
import bs4
import sys


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
        TODO : some modifications needed
    base_url : str
        base url of website that contains article
    create_dir : TYPE
        Description
    encode : str
        files encoding
    file_names_prefix : str
        prefix files name 
    next_page_css : list or str
        CSS selector(s) used to determine next page that contain article links
        if this property equals None will be ignored
    number_of_articles : int
        number of articles to crawl from `base_url`, should be positive
    website_base_url_regexp : str
        regular expression to extract website from `self.base_url`
    """

    def __init__(self, base_url=None, number_of_articles=20, article_link_css=None,
                 article_body_css=None, next_page_css=None, file_names_prefix=None,
                 create_dir=False, encode="utf-8"):
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
        """
        self.base_url = base_url
        self.number_of_articles = number_of_articles
        self.article_link_css = article_link_css
        self.article_body_css = article_body_css
        self.next_page_css = next_page_css
        self.file_names_prefix = file_names_prefix if isinstance(file_names_prefix, str) else ''
        self.encode = encode
        self.create_dir = create_dir
        if isinstance(self.create_dir, str):
            self._create_output_dir()
        self.website_base_url_regexp = r'^(http(s)?:\/\/(www\.)?[a-z0-9]+\.(\w){2,3})'

    def run(self):
        """you should call this function to start crawling
        
        Raises
        ------
        ValueError
            in case any missing or invalid values for parameters
        """
        if not self._check_attributes():
            raise ValueError("some attribute values missing")
        # single threaded
        internal_counter = 0
        base_url = self.base_url  # URL to web page containing articles links
        while True:
            articles_links, bs4_object = self._extract_article_links(base_url)
            bodies = []
            for link in articles_links:
                temp = self._extract_article_body(link)
                internal_counter = internal_counter + 1
                self._save_to_file(temp, internal_counter)
                if internal_counter > self.number_of_articles:
                    break

            if internal_counter >= self.number_of_articles:
                break

            # get next link
            base_url = self._extract_elements(self.next_page_css,
                                              bs4_object=bs4_object, attributes=['href'])[0]
            if base_url[0] == '/':
                import re
                pattern = re.compile(self.website_base_url_regexp)
                match_obj = re.match(pattern=pattern, string=self.base_url)
                aux_url = match_obj.group()
                # check for urls now
                base_url = aux_url + base_url

    def _check_attributes(self):
        """Summary
        
        Returns
        -------
        bool
            Description
        """
        return True

    def _get_url_contents(self, link, method="GET", headers=None,
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

    def _extract_elements(self, css_selectors, html_doc="", bs4_object=None, attributes=None):
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
                "css_selector must be either str or list of str").with_traceback(tb)

        if isinstance(bs4_object, bs4.BeautifulSoup):
            return self._extract_elements_from_bs4_object(css_selectors=css_selectors,
                                                          bs4_object=bs4_object,
                                                          attributes=attributes)
        # check for html_doc
        elif isinstance(html_doc, str) and not html_doc == "":
            return self._extract_elements_from_str(css_selectors, html_doc, attributes)
        else:
            tb = sys.exc_info()[2]
            raise TypeError(
                "html_doc must be either str or pass a bs4.BeautifulSoup object"
            ).with_traceback(tb)

    def _extract_elements_from_bs4_object(self, css_selectors: list,
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
        return self._extract_elements_from_bs4_object(css_selectors=css_selectors, bs4_object=bs4_object,
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
        html_doc, encode = self._get_url_contents(url)
        data = str(html_doc, encoding=encode)
        bs4_object = bs4.BeautifulSoup(html_doc, 'html.parser')

        links = self._extract_elements(self.article_link_css, bs4_object=bs4_object, attributes=['href'])
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
        page_content, encode = self._get_url_contents(article_link)
        page_content = str(page_content, encoding=encode)
        page_content = bs4.BeautifulSoup(page_content, 'html.parser')
        page_content = self._extract_elements(self.article_body_css, bs4_object=page_content)
        ret = ''
        for item in page_content:
            ret = ret + item.get_text()
        return ret

    def _save_to_file(self, content, number):
        """Summary
        
        Parameters
        ----------
        content : TYPE
            Description
        number : TYPE
            Description
        """
        pad_len = len(str(self.number_of_articles))
        if not self.create_dir == '':
            base_dir = self.create_dir + '/' + self.file_names_prefix
        else:
            base_dir = self.file_names_prefix

        file_name = f'{base_dir}_{number:0{pad_len}}.txt'
        print(file_name)
        with open(file_name, mode='w+',
                  encoding=self.encode) as f:
            f.write(content)

    def _create_output_dir(self):
        """Summary
        """
        import os
        if not os.path.exists(self.create_dir):
            os.mkdir(self.create_dir)
