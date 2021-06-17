# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

import re
import os
import glob
import shutil
import unittest
import tempfile
from os.path import join as pjoin
from subprocess import check_output

import textworld


class TestTwExtract(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = pjoin(tempfile.mkdtemp(prefix="test_tw_extract"), "")
        options = textworld.GameOptions()
        options.path = cls.tmpdir
        options.nb_rooms = 5
        options.nb_objects = 10
        options.quest_length = 5
        options.quest_breadth = 2
        options.seeds = 1234
        cls.game_file1, cls.game1 = textworld.make(options)
        options.seeds = 12345
        options.file_ext = ".z8"
        cls.game_file2, cls.game2 = textworld.make(options)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)

    def tearDown(self):
        for f in glob.glob(pjoin(self.tmpdir, "*.txt")):
            os.remove(f)

    def test_extract_vocab(self):
        outfile = pjoin(self.tmpdir, "vocab.txt")
        command = ["tw-extract", "vocab", self.game_file1, self.game_file2, "--output", outfile]
        stdout = check_output(command).decode()
        assert os.path.isfile(outfile)
        nb_words = len(open(outfile).readlines())
        assert "Found {}".format(nb_words) in stdout

    def test_extract_vocab_theme(self):
        outfile = pjoin(self.tmpdir, "vocab.txt")
        command = ["tw-extract", "vocab", "--theme", "house", "--output", outfile]
        stdout = check_output(command).decode()
        assert os.path.isfile(outfile)
        assert int(re.findall(r"Found (\d+)", stdout)[0]) > 0

    def test_extract_entities(self):
        outfile = pjoin(self.tmpdir, "entities.txt")
        command = ["tw-extract", "entities", self.game_file1, "--output", outfile]
        stdout = check_output(command).decode()
        assert os.path.isfile(outfile)
        nb_entities = len(open(outfile).readlines())
        assert "Found {}".format(nb_entities) in stdout

    def test_extract_walkthroughs(self):
        outfile = pjoin(self.tmpdir, "walkthroughs.txt")
        command = ["tw-extract", "walkthroughs", self.game_file1, self.game_file2, "--output", outfile]
        stdout = check_output(command).decode()
        assert os.path.isfile(outfile)
        walkthrough1 = " > ".join(self.game1.metadata["walkthrough"])
        walkthrough2 = " > ".join(self.game2.metadata["walkthrough"])
        walkthroughs = open(outfile).readlines()
        assert len(walkthroughs) == 2
        assert walkthrough1 == walkthroughs[0].strip()
        assert walkthrough2 == walkthroughs[1].strip()
        assert "Found {}".format(2) in stdout

        # Simulate game without a walkthrough and the --force argument.
        gamefile = pjoin(self.tmpdir, "game_walkthrough_missing.json")
        game = self.game2.copy()
        del game.metadata["walkthrough"]
        game.save(gamefile)
        command = ["tw-extract", "walkthroughs", gamefile, "--output", outfile, "--force"]
        stdout = check_output(command).decode()
        assert os.path.isfile(outfile)
        walkthroughs = open(outfile).readlines()
        assert len(walkthroughs) == 1
        assert walkthrough2 == walkthroughs[0].strip()

    def test_extract_commands(self):
        outfile = pjoin(self.tmpdir, "commands.txt")
        command = ["tw-extract", "commands", self.game_file1, self.game_file2, "--output", outfile]
        stdout = check_output(command).decode()
        assert os.path.isfile(outfile)
        assert "Found" in stdout

        content = open(outfile).read()
        for name in self.game1.entity_names + self.game2.entity_names:
            assert name in content

        for verb in self.game1.verbs + self.game2.verbs:
            assert verb in content

        # Check inheritance of command templates, e.g., 'examine {t}' -> ['examine {o}', 'examine {k}', 'examine {f}']
        for obj_name in self.game1.objects_names:
            assert "examine {}".format(obj_name) in content
