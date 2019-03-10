class HomieModule:
    def __init__(self, homie):
        self._homie = homie
        self._status = "stopped"

    @property
    def status(self):
        return self._status

    def init(self):
        pass

    def start(self):
        pass

    def stop(self, _):
        pass


def import_module(homie, module_name, status="started"):  # TODO: Move this to homie core ?
    module = homie.get_module(module_name)
    if not module:
        raise Exception("{} is not registered with homie.".format(module_name))
    if not module.status == status:
        raise Exception("{} does not have a status of {}".format(module_name, status))
    return module
