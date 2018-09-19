// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Enchanter: http://ifdb.tads.org/viewgame?id=vu4xhul3abknifcr

char** enchanter_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* enchanter_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '\n');
  if (pch != NULL) {
    return pch+1;
  }
  return obs;
}

int enchanter_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int enchanter_game_over() {
  char *death_text = "****  You have died  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int enchanter_get_self_object_num() {
  return 55;
}

int enchanter_get_moves() {
  return (((short) zmp[8767]) << 8) | zmp[8768]; //9080
}

int enchanter_get_score() {
  return zmp[8766];
}

int enchanter_max_score() {
  return 400;
}

int enchanter_get_num_world_objs() {
  return 255;
}

int enchanter_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int enchanter_ignore_attr_diff(zword obj_num, zword attr_idx) {
  return 0;
}

int enchanter_ignore_attr_clr(zword obj_num, zword attr_idx) {
  return 0;
}
