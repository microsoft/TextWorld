// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// The Enterprise Incidents: http://ifdb.tads.org/viewgame?id=ld1f3t5epeagilfz

char** enter_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* enter_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int enter_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int enter_game_over() {
  char *death_text = "****  You have died  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int enter_get_self_object_num() {
  return 20;
}

int enter_get_moves() {
  return (((short) zmp[11070]) << 8) | zmp[11071];
}

int enter_get_score() {
  return zmp[11069]; // 11095
}

int enter_max_score() {
  return 20;
}

int enter_get_num_world_objs() {
  return 183;
}

int enter_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int enter_ignore_attr_diff(zword obj_num, zword attr_idx) {
  return 0;
}

int enter_ignore_attr_clr(zword obj_num, zword attr_idx) {
  return 0;
}
