// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// The Moonlit Tower - http://ifdb.tads.org/viewgame?id=10387w68qlwehbyq

char** moonlit_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* moonlit_clean_observation(char* obs) {
  char* pch;
  pch = strstr(obs, ">  ");
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int moonlit_victory() {
  char *victory_text = "*** You have won ***";
  if (strstr(world, victory_text)) {
    return 1;
  }
  return 0;
}

int moonlit_game_over() {
  char *death_text = "*** You have died ***";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int moonlit_get_self_object_num() {
  return 20;
}

int moonlit_get_moves() {
  return (((short) zmp[10551]) << 8) | zmp[10552];
}

int moonlit_get_score() {
  if (moonlit_victory()) {
    return 1;
  }
  return 0;
}

int moonlit_max_score() {
  return 1;
}

int moonlit_get_num_world_objs() {
  return 198;
}

int moonlit_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int moonlit_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 25 || attr_idx == 31)
    return 1;
  return 0;
}

int moonlit_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 25 || attr_idx == 31)
    return 1;
  return 0;
}
