from textworld.gym.spaces.text_spaces import Word


def test_word_space():
    vocab = ["word1", "word2", "word3"]
    space = Word(max_length=5, vocab=vocab)

    out = space.tokenize("This is word2!")
    expected = [space.BOS_id, space.UNK_id, space.UNK_id, space.w2id["word2"], space.EOS_id]
    assert list(out) == expected
