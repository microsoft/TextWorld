import re
import string
import numpy as np

import gym


class VocabularyHasDuplicateTokens(ValueError):
    pass


class Char(gym.spaces.MultiDiscrete):
    """ Character observation/action space

    This space consists of a series of `gym.spaces.Discrete` objects all with
    the same parameters. Each `gym.spaces.Discrete` can take integer values
    between 0 and len(self.vocab).

    Notes
    -----
    The following special token will be prepended (if needed) to the vocabulary:
    # : Padding token
    """

    def __init__(self, max_length, vocab=None, extra_vocab=[]):
        """
        Parameters
        ----------
        max_length : int
            Maximum number of characters in a text.
        vocab : list of char, optional
            Vocabulary defining this space. It shouldn't contain any
            duplicate characters. If not provided, the vocabulary will consists
            in characters [a-z0-9], punctuations [" ", "-", "'"] and padding '#'.
        extra_vocab : list of char, optional
            Additional tokens to add to the vocabulary.
        """
        if vocab is None:
            vocab = list(string.ascii_lowercase + string.digits)
            vocab += [" ", "-", "'"]

        vocab += extra_vocab

        if len(vocab) != len(set(vocab)):
            raise VocabularyHasDuplicateTokens()

        self.max_length = max_length
        self.PAD = "#"
        special_tokens = [self.PAD]
        self.vocab = [t for t in special_tokens if t not in vocab]
        self.vocab += list(vocab)
        self.vocab_set = set(self.vocab)  # For faster lookup.
        self.vocab_size = len(self.vocab)
        self.id2c = {i: c for i, c in enumerate(self.vocab)}
        self.c2id = {c: i for i, c in self.id2c.items()}
        self.PAD_id = self.c2id[self.PAD]
        super().__init__([len(self.vocab) - 1] * self.max_length)
        self.dtype = np.int64  # Overwrite Gym's dtype=int8.

    def filter_unknown(self, text):
        """ Strip out all characters not in the vocabulary. """
        return "".join(c for c in text if c in self.vocab_set)

    def tokenize(self, text, padding=False):
        """ Tokenize characters found in the vocabulary.

        Note: text will be padded up to `self.max_length`.
        """
        text = self.filter_unknown(text.lower())
        ids = [self.c2id[c] for c in text]

        # Add padding.
        if padding:
            nb_pads = self.max_length - len(ids)
            msg = "Provided `max_length` was not large enough ({} chars).".format(len(ids))
            assert nb_pads >= 0, msg
            ids += [self.PAD_id] * nb_pads

        return np.array(ids)

    def __repr__(self):
        return "Character({})".format(self.max_length)


class Word(gym.spaces.MultiDiscrete):
    """ Word observation/action space

    This space consists of a series of `gym.spaces.Discrete` objects all with
    the same parameters. Each `gym.spaces.Discrete` can take integer values
    between 0 and `len(self.vocab)`.

    Notes
    -----
    The following special tokens will be prepended (if needed) to the vocabulary:
    <PAD> : Padding
    <UNK> : Unknown word
    <S>   : Beginning of sentence
    </S>  : End of sentence
    """

    def __init__(self, max_length, vocab):
        """
        Parameters
        ----------
        max_length : int
            Maximum number of words in a text.
        vocab : list of strings
            Vocabulary defining this space. It shouldn't contain any
            duplicate words.
        """
        if len(vocab) != len(set(vocab)):
            raise VocabularyHasDuplicateTokens()

        self.max_length = max_length
        self.PAD = "<PAD>"
        self.UNK = "<UNK>"
        self.BOS = "<S>"
        self.EOS = "</S>"
        self.SEP = "<|>"
        special_tokens = [self.PAD, self.UNK, self.EOS, self.BOS, self.SEP]
        self.vocab = [w for w in special_tokens if w not in vocab]
        self.vocab += list(vocab)
        self.vocab_set = set(self.vocab)  # For faster lookup.
        self.vocab_size = len(self.vocab)
        self.id2w = {i: w for i, w in enumerate(self.vocab)}
        self.w2id = {w: i for i, w in self.id2w.items()}
        self.PAD_id = self.w2id[self.PAD]
        self.UNK_id = self.w2id[self.UNK]
        self.BOS_id = self.w2id[self.BOS]
        self.EOS_id = self.w2id[self.EOS]
        self.SEP_id = self.w2id[self.SEP]
        super().__init__([len(self.vocab) - 1] * self.max_length)
        self.dtype = np.int64  # Overwrite Gym's dtype=int8.

    def tokenize(self, text, padding=False):
        """ Tokenize words found in the vocabulary.

        Note: text will be padded up to `self.max_length`.
        """
        text = text.lower()  # Work only with lowercase letters.
        # Find beginning and end of sentences.
        text = re.sub(".", " </S> <S> ", text)
        text = "<S> " + text + " </S>"

        # Strip out all non-alphabetic characters.
        text = re.sub("'", "", text)
        text = re.sub("[^a-z0-9 ]", " ", text)
        # TODO: convert numbers to text?

        # Get words ids and replace unknown words with <UNK>.
        words = text.split()
        ids = [self.w2id.get(w, self.UNK_id) for w in words]

        # Add padding.
        if padding:
            nb_pads = self.max_length - len(ids)
            msg = "Provided `max_length` was not large enough ({} words).".format(len(ids))
            assert nb_pads >= 0, msg
            ids += [self.PAD_id] * nb_pads

        return np.array(ids)

    def __repr__(self):
        return "Word(L={}, V={})".format(self.max_length, self.vocab_size)
