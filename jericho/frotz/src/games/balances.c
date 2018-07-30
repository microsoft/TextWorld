// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// The Balancesing: http://www.ifwiki.org/index.php/The_Balancesing

char** balances_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* balances_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int balances_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int balances_game_over() {
  char *death_text = "*** You have died ***";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int balances_get_self_object_num() {
  return 20;
}

int balances_get_moves() {
  return (((short) zmp[6843]) << 8) | zmp[6844];
}

int balances_get_score() {
  return zmp[6842]; // Also 6866, 6868
}

int balances_max_score() {
  return 51;
}

int balances_get_num_world_objs() {
  return 124;
}

int balances_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int balances_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}

int balances_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}
