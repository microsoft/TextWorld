#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// The Meteor, the Stone and a Long Glass of Sherbet: http://ifdb.tads.org/viewgame?id=273o81yvg64m4pkz

char** sherbet_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* sherbet_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int sherbet_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int sherbet_game_over() {
  char *death_text = "****  You have died  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int sherbet_get_self_object_num() {
  return 40;
}

int sherbet_get_moves() {
  return (((short) zmp[12378]) << 8) | zmp[12379]; //12391
}

int sherbet_get_score() {
  return zmp[12377]; //12401, 12403
}

int sherbet_max_score() {
  return 30;
}

int sherbet_get_num_world_objs() {
  return 230;
}

int sherbet_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int sherbet_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}

int sherbet_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}
