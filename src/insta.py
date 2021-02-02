import os
import re
import bs4
from typing import Union
from tqdm import tqdm
from time import sleep
from urllib import parse
from bs4 import BeautifulSoup
from selenium import webdriver
from urllib.request import urlopen
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from typing import Generator

class Instagram:
    DRIVER_WAIT_TIME = 10
    SLEEP_TIME = 2
    PARSER = "html.parser"
    ATTRS_POSTS = "Nnq7C weEfm"
    ATTRS_USER_ID = "e1e1d"
    ATTRS_DATE = "c-Yi7"
    ATTRS_POST_TEXT = "C4VMK"
    ATTRS_LIKES = "Nm9Fw"
    # ATTRS_COMMENT = "EtaWk"
    ATTRS_IMG = "FFVAD"
    ATTRS_TAGS = "xil3i"
    ATTRS_ARIA_LABEL = "u7YqG"
    ATTRS_POST_LIST = "Ckrof"
    INSTA_POST_REPLY_XPATH = '//*[@id="react-root"]/section/main/div/div[1]/article/div[3]/div[1]/ul/ul{}/li/ul/li/div/button'
    INSTA_FIRST_BTN_XPATH = '//*[@id="react-root"]/section/main/div/div[1]/article/div[2]/div/div[1]/div[2]/div/button'
    INSTA_PREV_BTN_XPATH = '//*[@id="react-root"]/section/main/div/div[1]/article/div[2]/div/div[1]/div[2]/div/button[1]'
    INSTA_NEXT_BTN_XPATH = '//*[@id="react-root"]/section/main/div/div[1]/article/div[2]/div/div[1]/div[2]/div/button[2]'
    ATTRS_SAVE_INFO = "cmbtv"
    ATTRS_ALRAM_OFF = "mt3GC"
    INSTA_SAVE_INFO_LATER_XPATH = '//*[@id="react-root"]/section/main/div/div/div/div/button'
    INSTA_ALRAM_OFF_XPATH = '/html/body/div[4]/div/div/div/div[3]/button[2]'
    INSTA_SCROLL_POST_CSS = '#react-root > section > main > article > div:nth-child(3) > div'
    INSTA_SCROLL_POST_XPATH = '//*[@id="react-root"]/section/main/article/div[2]/div/div[{}]'
    LOGIN_ID_XPATH = '//*[@id="loginForm"]/div/div[1]/div/label/input'
    LOGIN_PW_XPATH = '//*[@id="loginForm"]/div/div[2]/div/label/input'
    IMG_SPLIT_TAG = b"<IMG>"

    def __init__(self, **kwargs):
        if os.name == "nt":
            chrome_p = kwargs["driver_path_win"]
        elif os.name == "posix":
            chrome_p = kwargs["driver_path_mac"]
        else:
            chrome_p = kwargs["driver_path_lin"]

        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        if kwargs["driver_no_sandbox"]:
            options.add_argument("--no-sandbox")
        if kwargs["driver_headless"]:
            options.add_argument("--headless")
        # options.add_argument('--disable-dev-shm-usage')
        # options.add_argument("user-agent=Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko")

        self.driver = webdriver.Chrome(chrome_p, options=options)
        self.thres_links = kwargs["thres_links"]
        # Force to login: if kwargs["login"]:
        print("[INFO] Trying to Login...")
        # TODO: 
        # write a check function to whether it is verified email
        # of only has one of id / pw
        insta_id = kwargs["insta_id"] 
        insta_pw = kwargs["insta_pw"]
        self.login(insta_id, insta_pw)
            
        print("[INFO] Login Done!")

    def login(self, insta_id: str, insta_pw: str):
        r"""login to instagram

        Args:
            insta_id (str): your insta id, should be email form 'xxx@email.com'
            insta_pw (str): your insta password
        """      
        login_url = "https://www.instagram.com/accounts/login/?source=auth_switcher"
        self.driver.get(login_url)
        sleep(self.SLEEP_TIME)
        try:
            self.INSTA_SCROLL_POST_XPATH
            username_box_check = WebDriverWait(self.driver, self.DRIVER_WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, self.LOGIN_ID_XPATH))
            )
            print(f"[INFO] Box Check: {username_box_check}")
        except:
            raise Exception("Cannot find XPATH, set `DRIVER_WAIT_TIME` longer")

        id_input = self.driver.find_element(By.XPATH, self.LOGIN_ID_XPATH)
        id_input.send_keys(insta_id)
        pw_input = self.driver.find_element(By.XPATH, self.LOGIN_PW_XPATH)
        pw_input.send_keys(insta_pw)
        pw_input.submit()
        sleep(5)

        soup = self.get_soup()
        if soup.find_all(attrs={"class": self.ATTRS_SAVE_INFO}):
            self.click_button(self.INSTA_SAVE_INFO_LATER_XPATH)
        if soup.find_all(attrs={"class": self.ATTRS_ALRAM_OFF}):
            self.click_button(self.INSTA_ALRAM_OFF_XPATH)
        
    def parse_tag(self, tag: str) -> str:     
        r"""parse the hashtag to ascii encoded string

        Args:
            tag (str): the hashtag that you want to search

        Returns:
            str: ascii encoded string
        """
                
        return parse.quote(tag)

    def get_soup(self) -> bs4.BeautifulSoup:
        webpage = self.driver.page_source
        soup = BeautifulSoup(webpage, self.PARSER)
        return soup

    def get_link(self, url: str):
        self.driver.get(url)
        sleep(self.SLEEP_TIME)

    def exists_xpath(self, xpath: str):
        try:
            self.driver.find_element(By.XPATH, xpath)
            return True
        except NoSuchElementException:
            return False

    def click_button(self, xpath: str):    
        self.driver.find_element(By.XPATH, xpath).click()
        sleep(self.SLEEP_TIME)

    def close(self):
        self.driver.close()
        print("[INFO] driver closed")

    def collect_links(self, tag: str) -> list:
        """collect links of posts

        Args:
            tag (str): the hashtag keyword that you want to search

        Returns:
            list: links of posts
        """
        links = []
        url = f"https://www.instagram.com/explore/tags/{self.parse_tag(tag)}/"
        self.get_link(url)
        try:
            page_loaded_check = WebDriverWait(self.driver, self.DRIVER_WAIT_TIME).until(
                EC.presence_of_element_located((By.CLASS_NAME, self.ATTRS_POSTS))
            )
        except:
            print(f"[INFO] Waiting for loading {url}")

        pbar = tqdm(total=self.thres_links)

        while len(links) < self.thres_links:
            soup = self.get_soup()
            posts = list(soup.find_all(name="div", attrs={"class": self.ATTRS_POSTS}))
            for link in posts:
                for post in link.select("a"):
                    if post.attrs["href"] in links:
                        continue
                    if len(links) >= self.thres_links:
                        break
                    # skip all videos
                    exists_label = post.find_all(attrs={"class": self.ATTRS_ARIA_LABEL})
                    is_slides = exists_label[0].find("span").attrs["aria-label"] == "슬라이드" if exists_label else False
                    if not exists_label or is_slides:
                        l = post.attrs["href"]
                        links.append(l)
                        pbar.update(1)

            scroll_contin = soup.select(self.INSTA_SCROLL_POST_CSS)
            if scroll_contin:
                recent_row_length = len(scroll_contin[0].find_all(
                    attrs={"class": self.ATTRS_POSTS}))
                pbar.set_description(f"Recent Posts Length: {recent_row_length}")
            else:
                # if no recent post. break 
                break

            last_height = self.driver.execute_script("return document.body.scrollHeight")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(self.SLEEP_TIME)
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                sleep(self.SLEEP_TIME)
                new_height = self.driver.execute_script("return document.body.scrollHeight")

                if new_height == last_height:
                    # if cannot scroll, stop crawling
                    pbar.total = len(links)
                    pbar.refresh()
                    break
                    
                else:
                    last_height = new_height
                    continue
        pbar.close()
        return links

    def get_byte_img(self, img_link):
        with urlopen(img_link) as img_reader:
            img_byte = img_reader.read()
        return img_byte

    def get_img(self, soup: bs4.BeautifulSoup, idx: int) -> Union[str, list]:
        """return img source, if no <img> tag will return empty list
        if the post_list is empty, means only have single image
        else means having multiple images

        Args:
            soup (bs4.BeautifulSoup): soup object 
            idx (int): post list index

        Returns:
            Union[str, list]: img source link or empty list 
        """        
        post_list = soup.find_all(attrs={"class": self.ATTRS_POST_LIST})
        if post_list:
            img_link = self.get_img_from_post_div(post_list[idx])
        else:
            img_link = soup.find_all(attrs={"class": self.ATTRS_IMG})[0]["src"]
        return img_link

    def get_img_from_post_div(self, post_div: bs4.element.Tag) -> Union[str, list]:
        """return img source, if no <img> tag will return empty list

        Args:
            post_div (bs4.element.Tag): `bs4.element.Tag` object that can find tags by attributes

        Returns:
            Union[str, list]: img source link or empty list 
        """        
        x = post_div.find_all(attrs={"class": self.ATTRS_IMG})
        if x:
            return x[0]["src"]
        else:
            return x

    def get_data(self, links: list) -> Generator:
        for i in range(len(links)):
            post_link = f"https://www.instagram.com{links[i]}"
            self.get_link(post_link)
            try:
                img_loaded_check = WebDriverWait(self.driver, self.DRIVER_WAIT_TIME).until(
                    EC.presence_of_element_located((By.CLASS_NAME, self.ATTRS_IMG))
                )
            except:
                print(f"[WARNING] Not exists: {post_link}")
                continue
                # raise Exception("Cannot find XPATH, set `DRIVER_WAIT_TIME` longer")

            soup = self.get_soup()

            # user_id
            user_id = soup.find_all(attrs={"class": self.ATTRS_USER_ID})[0].text

            # date
            date = soup.find_all(attrs={"class": self.ATTRS_DATE})[0].find("time").get("datetime")[:10]
            
            
            # likes
            x = soup.find_all(attrs={"class": self.ATTRS_LIKES})
            number_text = re.findall("[0-9]", x[0].text) if x else False
            if number_text:
                likes = int("".join(number_text))
            else:
                likes = -1
            
            # imgs
            # TODO: bug, cannot find the class element when we make the window smallest
            img_link = self.get_img(soup=soup, idx=0)
            # create image container, if first image is video, will create empty list
            imgs = [self.get_byte_img(img_link)] if img_link else img_link
            if self.exists_xpath(self.INSTA_FIRST_BTN_XPATH):
                self.click_button(self.INSTA_FIRST_BTN_XPATH)
                soup = self.get_soup()
                img_link = self.get_img(soup=soup, idx=1)
                if img_link:
                    imgs.append(self.get_byte_img(img_link))
                while self.exists_xpath(self.INSTA_NEXT_BTN_XPATH):
                    self.click_button(self.INSTA_NEXT_BTN_XPATH)
                    soup = self.get_soup()
                    img_link = self.get_img(soup=soup, idx=1)
                    if img_link:
                        imgs.append(self.get_byte_img(img_link))

            if len(imgs) == 0:
                continue
            else:
                imgs = self.IMG_SPLIT_TAG.join(imgs)

            # Treat all self comment as post, do not open other id's comment
            f_get_text = lambda html_div: " ".join([html.get_text(separator=" ").strip() for html in list(html_div)[1:-1]])
            x = soup.find_all(attrs={"class": self.ATTRS_POST_TEXT})
            post_text = ""
            if x:
                for i, html_div in enumerate(x):
                    if html_div.find("a").text == user_id:
                        if i == 0:
                            continue
                        if i == 1:
                            x_path = self.INSTA_POST_REPLY_XPATH.format("")
                        else:
                            x_path = self.INSTA_POST_REPLY_XPATH.format(f"[{i}]")
                        if self.exists_xpath(x_path):
                            self.click_button(x_path)
                # post text
                soup = self.get_soup()
                x = soup.find_all(attrs={"class": self.ATTRS_POST_TEXT})
                for html_div in x:
                    if list(html_div)[0].get_text() == user_id:
                        post_text += f_get_text(html_div).replace(f"@{user_id}", "")
                # othertags
                x = soup.find_all(attrs={"class": self.ATTRS_TAGS})
                if x:
                    othertags = " ".join([t.text for t in x])
                else:
                    othertags = " "

            else:
                post_text = " "
                othertags = " "
            
            # (... postlink TEXT, post TEXT, imgs TEXT, othertags TEXT, uid INTEGER, date TEXT, likes INTEGER)
            temp = [
                links[i], post_text, imgs, othertags, user_id, date, likes
            ]
            yield temp