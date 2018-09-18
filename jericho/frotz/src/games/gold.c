#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Goldilocks is a FOX!: http://ifdb.tads.org/viewgame?id=59ztsy9p01avd6wp

char** gold_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* gold_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int gold_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int gold_game_over() {
  char *death_text = "Would I like to RESTART";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int gold_get_self_object_num() {
  return 85;
}

int gold_get_moves() {
  return (((short) zmp[20789]) << 8) | zmp[20790];
}

int gold_get_score() {
  return zmp[20768]; // 20800, 20802
}

int gold_max_score() {
  return 100;
}

int gold_get_num_world_objs() {
  return 255;
}

int gold_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int gold_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 25 || attr_idx == 31)
    return 1;
  return 0;
}

int gold_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 25 || attr_idx == 31)
    return 1;
  return 0;
}
