// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Spellbreaker: http://ifdb.tads.org/viewgame?id=wqsmrahzozosu3r

char** spellbrkr_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* spellbrkr_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '\n');
  if (pch != NULL) {
    return pch+1;
  }
  return obs;
}

int spellbrkr_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int spellbrkr_game_over() {
  char *death_text = "****  You have died  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int spellbrkr_get_self_object_num() {
  return 52;
}

int spellbrkr_get_moves() {
  return (((short) zmp[8726]) << 8) | zmp[8727];
}

int spellbrkr_get_score() {
  return zmp[8725];
}

int spellbrkr_max_score() {
  return 600;
}

int spellbrkr_get_num_world_objs() {
  return 249;
}

int spellbrkr_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int spellbrkr_ignore_attr_diff(zword obj_num, zword attr_idx) {
  return 0;
}

int spellbrkr_ignore_attr_clr(zword obj_num, zword attr_idx) {
  return 0;
}
