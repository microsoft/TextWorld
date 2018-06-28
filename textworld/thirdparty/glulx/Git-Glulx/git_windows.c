// Startup code for Windows Git

#include "glk.h"
#include "WinGlk.h"
#include "git.h"

#include <math.h>

const char* gFilename = NULL;
char gExePath[_MAX_PATH];

int winglk_startup_code(const char* cmdline)
{
    char* sep;
    int i;

    winglk_set_gui(100);
    winglk_app_set_name("Git");
    winglk_set_menu_name("&Git");
    winglk_window_set_title("Windows Git");
    winglk_set_about_text("Windows Git "GIT_VERSION_STR);
    winglk_show_game_dialog();

    if (GetModuleFileName(0,gExePath,_MAX_PATH) == 0)
        return 0;
    sep = strrchr(gExePath,'.');
    if (sep != 0)
    {
        strcpy(sep,".chm");
        winglk_set_help_file(gExePath);
    }

    if (GetModuleFileName(0,gExePath,_MAX_PATH) == 0)
        return 0;
    sep = strrchr(gExePath,'.');
    if (sep != 0)
    {
        static char* exts[5] = { ".blb",".blorb",".glb",".gblorb",".ulx" };
        for (i = 0; i < 5; i++)
        {
            strcpy(sep,exts[i]);
            if (GetFileAttributes(gExePath) != INVALID_FILE_ATTRIBUTES)
            {
                gFilename = gExePath;
                break;
            }
        }
    }

    if (gFilename == NULL)
    {
        gFilename = (char*)winglk_get_initial_filename(cmdline,
            "Select a Glulx game to run",
            "Glulx Files (.ulx;.blb;.blorb;.glb;.gblorb)|*.ulx;*.blb;*.blorb;*.glb;*.gblorb|"
                "All Files (*.*)|*.*||");
    }

    if (gFilename == NULL)
       return 0;
    winglk_load_config_file(gFilename);
    return 1;
}

#define CACHE_SIZE (256 * 1024)
#define UNDO_SIZE (2 * 1024 * 1024)

void fatalError (const char * s)
{
    MessageBox(0,s,"Git Fatal Error",MB_OK|MB_ICONERROR);
    exit (1);
}

void glk_main()
{
    void* file    = INVALID_HANDLE_VALUE;
    void* mapping = NULL;
    void* ptr     = NULL;
    size_t size   = 0;

    // Memory-map the gamefile
    file = CreateFile(gFilename,GENERIC_READ,FILE_SHARE_READ,0,
        OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,0);
    if (file != INVALID_HANDLE_VALUE)
    {
        size = GetFileSize(file,0);
        mapping = CreateFileMapping(file,0,PAGE_READONLY,0,0,0);
    }
    if (mapping)
        ptr = MapViewOfFile(mapping,FILE_MAP_READ,0,0,0);

    // Pass the gamefile to git
    if (ptr)
        git(ptr,size,CACHE_SIZE,UNDO_SIZE);
    else
        fatalError("Can't open gamefile");

    // Close the gamefile
    if (ptr)
        UnmapViewOfFile(ptr);
    if (mapping)
        CloseHandle(mapping);
    if (file != INVALID_HANDLE_VALUE)
        CloseHandle(file);
}

float git_powf(float x, float y)
{
  if (x == 1.0f)
    return 1.0f;
  else if ((y == 0.0f) || (y == -0.0f))
    return 1.0f;
  else if ((x == -1.0f) && isinf(y))
    return 1.0f;
  return powf(x,y);
}
