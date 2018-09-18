#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Deephome: A Telleen Adventure: http://ifdb.tads.org/viewgame?id=x85otcikhwp8bwup

char** deephome_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* deephome_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int deephome_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int deephome_game_over() {
  char *death_text = "Would you like to RESTART, RESTORE a saved game, give the FULL score for that game or QUIT?";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int deephome_get_self_object_num() {
  return 20;
}

int deephome_get_moves() {
  return (((short) zmp[12411]) << 8) | zmp[12412]; // 12424
}

int deephome_get_score() {
  return zmp[12434]; // 12436, 12410: 1.0
}

int deephome_max_score() {
  return 300;
}

int deephome_get_num_world_objs() {
  return 255;
}

int deephome_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int deephome_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 29)
    return 1;
  return 0;
}

int deephome_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 29)
    return 1;
  return 0;
}
