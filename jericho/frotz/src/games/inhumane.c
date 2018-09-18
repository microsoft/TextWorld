#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Inhumane: http://ifdb.tads.org/viewgame?id=wvs2vmbigm9unlpd

char** inhumane_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* inhumane_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int inhumane_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int inhumane_game_over() {
  // You have to die 9 times to solve this one
  return 0;
}

int inhumane_get_self_object_num() {
  return 15;
}

int inhumane_get_moves() {
  return (((short) zmp[4788]) << 8) | zmp[4789]; // 4799
  /* return zmp[4789]; //4799 */
}

int inhumane_get_score() {
  return zmp[4787]; // 4797
}

int inhumane_max_score() {
  return 300;
}

int inhumane_get_num_world_objs() {
  return 108;
}

int inhumane_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int inhumane_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 27)
    return 1;
  return 0;
}

int inhumane_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 27)
    return 1;
  return 0;
}
