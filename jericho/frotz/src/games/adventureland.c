// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Adventureland: http://ifdb.tads.org/viewgame?id=dy4ok8sdlut6ddj7

char** adventureland_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* adventureland_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int adventureland_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int adventureland_game_over() {
  char *death_text = "*** You have died ***";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int adventureland_get_self_object_num() {
  return 20;
}

int adventureland_get_moves() {
  return (((short) zmp[5320]) << 8) | zmp[5321]; // Also 5331
}

int adventureland_get_score() {
  return zmp[5319]; // Also 5329, 5345
}

int adventureland_max_score() {
  return 100;
}

int adventureland_get_num_world_objs() {
  return 106;
}

int adventureland_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int adventureland_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 2 || attr_idx == 25)
    return 1;
  return 0;
}

int adventureland_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 2 || attr_idx == 25)
    return 1;
  return 0;
}
