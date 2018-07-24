# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


from cffi import FFI
import platform


ffibuilder = FFI()

with open('src/glk_comm.c') as f:
    libraries = []
    if platform.system() == 'Linux':
        libraries.append("uuid")

    ffibuilder.set_source("glk", f.read(), libraries=libraries)

    ffibuilder.cdef(r"""
        struct sock_names {
            char* sock_name;
            ...;
        };
        """)

    ffibuilder.cdef(r"""
        int init_glulx(struct sock_names* names);
        const char* communicate(struct sock_names* names, const char* msg);
        const char* get_output_nosend(struct sock_names* names);
        void cleanup_glulx(struct sock_names* names);
        void free(void* ptr);
        """)

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
