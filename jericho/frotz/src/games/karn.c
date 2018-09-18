#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Return to Karn: http://ifdb.tads.org/viewgame?id=bx8118ggp6j7nslo

char** karn_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* karn_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int karn_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int karn_game_over() {
  char *death_text = "****  You have died  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int karn_get_self_object_num() {
  return 20;
}

int karn_get_moves() {
  return (((short) zmp[13817]) << 8) | zmp[13818]; // 13828
}

int karn_get_score() {
  return zmp[13816]; // 13826, 13842
}

int karn_max_score() {
  return 170;
}

int karn_get_num_world_objs() {
  return 255;
}

int karn_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int karn_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}

int karn_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}
