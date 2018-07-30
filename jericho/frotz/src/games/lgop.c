// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Leather Goddesses of Phobos: http://ifdb.tads.org/viewgame?id=3p9fdt4fxr2goctw

char** lgop_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* lgop_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '\n');
  if (pch != NULL) {
    return pch+1;
  }
  return obs;
}

int lgop_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int lgop_game_over() {
  char *death_text = "(Type RESTART, RESTORE, or QUIT)";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int lgop_get_self_object_num() {
  return 199;
}

int lgop_get_moves() {
  return (((short) zmp[8235]) << 8) | zmp[8236];
}

int lgop_get_score() {
  return zmp[8234];
}

int lgop_max_score() {
  return 316;
}

int lgop_get_num_world_objs() {
  return 227;
}

int lgop_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int lgop_ignore_attr_diff(zword obj_num, zword attr_idx) {
  return 0;
}

int lgop_ignore_attr_clr(zword obj_num, zword attr_idx) {
  return 0;
}
