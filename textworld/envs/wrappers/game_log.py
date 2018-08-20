import json

class GameLog:
    def __init__(self):
        """
        GameLog object. Allows your to load and save previous game logs.
        """
        self._logs = [[]]
        self._current_game = self._logs[-1]
        self._filename = ''

    def __getitem__(self, idx):
        assert idx <= len(self._logs)
        return self._logs[idx]

    def __len__(self):
        return len(self._logs)

    @property
    def current_game(self):
        return self._current_game

    @property
    def logs(self):
        return self._logs

    def new_game(self):
        self._logs.append([])
        self._current_game = self._logs[-1]
        return self._current_game

    def save(self, filename):
        self._filename = filename
        try:
            with open(filename, 'w') as outfile:
                json.dump(self._logs, outfile)
        except TypeError as e:
            raise TypeError('Log not serializable')

    def load(self, filename):
        self._filename = filename
        with open(filename) as f:
            self._logs= json.load(f)