// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.


#ifndef frotz_interface_h__
#define frotz_interface_h__

typedef struct {
  unsigned int num;
  char name[64];
  int parent;
  int sibling;
  int child;
  char attr[4];
  int properties[16];
} zobject;

extern char* setup(char *story_file, int seed);

extern void shutdown();

extern char* step(char *next_action);

extern int save(char *filename);

extern int restore(char *filename);

extern int undo();

extern int getRAMSize();

extern void getRAM(unsigned char *ram);

extern char world[8192];


#endif
