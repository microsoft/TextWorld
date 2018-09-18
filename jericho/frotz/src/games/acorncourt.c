#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// The Acorn Court: http://ifdb.tads.org/viewgame?id=tqvambr6vowym20v

char** acorn_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* acorn_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '[');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int acorn_victory() {
    char *victory_text = "*** You have won ***";
    if (strstr(world, victory_text)) {
        return 1;
    }
    return 0;
}

int acorn_game_over() {
  char *death_text = "Would you like to RESTART, RESTORE a saved game or QUIT?";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int acorn_get_self_object_num() {
  return 20;
}

int acorn_get_moves() {
  return (((short) zmp[3711]) << 8) | zmp[3712];
}

int acorn_get_score() {
  return zmp[3710]; // Also 3734 and 3736
}

int acorn_max_score() {
  return 30;
}

int acorn_get_num_world_objs() {
  return 63;
}

int acorn_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int acorn_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}

int acorn_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 25)
    return 1;
  return 0;
}
