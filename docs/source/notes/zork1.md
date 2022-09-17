# Zork1
Some notes about Zork1.

## Stochasticity
Zork1 has some stochasticity in it:

  - the thief will wander randomly in the dungeon stealing stuff.
  - when attacking someone, you can miss (to confirm)

## Death
It seems that when you died, you get to continue playing but you lose 10 points (I think it is always 10). However, on your third death, the game ends.

Everytime, when you get to continue playing, you seem to respawn in the Forest (but maybe the location can change, to confirm).

## Technical details
When using the frotz interpreter, it is possible to provide the random seed as a parameter.
`./frotz/dfrotz -s 1 zork1.z5`

## Additional documentation
### Game file
The game file can be found here: [zork1.z5](https://archive.org/download/Zork1Release88Z-machineFile/zork1.z5).

### Map
![](http://oldsite.ironrealms.com/sites/default/files/zork-1-map.jpg)

### Walkthrough
Here is a walkthrough (not optimal) when the Frotz's seed is set to one: [zork1_walkthrough.txt](./zork1_walkthrough.txt).
