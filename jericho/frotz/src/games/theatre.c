// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Theatre: http://ifdb.tads.org/viewgame?id=bv8of8y9xeo7307g

char** theatre_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* theatre_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int theatre_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int theatre_game_over() {
  char *death_text = "****  You have died  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int theatre_get_self_object_num() {
  return 15;
}

int theatre_get_moves() {
  return (((short) zmp[17579]) << 8) | zmp[17580]; //17590
}

int theatre_get_score() {
  return zmp[17578]; //17588, 17604
}

int theatre_max_score() {
  return 50;
}

int theatre_get_num_world_objs() {
  return 255;
}

int theatre_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int theatre_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 27)
    return 1;
  return 0;
}

int theatre_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 27)
    return 1;
  return 0;
}
