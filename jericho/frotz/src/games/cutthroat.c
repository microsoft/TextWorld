#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Cutthroats: http://ifdb.tads.org/viewgame?id=4ao65o1u0xuvj8jf

char** cutthroat_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* cutthroat_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '\n');
  if (pch != NULL) {
    return pch+1;
  }
  return obs;
}

int cutthroat_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int cutthroat_game_over() {
  char *death_text = "RESTART, RESTORE, or QUIT";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int cutthroat_get_self_object_num() {
  return 184;
}

int cutthroat_get_moves() {
  return (((short) zmp[8644]) << 8) | zmp[8645]; //9041
}

int cutthroat_get_score() {
  return zmp[8871]; //8873
}

int cutthroat_max_score() {
  return 250;
}

int cutthroat_get_num_world_objs() {
  return 220;
}

int cutthroat_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int cutthroat_ignore_attr_diff(zword obj_num, zword attr_idx) {
  return 0;
}

int cutthroat_ignore_attr_clr(zword obj_num, zword attr_idx) {
  return 0;
}
