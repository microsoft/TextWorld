// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// The Ludicorp Mystery: http://ifdb.tads.org/viewgame?id=r6g7pflngn3uxbam

char** ludicorp_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* ludicorp_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int ludicorp_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int ludicorp_game_over() {
  char *death_text = "*** You have died ***";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int ludicorp_get_self_object_num() {
  return 20;
}

int ludicorp_get_moves() {
  return (((short) zmp[24205]) << 8) | zmp[24206]; //24194
}

int ludicorp_get_score() {
  return zmp[24216]; //24192, 24218
}

int ludicorp_max_score() {
  return 150;
}

int ludicorp_get_num_world_objs() {
  return 392;
}

int ludicorp_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int ludicorp_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}

int ludicorp_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}
