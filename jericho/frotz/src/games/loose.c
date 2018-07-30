// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Mother Loose: http://ifdb.tads.org/viewgame?id=4wd3lyaxi4thp8qi

char** loose_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* loose_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int loose_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int loose_game_over() {
  char *death_text = "****  You have died  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int loose_get_self_object_num() {
  return 34;
}

int loose_get_moves() {
  return (((short) zmp[10392]) << 8) | zmp[10393]; // 10405
}

int loose_get_score() {
  return zmp[10391]; // 10415, 10417
}

int loose_max_score() {
  return 50;
}

int loose_get_num_world_objs() {
  return 178;
}

int loose_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int loose_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}

int loose_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}
