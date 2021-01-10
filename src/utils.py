import yaml

def load_settings(setting_path):
    with open(setting_path) as f:
        conf = yaml.load(f, Loader=yaml.FullLoader)
    return conf