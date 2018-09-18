#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Adventure: http://ifdb.tads.org/viewgame?id=fft6pu91j85y4acv

char** advent_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* advent_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int advent_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int advent_game_over() {
  char *death_text = "****  You have died  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int advent_get_self_object_num() {
  return 20;
}

int advent_get_moves() {
  return (((short) zmp[15361]) << 8) | zmp[15362]; // Also 15342
}

int advent_get_score() {
  return zmp[15372]; // Also 15374, 15340
}

int advent_max_score() {
  return 350;
}

int advent_get_num_world_objs() {
  return 255;
}

int advent_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int advent_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}

int advent_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}
