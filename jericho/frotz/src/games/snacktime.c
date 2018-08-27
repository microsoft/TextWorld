// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Snack Time!: http://ifdb.tads.org/viewgame?id=yr3y8s9k8e40hl5q

char** snacktime_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* snacktime_clean_observation(char* obs) {
  char* pch;
  pch = strstr(obs, ">  ");
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int snacktime_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int snacktime_game_over() {
  char *death_text = "*** You have missed your chance to snack ***";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int snacktime_get_self_object_num() {
  return 44;
}

int snacktime_get_moves() {
  return (((short) zmp[9115]) << 8) | zmp[9116];
}

int snacktime_get_score() {
  return zmp[9114]; // 9122 9164 9166
}

int snacktime_max_score() {
  return 50;
}

int snacktime_get_num_world_objs() {
  return 84;
}

int snacktime_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int snacktime_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 30 || attr_idx == 34 || attr_idx == 21)
    return 1;
  return 0;
}

int snacktime_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 30)
    return 1;
  return 0;
}
