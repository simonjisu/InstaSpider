# InstaSpider

Get datas from Instagram, searching by hashtag

```
python >= 3.7
beautifulsoup4 
PyYAML
selenium
sqlite
tqdm
```

# Usage

1. Download the Chrome driver from [link](https://chromedriver.chromium.org/downloads) and change driver name and put into `chrome` folder as followings:
    - for windows users: `./chrome/chromedriver_win.exe`
    - for mac users: `./chrome/chromedriver_mac`
    - for linux users: `./chrome/chromedriver_linux`
2. Change your `settings.yaml`
3. Change or write your own code, or try `example.py --test 1`
    ```python
    from src import Spider

    tag = "food"
    sp = Spider("./settings.yaml")
    sp.main(tag)
    ```
4. Check you sqlite db, or try `example.py --test 2`
    ```python
    from src import Database, load_settings

    conf = load_settings("./settings.yaml")
    db = Database(**conf["db_settings"])
    sql = f"""SELECT * FROM {db.table_name} LIMIT 5"""
    c = db.get_cursor()
    res = c.execute(sql).fetchall()
    c.close()
    ```

# License

