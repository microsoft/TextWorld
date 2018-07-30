// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Ballyhoo: http://ifdb.tads.org/viewgame?id=b0i6bx7g4rkrekgg

char** ballyhoo_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* ballyhoo_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '\n');
  if (pch != NULL) {
    return pch+1;
  }
  return obs;
}

int ballyhoo_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int ballyhoo_game_over() {
  char *death_text = "(Type RESTART, RESTORE, or QUIT)";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int ballyhoo_get_self_object_num() {
  return 211;
}

int ballyhoo_get_moves() {
  return (((short) zmp[8496]) << 8) | zmp[8497];
}

int ballyhoo_get_score() {
  return zmp[8495];
}

int ballyhoo_max_score() {
  return 200;
}

int ballyhoo_get_num_world_objs() {
  return 235;
}

int ballyhoo_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int ballyhoo_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (obj_num == 211 && attr_idx == 13)
    return 1;
  if (attr_idx == 30)
    return 1;
  return 0;
}

int ballyhoo_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (obj_num == 211 && attr_idx == 13)
    return 1;
  if (attr_idx == 20)
    return 1;
  return 0;
}
