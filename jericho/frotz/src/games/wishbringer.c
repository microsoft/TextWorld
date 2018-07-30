// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Wishbringer: http://ifdb.tads.org/viewgame?id=z02joykzh66wfhcl

char** wishbringer_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* wishbringer_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '\n');
  if (pch != NULL) {
    return pch+1;
  }
  return obs;
}

int wishbringer_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int wishbringer_game_over() {
  char *death_text = "Type RESTART, RESTORE or QUIT";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int wishbringer_get_self_object_num() {
  return 238;
}

int wishbringer_get_moves() {
  return (((short) zmp[9495]) << 8) | zmp[9496];
}

int wishbringer_get_score() {
  return zmp[9498];
}

int wishbringer_max_score() {
  return 100;
}

int wishbringer_get_num_world_objs() {
  return 247;
}

int wishbringer_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int wishbringer_ignore_attr_diff(zword obj_num, zword attr_idx) {
  return 0;
}

int wishbringer_ignore_attr_clr(zword obj_num, zword attr_idx) {
  return 0;
}
