// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#include <stdlib.h>
#include <string.h>
#include "frotz.h"
#include "games.h"
#include "frotz_interface.h"

// Games generated with TextWorld.

int num_world_objs = 0;
int player_obj_num = 0;
int move_count = 0;

// Parse the move count from the world observation; Eg -= Studio =-0/4 --> 4
void parse_move_count(char* obs) {
  char* pch = obs;
  char* last;
  while (pch != NULL) {
    last = pch;
    pch = strchr(pch+1, '/');
  }
  if (last != NULL) {
    move_count = strtol(last+1, &last, 10);
  }
}

char** textworld_intro_actions(int *n) {
  *n = 0;
  return NULL;
}

char* textworld_clean_observation(char* obs) {
  char* pch;
  parse_move_count(obs);
  pch = strchr(obs, '>');
  if (pch != NULL) {
    *(pch-2) = '\0';
  }
  return obs+1;
}

int textworld_victory() {
  char *death_text = "*** The End ***";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int textworld_game_over() {
  char *death_text = "*** You lost! ***";
  if (strstr(world, death_text)) {
    return 1;
  }
  return 0;
}

int textworld_get_self_object_num() {
  return player_obj_num;
}

int textworld_get_moves() {
  return move_count;
}

int textworld_get_score() {
  if (textworld_victory()) {
    return 1;
  }
  return 0;
}

int textworld_max_score() {
  return 1;
}

int textworld_get_num_world_objs() {
  return num_world_objs;
}

int textworld_ignore_moved_obj(zword obj_num, zword dest_num) {
  return 0;
}

int textworld_ignore_attr_diff(zword obj_num, zword attr_idx) {
  if (attr_idx == 35 || attr_idx == 31)
    return 1;
  return 0;
}

int textworld_ignore_attr_clr(zword obj_num, zword attr_idx) {
  if (attr_idx == 35 || attr_idx == 31)
    return 1;
  return 0;
}

void textworld_parse_object_tree(char* text) {
  char* pch;
  long ret;

  // printf("ObjectTree: %s\n", text);
  pch = strstr(text, "EndOfObject");
  if (pch == NULL) {
    printf("ERROR: Can't find EndOfObject!\n");
    exit(1);
  }
  pch = strchr(pch, '(');
  if (pch == NULL) {
    printf("ERROR: Can't find Paren after EndOfObject!\n");
    exit(1);
  }
  ret = strtol(pch+1, &pch, 10);
  // printf("EndOfObject: %ld\n", ret);
  num_world_objs = ret;
}

void textworld_parse_player_object(char* text) {
  char* s;
  // printf("Scope: %s\n", text);
  s = strstr(text, "yourself (");
  if (s == NULL) {
    printf("ERROR: Can't find player object!\n");
    exit(1);
  }
  player_obj_num = (int) strtol(s+10, &s, 10);
  // printf("PlayerObjNum: %d\n", player_obj_num);
}
