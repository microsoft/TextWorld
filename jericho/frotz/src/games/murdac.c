#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Monsters of Murdac: http://ifdb.tads.org/viewgame?id=q36lh5np0q9nak28

char** murdac_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* murdac_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int murdac_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int murdac_game_over() {
  char *death_text = "****  You have died  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int murdac_get_self_object_num() {
  return 7;
}

int murdac_get_moves() {
  return (((short) zmp[6372]) << 8) | zmp[6373]; //6375,6383
}

int murdac_get_score() {
  return zmp[6357];
}

int murdac_max_score() {
  return 250;
}

int murdac_get_num_world_objs() {
  return 126;
}

int murdac_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int murdac_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 1)
    return 1;
  return 0;
}

int murdac_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 1)
    return 1;
  return 0;
}
