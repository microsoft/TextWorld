// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Omniquest: http://ifdb.tads.org/viewgame?id=mygqz9tzxqvryead

char** omniquest_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* omniquest_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int omniquest_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int omniquest_game_over() {
  char *death_text = "*** You have died ***";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int omniquest_get_self_object_num() {
  return 20;
}

int omniquest_get_moves() {
  return (((short) zmp[5980]) << 8) | zmp[5981]; //5995
}

int omniquest_get_score() {
  return zmp[5979]; //6005, 6007
}

int omniquest_max_score() {
  return 50;
}

int omniquest_get_num_world_objs() {
  return 138;
}

int omniquest_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int omniquest_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}

int omniquest_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}
