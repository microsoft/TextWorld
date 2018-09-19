// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// 9:05 - http://ifdb.tads.org/viewgame?id=qzftg3j8nh5f34i2

char** nine05_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* nine05_clean_observation(char* obs) {
  char* pch;
  pch = strstr(obs, ">  ");
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int nine05_victory() {
  char *death_text = "*** You have left Las Mesas ***";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int nine05_game_over() {
  char *death_text = "*** You have died ***";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int nine05_get_self_object_num() {
  return 28;
}

int nine05_get_moves() {
  return (((short) zmp[4295]) << 8) | zmp[4296];
}

int nine05_get_score() {
  if (nine05_victory()) {
    return 1;
  }
  return 0;
}

int nine05_max_score() {
  return 1;
}

int nine05_get_num_world_objs() {
  return 84;
}

int nine05_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int nine05_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}

int nine05_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}
