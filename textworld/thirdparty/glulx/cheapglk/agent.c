#include <string.h>
#include <memory.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>

/* posix */
#include <errno.h>
#include <fcntl.h>
#include <sys/stat.h>

/* sockets */
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/un.h>

#include "glk.h"
#include "cheapglk.h"
#include "agent.h"

const glui32 INIT_BUF_SIZE = 8192;

char* cur_buf = 0;
glui32 str_len = 0;
glui32 cur_buf_len = 0;
int sock_fh = -1;

void agent_init(char* sock_name)
{
    if(sock_name == NULL) {
        gli_strict_warning("agent_init: Cannot initialize process without socket name");
        glk_exit();
    }

    /* Memory buffer */
    if(cur_buf) {
        free(cur_buf);
        cur_buf = 0;
    }
    cur_buf = malloc(INIT_BUF_SIZE);
    cur_buf_len = INIT_BUF_SIZE;
    memset(cur_buf, 0, cur_buf_len);

    /* socket */
    sock_fh = socket(AF_LOCAL, SOCK_STREAM, 0);
    if(sock_fh == -1) {
        gli_strict_warning("agent_init: Could not open socket");
        glk_exit();
    }

    struct sockaddr_un sock_addr;
    sock_addr.sun_family = AF_UNIX;
    snprintf(sock_addr.sun_path, sizeof(sock_addr.sun_path), "%s", sock_name);

    int conn_status = connect(sock_fh, (struct sockaddr*)&sock_addr, sizeof(sock_addr));
    if(conn_status < 0) {
        gli_strict_warning("agent_init: Could not connect socket");
        glk_exit();
    }
}

void agent_put_string(char* buf, glui32 len)
{
    glui32 new_str_len, new_buf_len;
    char* new_buf;

    /* check for capacity */
    new_str_len = str_len + len;
    if(new_str_len >= cur_buf_len) {
        /* resize buffer */
        new_buf_len = new_str_len << 1;
        if(new_buf_len < cur_buf_len) { /* overflow check */
            gli_strict_warning("agent_put_string: CANNOT write to output, buffer too large");
        }
        new_buf = realloc(cur_buf, new_buf_len);
        if(new_buf == 0) { /* malloc fail check */
            gli_strict_warning("agent_put_string: CANNOT write to output, buffer too long");
            return;
        }

        cur_buf = new_buf;
        cur_buf_len = new_buf_len;
    }

    /* do the copy */
    memmove(cur_buf+str_len, buf, len);
    str_len = new_str_len;
}

glui32 agent_get_output(char* buf, glui32 len)
{
    char* dest_buf = NULL; /* forward declare for goto; see para 6.8.6.1 */
    glui32 dest_buf_len = 0;
     /*
     * write to out as one large packet
     */
    ssize_t sent = -1;

    glui32 net_len = htonl(str_len);
    sent = send(sock_fh, &net_len, 4, 0);
    if(sent < 0) {
        int err = errno;
        gli_strict_warning("agent.c: send size");
        gli_strict_warning(strerror(err));
        goto cleanup;
    }

    sent = send(sock_fh, cur_buf, str_len, 0);

    if(sent < 0) {
        int err = errno;
        gli_strict_warning("agent.c: send message");
        gli_strict_warning(strerror(err));
        goto cleanup;
    }

    /*
     * receive size, then message
     */
    bool restart = false;
    glui32 net_dest_buf_len;

    do { //handle EINTR
        restart = 0;
        ssize_t in_len = recv(sock_fh, &net_dest_buf_len, sizeof(glui32), MSG_WAITALL);
        if(in_len == -1) {
            int err = errno;
            if(err == EINTR) {
                restart = true;
                continue;
            }
            gli_strict_warning("agent.c: receive size");
            gli_strict_warning(strerror(err));
            goto cleanup;
        }
    } while(restart);

    dest_buf_len = ntohl(net_dest_buf_len);
    dest_buf = calloc(dest_buf_len+1, 1);

    do { //handle EINTR
        restart = false;
        ssize_t in_len = recv(sock_fh, dest_buf, dest_buf_len, MSG_WAITALL);
        if(in_len == -1) {
            int err = errno;
            if(err == EINTR) {
                restart = true;
                continue;
            }
            gli_strict_warning("agent.c: receive message");
            gli_strict_warning(strerror(err));
            goto cleanup;
        }
    } while(restart);

    if(dest_buf_len > len) {
        dest_buf_len = strlen(dest_buf)+1;
    }
    if(dest_buf_len > len) {
        char errmsg[100];
        snprintf(errmsg, 100, "agent_get_output: string too large for buffer (%d versus %d)", dest_buf_len, len);
        gli_strict_warning(errmsg);
        goto cleanup;
    }

    memmove(buf, dest_buf, dest_buf_len);

    /* "deallocate" buffer */
    cleanup:
    if(dest_buf != NULL) {
        free(dest_buf);
        dest_buf = NULL;
    }
    memset(cur_buf, 0, str_len);
    str_len = 0;

    return dest_buf_len;
}

void agent_exit() {
    if(cur_buf != NULL) {
        free(cur_buf);
        cur_buf = NULL;
    }

    if(sock_fh == -1) {
        return; /* never connected */
    }

    char out_buf[11];

    out_buf[0] = 127; //continuation
    out_buf[1] = 0x10; //DLE
    strncpy(out_buf+2, "+++EXIT", 8);
    out_buf[9] = 0x10; //DLE
    out_buf[10] = 0;

    int sent = send(sock_fh, out_buf, 11, 0);

    if(sent < 0) {
        int err = errno;
        gli_strict_warning("agent.c: agent_exit");
        gli_strict_warning(strerror(err));
    }
}

