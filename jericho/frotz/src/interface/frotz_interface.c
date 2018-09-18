#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "frotz.h"
#include "frotz_interface.h"
#include "games.h"
#include "ztools.h"

extern void interpret (void);
extern void interpret_until_read (void);
extern void init_memory (void);
extern void init_undo (void);
extern void reset_memory (void);
extern zbyte get_next_opcode (void);
extern void run_opcode (zbyte opcode);
extern void dumb_set_next_action (char *a);
extern void dumb_show_screen (int a);
extern char* dumb_get_screen(void);
extern void dumb_clear_screen(void);
extern void z_save (void);
extern void load_story(char *s);
extern zword save_quetzal (FILE *, FILE *);
extern zword restore_quetzal (FILE *, FILE *);
extern int restore_undo (void);
extern void split_window (zword);
extern void erase_window (zword);
extern void restart_header (void);
extern zword restore_squetzal (unsigned char *svf, unsigned char *stf);
extern zword save_squetzal (unsigned char *svf, unsigned char *stf);
extern zword object_name (zword);
extern zword object_address (zword);
extern zword get_parent (zword);
extern zword get_child (zword);
extern zword get_sibling (zword);
extern void insert_tree(zword obj1, zword obj2);
extern void insert_obj(zword obj1, zword obj2);
extern void seed_random (int value);
extern void set_random_seed (int seed);

zbyte next_opcode;
unsigned char *stf_buff = 0; // Holds the current story file
int desired_seed = 0;
int ROM_IDX = 0;
char world[8192] = "";

// Runs a single opcode on the Z-Machine
void zstep() {
  run_opcode(next_opcode);
  next_opcode = get_next_opcode();
}

// Run the Z-Machine until it reaches a particular opcode
void run_until_opcode(int opcode) {
  while (next_opcode != opcode) {
    zstep();
  }
}

// Save the story file in a buffer (useful for subsequent load/save)
void read_story_file_to_buffer(char *story_file) {
  size_t ret;
  if (stf_buff) {
    free(stf_buff);
  }
  FILE * f = fopen (story_file, "rb");
  fseek (f, 0, SEEK_END);
  long length = ftell(f);
  stf_buff = malloc (length);
  fseek (f, 0, SEEK_SET);
  if (stf_buff) {
    ret = fread(stf_buff, sizeof(char), length, f);
  }
  fclose(f);
}

void replace_newlines_with_spaces(char *s) {
  char* pch;
  for (;;) {
    pch = strchr(s, '\n');
    if (pch == NULL) {
      break;
    }
    *pch = ' ';
    s = pch;
  }
}

enum SUPPORTED {
  DEFAULT_,
  ACORNCOURT_,
  ADVENTURELAND_,
  ADVENT_,
  AFFLICTED_,
  ANCHOR_,
  AWAKEN_,
  BALANCES_,
  BALLYHOO_,
  CURSES_,
  CUTTHROAT_,
  DEEPHOME_,
  DETECTIVE_,
  DRAGON_,
  ENCHANTER_,
  ENTER_,
  GOLD_,
  HHGG_,
  HOLLYWOOD_,
  HUNTDARK_,
  INFIDEL_,
  INHUMANE_,
  JEWEL_,
  KARN_,
  LGOP_,
  LIBRARY_,
  LOOSE_,
  LOSTPIG_,
  LUDICORP_,
  LURKING_,
  MOONLIT_,
  MURDAC_,
  NIGHT_,
  NINE05_,
  OMNIQUEST_,
  PARTYFOUL_,
  PENTARI_,
  PLANETFALL_,
  PLUNDERED_,
  REVERB_,
  SEASTALKER_,
  SHERBET_,
  SHERLOCK_,
  SNACKTIME_,
  SORCERER_,
  SPELLBRKR_,
  SPIRIT_,
  TEMPLE_,
  THEATRE_,
  TRINITY_,
  TRYST_,
  WEAPON_,
  WISHBRINGER_,
  YOMOMMA_,
  ZENON_,
  ZORK1_,
  ZORK2_,
  ZORK3_,
  ZTUU_,
  TEXTWORLD_
};

// Set ROM_IDX according to the story_file.
void load_rom_bindings(char *story_file) {
  char *start;
  char *end;
  start = strrchr(story_file,'/');
  end = strrchr(story_file,'.');
  if (start == NULL || end == NULL) {
    printf("ERROR: Expecting period and slash in story filename: %s\n", story_file);
    return;
  }
  start++;     // Skip the "/".
  *end = '\0'; // Temporarily terminate the string for comparison.

  if (strcmp(start, "acorncourt") == 0) {
    ROM_IDX = ACORNCOURT_;
  } else if (strcmp(start, "adventureland") == 0) {
    ROM_IDX = ADVENTURELAND_;
  } else if (strcmp(start, "advent") == 0) {
    ROM_IDX = ADVENT_;
  } else if (strcmp(start, "afflicted") == 0) {
    ROM_IDX = AFFLICTED_;
  } else if (strcmp(start, "anchor") == 0) {
    ROM_IDX = ANCHOR_;
  } else if (strcmp(start, "awaken") == 0) {
    ROM_IDX = AWAKEN_;
  } else if (strcmp(start, "balances") == 0) {
    ROM_IDX = BALANCES_;
  } else if (strcmp(start, "ballyhoo") == 0) {
    ROM_IDX = BALLYHOO_;
  } else if (strcmp(start, "curses") == 0) {
    ROM_IDX = CURSES_;
  } else if (strcmp(start, "cutthroat") == 0) {
    ROM_IDX = CUTTHROAT_;
  } else if (strcmp(start, "deephome") == 0) {
    ROM_IDX = DEEPHOME_;
  } else if (strcmp(start, "detective") == 0) {
    ROM_IDX = DETECTIVE_;
  } else if (strcmp(start, "dragon") == 0) {
    ROM_IDX = DRAGON_;
  } else if (strcmp(start, "enchanter") == 0) {
    ROM_IDX = ENCHANTER_;
  } else if (strcmp(start, "enter") == 0) {
    ROM_IDX = ENTER_;
  } else if (strcmp(start, "gold") == 0) {
    ROM_IDX = GOLD_;
  } else if (strcmp(start, "hhgg") == 0) {
    ROM_IDX = HHGG_;
  } else if (strcmp(start, "hollywood") == 0) {
    ROM_IDX = HOLLYWOOD_;
  } else if (strcmp(start, "huntdark") == 0) {
    ROM_IDX = HUNTDARK_;
  } else if (strcmp(start, "infidel") == 0) {
    ROM_IDX = INFIDEL_;
  } else if (strcmp(start, "inhumane") == 0) {
    ROM_IDX = INHUMANE_;
  } else if (strcmp(start, "jewel") == 0) {
    ROM_IDX = JEWEL_;
  } else if (strcmp(start, "karn") == 0) {
    ROM_IDX = KARN_;
  } else if (strcmp(start, "lgop") == 0) {
    ROM_IDX = LGOP_;
  } else if (strcmp(start, "library") == 0) {
    ROM_IDX = LIBRARY_;
  } else if (strcmp(start, "loose") == 0) {
    ROM_IDX = LOOSE_;
  } else if (strcmp(start, "lostpig") == 0) {
    ROM_IDX = LOSTPIG_;
  } else if (strcmp(start, "ludicorp") == 0) {
    ROM_IDX = LUDICORP_;
  } else if (strcmp(start, "lurking") == 0) {
    ROM_IDX = LURKING_;
  } else if (strcmp(start, "moonlit") == 0) {
    ROM_IDX = MOONLIT_;
  } else if (strcmp(start, "murdac") == 0) {
    ROM_IDX = MURDAC_;
  } else if (strcmp(start, "night") == 0) {
    ROM_IDX = NIGHT_;
  } else if (strcmp(start, "905") == 0) {
    ROM_IDX = NINE05_;
  } else if (strcmp(start, "omniquest") == 0) {
    ROM_IDX = OMNIQUEST_;
  } else if (strcmp(start, "partyfoul") == 0) {
    ROM_IDX = PARTYFOUL_;
  } else if (strcmp(start, "pentari") == 0) {
    ROM_IDX = PENTARI_;
  } else if (strcmp(start, "planetfall") == 0) {
    ROM_IDX = PLANETFALL_;
  } else if (strcmp(start, "plundered") == 0) {
    ROM_IDX = PLUNDERED_;
  } else if (strcmp(start, "reverb") == 0) {
    ROM_IDX = REVERB_;
  } else if (strcmp(start, "seastalker") == 0) {
    ROM_IDX = SEASTALKER_;
  } else if (strcmp(start, "sherbet") == 0) {
    ROM_IDX = SHERBET_;
  } else if (strcmp(start, "sherlock") == 0) {
    ROM_IDX = SHERLOCK_;
  } else if (strcmp(start, "snacktime") == 0) {
    ROM_IDX = SNACKTIME_;
  } else if (strcmp(start, "sorcerer") == 0) {
    ROM_IDX = SORCERER_;
  } else if (strcmp(start, "spellbrkr") == 0) {
    ROM_IDX = SPELLBRKR_;
  } else if (strcmp(start, "spirit") == 0) {
    ROM_IDX = SPIRIT_;
  } else if (strcmp(start, "temple") == 0) {
    ROM_IDX = TEMPLE_;
  } else if (strcmp(start, "theatre") == 0) {
    ROM_IDX = THEATRE_;
  } else if (strcmp(start, "trinity") == 0) {
    ROM_IDX = TRINITY_;
  } else if (strcmp(start, "tryst205") == 0) {
    ROM_IDX = TRYST_;
  } else if (strcmp(start, "weapon") == 0) {
    ROM_IDX = WEAPON_;
  } else if (strcmp(start, "wishbringer") == 0) {
    ROM_IDX = WISHBRINGER_;
  } else if (strcmp(start, "yomomma") == 0) {
    ROM_IDX = YOMOMMA_;
  } else if (strcmp(start, "zenon") == 0) {
    ROM_IDX = ZENON_;
  } else if (strcmp(start, "zork1") == 0) {
    ROM_IDX = ZORK1_;
  } else if (strcmp(start, "zork2") == 0) {
    ROM_IDX = ZORK2_;
  } else if (strcmp(start, "zork3") == 0) {
    ROM_IDX = ZORK3_;
  } else if (strcmp(start, "ztuu") == 0) {
    ROM_IDX = ZTUU_;
  } else if (strncmp(start, "tw-", 3) == 0) {
    ROM_IDX = TEXTWORLD_;
  } else {
    ROM_IDX = DEFAULT_;
  }
  *end = '.'; // Return to the original string
}

void shutdown() {
  reset_memory();
}

// Save the state of the game into a string buffer
int save_str(unsigned char *s) {
  zword success = 0;
  dumb_set_next_action("save\n");
  // Opcode 181 (z_save) is used on ZorkI/II/III, Opcode 190 on others
  while (next_opcode != 181 && next_opcode != 190) {
    zstep();
  }
  zstep();
  success = save_squetzal(s, stf_buff);
  if ((short) success < 1) {
    printf("Failed to save!\n");
    return -1;
  }
  run_until_opcode(228);
  dumb_clear_screen();
  return success;
}

// Restore a saved game from a string buffer
int restore_str(unsigned char *s) {
  zword success = 0;
  dumb_set_next_action("restore\n");
  // Opcode 182 (z_restore) is used on ZorkI/II/III, Opcode 190 on others
  while (next_opcode != 182 && next_opcode != 190) {
    zstep();
  }
  zstep();
  success = restore_squetzal(s, stf_buff);
  if ((short) success <= 0) {
    printf("Error Restoring!\n");
    return success;
  }
  zbyte old_screen_rows;
  zbyte old_screen_cols;
  /* In V3, reset the upper window. */
  if (h_version == V3)
    split_window (0);
  LOW_BYTE (H_SCREEN_ROWS, old_screen_rows);
  LOW_BYTE (H_SCREEN_COLS, old_screen_cols);
  /* Reload cached header fields. */
  restart_header ();
  /*
   * Since QUETZAL files may be saved on many different machines,
   * the screen sizes may vary a lot. Erasing the status window
   * seems to cover up most of the resulting badness.
   */
  if (h_version > V3 && h_version != V6
      && (h_screen_rows != old_screen_rows
          || h_screen_cols != old_screen_cols))
    erase_window (1);
  run_until_opcode(228);

  dumb_clear_screen();
  // Re-seed the RNG for determinism after a load
  seed_random(desired_seed);
  return success;
}

// Save the state of the game into a file
int save(char *filename) {
  FILE *gfp;
  zword success = 0;
  if ((gfp = fopen (filename, "wb")) == NULL) {
    printf("Unable to open savefile!\n");
    return -1;
  }
  dumb_set_next_action("save\n");
  // Opcode 181 (z_save) is used on ZorkI/II/III, Opcode 190 on others
  while (next_opcode != 181 && next_opcode != 190) {
    zstep();
  }
  zstep();
  success = save_quetzal(gfp, story_fp);
  if ((short) success < 1) {
    printf("Failed to save!\n");
    return -1;
  }
  if (fclose (gfp) == EOF || ferror (story_fp)) {
    print_string ("Error writing save file\n");
    return -1;
  }
  run_until_opcode(228);
  dumb_clear_screen();
  return success;
}

// Restore a saved file
int restore(char *filename) {
  FILE *gfp;
  zword success = 0;
  if ((gfp = fopen (filename, "rb")) == NULL) {
    printf("Unable to open save file!\n");
    return -1;
  }
  dumb_set_next_action("restore\n");
  // Opcode 182 (z_restore) is used on ZorkI/II/III, Opcode 190 on others
  while (next_opcode != 182 && next_opcode != 190) {
    zstep();
  }
  zstep();
  success = restore_quetzal(gfp, story_fp);
  if ((short) success <= 0) {
    printf("Error reading save file!\n");
    return success;
  }
  fclose(gfp);
  zbyte old_screen_rows;
  zbyte old_screen_cols;
  /* In V3, reset the upper window. */
  if (h_version == V3)
    split_window (0);
  LOW_BYTE (H_SCREEN_ROWS, old_screen_rows);
  LOW_BYTE (H_SCREEN_COLS, old_screen_cols);
  /* Reload cached header fields. */
  restart_header ();
  /*
   * Since QUETZAL files may be saved on many different machines,
   * the screen sizes may vary a lot. Erasing the status window
   * seems to cover up most of the resulting badness.
   */
  if (h_version > V3 && h_version != V6
      && (h_screen_rows != old_screen_rows
          || h_screen_cols != old_screen_cols))
    erase_window (1);
  run_until_opcode(228);
  dumb_clear_screen();
  // Re-seed the RNG for determinism after a load
  seed_random(desired_seed);
  return success;
}

int getRAMSize() {
  return h_dynamic_size;
}

void getRAM(unsigned char *ram) {
  memcpy(ram, zmp, h_dynamic_size);
}

int zmp_diff(int addr) {
  if (zmp[addr] != prev_zmp[addr]) {
    return 1;
  }
  return 0;
}

int zmp_diff_range(int start, int end) {
  int i;
  for (i=start; i<end; ++i) {
    if (zmp_diff(i)) {
      return 1;
    }
  }
  return 0;
}

int getPC() {
  return pcp - zmp;
}

int getStackSize() {
  return STACK_SIZE;
}

void getStack(unsigned char *s) {
  memcpy(s, stack, STACK_SIZE*sizeof(zword));
}

void getZArgs(unsigned char *s) {
  memcpy(s, zargs, 8*sizeof(zword));
}

void get_world_diff(zword *objs, zword *dest) {
  int i;
  for (i=0; i<move_diff_cnt; ++i) {
    objs[i] = move_diff_objs[i];
    dest[i] = move_diff_dest[i];
  }
  for (i=0; i<attr_diff_cnt; ++i) {
    objs[16+i] = attr_diff_objs[i];
    dest[16+i] = attr_diff_nb[i];
  }
  for (i=0; i<attr_clr_cnt; ++i) {
    objs[32+i] = attr_clr_objs[i];
    dest[32+i] = attr_clr_nb[i];
  }
}

//==========================//
//   Function pointers      //
//==========================//

char** (*intro_action_fns[]) (int* num_actions) = {
  default_intro_actions,
  acorn_intro_actions,
  adventureland_intro_actions,
  advent_intro_actions,
  afflicted_intro_actions,
  anchor_intro_actions,
  awaken_intro_actions,
  balances_intro_actions,
  ballyhoo_intro_actions,
  curses_intro_actions,
  cutthroat_intro_actions,
  deephome_intro_actions,
  detective_intro_actions,
  dragon_intro_actions,
  enchanter_intro_actions,
  enter_intro_actions,
  gold_intro_actions,
  hhgg_intro_actions,
  hollywood_intro_actions,
  huntdark_intro_actions,
  infidel_intro_actions,
  inhumane_intro_actions,
  jewel_intro_actions,
  karn_intro_actions,
  lgop_intro_actions,
  library_intro_actions,
  loose_intro_actions,
  lostpig_intro_actions,
  ludicorp_intro_actions,
  lurking_intro_actions,
  moonlit_intro_actions,
  murdac_intro_actions,
  night_intro_actions,
  nine05_intro_actions,
  omniquest_intro_actions,
  partyfoul_intro_actions,
  pentari_intro_actions,
  planetfall_intro_actions,
  plundered_intro_actions,
  reverb_intro_actions,
  seastalker_intro_actions,
  sherbet_intro_actions,
  sherlock_intro_actions,
  snacktime_intro_actions,
  sorcerer_intro_actions,
  spellbrkr_intro_actions,
  spirit_intro_actions,
  temple_intro_actions,
  theatre_intro_actions,
  trinity_intro_actions,
  tryst_intro_actions,
  weapon_intro_actions,
  wishbringer_intro_actions,
  yomomma_intro_actions,
  zenon_intro_actions,
  zork1_intro_actions,
  zork2_intro_actions,
  zork3_intro_actions,
  ztuu_intro_actions,
  textworld_intro_actions
};

char* (*clean_observation_fns[]) (char* obs) = {
  default_clean_observation,
  acorn_clean_observation,
  adventureland_clean_observation,
  advent_clean_observation,
  afflicted_clean_observation,
  anchor_clean_observation,
  awaken_clean_observation,
  balances_clean_observation,
  ballyhoo_clean_observation,
  curses_clean_observation,
  cutthroat_clean_observation,
  deephome_clean_observation,
  detective_clean_observation,
  dragon_clean_observation,
  enchanter_clean_observation,
  enter_clean_observation,
  gold_clean_observation,
  hhgg_clean_observation,
  hollywood_clean_observation,
  huntdark_clean_observation,
  infidel_clean_observation,
  inhumane_clean_observation,
  jewel_clean_observation,
  karn_clean_observation,
  lgop_clean_observation,
  library_clean_observation,
  loose_clean_observation,
  lostpig_clean_observation,
  ludicorp_clean_observation,
  lurking_clean_observation,
  moonlit_clean_observation,
  murdac_clean_observation,
  night_clean_observation,
  nine05_clean_observation,
  omniquest_clean_observation,
  partyfoul_clean_observation,
  pentari_clean_observation,
  planetfall_clean_observation,
  plundered_clean_observation,
  reverb_clean_observation,
  seastalker_clean_observation,
  sherbet_clean_observation,
  sherlock_clean_observation,
  snacktime_clean_observation,
  sorcerer_clean_observation,
  spellbrkr_clean_observation,
  spirit_clean_observation,
  temple_clean_observation,
  theatre_clean_observation,
  trinity_clean_observation,
  tryst_clean_observation,
  weapon_clean_observation,
  wishbringer_clean_observation,
  yomomma_clean_observation,
  zenon_clean_observation,
  zork1_clean_observation,
  zork2_clean_observation,
  zork3_clean_observation,
  ztuu_clean_observation,
  textworld_clean_observation
};

int (*victory_fns[]) (void) = {
  default_victory,
  acorn_victory,
  adventureland_victory,
  advent_victory,
  afflicted_victory,
  anchor_victory,
  awaken_victory,
  balances_victory,
  ballyhoo_victory,
  curses_victory,
  cutthroat_victory,
  deephome_victory,
  detective_victory,
  dragon_victory,
  enchanter_victory,
  enter_victory,
  gold_victory,
  hhgg_victory,
  hollywood_victory,
  huntdark_victory,
  infidel_victory,
  inhumane_victory,
  jewel_victory,
  karn_victory,
  lgop_victory,
  library_victory,
  loose_victory,
  lostpig_victory,
  ludicorp_victory,
  lurking_victory,
  moonlit_victory,
  murdac_victory,
  night_victory,
  nine05_victory,
  omniquest_victory,
  partyfoul_victory,
  pentari_victory,
  planetfall_victory,
  plundered_victory,
  reverb_victory,
  seastalker_victory,
  sherbet_victory,
  sherlock_victory,
  snacktime_victory,
  sorcerer_victory,
  spellbrkr_victory,
  spirit_victory,
  temple_victory,
  theatre_victory,
  trinity_victory,
  tryst_victory,
  weapon_victory,
  wishbringer_victory,
  yomomma_victory,
  zenon_victory,
  zork1_victory,
  zork2_victory,
  zork3_victory,
  ztuu_victory,
  textworld_victory
};

int (*game_over_fns[]) (void) = {
  default_game_over,
  acorn_game_over,
  adventureland_game_over,
  advent_game_over,
  afflicted_game_over,
  anchor_game_over,
  awaken_game_over,
  balances_game_over,
  ballyhoo_game_over,
  curses_game_over,
  cutthroat_game_over,
  deephome_game_over,
  detective_game_over,
  dragon_game_over,
  enchanter_game_over,
  enter_game_over,
  gold_game_over,
  hhgg_game_over,
  hollywood_game_over,
  huntdark_game_over,
  infidel_game_over,
  inhumane_game_over,
  jewel_game_over,
  karn_game_over,
  lgop_game_over,
  library_game_over,
  loose_game_over,
  lostpig_game_over,
  ludicorp_game_over,
  lurking_game_over,
  moonlit_game_over,
  murdac_game_over,
  night_game_over,
  nine05_game_over,
  omniquest_game_over,
  partyfoul_game_over,
  pentari_game_over,
  planetfall_game_over,
  plundered_game_over,
  reverb_game_over,
  seastalker_game_over,
  sherbet_game_over,
  sherlock_game_over,
  snacktime_game_over,
  sorcerer_game_over,
  spellbrkr_game_over,
  spirit_game_over,
  temple_game_over,
  theatre_game_over,
  trinity_game_over,
  tryst_game_over,
  weapon_game_over,
  wishbringer_game_over,
  yomomma_game_over,
  zenon_game_over,
  zork1_game_over,
  zork2_game_over,
  zork3_game_over,
  ztuu_game_over,
  textworld_game_over
};

int (*get_self_object_num_fns[]) (void) = {
  default_get_self_object_num,
  acorn_get_self_object_num,
  adventureland_get_self_object_num,
  advent_get_self_object_num,
  afflicted_get_self_object_num,
  anchor_get_self_object_num,
  awaken_get_self_object_num,
  balances_get_self_object_num,
  ballyhoo_get_self_object_num,
  curses_get_self_object_num,
  cutthroat_get_self_object_num,
  deephome_get_self_object_num,
  detective_get_self_object_num,
  dragon_get_self_object_num,
  enchanter_get_self_object_num,
  enter_get_self_object_num,
  gold_get_self_object_num,
  hhgg_get_self_object_num,
  hollywood_get_self_object_num,
  huntdark_get_self_object_num,
  infidel_get_self_object_num,
  inhumane_get_self_object_num,
  jewel_get_self_object_num,
  karn_get_self_object_num,
  lgop_get_self_object_num,
  library_get_self_object_num,
  loose_get_self_object_num,
  lostpig_get_self_object_num,
  ludicorp_get_self_object_num,
  lurking_get_self_object_num,
  moonlit_get_self_object_num,
  murdac_get_self_object_num,
  night_get_self_object_num,
  nine05_get_self_object_num,
  omniquest_get_self_object_num,
  partyfoul_get_self_object_num,
  pentari_get_self_object_num,
  planetfall_get_self_object_num,
  plundered_get_self_object_num,
  reverb_get_self_object_num,
  seastalker_get_self_object_num,
  sherbet_get_self_object_num,
  sherlock_get_self_object_num,
  snacktime_get_self_object_num,
  sorcerer_get_self_object_num,
  spellbrkr_get_self_object_num,
  spirit_get_self_object_num,
  temple_get_self_object_num,
  theatre_get_self_object_num,
  trinity_get_self_object_num,
  tryst_get_self_object_num,
  weapon_get_self_object_num,
  wishbringer_get_self_object_num,
  yomomma_get_self_object_num,
  zenon_get_self_object_num,
  zork1_get_self_object_num,
  zork2_get_self_object_num,
  zork3_get_self_object_num,
  ztuu_get_self_object_num,
  textworld_get_self_object_num
};

int (*get_moves_fns[]) (void) = {
  default_get_moves,
  acorn_get_moves,
  adventureland_get_moves,
  advent_get_moves,
  afflicted_get_moves,
  anchor_get_moves,
  awaken_get_moves,
  balances_get_moves,
  ballyhoo_get_moves,
  curses_get_moves,
  cutthroat_get_moves,
  deephome_get_moves,
  detective_get_moves,
  dragon_get_moves,
  enchanter_get_moves,
  enter_get_moves,
  gold_get_moves,
  hhgg_get_moves,
  hollywood_get_moves,
  huntdark_get_moves,
  infidel_get_moves,
  inhumane_get_moves,
  jewel_get_moves,
  karn_get_moves,
  lgop_get_moves,
  library_get_moves,
  loose_get_moves,
  lostpig_get_moves,
  ludicorp_get_moves,
  lurking_get_moves,
  moonlit_get_moves,
  murdac_get_moves,
  night_get_moves,
  nine05_get_moves,
  omniquest_get_moves,
  partyfoul_get_moves,
  pentari_get_moves,
  planetfall_get_moves,
  plundered_get_moves,
  reverb_get_moves,
  seastalker_get_moves,
  sherbet_get_moves,
  sherlock_get_moves,
  snacktime_get_moves,
  sorcerer_get_moves,
  spellbrkr_get_moves,
  spirit_get_moves,
  temple_get_moves,
  theatre_get_moves,
  trinity_get_moves,
  tryst_get_moves,
  weapon_get_moves,
  wishbringer_get_moves,
  yomomma_get_moves,
  zenon_get_moves,
  zork1_get_moves,
  zork2_get_moves,
  zork3_get_moves,
  ztuu_get_moves,
  textworld_get_moves
};

int (*get_score_fns[]) (void) = {
  default_get_score,
  acorn_get_score,
  adventureland_get_score,
  advent_get_score,
  afflicted_get_score,
  anchor_get_score,
  awaken_get_score,
  balances_get_score,
  ballyhoo_get_score,
  curses_get_score,
  cutthroat_get_score,
  deephome_get_score,
  detective_get_score,
  dragon_get_score,
  enchanter_get_score,
  enter_get_score,
  gold_get_score,
  hhgg_get_score,
  hollywood_get_score,
  huntdark_get_score,
  infidel_get_score,
  inhumane_get_score,
  jewel_get_score,
  karn_get_score,
  lgop_get_score,
  library_get_score,
  loose_get_score,
  lostpig_get_score,
  ludicorp_get_score,
  lurking_get_score,
  moonlit_get_score,
  murdac_get_score,
  night_get_score,
  nine05_get_score,
  omniquest_get_score,
  partyfoul_get_score,
  pentari_get_score,
  planetfall_get_score,
  plundered_get_score,
  reverb_get_score,
  seastalker_get_score,
  sherbet_get_score,
  sherlock_get_score,
  snacktime_get_score,
  sorcerer_get_score,
  spellbrkr_get_score,
  spirit_get_score,
  temple_get_score,
  theatre_get_score,
  trinity_get_score,
  tryst_get_score,
  weapon_get_score,
  wishbringer_get_score,
  yomomma_get_score,
  zenon_get_score,
  zork1_get_score,
  zork2_get_score,
  zork3_get_score,
  ztuu_get_score,
  textworld_get_score
};

int (*get_num_world_objs_fns[]) (void) = {
  default_get_num_world_objs,
  acorn_get_num_world_objs,
  adventureland_get_num_world_objs,
  advent_get_num_world_objs,
  afflicted_get_num_world_objs,
  anchor_get_num_world_objs,
  awaken_get_num_world_objs,
  balances_get_num_world_objs,
  ballyhoo_get_num_world_objs,
  curses_get_num_world_objs,
  cutthroat_get_num_world_objs,
  deephome_get_num_world_objs,
  detective_get_num_world_objs,
  dragon_get_num_world_objs,
  enchanter_get_num_world_objs,
  enter_get_num_world_objs,
  gold_get_num_world_objs,
  hhgg_get_num_world_objs,
  hollywood_get_num_world_objs,
  huntdark_get_num_world_objs,
  infidel_get_num_world_objs,
  inhumane_get_num_world_objs,
  jewel_get_num_world_objs,
  karn_get_num_world_objs,
  lgop_get_num_world_objs,
  library_get_num_world_objs,
  loose_get_num_world_objs,
  lostpig_get_num_world_objs,
  ludicorp_get_num_world_objs,
  lurking_get_num_world_objs,
  moonlit_get_num_world_objs,
  murdac_get_num_world_objs,
  night_get_num_world_objs,
  nine05_get_num_world_objs,
  omniquest_get_num_world_objs,
  partyfoul_get_num_world_objs,
  pentari_get_num_world_objs,
  planetfall_get_num_world_objs,
  plundered_get_num_world_objs,
  reverb_get_num_world_objs,
  seastalker_get_num_world_objs,
  sherbet_get_num_world_objs,
  sherlock_get_num_world_objs,
  snacktime_get_num_world_objs,
  sorcerer_get_num_world_objs,
  spellbrkr_get_num_world_objs,
  spirit_get_num_world_objs,
  temple_get_num_world_objs,
  theatre_get_num_world_objs,
  trinity_get_num_world_objs,
  tryst_get_num_world_objs,
  weapon_get_num_world_objs,
  wishbringer_get_num_world_objs,
  yomomma_get_num_world_objs,
  zenon_get_num_world_objs,
  zork1_get_num_world_objs,
  zork2_get_num_world_objs,
  zork3_get_num_world_objs,
  ztuu_get_num_world_objs,
  textworld_get_num_world_objs
};

int (*max_score_fns[]) (void) = {
  default_max_score,
  acorn_max_score,
  adventureland_max_score,
  advent_max_score,
  afflicted_max_score,
  anchor_max_score,
  awaken_max_score,
  balances_max_score,
  ballyhoo_max_score,
  curses_max_score,
  cutthroat_max_score,
  deephome_max_score,
  detective_max_score,
  dragon_max_score,
  enchanter_max_score,
  enter_max_score,
  gold_max_score,
  hhgg_max_score,
  hollywood_max_score,
  huntdark_max_score,
  infidel_max_score,
  inhumane_max_score,
  jewel_max_score,
  karn_max_score,
  lgop_max_score,
  library_max_score,
  loose_max_score,
  lostpig_max_score,
  ludicorp_max_score,
  lurking_max_score,
  moonlit_max_score,
  murdac_max_score,
  night_max_score,
  nine05_max_score,
  omniquest_max_score,
  partyfoul_max_score,
  pentari_max_score,
  planetfall_max_score,
  plundered_max_score,
  reverb_max_score,
  seastalker_max_score,
  sherbet_max_score,
  sherlock_max_score,
  snacktime_max_score,
  sorcerer_max_score,
  spellbrkr_max_score,
  spirit_max_score,
  temple_max_score,
  theatre_max_score,
  trinity_max_score,
  tryst_max_score,
  weapon_max_score,
  wishbringer_max_score,
  yomomma_max_score,
  zenon_max_score,
  zork1_max_score,
  zork2_max_score,
  zork3_max_score,
  ztuu_max_score,
  textworld_max_score
};

int (*ignore_moved_obj_fns[]) (zword obj_num, zword dest_num) = {
  default_ignore_moved_obj,
  acorn_ignore_moved_obj,
  adventureland_ignore_moved_obj,
  advent_ignore_moved_obj,
  afflicted_ignore_moved_obj,
  anchor_ignore_moved_obj,
  awaken_ignore_moved_obj,
  balances_ignore_moved_obj,
  ballyhoo_ignore_moved_obj,
  curses_ignore_moved_obj,
  cutthroat_ignore_moved_obj,
  deephome_ignore_moved_obj,
  detective_ignore_moved_obj,
  dragon_ignore_moved_obj,
  enchanter_ignore_moved_obj,
  enter_ignore_moved_obj,
  gold_ignore_moved_obj,
  hhgg_ignore_moved_obj,
  hollywood_ignore_moved_obj,
  huntdark_ignore_moved_obj,
  infidel_ignore_moved_obj,
  inhumane_ignore_moved_obj,
  jewel_ignore_moved_obj,
  karn_ignore_moved_obj,
  lgop_ignore_moved_obj,
  library_ignore_moved_obj,
  loose_ignore_moved_obj,
  lostpig_ignore_moved_obj,
  ludicorp_ignore_moved_obj,
  lurking_ignore_moved_obj,
  moonlit_ignore_moved_obj,
  murdac_ignore_moved_obj,
  night_ignore_moved_obj,
  nine05_ignore_moved_obj,
  omniquest_ignore_moved_obj,
  partyfoul_ignore_moved_obj,
  pentari_ignore_moved_obj,
  planetfall_ignore_moved_obj,
  plundered_ignore_moved_obj,
  reverb_ignore_moved_obj,
  seastalker_ignore_moved_obj,
  sherbet_ignore_moved_obj,
  sherlock_ignore_moved_obj,
  snacktime_ignore_moved_obj,
  sorcerer_ignore_moved_obj,
  spellbrkr_ignore_moved_obj,
  spirit_ignore_moved_obj,
  temple_ignore_moved_obj,
  theatre_ignore_moved_obj,
  trinity_ignore_moved_obj,
  tryst_ignore_moved_obj,
  weapon_ignore_moved_obj,
  wishbringer_ignore_moved_obj,
  yomomma_ignore_moved_obj,
  zenon_ignore_moved_obj,
  zork1_ignore_moved_obj,
  zork2_ignore_moved_obj,
  zork3_ignore_moved_obj,
  ztuu_ignore_moved_obj,
  textworld_ignore_moved_obj
};

int (*ignore_attr_diff_fns[]) (zword obj_num, zword attr_idx) = {
  default_ignore_attr_diff,
  acorn_ignore_attr_diff,
  adventureland_ignore_attr_diff,
  advent_ignore_attr_diff,
  afflicted_ignore_attr_diff,
  anchor_ignore_attr_diff,
  awaken_ignore_attr_diff,
  balances_ignore_attr_diff,
  ballyhoo_ignore_attr_diff,
  curses_ignore_attr_diff,
  cutthroat_ignore_attr_diff,
  deephome_ignore_attr_diff,
  detective_ignore_attr_diff,
  dragon_ignore_attr_diff,
  enchanter_ignore_attr_diff,
  enter_ignore_attr_diff,
  gold_ignore_attr_diff,
  hhgg_ignore_attr_diff,
  hollywood_ignore_attr_diff,
  huntdark_ignore_attr_diff,
  infidel_ignore_attr_diff,
  inhumane_ignore_attr_diff,
  jewel_ignore_attr_diff,
  karn_ignore_attr_diff,
  lgop_ignore_attr_diff,
  library_ignore_attr_diff,
  loose_ignore_attr_diff,
  lostpig_ignore_attr_diff,
  ludicorp_ignore_attr_diff,
  lurking_ignore_attr_diff,
  moonlit_ignore_attr_diff,
  murdac_ignore_attr_diff,
  night_ignore_attr_diff,
  nine05_ignore_attr_diff,
  omniquest_ignore_attr_diff,
  partyfoul_ignore_attr_diff,
  pentari_ignore_attr_diff,
  planetfall_ignore_attr_diff,
  plundered_ignore_attr_diff,
  reverb_ignore_attr_diff,
  seastalker_ignore_attr_diff,
  sherbet_ignore_attr_diff,
  sherlock_ignore_attr_diff,
  snacktime_ignore_attr_diff,
  sorcerer_ignore_attr_diff,
  spellbrkr_ignore_attr_diff,
  spirit_ignore_attr_diff,
  temple_ignore_attr_diff,
  theatre_ignore_attr_diff,
  trinity_ignore_attr_diff,
  tryst_ignore_attr_diff,
  weapon_ignore_attr_diff,
  wishbringer_ignore_attr_diff,
  yomomma_ignore_attr_diff,
  zenon_ignore_attr_diff,
  zork1_ignore_attr_diff,
  zork2_ignore_attr_diff,
  zork3_ignore_attr_diff,
  ztuu_ignore_attr_diff,
  textworld_ignore_attr_diff
};

int (*ignore_attr_clr_fns[]) (zword obj_num, zword attr_idx) = {
  default_ignore_attr_clr,
  acorn_ignore_attr_clr,
  adventureland_ignore_attr_clr,
  advent_ignore_attr_clr,
  afflicted_ignore_attr_clr,
  anchor_ignore_attr_clr,
  awaken_ignore_attr_clr,
  balances_ignore_attr_clr,
  ballyhoo_ignore_attr_clr,
  curses_ignore_attr_clr,
  cutthroat_ignore_attr_clr,
  deephome_ignore_attr_clr,
  detective_ignore_attr_clr,
  dragon_ignore_attr_clr,
  enchanter_ignore_attr_clr,
  enter_ignore_attr_clr,
  gold_ignore_attr_clr,
  hhgg_ignore_attr_clr,
  hollywood_ignore_attr_clr,
  huntdark_ignore_attr_clr,
  infidel_ignore_attr_clr,
  inhumane_ignore_attr_clr,
  jewel_ignore_attr_clr,
  karn_ignore_attr_clr,
  lgop_ignore_attr_clr,
  library_ignore_attr_clr,
  loose_ignore_attr_clr,
  lostpig_ignore_attr_clr,
  ludicorp_ignore_attr_clr,
  lurking_ignore_attr_clr,
  moonlit_ignore_attr_clr,
  murdac_ignore_attr_clr,
  night_ignore_attr_clr,
  nine05_ignore_attr_clr,
  omniquest_ignore_attr_clr,
  partyfoul_ignore_attr_clr,
  pentari_ignore_attr_clr,
  planetfall_ignore_attr_clr,
  plundered_ignore_attr_clr,
  reverb_ignore_attr_clr,
  seastalker_ignore_attr_clr,
  sherbet_ignore_attr_clr,
  sherlock_ignore_attr_clr,
  snacktime_ignore_attr_clr,
  sorcerer_ignore_attr_clr,
  spellbrkr_ignore_attr_clr,
  spirit_ignore_attr_clr,
  temple_ignore_attr_clr,
  theatre_ignore_attr_clr,
  trinity_ignore_attr_clr,
  tryst_ignore_attr_clr,
  weapon_ignore_attr_clr,
  wishbringer_ignore_attr_clr,
  yomomma_ignore_attr_clr,
  zenon_ignore_attr_clr,
  zork1_ignore_attr_clr,
  zork2_ignore_attr_clr,
  zork3_ignore_attr_clr,
  ztuu_ignore_attr_clr,
  textworld_ignore_attr_clr
};


//==========================//
// Function Instantiations  //
//==========================//

char** get_intro_actions(int* num_actions) {
  return (*intro_action_fns[ROM_IDX])(num_actions);
}

char* clean_observation(char* obs) {
  return (*clean_observation_fns[ROM_IDX])(obs);
}

int get_score() {
  return (*get_score_fns[ROM_IDX])();
}

int get_max_score() {
  return (*max_score_fns[ROM_IDX])();
}

int get_moves() {
  return (*get_moves_fns[ROM_IDX])();
}

int get_self_object_num() {
  return (*get_self_object_num_fns[ROM_IDX])();
}

int get_num_world_objs() {
  return (*get_num_world_objs_fns[ROM_IDX])();
}

int game_over() {
  return (*game_over_fns[ROM_IDX])();
}

int victory() {
  return (*victory_fns[ROM_IDX])();
}

int ignore_moved_obj(zword obj_num, zword dest_num) {
  return (*ignore_moved_obj_fns[ROM_IDX])(obj_num, dest_num);
}

int ignore_attr_diff(zword obj_num, zword dest_num) {
  return (*ignore_attr_diff_fns[ROM_IDX])(obj_num, dest_num);
}

int ignore_attr_clr(zword obj_num, zword dest_num) {
  return (*ignore_attr_clr_fns[ROM_IDX])(obj_num, dest_num);
}

int is_supported(char *story_file) {
  load_rom_bindings(story_file);
  return ROM_IDX != DEFAULT_;
}

// Takes game-specific introduction actions
void take_intro_actions() {
  int num_actions = 0;
  char **intro_actions = NULL;
  int i;
  intro_actions = get_intro_actions(&num_actions);
  if (num_actions <= 0 || intro_actions == NULL)
    return;
  for (i=0; i<num_actions; ++i) {
    dumb_set_next_action(intro_actions[i]);
    zstep();
    run_until_opcode(228);
  }
}

char* setup(char *story_file, int seed) {
  char* text;
  os_init_setup();
  desired_seed = seed;
  set_random_seed(desired_seed);
  load_story(story_file);
  read_story_file_to_buffer(story_file);
  init_buffer();
  init_err();
  init_memory();
  init_process();
  init_sound();
  os_init_screen();
  init_undo();
  z_restart();
  next_opcode = get_next_opcode();
  dumb_set_next_action("\n");
  zstep();
  run_until_opcode(228);
  load_rom_bindings(story_file);
  take_intro_actions();

  // Extra procedures for TextWorld
  if (ROM_IDX == TEXTWORLD_) {
    dumb_clear_screen();
    dumb_set_next_action("tree\n");
    zstep();
    run_until_opcode(228);
    char* text = dumb_get_screen();
    replace_newlines_with_spaces(text);
    textworld_parse_object_tree(text);
    dumb_clear_screen();
    dumb_set_next_action("scope\n");
    zstep();
    run_until_opcode(228);
    text = dumb_get_screen();
    replace_newlines_with_spaces(text);
    textworld_parse_player_object(text);
    dumb_clear_screen();
    z_restart();
    next_opcode = get_next_opcode();
    zstep();
    run_until_opcode(228);
  }

  text = dumb_get_screen();
  text = clean_observation(text);
  strcpy(world, text);
  dumb_clear_screen();
  return world;
}

char* step(char *next_action) {
  char* text;

  // Clear the object & attr diff
  move_diff_cnt = 0;
  attr_diff_cnt = 0;
  attr_clr_cnt = 0;

  dumb_set_next_action(next_action);

  zstep();
  run_until_opcode(228);

  text = dumb_get_screen();
  text = clean_observation(text);
  strcpy(world, text);
  dumb_clear_screen();
  return world;
}

// Returns a world diff that ignores selected objects
void get_cleaned_world_diff(zword *objs, zword *dest) {
  int i;
  int j = 0;
  for (i=0; i<move_diff_cnt; ++i) {
    if (ignore_moved_obj(move_diff_objs[i], move_diff_dest[i])) {
      continue;
    }
    objs[j] = move_diff_objs[i];
    dest[j] = move_diff_dest[i];
    j++;
  }
  j = 0;
  for (i=0; i<attr_diff_cnt; ++i) {
    if (ignore_attr_diff(attr_diff_objs[i], attr_diff_nb[i])) {
      continue;
    }
    objs[16+j] = attr_diff_objs[i];
    dest[16+j] = attr_diff_nb[i];
    j++;
  }
  j = 0;
  for (i=0; i<attr_clr_cnt; ++i) {
    if (ignore_attr_clr(attr_clr_objs[i], attr_clr_nb[i])) {
      continue;
    }
    objs[32+j] = attr_clr_objs[i];
    dest[32+j] = attr_clr_nb[i];
    j++;
  }
}

// Returns 1 if the last action changed the state of the world.
int world_changed() {
  int i;
  for (i=0; i<move_diff_cnt; ++i) {
    if (ignore_moved_obj(move_diff_objs[i], move_diff_dest[i])) {
      continue;
    }
    return 1;
  }
  for (i=0; i<attr_diff_cnt; ++i) {
    if (ignore_attr_diff(attr_diff_objs[i], attr_diff_nb[i])) {
      continue;
    }
    return 1;
  }
  for (i=0; i<attr_clr_cnt; ++i) {
    if (ignore_attr_clr(attr_clr_objs[i], attr_clr_nb[i])) {
      continue;
    }
    return 1;
  }
  return 0;
}

void get_object(zobject *obj, zword obj_num) {
  int i;
  int prop_value;

  if (obj_num < 1 || obj_num > get_num_world_objs()) {
    return;
  }

  zword obj_name_addr = object_name(obj_num);
  zbyte length;
  LOW_BYTE(obj_name_addr, length);

  if (length <= 0 || length > 64) {
    return;
  }

  (*obj).num = obj_num;
  get_text(0, obj_name_addr+1, &(*obj).name);

  (*obj).parent = get_parent(obj_num);
  (*obj).sibling = get_sibling(obj_num);
  (*obj).child = get_child(obj_num);

  // Get the attributes of the object
  zword obj_addr = object_address(obj_num);
  for (i=0; i<4; ++i) {
    LOW_BYTE(obj_addr + i, (*obj).attr[i]);
  }

  // Get the properties of the object
  zword prop_addr = first_property(obj_num);
  LOW_BYTE(prop_addr, prop_value);
  for (i=0; i<16 && prop_value != 0; ++i) {
    (*obj).properties[i] = (int) (prop_value & (0x20-1));
    prop_addr = next_property(prop_addr);
    LOW_BYTE(prop_addr, prop_value);
  }
  for (; i<16; ++i) {
    (*obj).properties[i] = 0;
  }
}

void get_world_objects(zobject *objs) {
  int i;
  for (i=1; i<=get_num_world_objs(); ++i) {
    get_object(&objs[i-1], (zword) i);
  }
}

// Teleports an object (and all children) to the desired destination
void teleport_obj(zword obj, zword dest) {
  insert_obj(obj, dest);
}

// Teleports an object (and all siblings + children + children of
// siblings) to the last child of desired destination
void teleport_tree(zword obj, zword dest) {
  insert_tree(obj, dest);
}

void test() {
  int i;
  for (i=0; i<move_diff_cnt; ++i) {
    printf("Move Diff %d: %d --> %d\n", i, move_diff_objs[i], move_diff_dest[i]);
  }
  for (i=0; i<attr_diff_cnt; ++i) {
    printf("Attr Diff %d: %d --> %d\n", i, attr_diff_objs[i], attr_diff_nb[i]);
  }
  for (i=0; i<attr_clr_cnt; ++i) {
    printf("Attr Clr %d: %d --> %d\n", i, attr_clr_objs[i], attr_clr_nb[i]);
  }
}
