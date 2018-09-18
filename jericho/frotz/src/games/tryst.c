#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Tryst of Fate: http://ifdb.tads.org/viewgame?id=ic0ebhbi70bdmyc2

char** tryst_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* tryst_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int tryst_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int tryst_game_over() {
  char *death_text = "****  You have died  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int tryst_get_self_object_num() {
  return 20;
}

int tryst_get_moves() {
  return (((short) zmp[15262]) << 8) | zmp[15263]; //15275
}

int tryst_get_score() {
  return zmp[15261]; //15285, 15287
}

int tryst_max_score() {
  return 350;
}

int tryst_get_num_world_objs() {
  return 255;
}

int tryst_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int tryst_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}

int tryst_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}
