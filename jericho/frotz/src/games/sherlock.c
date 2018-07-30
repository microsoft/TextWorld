// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Sherlock: http://ifdb.tads.org/viewgame?id=ug3qu521hze8bsvz

char** sherlock_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* sherlock_clean_observation(char* obs) {
  return obs;
}

int sherlock_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int sherlock_game_over() {
  char *death_text = "****  You have died  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int sherlock_get_self_object_num() {
  return 232;
}

int sherlock_get_moves() {
  return (((short) zmp[1002]) << 8) | zmp[1003];
}

int sherlock_get_score() {
  return zmp[739]; //993
}

int sherlock_max_score() {
  return 100;
}

int sherlock_get_num_world_objs() {
  return 314;
}

int sherlock_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int sherlock_ignore_attr_diff(zword obj_num, zword attr_idx) {
  return 0;
}

int sherlock_ignore_attr_clr(zword obj_num, zword attr_idx) {
  return 0;
}
