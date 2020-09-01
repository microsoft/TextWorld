// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT license.


//
// Created by james on 8/10/17.
//

#include <limits.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
/* posix */
#include <errno.h>
#include <fcntl.h>
#include <libgen.h>
#include <signal.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>
/* socket */
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/un.h>
/* ulimit */
#include <sys/resource.h>
#include <sys/time.h>

struct sock_names {
    char* sock_name;
    int serv_sock_fd;
    int sock_fd;
};

void cleanup_glulx(struct sock_names* names) {
    if (names->sock_fd != -1) {
        int close_res = close(names->sock_fd);
        if (close_res == -1) {
            perror("glk_comm.c: Cannot close socket");
        }

        names->sock_fd = -1; /* protection against double-kill */
    }

    if (names->serv_sock_fd != -1) {
        int close_res = close(names->serv_sock_fd);
        if (close_res == -1) {
            perror("glk_comm.c: Cannot close server socket");
        }
        names->serv_sock_fd = -1;
    }

    if (names->sock_name != NULL) {
        int status = unlink(names->sock_name);
        if (status == -1 && errno != ENOENT) {
            perror("glk_comm.c: Cannot unlink socket");
        }

        const char *dir = dirname(names->sock_name);
        status = rmdir(dir);
        if (status == -1 && errno != ENOENT) {
            perror("glk_comm.c: Cannot unlink socket directory");
        }

        free(names->sock_name);
        names->sock_name = NULL;
    }
}

static int init_mq(struct sock_names* names) {
    names->sock_name = NULL;
    names->sock_fd = -1;
    names->serv_sock_fd = -1;

    char temp[25] = "/tmp/mlglk_XXXXXX";
    if (mkdtemp(temp) == NULL) {
        perror("glk_comm.c: mkdtemp()");
        return -1;
    }
    strcat(temp, "/socket");

    names->sock_name = strdup(temp);
    if (!names->sock_name) {
        perror("glk_comm.c: strdup()");
        return -1;
    }

    /* sockets */
    struct sockaddr_un sock_addr;
    sock_addr.sun_family = AF_UNIX;
    memset(sock_addr.sun_path, 0, sizeof(sock_addr.sun_path));
    strncpy(sock_addr.sun_path, names->sock_name, sizeof(sock_addr.sun_path) - 1);

    names->serv_sock_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (names->serv_sock_fd == -1) {
        perror("glk_comm.c: Error opening socket");
        return -1;
    }

    int status = bind(names->serv_sock_fd, (struct sockaddr*)&sock_addr, sizeof(sock_addr));
    if (status == -1) {
        perror("glk_comm.c: Error binding socket");
        return -1;
    }

    status = listen(names->serv_sock_fd, 1);
    if (status == -1) {
        perror("glk_comm.c: Error listening socket");
        return -1;
    }

    return 0;
}

/**
 * accept() wrapper that handles EINTR.
 */
static int robust_accept(int socket, struct sockaddr* address, socklen_t* address_len) {
    while (true) {
        int ret = accept(socket, address, address_len);
        if (ret >= 0 || errno != EINTR) {
            return ret;
        }
    }
}

/**
 * recv() wrapper that handles EINTR.
 */
static ssize_t robust_recv(int socket, void* buffer, size_t length, int flags) {
    while (true) {
        ssize_t ret = recv(socket, buffer, length, flags);
        if (ret >= 0 || errno != EINTR) {
            return ret;
        }
    }
}

static int glk_connect(struct sock_names* names) { /* arg mutable for connection */
    if (names->sock_fd != -1) {
        return 0;
    }

    names->sock_fd = robust_accept(names->serv_sock_fd, NULL, NULL);
    if (names->sock_fd == -1) {
        perror("glk_comm.c: Could not accept socket");
        return -1;
    }

    return 0;
}

const char* get_output_nosend(struct sock_names* names) {
    if (glk_connect(names) != 0) {
        return NULL;
    }

    uint32_t net_buf_size = 0;
    ssize_t amt = robust_recv(names->sock_fd, &net_buf_size, sizeof(net_buf_size), MSG_WAITALL);
    if (amt <= 0) {
        perror("glk_comm.c: Could not read msg size");
        return NULL;
    }

    uint32_t buf_size = ntohl(net_buf_size);
    char* msg_buf = calloc(buf_size + 1, 1);
    if (!msg_buf) {
        return NULL;
    }
    amt = robust_recv(names->sock_fd, msg_buf, buf_size, MSG_WAITALL);
    if (amt < 0) {
        perror("glk_comm.c: Could not read msg");
        free(msg_buf);
        return NULL;
    }
    if (amt == 0 && buf_size != 0) {
        fprintf(stderr, "glk_comm.c: Expected %d but only got %zd!\n", buf_size, amt);
    }

    return msg_buf;
}

const char* communicate(struct sock_names* names, const char* message) {
    if (glk_connect(names) != 0) {
        return NULL;
    }

    int msg_len = strlen(message);
    uint32_t net_msg_len = htonl(msg_len);

    int result = send(names->sock_fd, &net_msg_len, sizeof(net_msg_len), 0);
    if (result == -1) {
        perror("glk_comm.c: Could not send msg size");
        return NULL;
    }

    result = send(names->sock_fd, message, msg_len, 0);
    if (result == -1) {
        perror("glk_comm.c: Could not send msg");
        return NULL;
    }

    return get_output_nosend(names);
}

/* ensure we're allowed as many open files as we want */
static void check_rlimit(void) {
    struct rlimit limits;

    int status = getrlimit(RLIMIT_NOFILE, &limits);
    if (status == -1) {
        perror("glk_comm.c: Cannot get rlimit");
        return; /* fail */
    }

    // It's not likely we can really open infinity files.  macOS apparently
    // recommends using the minimum of rlim_max and OPEN_MAX.
    rlim_t max = limits.rlim_max;
    if (max == RLIM_INFINITY) {
#ifdef OPEN_MAX
        max = OPEN_MAX;
#else
        max = _POSIX_OPEN_MAX;
#endif
    }

    if (limits.rlim_cur != RLIM_INFINITY && limits.rlim_cur < max) {
        limits.rlim_cur = max;
        status = setrlimit(RLIMIT_NOFILE, &limits);
        if (status == -1) {
            perror("glk_comm.c: Cannot set rlimit");
            return;
        }
    }
}

int init_glulx(struct sock_names* names) {
    // check_rlimit();
    return init_mq(names);
}
