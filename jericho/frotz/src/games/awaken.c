#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// The Awakening: http://www.ifwiki.org/index.php/The_Awakening

char** awaken_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* awaken_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int awaken_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int awaken_game_over() {
  char *death_text = "****  You have died  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int awaken_get_self_object_num() {
  return 20;
}

int awaken_get_moves() {
  return (((short) zmp[10667]) << 8) | zmp[10668]; //10680
}

int awaken_get_score() {
  return zmp[10666]; //10690, 10692
}

int awaken_max_score() {
  return 50;
}

int awaken_get_num_world_objs() {
  return 184;
}

int awaken_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int awaken_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}

int awaken_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}
