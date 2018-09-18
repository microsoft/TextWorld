#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Zork III: http://ifdb.tads.org/viewgame?id=vrsot1zgy1wfcdru

char** zork3_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* zork3_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '\n');
  if (pch != NULL) {
    return pch+1;
  }
  return obs;
}

int zork3_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int zork3_game_over() {
  char *death_text = "****  You have died  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int zork3_get_self_object_num() {
  return 202;
}

int zork3_get_moves() {
  return (((short) zmp[7956]) << 8) | zmp[7957];
}

int zork3_get_score() {
  return zmp[7955];
}

int zork3_max_score() {
  return 7;
}

int zork3_get_num_world_objs() {
  return 219;
}

int zork3_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int zork3_ignore_attr_diff(zword obj_num, zword attr_idx) {
  return 0;
}

int zork3_ignore_attr_clr(zword obj_num, zword attr_idx) {
  return 0;
}
