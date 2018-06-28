#ifndef AGENT_H
#define AGENT_H
#pragma once

/**
 * Initializes the agent.
 * @param sock_name The name of the unix socket file to connect to
 */
void agent_init(char* sock_name);

/**
 * Adds an output-encoded string (UTF-8 or latin1) as input to the agent
 * @param buf The buf containing the output
 * @param len The length of the output
 */
void agent_put_string(char* buf, glui32 len);

/**
 * Returns agent output for the input buffer for a continuous process.
 * @param output_buf Output buffer to write into
 * @param max_len Size of output buffer
 * @return The length of output actually written
 */
glui32 agent_get_output(char* output_buf, glui32 max_len);

/**
 * Should be called on glk_exit() to avoid client programs hanging.
 */
void agent_exit(void);

#endif //AGENT_H