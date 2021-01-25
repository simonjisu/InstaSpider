import yaml

def load_settings(settings_path):
    with open(settings_path) as f:
        conf = yaml.load(f, Loader=yaml.FullLoader)
    return conf