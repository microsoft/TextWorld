// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Lost Pig: http://ifdb.tads.org/viewgame?id=mohwfk47yjzii14w

char** lostpig_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* lostpig_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int lostpig_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int lostpig_game_over() {
  char *death_text = "****  You have died  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int lostpig_get_self_object_num() {
  return 87;
}

int lostpig_get_moves() {
  return (((short) zmp[39582]) << 8) | zmp[39583]; // 39607
}

int lostpig_get_score() {
  return zmp[39581]; //39617, 39619
}

int lostpig_max_score() {
  return 7;
}

int lostpig_get_num_world_objs() {
  return 535;
}

int lostpig_ignore_moved_obj(zword obj_num, zword dest_num) {
  if (obj_num != 87 && dest_num != 87)
    return 1;
  return 0;
}

int lostpig_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 14 || attr_idx == 15)
    return 1;
  return 0;
}

int lostpig_ignore_attr_clr(zword obj_num, zword attr_idx) {
  /* if (attr_idx == 14 || attr_idx == 15) */
  return 1;
  /* return 0; */
}
