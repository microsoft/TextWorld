// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Hitchhiker's Guide to the Galaxy

char** hhgg_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* hhgg_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '\n');
  if (pch != NULL) {
    return pch+1;
  }
  return obs;
}

int hhgg_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int hhgg_game_over() {
  char *death_text = "(Type RESTART, RESTORE, or QUIT)";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int hhgg_get_self_object_num() {
  return 31;
}

int hhgg_get_moves() {
  return (((short) zmp[7912]) << 8) | zmp[7913];
}

int hhgg_get_score() {
  return zmp[7911];
}

int hhgg_max_score() {
  return 400;
}

int hhgg_get_num_world_objs() {
  return 220;
}

int hhgg_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int hhgg_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (obj_num == 31 && attr_idx == 17)
    return 1;
  return 0;
}

int hhgg_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (obj_num == 31 && attr_idx == 17)
    return 1;
  return 0;
}
