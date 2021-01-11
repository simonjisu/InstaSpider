import os
import re
from tqdm import tqdm
from time import sleep
from urllib import parse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from typing import Generator

class Instagram:
    DRIVER_WAIT_TIME = 10
    SLEEP_TIME = 1.5
    PARSER = "html.parser"
    ATTRS_POSTS = "Nnq7C weEfm"
    ATTRS_USER_ID = "e1e1d"
    ATTRS_DATE = "c-Yi7"
    ATTRS_POST_TEXT = "C4VMK"
    ATTRS_LIKES = "Nm9Fw"
    ATTRS_IMG = "FFVAD"
    ATTRS_TAGS = "xil3i"
    ATTRS_ARIA_LABEL = "u7YqG"
    INSTA_POSTS_LEN = 3
    INSTA_FIRST_BTN_XPATH = '//*[@id="react-root"]/section/main/div/div[1]/article/div[2]/div/div[1]/div[2]/div/button'
    INSTA_NEXT_BTN_XPATH = '//*[@id="react-root"]/section/main/div/div[1]/article/div[2]/div/div[1]/div[2]/div/button[2]'
    ATTRS_SAVE_INFO = "cmbtv"
    ATTRS_ALRAM_OFF = "mt3GC"
    INSTA_SAVE_INFO_LATER_XPATH = '//*[@id="react-root"]/section/main/div/div/div/div/button'
    INSTA_ALRAM_OFF_XPATH = '/html/body/div[4]/div/div/div/div[3]/button[2]'
    LOGIN_ID_XPATH = '//*[@id="loginForm"]/div/div[1]/div/label/input'
    LOGIN_PW_XPATH = '//*[@id="loginForm"]/div/div[2]/div/label/input'

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
            
        print("[INFO] Done!")

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
            username_box_check = WebDriverWait(self.driver, self.DRIVER_WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, self.LOGIN_ID_XPATH))
            )
            print(f"[INFO] Box Check: {username_box_check}")
        except:
            raise Exception("Cannot find XPATH, set `DRIVER_WAIT_TIME` longer")

        id_input = self.driver.find_element_by_xpath(self.LOGIN_ID_XPATH)
        id_input.send_keys(insta_id)
        pw_input = self.driver.find_element_by_xpath(self.LOGIN_PW_XPATH)
        pw_input.send_keys(insta_pw)
        pw_input.submit()
        sleep(5)

        soup = self.get_soup()
        if soup.find_all(attrs={"class": self.ATTRS_SAVE_INFO}):
            self.click_button(self.INSTA_SAVE_INFO_LATER_XPATH)
        if soup.find_all(attrs={"class": self.ATTRS_ALRAM_OFF}):
            self.click_button(self.INSTA_ALRAM_OFF_XPATH)
        
    def parse_tag(self, tag: str) -> str:     
        """parse the hashtag to ascii encoded string 

        Args:
            tag (str): the hashtag that you want to search

        Returns:
            str: ascii encoded string
        """         
        return parse.quote(tag)

    def get_soup(self) -> BeautifulSoup:
        webpage = self.driver.page_source
        soup = BeautifulSoup(webpage, self.PARSER)
        return soup

    def get_link(self, url: str):
        self.driver.get(url)
        sleep(self.SLEEP_TIME)

    def click_button(self, xpath: str):    
        self.driver.find_element_by_xpath(xpath).click()
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
        previous_max_row = 0
        pbar = tqdm(total=self.thres_links)

        while len(links) < self.thres_links:
            soup = self.get_soup()
            posts = list(soup.find_all(name="div", attrs={"class": self.ATTRS_POSTS}))
            for link in posts[previous_max_row:]:
                for post in link.select("a"):
                    if len(links) >= self.thres_links:
                        break
                    # skip all videos
                    exists_label = post.find_all(attrs={"class": self.ATTRS_ARIA_LABEL})
                    is_slides = exists_label[0].find("span").attrs["aria-label"] == "슬라이드" if exists_label else False
                    if not exists_label or is_slides:
                        l = post.attrs["href"]
                        links.append(l)
                        pbar.update(1)
            

            last_height = self.driver.execute_script("return document.body.scrollHeight")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            previous_max_row = len(posts)
            pbar.set_description(f"previous max_row: {previous_max_row}")
            sleep(self.SLEEP_TIME)
            if new_height == last_height:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                sleep(self.SLEEP_TIME)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                previous_max_row = len(posts)
                if new_height == last_height:
                    # if cannot scroll, stop crawling
                    break
                    
                else:
                    last_height = new_height
                    continue
        pbar.close()
        return links


    def get_data(self, links: list) -> Generator:
        for i in range(len(links)):
            post_link = f"https://www.instagram.com/{links[i]}"
            self.get_link(post_link)
            soup = self.get_soup()

            # user_id
            user_id = hash(soup.find_all(attrs={"class": self.ATTRS_USER_ID})[0].text)

            # date
            date = soup.find_all(attrs={"class": self.ATTRS_DATE})[0].find("time").get("datetime")[:10]
            
            # post_text
            x = soup.find_all(attrs={"class": self.ATTRS_POST_TEXT})[0]
            post_text = " ".join(html.get_text(separator=" ").strip() for html in list(x)[1:-1])

            # likes
            x = soup.find_all(attrs={"class": self.ATTRS_LIKES})
            number_text = re.findall("[0-9]", x[0].text) if x else False
            if number_text:
                likes = int("".join(number_text))
            else:
                likes = -1
            
            # imgs
            img_link = soup.find_all("img", attrs={"class": self.ATTRS_IMG})[0]["src"]
            imgs = [img_link]
            try:
                self.click_button(self.INSTA_FIRST_BTN_XPATH)
                soup = self.get_soup()
                img_link = soup.find_all("img", attrs={"class": self.ATTRS_IMG})[0]["src"]
                imgs.append(img_link)
                keep_click = True
                while keep_click:
                    try: 
                        self.click_button(self.INSTA_NEXT_BTN_XPATH)
                        soup = self.get_soup()
                        img_link = soup.find_all("img", attrs={"class": self.ATTRS_IMG})[0]["src"]
                        imgs.append(img_link)
                    except NoSuchElementException:
                        keep_click = False
            except NoSuchElementException:
                pass
            imgs = "\t".join(imgs)

            # othertags
            x = soup.find_all(attrs={"class": self.ATTRS_TAGS})
            if x:
                othertags = "".join([t.text for t in x])
            else:
                othertags = ""
            
            # (... postlink TEXT, post TEXT, imgs TEXT, othertags TEXT, uid INTEGER, date TEXT, likes INTEGER)
            temp = [
                links[i], post_text, imgs, othertags, user_id, date, likes
            ]
            yield temp