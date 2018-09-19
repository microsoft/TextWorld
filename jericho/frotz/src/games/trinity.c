// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Trinity: http://ifdb.tads.org/viewgame?id=j18kjz80hxjtyayw

char** trinity_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* trinity_clean_observation(char* obs) {
  return obs+2;
}

int trinity_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int trinity_game_over() {
  char *death_text = "[Type RESTART, RESTORE or QUIT.]";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int trinity_get_self_object_num() {
  return 103;
}

int trinity_get_moves() {
  return (((short) zmp[34172]) << 8) | zmp[34173];
}

int trinity_get_score() {
  return zmp[34215];
}

int trinity_max_score() {
  return 60;
}

int trinity_get_num_world_objs() {
  return 593;
}

int trinity_ignore_moved_obj(zword obj_num, zword dest_num) {
  if (dest_num == 483)
    return 1;
  return 0;
}

int trinity_ignore_attr_diff(zword obj_num, zword attr_idx) {
  return 0;
}

int trinity_ignore_attr_clr(zword obj_num, zword attr_idx) {
  return 0;
}
