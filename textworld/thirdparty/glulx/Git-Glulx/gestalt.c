#include "git.h"

git_uint32 gestalt (enum GestaltSelector sel, git_uint32 param)
{
    switch (sel)
    {
        case GESTALT_SPEC_VERSION:
            return 0x00030102;
    
        case GESTALT_TERP_VERSION:
            return GIT_VERSION_NUM;
    
        case GESTALT_RESIZEMEM:
            return 1;
    
        case GESTALT_UNDO:
            return 1;
    
        case GESTALT_IO_SYSTEM:
            if (param == IO_NULL || param == IO_FILTER || param == IO_GLK)
                return 1;
            else
                return 0;
                
        case GESTALT_UNICODE:
            return 1;
            
        case GESTALT_MEM_COPY:
            return 1;
            
        case GESTALT_MALLOC:
            return 1;
            
        case GESTALT_MALLOC_HEAP:
          return heap_get_start();
            
        case GESTALT_ACCELERATION:
            return 1;

        case GESTALT_ACCELFUNC:
            if (accel_find_func(param))
                return 1;
            return 0;

        case GESTALT_FLOAT:
            return 1;

        case GESTALT_GIT_CACHE_CONTROL:
            return 1;
            
        default: // Unknown selector.
            return 0;
    }
}
