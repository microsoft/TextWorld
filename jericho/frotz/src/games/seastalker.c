#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Seastalker: http://ifdb.tads.org/viewgame?id=56wb8hflec2isvzm

char** seastalker_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* seastalker_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '\n');
  if (pch != NULL) {
    return pch+1;
  }
  return obs;
}

int seastalker_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int seastalker_game_over() {
  char *death_text = "RESTART the story from the beginning";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int seastalker_get_self_object_num() {
  return 191;
}

int seastalker_get_moves() {
  return (((short) zmp[9311]) << 8) | zmp[9312];
}

int seastalker_get_score() {
  return zmp[9310];
}

int seastalker_max_score() {
  return 100;
}

int seastalker_get_num_world_objs() {
  return 249;
}

int seastalker_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int seastalker_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 6)
    return 1;
  return 0;
}

int seastalker_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 6)
    return 1;
  return 0;
}
