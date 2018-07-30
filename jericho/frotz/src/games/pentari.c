// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Pentari: http://ifdb.tads.org/viewgame?id=llchvog0ukwrphih

char** pentari_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* pentari_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int pentari_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int pentari_game_over() {
  char *death_text = "****  You have died  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int pentari_get_self_object_num() {
  return 20;
}

int pentari_get_moves() {
  return (((short) zmp[4939]) << 8) | zmp[4940]; //4952
}

int pentari_get_score() {
  return zmp[4938];//4962, 4964
}

int pentari_max_score() {
  return 70;
}

int pentari_get_num_world_objs() {
  return 104;
}

int pentari_ignore_moved_obj(zword obj_num, zword dest_num) {
  if (obj_num == 103)
    return 1;
  return 0;
}

int pentari_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}

int pentari_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}
