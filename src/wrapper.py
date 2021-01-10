from tqdm import tqdm
from .database import Database
from .insta import Instagram
from .utils import load_settings

class Spider:
    def __init__(self, setting_path):
        conf = load_settings(setting_path)
        
        self.conf_insta = conf["insta_settings"]
        self.conf_db = conf["db_settings"]
        self.conf_spider = conf["spider_settings"]
        

    def main(self, tag):
        db = Database(**self.conf_db)
        insta = Instagram(**self.conf_insta)
        links = insta.collect_links(tag)
        
        table_idx = db.get_last_id()
        table_idx = table_idx[0] if table_idx else 0
        
        pbar = tqdm(enumerate(insta.get_data(links), 1),
            desc="Getting data", total=len(links))

        batch = []
        freq = self.conf_spider["insert_freq"]
        for i, x in pbar:
            batch.append([table_idx+i, tag] + x)

            if len(batch) == freq:
                pbar.set_description("Inserting data")
                db.insert(batch)
                db.commit()
                batch = []
                pbar.set_description("Getting data")

        # insert remaining data
        db.insert(batch)
        db.commit()
        db.close()
        insta.close()