// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Party Foul - http://ifdb.tads.org/viewgame?id=cqwq699i9qiqdju

const char *partyfoul_intro[] = { "\n",
                                  "no\n" };

char** partyfoul_intro_actions(int *n) {
  *n = 2;
  return partyfoul_intro;
}

char* partyfoul_clean_observation(char* obs) {
  char* pch;
  pch = strstr(obs, ">  ");
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int partyfoul_victory() {
  char *victory_text = "*** You have won ***";
  if (strstr(world, victory_text)) {
    return 1;
  }
  return 0;
}

int partyfoul_game_over() {
  char *death_text = "*** You have died ***";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int partyfoul_get_self_object_num() {
  return 48;
}

int partyfoul_get_moves() {
  return (((short) zmp[15810]) << 8) | zmp[15811];
}

int partyfoul_get_score() {
  if (partyfoul_victory()) {
    return 1;
  }
  return 0;
}

int partyfoul_max_score() {
  return 1;
}

int partyfoul_get_num_world_objs() {
  return 141;
}

int partyfoul_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int partyfoul_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 35 || attr_idx == 29)
    return 1;
  return 0;
}

int partyfoul_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 35)
    return 1;
  return 0;
}
