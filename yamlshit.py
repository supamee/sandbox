import yaml

class Config:
    """
    Manages config files.
    Parameters:
    -----------
    path: str
        The config file path.
    """

    def __init__(self, path):
        try:
            if path is None:
                path = sentry_config_path()
            print('path: ', path)
            conf = yaml.load(open(path), Loader=yaml.Loader)
            # self.sentry = conf["sentry"]
            # self=conf
            self.sentry="thing"
        except KeyError as e:
            print("nope")

    def _load_sentry(self, conf):
        """
        Loads the sentry config.
        """
        return SentryConfig(conf["name"], conf["location"])
def save_config(path, conf):
    print("saving")
    with open(path, "w") as yaml_file:
        yaml.safe_dump(conf, yaml_file, default_flow_style=False)

thing=Config("test.yaml")

print(type(thing),thing)
save_config("test.yaml",thing)