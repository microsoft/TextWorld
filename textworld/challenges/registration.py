# Registry for all challenges in TextWorld.
CHALLENGES = {}


def register(name: str, desc: str,
             make: callable, add_arguments: callable) -> None:
    """ Register a new TextWorld challenge.

    Arguments:
        name:
            Name of the challenge (must be unique).
        desc:
            Bried description of the challenge (for `tw-make --help`).
        make:
            Function that makes a game for this challenge. The provided function
            should expect `(settings: Mapping[str, str], options: GameOptions)`.
        add_arguments:
            Function that should add the `argparse` arguments needed for the
            challenge. The provided function should expect a `argparse.ArgumentParser`
            object.

    Example:

        >>> from textworld.challenges import register
        >>> from textworld.challenges import coin_collector
        >>> def _add_arguments(parser):
                parser.add_argument("--level", required=True, type=int,
                                    help="The difficulty level.")
        >>> \
        >>> register(name="coin_collector",
        >>>          make=coin_collector.make,
        >>>          add_arguments=_add_arguments)
    """
    if name in CHALLENGES:
        raise ValueError("Challenge '{}' already registered.".format(name))

    CHALLENGES[name] = (desc, make, add_arguments)
