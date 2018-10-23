Known Issues
============

Inform 7
--------
Inform 7 command line tools don't support Windows Linux Subsystem (a.k.a Bash on Ubuntu on Windows).

FrotzEnvironment
----------------
This is known to cause some concurrency issues when commands are rapidely sent to the game's interpreter. An alternative is to use the :py:class:`JerichoEnvironment <textworld.envs.zmachine.jericho.JerichoEnvironment>` for Z-Machine games or :py:class:`JerichoEnvironment <textworld.envs.glulx.git_glulx_ml.GitGlulxEnvironment>` for games generated with TextWorld.
