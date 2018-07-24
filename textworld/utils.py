# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import os
import re
import shutil
import tempfile
import contextlib
from collections import OrderedDict

import numpy as np


class RandomGenerator:
    """ Random generator controlling the games generation. """

    def __init__(self, seed=None):
        self.set_seed(seed)

    @property
    def seed(self):
        return self._seed

    def set_seed(self, seed):
        self._seed = seed
        if self._seed is None:
            self._seed = np.random.randint(65635)

        self._orig_seed = self.seed

    def next(self):
        """ Start a new random generator using a new seed. """
        rng = np.random.RandomState(self._seed)
        self._seed += 1
        return rng


def which(program):
    """
    helper to see if a program is in PATH
    :param program: name of program
    :return: path of program or None
    """
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

def get_driver(path=None):
    """
    Get the driver and options objects.
    :param path: path to browser binary.
    :return: driver
    """
    from selenium import webdriver

    def chrome_driver(path=None):
        from selenium.webdriver.chrome.options import Options
        options = Options()
        options.add_argument('headless')
        options.add_argument('ignore-certificate-errors')
        options.add_argument("test-type")
        options.add_argument("no-sandbox")
        options.add_argument("disable-gpu")
        if path is not None:
            options.binary_location = path

        driver = webdriver.Chrome(chrome_options=options)

        return driver

    def firefox_driver(path=None):
        from selenium.webdriver.firefox.options import Options
        options = Options()
        options.add_argument('headless')
        driver = webdriver.Firefox(firefox_binary=path, options=options)
        return driver


    driver_mapping = {
        'geckodriver': firefox_driver,
        'chromedriver': chrome_driver,
        'chromium-driver': chrome_driver
    }

    for driver in driver_mapping.keys():
        found = which(driver)
        if found is not None:
            return driver_mapping.get(driver, None)(path)

    raise ModuleNotFoundError("Chrome/Chromium/FireFox Webdriver not found.")


class RegexDict(OrderedDict):
    """ Ordered dictionary that supports querying with regex.

    References
    ----------
    Adapted from
    https://stackoverflow.com/questions/21024822/python-accessing-dictionary-with-wildcards.
    """
    def get_matching(self, *regexes):
        """ Query the dictionary using a regex. """
        matches = []
        for regex in regexes:
            matches += [self[key] for key in self if re.fullmatch(regex, key)]

        if len(matches) == 0:
            raise ValueError("No rule matches your regex: {}.".format(regexes))

        return matches


def str2bool(v):
    """ Convert string to a boolean value.
    References
    ----------
    https://stackoverflow.com/questions/715417/converting-from-a-string-to-boolean-in-python/715468#715468
    """
    return str(v).lower() in ("yes", "true", "t", "1")


def maybe_mkdir(dirpath):
    """ Create all parent folders if needed. """
    try:
        os.makedirs(dirpath)
    except FileExistsError:
        pass

    return dirpath


@contextlib.contextmanager
def make_temp_directory(suffix='', prefix='tmp', dir=None):
    """ Create temporary folder to used in a with statement. """
    temp_dir = tempfile.mkdtemp(suffix, prefix, dir)
    try:
        yield temp_dir
    finally:
        if not str2bool(os.environ.get("TEXTWORLD_DEBUG", False)):
            shutil.rmtree(temp_dir)


def uniquify(seq):
    """ Order preserving uniquify.

    References
    ----------
    Made by Dave Kirby
    https://www.peterbe.com/plog/uniqifiers-benchmark
    """
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]


def encode_seeds(seeds):
    """ Generate UID from a list of seeds.
    """
    from hashids import Hashids
    hashids = Hashids(salt="TextWorld")
    return hashids.encode(*seeds)


def save_graph_to_svg(G, labels, filename, backward=False):
    """ Generate a figure of a networkx's graph object and save it. """
    import networkx as nx
    if backward:
        G = G.reverse()

    pydot_graph = nx.drawing.nx_pydot.to_pydot(G)
    pydot_graph.set_rankdir("LR")
    pydot_graph.set_nodesep(0.5)
    for n in pydot_graph.get_nodes():
        name = n.get_name()
        n.set_style("rounded")
        n.set_style("filled")
        n.set_shape("box")
        n.set_fillcolor("#E5E5E5")
        n.set_width(0)
        n.set_height(0)
        n.set_label(labels[name])

    pydot_graph.write_svg(filename)


#: Global random generator.
g_rng = RandomGenerator()
