from tqdm import tqdm
from pathlib import Path
from typing import Union
from urllib.request import urlopen
from .database import Database
from .insta import Instagram
from .utils import load_settings

class Spider:
    def __init__(self, setting_path: str):
        self.check_path(setting_path, "file")
        conf = load_settings(setting_path)
        
        self.conf_insta = conf["insta_settings"]
        self.conf_db = conf["db_settings"]
        self.conf_spider = conf["spider_settings"]

        self.db = Database(**self.conf_db)
        self.insta = Instagram(**self.conf_insta)
        if self.conf_spider["recreate"]:
            self.db.recreate()
    
    def run(self, tag: str):
        links = self.insta.collect_links(tag)
   
        table_idx = self.db.get_last_id()
        table_idx = table_idx[0][0] if table_idx else 0
        
        pbar = tqdm(enumerate(self.insta.get_data(links), 1),
            desc="Getting data", total=len(links))

        batch = []
        freq = self.conf_spider["insert_freq"]
        for i, x in pbar:
            batch.append([table_idx+i, tag] + x)

            if len(batch) == freq:
                pbar.set_description("Inserting data")
                self.db.insert(batch)
                self.db.commit()
                batch = []
                pbar.set_description("Getting data")

        # insert remaining data
        self.db.insert(batch)
        self.db.commit()

    def main(self, tags: Union[list, str]):
        if isinstance(tags, list):
            for tag in tags:
                print(f"[INFO] Search tag: {tag}")
                self.run(tag)
        elif isinstance(tags, str):
            print(f"[INFO] Search tag: {tags}")
            self.run(tags)
        else:
            raise Exception("Error type of tags, should be `list`(list of tags) or `str`(single tag)")

        self.db.close()
        self.insta.close()

    def check_path(self, path: Path, typ: str="dir"):
        if not isinstance(path, Path):
            path = Path(path)
        if typ == "dir" and not path.exists():
            path.mkdir()
        if typ == "file" and not path.exists():
            raise Exception(f"file {path} not exists.")

    def extract(self):
        output_path = Path(self.conf_spider["output_path"])
        self.check_path(output_path, "dir")
        img_fmt = self.conf_spider["img_fmt"]
        
        self.db = Database(**self.conf_db)
        c = self.db.get_cursor()
        # get all tags
        sql = f"""SELECT DISTINCT tag FROM {self.db.table_name}"""
        res = c.execute(sql).fetchall()
        tags = list(map(lambda x: x[0], res))
        pbar = tqdm()

        for tag in tags:
            pbar.set_description(f"[INFO] Extracting: {tag}")
            
            tag_path = output_path / tag
            self.check_path(tag_path, "dir")
            sql = f"""SELECT id, imgs, post, othertags, date, likes 
                FROM {self.db.table_name} 
                WHERE tag = '{tag}';"""
            res = c.execute(sql).fetchall()

            pbar.reset(total=len(res))
            for idx, imgs, post, hashtags, date, likes in res:
                id_path = tag_path / f"{idx}_{date}_{likes}"
                self.check_path(id_path, "dir")
                # info.txt: be aware of having no hashtags
                with (id_path / "info.txt").open("w", encoding="utf-8") as file:
                    print("\t".join([hashtags, post]), file=file)
                # images
                for i, img_url in enumerate(imgs.split("\t"), 1):
                    with urlopen(img_url) as img_reader:
                        with (id_path / f"{i}{img_fmt}").open("wb") as img_writer:
                            img = img_reader.read()
                            img_writer.write(img)
                pbar.update(1)
        c.close()
        self.db.close()
        print("[INFO] Extract Done!")
        