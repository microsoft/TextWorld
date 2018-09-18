#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Spiritwrak: http://ifdb.tads.org/viewgame?id=tqpowvmdoemtooqf

char** spirit_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* spirit_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int spirit_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int spirit_game_over() {
  char *death_text = "****  You have died  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int spirit_get_self_object_num() {
  return 15;
}

int spirit_get_moves() {
  return (((short) zmp[36357]) << 8) | zmp[36358]; //36368
}

int spirit_get_score() {
  return zmp[36356]; //36366, 36382
}

int spirit_max_score() {
  return 250;
}

int spirit_get_num_world_objs() {
  return 176;
}

int spirit_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int spirit_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}

int spirit_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}
