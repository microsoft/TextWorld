// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Raising the Flag on Mount Yomomma - http://ifdb.tads.org/viewgame?id=1iqmpkn009h9gbug

char** yomomma_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* yomomma_clean_observation(char* obs) {
  char* pch;
  pch = strstr(obs, ">  ");
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int yomomma_victory() {
  char *victory_text = "*** You have won ***";
  if (strstr(world, victory_text)) {
    return 1;
  }
  return 0;
}

int yomomma_game_over() {
  char *death_text = "*** You have died ***";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int yomomma_get_self_object_num() {
  return 59;
}

int yomomma_get_moves() {
  return (((short) zmp[15532]) << 8) | zmp[15533];
}

int yomomma_get_score() {
  return zmp[15531];
}

int yomomma_max_score() {
  return 35;
}

int yomomma_get_num_world_objs() {
  return 139;
}

int yomomma_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int yomomma_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 30)
    return 1;
  return 0;
}

int yomomma_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 30)
    return 1;
  return 0;
}
