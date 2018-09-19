// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Infidel: http://ifdb.tads.org/viewgame?id=anu79a4n1jedg5mm

char** infidel_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* infidel_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '\n');
  if (pch != NULL) {
    return pch+1;
  }
  return obs;
}

int infidel_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int infidel_game_over() {
  char *death_text = "****  You have died  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int infidel_get_self_object_num() {
  return 223;
}

int infidel_get_moves() {
  return (((short) zmp[8913]) << 8) | zmp[8914]; //9014
}

int infidel_get_score() {
  return zmp[8912];
}

int infidel_max_score() {
  return 400;
}

int infidel_get_num_world_objs() {
  return 246;
}

int infidel_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int infidel_ignore_attr_diff(zword obj_num, zword attr_idx) {
  return 0;
}

int infidel_ignore_attr_clr(zword obj_num, zword attr_idx) {
  return 0;
}
