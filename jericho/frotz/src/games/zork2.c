#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Zork II: http://ifdb.tads.org/viewgame?id=yzzm4puxyjakk8c4

char** zork2_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* zork2_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '\n');
  if (pch != NULL) {
    return pch+1;
  }
  return obs;
}

int zork2_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int zork2_game_over() {
  char *death_text = "****  You have died  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int zork2_get_self_object_num() {
  return 4;
}

int zork2_get_moves() {
  return (((short) zmp[8937]) << 8) | zmp[8938];
}

int zork2_get_score() {
  return (char) zmp[8936]; // 9110
}

int zork2_max_score() {
  return 400;
}

int zork2_get_num_world_objs() {
  return 250;
}

int zork2_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int zork2_ignore_attr_diff(zword obj_num, zword attr_idx) {
  return 0;
}

int zork2_ignore_attr_clr(zword obj_num, zword attr_idx) {
  return 0;
}
