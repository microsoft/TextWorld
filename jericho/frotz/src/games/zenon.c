// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Escape from the Starship Zenon: http://ifdb.tads.org/viewgame?id=rw7zv98mifbr3335

char** zenon_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* zenon_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int zenon_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int zenon_game_over() {
  char *death_text = "****  You have died  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int zenon_get_self_object_num() {
  return 20;
}

int zenon_get_moves() {
  return (((short) zmp[3743]) << 8) | zmp[3744]; //3756
}

int zenon_get_score() {
  return zmp[3742]; //3766, 3768
}

int zenon_max_score() {
  return 350;
}

int zenon_get_num_world_objs() {
  return 74;
}

int zenon_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int zenon_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}

int zenon_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}
