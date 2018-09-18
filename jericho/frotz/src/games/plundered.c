#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Plundered Hearts: http://ifdb.tads.org/viewgame?id=ddagftras22bnz8h

char** plundered_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* plundered_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '\n');
  if (pch != NULL) {
    return pch+1;
  }
  return obs;
}

int plundered_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int plundered_game_over() {
  char *death_text = "***   You have died   ***";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int plundered_get_self_object_num() {
  return 192;
}

int plundered_get_moves() {
  return (((short) zmp[678]) << 8) | zmp[679];
}

int plundered_get_score() {
  return zmp[677];
}

int plundered_max_score() {
  return 25;
}

int plundered_get_num_world_objs() {
  return 223;
}

int plundered_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int plundered_ignore_attr_diff(zword obj_num, zword attr_idx) {
  return 0;
}

int plundered_ignore_attr_clr(zword obj_num, zword attr_idx) {
  return 0;
}
