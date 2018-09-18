#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

char** default_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* default_clean_observation(char* obs) {
  return obs;
}

int default_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int default_game_over() {
  char *death_text = "****  You have died  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int default_get_self_object_num() {
  return 20;
}

int default_get_moves() {
  return 0;
}

int default_get_score() {
  return 0;
}

int default_max_score() {
  return 0;
}

int default_get_num_world_objs() {
  return 0;
}

int default_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int default_ignore_attr_diff(zword obj_num, zword attr_idx) {
  return 0;
}

int default_ignore_attr_clr(zword obj_num, zword attr_idx) {
  return 0;
}
