#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Night at the Computer Center: http://ifdb.tads.org/viewgame?id=ydhwa11st460g9u3

char** night_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* night_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int night_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int night_game_over() {
  char *death_text = "****  You have died  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int night_get_self_object_num() {
  return 15;
}

int night_get_moves() {
  return (((short) zmp[5295]) << 8) | zmp[5296]; //5306
}

int night_get_score() {
  return zmp[5294]; //5304, 5320
}

int night_max_score() {
  return 10;
}

int night_get_num_world_objs() {
  return 113;
}

int night_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int night_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}

int night_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}
