
# Get data
def get_data(settings_path):
    from src import Spider

    tag = "food"
    sp = Spider(settings_path)
    sp.main(tag)

# Query
def query(settings_path):
    from src import Database, load_settings

    conf = load_settings(settings_path)
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
    parser.add_argument("--settings_path", type=str, default="./settings.yaml",
        help="settings path")
    args = parser.parse_args()
    if args.test == 1:
        get_data(args.settings_path)
    elif args.test == 2:
        query(args.settings_path)
    else:
        raise Exception("Not supported, insert `--test` 1 or 2")
