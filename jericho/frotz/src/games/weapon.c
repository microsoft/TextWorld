#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// The Weapon: http://ifdb.tads.org/viewgame?id=tcebhl79rlxo3qrk

char** weapon_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* weapon_clean_observation(char* obs) {
  char* pch;
  pch = strstr(obs, ">  ");
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int weapon_victory() {
  char *death_text = "*** You have won ***";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int weapon_game_over() {
  char *death_text = "*** You have died ***";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int weapon_get_self_object_num() {
  return 20;
}

int weapon_get_moves() {
  return (((short) zmp[31354]) << 8) | zmp[31355];
}

int weapon_get_score() {
  if (weapon_victory()) {
    return 1;
  }
  return 0;
}

int weapon_max_score() {
  return 1;
}

int weapon_get_num_world_objs() {
  return 455;
}

int weapon_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int weapon_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 25 || attr_idx == 14)
    return 1;
  return 0;
}

int weapon_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}
