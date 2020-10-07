from abc import ABCMeta, abstractmethod
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support import expected_conditions

import chromedriver_binary
import time
import sys
import traceback
from enum import Enum

USER_MAIL = 'kentarou.m@gmail.com' #ログイン時に入力するメールアドレス
USER_PASS = 'km19811216'  #ログイン時に入力するパスワード
PROCESS_TIME = 60 * 30

class MODELS(Enum):
    LOGIN = 0
    STAR_LIST = 1
    CART = 2
    BUY = 3
    NEW = 4

class AbstractWebpageModel(metaClass=ABCMeta):

    _DOMAIN = 'https://www.bookoffonline.co.jp'
    _driver = None
    _page = 0

    def __init__(self, driver, page):
        self._driver = driver
        self._page = page

    @abstractmethod
    def getInstance(self, driver: Chrome, model: MODELS):
        if model == MODELS.LOGIN:
            return LoginWebpageModel(driver, model)
        elif model == MODELS.STAR_LIST:
            return StarListWebpageModel(driver, model)
        elif model == MODELS.CART:
            return CartWebpageModel(driver, model)
        elif model == MODELS.BUY:
            return BuyWebpageModel(driver, model)
        elif model == MODELS.NEW:
            return NewWebpageModel(driver, model)

    @abstractmethod
    def getUrl(self):
        pass

    def refresh(self):
        self._driver.switch_to.window(self._driver.window_handles[self._page])
        self._driver.get(self.getUrl())

class LoginWebpageModel(AbstractWebpageModel):

    def getUrl(self):
        return self.DOMAIN + '/disp/BSfDispBookMarkAlertMailInfo.jsp?ss=u&ml=0&ct=00&sk=10&row=50'

class StarListWebpageModel(AbstractWebpageModel):
    def getUrl(self):
        return self.DOMAIN + '/disp/BSfDispBookMarkAlertMailInfo.jsp?ss=u&ml=0&ct=00&sk=10&row=50'
    
class CartWebpageModel(AbstractWebpageModel):
    def getUrl(self):
        return self.DOMAIN + '/disp/BSfDispBookMarkAlertMailInfo.jsp?ss=u&ml=0&ct=00&sk=10&row=50'
    
class BuyWebpageModel(AbstractWebpageModel):
    def getUrl(self):
        return self.DOMAIN + '/disp/BSfDispBookMarkAlertMailInfo.jsp?ss=u&ml=0&ct=00&sk=10&row=50'
    
class NewWebpageModel(AbstractWebpageModel):
    def getUrl(self):
        return self.DOMAIN + '/disp/BSfDispBookMarkAlertMailInfo.jsp?ss=u&ml=0&ct=00&sk=10&row=50'
    

if __name__ == "__main__":
    options = webdriver.chrome.options.Options()
    # options.add_argument('--user-data-dir={}'.format(USER_DATA_DIR))
    options.add_argument('--headless')
    options.add_argument('--disable-application-cache')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--start-maximized')
    driver = webdriver.Chrome(options=options)

    webPages = {}
    for model in AbstractWebpageModel.MODELS.items():
        webPages[model] = AbstractWebpageModel.getInstance(driver, model)
        driver.execute_script('window.open()')
    