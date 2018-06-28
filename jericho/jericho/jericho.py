# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import os
import numpy as np
from ctypes import *
from numpy.ctypeslib import as_ctypes

frotz_lib = cdll.LoadLibrary(os.path.join(os.path.dirname(__file__),
                                          'libfrotz.so'))

class ZObject(Structure):
    """ A Z-Machine Object contains the following fields: More info:
    http://inform-fiction.org/zmachine/standards/z1point1/sect12.html

    num: Object number
    name: Short object name
    parent: Object number of parent
    sibling: Object number of sibling
    child: Object number of child
    attr: 32-bit array of object attributes
    properties: list of object properties

    """
    _fields_ = [("num",        c_int),
                ("_name",      c_char*64),
                ("parent",     c_int),
                ("sibling",    c_int),
                ("child",      c_int),
                ("_attr",      c_byte*4),
                ("properties", c_int*16)]

    def __init__(self):
        self.num = -1

    def __str__(self):
        return "Obj{}: {} Parent{} Sibling{} Child{} Attributes {} Properties {}"\
            .format(self.num, self.name, self.parent, self.sibling, self.child,
                    np.nonzero(self.attr)[0].tolist(), list(self.properties))

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        # Equality check doesn't compare siblings and children. This
        # makes comparison among object trees more flexible.
        if isinstance(self, other.__class__):
            return self.num   == other.num      and \
                self.name     == other.name     and \
                self.parent   == other.parent   and \
                self._attr[0] == other._attr[0] and \
                self._attr[1] == other._attr[1] and \
                self._attr[2] == other._attr[2] and \
                self._attr[3] == other._attr[3]
        return False

    def __hash__(self):
        return hash(str(self))

    @property
    def name(self):
        return self._name.decode('cp1252')

    @property
    def attr(self):
        return np.unpackbits(np.array(self._attr, dtype=np.uint8))


frotz_lib.setup.argtypes = [c_char_p, c_int]
frotz_lib.setup.restype = c_char_p
frotz_lib.shutdown.argtypes = []
frotz_lib.shutdown.restype = None
frotz_lib.step.argtypes = [c_char_p]
frotz_lib.step.restype = c_char_p
frotz_lib.save.argtypes = [c_char_p]
frotz_lib.save.restype = int
frotz_lib.restore.argtypes = [c_char_p]
frotz_lib.restore.restype = int
frotz_lib.get_object.argtypes = [c_void_p, c_int]
frotz_lib.get_object.restype = None
frotz_lib.get_num_world_objs.argtypes = []
frotz_lib.get_num_world_objs.restype = int
frotz_lib.get_world_objects.argtypes = [POINTER(ZObject)]
frotz_lib.get_world_objects.restype = None
frotz_lib.get_self_object_num.argtypes = []
frotz_lib.get_self_object_num.restype = int
frotz_lib.get_moves.argtypes = []
frotz_lib.get_moves.restype = int
frotz_lib.get_score.argtypes = []
frotz_lib.get_score.restype = int
frotz_lib.get_max_score.argtypes = []
frotz_lib.get_max_score.restype = int
frotz_lib.teleport_obj.argtypes = [c_int, c_int]
frotz_lib.teleport_obj.restype = None
frotz_lib.teleport_tree.argtypes = [c_int, c_int]
frotz_lib.teleport_tree.restype = None
frotz_lib.save_str.argtypes = [c_void_p]
frotz_lib.save_str.restype = int
frotz_lib.restore_str.argtypes = [c_void_p]
frotz_lib.restore_str.restype = int
frotz_lib.world_changed.argtypes = []
frotz_lib.world_changed.restype = int
frotz_lib.get_world_diff.argtypes = [c_void_p, c_void_p]
frotz_lib.get_world_diff.restype = None
frotz_lib.get_cleaned_world_diff.argtypes = [c_void_p, c_void_p]
frotz_lib.get_cleaned_world_diff.restype = None
frotz_lib.game_over.argtypes = []
frotz_lib.game_over.restype = int
frotz_lib.victory.argtypes = []
frotz_lib.victory.restype = int
frotz_lib.test.argtypes = []
frotz_lib.test.restype = None
frotz_lib.getRAMSize.argtypes = []
frotz_lib.getRAMSize.restype = int
frotz_lib.getRAM.argtypes = [c_void_p]
frotz_lib.getRAM.restype = None
frotz_lib.print_dictionary.argtypes = [c_char_p]
frotz_lib.print_dictionary.restype = None
frotz_lib.print_verbs.argtypes = [c_char_p]
frotz_lib.print_verbs.restype = None
frotz_lib.disassemble.argtypes = [c_char_p]
frotz_lib.disassemble.restype = None
frotz_lib.is_supported.argtypes = [c_char_p]
frotz_lib.is_supported.restype = int


class FrotzEnv():
    """ FrotzEnv is a fast interface to the ZMachine. """

    def __init__(self, story_file, seed=-1):
        assert os.path.exists(story_file), "Invalid story file: %s" % story_file
        if not self.is_fully_supported(story_file):
            print("[ERROR] Unsupported Rom \"{}\": Score, move, change detection disabled.".format(story_file))

        self.story_file = story_file.encode('utf-8')
        self.seed = seed
        frotz_lib.setup(self.story_file, self.seed)
        self.player_obj_num = frotz_lib.get_self_object_num()

    def print_dictionary(self):
        # Prints the dictionary used by the game's parser
        frotz_lib.print_dictionary(self.story_file)

    def print_verbs(self):
        # Prints the verbs used by the game's parser
        frotz_lib.print_verbs(self.story_file)

    def disassemble_game(self):
        # Prints the routines and strings used by the game
        frotz_lib.disassemble(self.story_file)

    def victory(self):
        # Returns true if the last step caused the game to be won
        return frotz_lib.victory() > 0

    def game_over(self):
        # Returns true if the last step caused the game to be over (lost)
        return frotz_lib.game_over() > 0

    def step(self, action):
        # Takes an action and returns the next state, total score
        next_state = frotz_lib.step((action+'\n').encode('utf-8')).decode('cp1252')
        return next_state, frotz_lib.get_score(), (self.game_over() or self.victory()),\
            {'moves':self.get_moves()}

    def world_changed(self):
        # Returns true if the last action caused a change in the world
        return frotz_lib.world_changed() > 0

    def close(self):
        frotz_lib.shutdown()

    def reset(self):
        # Resets the game and returns the initial state
        self.close()
        return frotz_lib.setup(self.story_file, self.seed).decode('cp1252')

    def save(self, fname):
        # Save the game to file. Prefer save_str() for efficiency.
        success = frotz_lib.save(fname.encode('utf-8'))
        assert success > 0, "ERROR: Failed to Save!"

    def load(self, fname):
        # Restore the game from a save file. Prefer load_str() for efficiency.
        success = frotz_lib.restore(fname.encode('utf-8'))
        assert success > 0, "ERROR: Failed to Restore!"

    def save_str(self):
        # Saves the game and returns a string containing the saved game
        buff = np.zeros(3200, dtype=np.uint8)
        success = frotz_lib.save_str(as_ctypes(buff))
        assert success > 0, "ERROR: Failed to Save!"
        return buff

    def load_str(self, buff):
        # Load the game from a string buffer given by save_str()
        success = frotz_lib.restore_str(as_ctypes(buff))
        assert success > 0, "ERROR: Failed to Restore!"

    def get_player_location(self):
        # Returns the object corresponding to the location of the player in the world
        parent = self.get_player_object().parent
        return self.get_object(parent)

    def get_object(self, obj_num):
        # Returns an ZObject with the corresponding number or None if
        # the object doesn't exist.
        obj = ZObject()
        frotz_lib.get_object(byref(obj), obj_num)
        if obj.num < 0:
            return None
        return obj

    def get_world_objects(self):
        # Returns an array containing all the objects in the world
        n_objs = frotz_lib.get_num_world_objs()
        objs = (ZObject * n_objs)()
        frotz_lib.get_world_objects(objs)
        return objs

    def get_player_object(self):
        # Returns the object corresponding to the player
        return self.get_object(self.player_obj_num)

    def get_inventory(self):
        # Returns a list of objects in the player's posession.
        inventory = []
        item_nb = self.get_player_object().child
        while item_nb > 0:
            item = self.get_object(item_nb)
            if not item:
                break
            inventory.append(item)
            item_nb = item.sibling
        return inventory

    def get_moves(self):
        # Returns the number of moves taken
        return frotz_lib.get_moves()

    def get_score(self):
        # Returns the score for the current game
        return frotz_lib.get_score()

    def get_max_score(self):
        # Returns the maximum possible score for the game
        return frotz_lib.get_max_score()

    def get_world_diff(self):
        # Gets the difference in world objects, set attributes, and
        # cleared attributes for the last timestep.
        # Returns three tuples of (obj_nb, dest):
        #   moved_objs:    Tuple of moved objects (obj_nb, obj_destination)
        #   set_attrs:     Tuple of objects with attrs set: (obj_nb, attr_nb)
        #   cleared_attrs: Tuple of objects with attrs cleared: (obj_nb, attr_nb)
        objs = np.zeros(48, dtype=np.uint16)
        dest = np.zeros(48, dtype=np.uint16)
        frotz_lib.get_cleaned_world_diff(as_ctypes(objs), as_ctypes(dest))
        # First 16 spots allocated for objects that have moved
        moved_objs = []
        for i in range(16):
            if objs[i] == 0 or dest[i] == 0:
                break
            moved_objs.append((objs[i], dest[i]))
        # Second 16 spots allocated for objects that have had attrs set
        set_attrs = []
        for i in range(16, 32):
            if objs[i] == 0 or dest[i] == 0:
                break
            set_attrs.append((objs[i], dest[i]))
        # Third 16 spots allocated for objects that have had attrs cleared
        cleared_attrs = []
        for i in range(32, 48):
            if objs[i] == 0 or dest[i] == 0:
                break
            cleared_attrs.append((objs[i], dest[i]))
        return (tuple(moved_objs), tuple(set_attrs), tuple(cleared_attrs))

    def teleport_obj(self, obj, dest):
        # Teleport an object to a destination. obj/dest may either be
        # a ZObject or a int corresponding to the object number.
        if isinstance(obj, ZObject):
            obj = obj.num
        if isinstance(dest, ZObject):
            dest = dest.num
        if type(obj) is not int:
            raise TypeError("obj must be an int or ZObject")
        if type(dest) is not int:
            raise TypeError("dest must be an int or ZObject")
        frotz_lib.teleport_obj(obj, dest)

    def teleport_player(self, dest):
        # Teleports the player to a given destination, where dest is
        # either an int corresponding to an object location or the
        # ZObject of the location. It is necessary to take an extra
        # step before the description of the new location loads.
        if type(dest) is int:
            self.teleport_obj(self.player_obj_num, dest)
        elif isinstance(dest, ZObject):
            self.teleport_obj(self.player_obj_num, dest.num)
        else:
            raise TypeError("dest must be an int or ZObject")

    def teleport_obj_to_player(self, obj):
        # Teleports an object to the player. obj may be a ZObject or int.
        if type(obj) is int:
            self.teleport_obj(obj, self.player_obj_num)
        elif isinstance(dest, ZObject):
            self.teleport_obj(obj.num, self.player_obj_num)
        else:
            raise TypeError("obj must be an int or ZObject")

    def teleport_tree(self, obj, dest):
        # Same as teleport_obj except it teleports all of obj's
        # children and siblings (e.g. entire object tree) to become
        # last child of dest
        if isinstance(obj, ZObject):
            obj = obj.num
        if isinstance(dest, ZObject):
            dest = dest.num
        if type(obj) is not int:
            raise TypeError("obj must be an int or ZObject")
        if type(dest) is not int:
            raise TypeError("dest must be an int or ZObject")
        frotz_lib.teleport_tree(obj, dest)

    def test(self):
        # Convenience function for testing new frotz_lib functionality
        frotz_lib.test()

    def get_ram(self):
        # Returns the contents of the ZMachine's RAM
        ram_size = frotz_lib.getRAMSize()
        ram = np.zeros(ram_size, dtype=np.uint8)
        frotz_lib.getRAM(as_ctypes(ram))
        return ram

    @classmethod
    def is_fully_supported(cls, story_file):
        return bool(frotz_lib.is_supported(story_file.encode('utf-8')))
