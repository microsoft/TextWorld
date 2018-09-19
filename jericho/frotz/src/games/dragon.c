// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Dragon Adventure: http://ifdb.tads.org/viewgame?id=sjiyffz8n5patu8l

char** dragon_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* dragon_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int dragon_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int dragon_game_over() {
  char *death_text = "You have just been lightly fried by the Dragon,";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int dragon_get_self_object_num() {
  return 20;
}

int dragon_get_moves() {
  return (((short) zmp[13452]) << 8) | zmp[13453]; // 13465
}

int dragon_get_score() {
  return (char) zmp[13451]; // 13475, 13477
}

int dragon_max_score() {
  return 25;
}

int dragon_get_num_world_objs() {
  return 268;
}

int dragon_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int dragon_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (obj_num == 52 && attr_idx == 17)
    return 1;
  if (attr_idx == 25)
    return 1;
  return 0;
}

int dragon_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}
