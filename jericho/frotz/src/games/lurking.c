#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// The Lurking Horror: http://ifdb.tads.org/viewgame?id=jhbd0kja1t57uop

const char *lurking_intro[] = { "sit on chair\n",
                                "turn pc on\n",
                                "login 872325412\n",
                                "password uhlersoth\n" };

char** lurking_intro_actions(int *n) {
  *n = 4;
  return lurking_intro;
}

char* lurking_clean_observation(char* obs) {
  char* pch;
  pch = strchr(obs, '\n');
  if (pch != NULL) {
    return pch+1;
  }
  return obs;
}

int lurking_victory() {
  char *death_text = "****  You have won  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int lurking_game_over() {
  char *death_text = "****  You have died  ****";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int lurking_get_self_object_num() {
  return 56;
}

int lurking_get_moves() {
  return (((short) zmp[696]) << 8) | zmp[697];
}

int lurking_get_score() {
  return zmp[695];
}

int lurking_max_score() {
  return 100;
}

int lurking_get_num_world_objs() {
  return 252;
}

int lurking_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int lurking_ignore_attr_diff(zword obj_num, zword attr_idx) {
  return 0;
}

int lurking_ignore_attr_clr(zword obj_num, zword attr_idx) {
  return 0;
}
