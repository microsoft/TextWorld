#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// All Quiet on the Library Front: http://ifdb.tads.org/viewgame?id=400zakqderzjnu1i

char** library_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* library_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int library_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int library_game_over() {
  char *death_text = "Would you like to RESTART";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int library_get_self_object_num() {
  return 15;
}

int library_get_moves() {
  return (((short) zmp[3611]) << 8) | zmp[3612];
}

int library_get_score() {
  return zmp[3610]; //3626
}

int library_max_score() {
  return 30;
}

int library_get_num_world_objs() {
  return 76;
}

int library_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int library_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}

int library_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}
