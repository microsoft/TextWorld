#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Hunter, in Darkness: http://ifdb.tads.org/viewgame?id=mh1a6hizgwjdbeg7

char** huntdark_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* huntdark_clean_observation(char* obs) {
  char* pch;
  pch = strstr(obs, ">  ");
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int huntdark_victory() {
  char *death_text = "*** It's over ***";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int huntdark_game_over() {
  char *death_text = "*** You have died ***";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int huntdark_get_self_object_num() {
  return 17;
}

int huntdark_get_moves() {
  return (((short) zmp[8915]) << 8) | zmp[8916];
}

int huntdark_get_score() {
  if (huntdark_victory()) {
    return 1;
  }
  return 0;
}

int huntdark_max_score() {
  return 1;
}

int huntdark_get_num_world_objs() {
  return 151;
}

int huntdark_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int huntdark_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 26)
    return 1;
  return 0;
}

int huntdark_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 26)
    return 1;
  return 0;
}
