
# Get data
def get_data(setting_path):
    from src import Spider

    tag = "food"
    sp = Spider(setting_path)
    sp.main(tag)

# Query
def query(setting_path):
    from src import Database, load_settings

    conf = load_settings(setting_path)
    db = Database(**conf["db_settings"])
    sql = f"""SELECT * FROM {db.table_name} LIMIT 1"""
    c = db.get_cursor()
    res = c.execute(sql).fetchall()
    c.close()
    print(res)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Example")
    parser.add_argument("--test", type=int, 
        help="1: get_data, 2: query")
    parser.add_argument("--settings_path", type=str, default="./settings.yaml"
        help="settings path")
    args = parser.parse_args()
    if args == 1:
        get_data(setting_path)
    elif args == 2:
        query(setting_path)
    else:
        raise Exception("Not supported, insert `--test` 1 or 2")
