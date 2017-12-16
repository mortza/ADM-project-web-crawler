import requests
import bs4
import sys


class ArticleCrawler:
    """A class to crawl news from various sites

    to start crawling you must

    Attributes
    ----------
    article_body_css : list or str
        CSS selector(s) used to extract body of article
    article_link_css : list or str
        CSS selector(s) used to find articles link (direct link to this)
        TODO : some modifications needed
    base_url : str
        base url of website that contains article
    encode : str
        files encoding
    file_names_prefix : str
        prefix files name 
    next_page_css : list or str
        CSS selector(s) used to determine next page that contain article links
        if this property equals None will be ignored
    number_of_articles : int
        number of articles to crawl from `base_url`
    """

    def __init__(self, base_url=None, number_of_articles=20, article_link_css=None,
                 article_body_css=None, next_page_css=None, file_names_prefix=None,
                 encode="utf-8"):
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
        encode : str, optional
            refer to class attributes
        """
        self.base_url = base_url
        self.number_of_articles = number_of_articles
        self.article_link_css = article_link_css
        self.article_body_css = article_body_css
        self.next_page_css = next_page_css
        self.file_names_prefix = file_names_prefix
        self.encode = encode

    def run(self):
        if not self._check_attributes():
            raise ValueError("some attribute values missing")
        internal_counter = 0


    def _check_attributes(self):
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

    def _extract_elements(self, css_selectors, html_doc, bs4_object=None) -> list:
        """Summary

        Parameters
        ----------
        css_selectors : TYPE
            Description
        html_doc : TYPE
            Description
        bs4_object : None, optional
            Description

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
                                                          bs4_object=bs4_object)
        # check for html_doc
        elif isinstance(html_doc, str) and not html_doc == "":
            return self._extract_elements_from_str(css_selectors, html_doc)
        else:
            tb = sys.exc_info()[2]
            raise TypeError(
                "html_doc must be either str or pass a bs4.BeautifulSoup object"
            ).with_traceback(tb)

    def _extract_elements_from_bs4_object(self, css_selectors: list,
                                          bs4_object: bs4.BeautifulSoup) -> list:
        """Summary

        Parameters
        ----------
        css_selectors : list
            list of selectors
        bs4_object : bs4.BeautifulSoup
            bs4 object used to search
        """
        ret = []
        for css_selector in css_selectors:
            ret = ret + bs4_object.select(css_selector)

        return ret

    def _extract_elements_from_str(self, css_selectors: list,
                                   html_doc: str) -> list:
        """Summary

        Parameters
        ----------
        css_selectors : list
            Description
        html_doc : str
            Description
        """
        bs4_object = bs4.BeautifulSoup(html_doc, 'html.parser')
        return self._extract_elements_from_bs4_object(css_selectors=css_selectors, bs4_object=bs4_object)

    def _extract_article_links(self, url, css_selectors):

        html_doc,encode = self._get_url_contents(url)
        data = str(html_doc, encoding=encode)
        bs4_object = bs4.BeautifulSoup(html_doc,'html.parser')

        links = self._extract_elements(css_selectors, "", bs4_object)
        return links
