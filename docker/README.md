# MS TextWorld Dockerfile
Dockerfile for running MS Text World, the open-source engine for generating and simulating text games by Microsoft.

For detailed information on this project see: https://github.com/microsoft/textworld

Instructions:

```
docker pull berndverst/mstextworld
docker run -it --rm berndverst/mstextworld
```

### Customize a game 

All values are integers:
- $WORLDSIZE controls the number of rooms in the world
- $NBCONTROLS controls the number of objects that can be interacted with (excluding doors)
- $QUESTLENGTH controls the minimum number of commands that is required to type in order to win the game.
- $SEED defines the seed for the random generated game

Run with:
`docker run -e SEED=$SEED-it -e WORLDSIZE=$WORLDSIZE -e NBCONTROLS=$NBCONTROLS -e QUESTLENGTH=$QUESTLENGTH --rm berndverst/mstextworld`

![TextWorld Image](https://github.com/berndverst/mstextworld/raw/master/textworldimage.png)
