// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Curses: http://ifdb.tads.org/viewgame?id=plvzam05bmz3enh8

char** curses_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* curses_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int curses_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int curses_game_over() {
  char *death_text = "Would you like to RESTART";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int curses_get_self_object_num() {
  return 15;
}

int curses_get_moves() {
  return (((short) zmp[23374]) << 8) | zmp[23375]; // Also 23385
}

int curses_get_score() {
  return zmp[23373]; // Also 23383 23399
}

int curses_max_score() {
  return 550;
}

int curses_get_num_world_objs() {
  return 255;
}

int curses_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int curses_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}

int curses_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}
