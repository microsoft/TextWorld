# Registry for all challenges in TextWorld.
CHALLENGES = {}


def register(name: str, make: callable, settings: str) -> None:
    """ Register a new TextWorld challenge.

    Arguments:
        name:
            Name of the challenge (must be unique).
        make:
            Function that makes a game for this challenge. That function
            should expect `(settings: str, options: GameOptions)`.
        settings:
            Expected settings for making a game for this challenge,
            e.g. 'tw-coin_collector-level[1-300]'.

    Example:

        >>> from textworld.challenges import register
        >>> from textworld.challenges import coin_collector
        >>> register(name="coin_collector",
        >>>          make=coin_collector.make,
        >>>          settings="level[1-300]")
    """
    if name in CHALLENGES:
        raise ValueError("Challenge '{}' already registered.".format(name))

    CHALLENGES[name] = (make, settings)
