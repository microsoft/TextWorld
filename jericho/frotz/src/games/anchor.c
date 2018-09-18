#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Anchorhead: http://ifdb.tads.org/viewgame?id=op0uw1gn1tjqmjt7

char** anchor_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* anchor_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int anchor_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int anchor_game_over() {
  char *death_text = "Do you want me to try to reincarnate you?";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int anchor_get_self_object_num() {
  return 20;
}

int anchor_get_moves() {
  return (((short) zmp[37999]) << 8) | zmp[38000]; //38012
}

int anchor_get_score() {
  return zmp[38024]; //37998, 38022
}

int anchor_max_score() {
  return 100;
}

int anchor_get_num_world_objs() {
  return 764;
}

int anchor_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int anchor_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}

int anchor_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}
