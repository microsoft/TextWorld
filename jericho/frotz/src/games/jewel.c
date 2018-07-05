#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// The Jewel of Knowledge: http://ifdb.tads.org/viewgame?id=hu60gp1bgkhlo5yx

const char *jewel_intro[] = { "ask jacob about jewel\n",
                              "ask jacob about amylya\n",
                              "ask jacob about druids\n",
                              "ask jacob about ariana\n",
                              "ask jacob about dragons\n",
                              "ask jacob about book\n" };

char** jewel_intro_actions(int *n) {
  *n = 6;
  return jewel_intro;
}

char* jewel_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int jewel_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int jewel_game_over() {
  char *death_text = "*** You have died ***";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int jewel_get_self_object_num() {
  return 211;
}

int jewel_get_moves() {
  return (((short) zmp[9971]) << 8) | zmp[9972]; // 9984
}

int jewel_get_score() {
  return zmp[9970]; //9996,9994
}

int jewel_max_score() {
  return 90;
}

int jewel_get_num_world_objs() {
  return 211;
}

int jewel_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int jewel_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}

int jewel_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}
