// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Detective: http://ifdb.tads.org/viewgame?id=1po9rgq2xssupefw

char** detective_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* detective_clean_observation(char* obs) {
  char* pch;
  pch = strstr(obs, ">  ");
  if (pch != NULL) {
    *(pch-1) = '\0';
  }
  return obs;
}

int detective_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int detective_game_over() {
  char *death_text = "*** You have died ***";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int detective_get_self_object_num() {
  return 90;
}

int detective_get_moves() {
  return (((short) zmp[6777]) << 8) | zmp[6778]; // 6792
}

int detective_get_score() {
  return zmp[6802]; // Also 6776, 6804
}

int detective_max_score() {
  return 360;
}

int detective_get_num_world_objs() {
  return 101;
}

int detective_ignore_moved_obj(zword obj_num, zword dest_num) {
  // Detective has an issue where if you select invalid movement
  // actions any location, it re-moves the player object to that
  // location.
  return 0;
}

int detective_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 26)
    return 1;
  return 0;
}

int detective_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 26)
    return 1;
  return 0;
}
