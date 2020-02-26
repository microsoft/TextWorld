import os
import gym
import re
import argparse
import numpy as np
from typing import Mapping, Any, Optional
from glob import glob
from os.path import join as pjoin
from time import time
from collections import defaultdict

import textworld.gym
from textworld.generator.data import KnowledgeBase
from textworld.challenges import register
from textworld.challenges.spaceship.maker import spaceship_maker_level_medium_v1
from textworld import EnvInfos

import torch
import torch.nn as nn
from torch import optim
import torch.nn.functional as F

PATH = pjoin(os.path.dirname(__file__), 'textworld_data')


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class CommandScorer(nn.Module):
    def __init__(self, input_size, hidden_size):
        super(CommandScorer, self).__init__()
        torch.manual_seed(42)  # For reproducibility
        self.embedding = nn.Embedding(input_size, hidden_size)
        self.encoder_gru = nn.GRU(hidden_size, hidden_size)
        self.cmd_encoder_gru = nn.GRU(hidden_size, hidden_size)
        self.state_gru = nn.GRU(hidden_size, hidden_size)
        self.hidden_size = hidden_size
        self.state_hidden = torch.zeros(1, 1, hidden_size, device=device)
        self.critic = nn.Linear(hidden_size, 1)
        self.att_cmd = nn.Linear(hidden_size * 2, 1)

    def reset_hidden(self, batch_size):
        self.state_hidden = torch.zeros(1, batch_size, self.hidden_size, device=device)

    def forward(self, obs, commands, **kwargs):
        input_length = obs.size(0)
        batch_size = obs.size(1)
        nb_cmds = commands.size(1)

        embedded = self.embedding(obs)
        encoder_output, encoder_hidden = self.encoder_gru(embedded)
        state_output, state_hidden = self.state_gru(encoder_hidden, self.state_hidden)
        self.state_hidden = state_hidden
        value = self.critic(state_output)

        # Attention network over the commands.
        cmds_embedding = self.embedding.forward(commands)
        _, cmds_encoding_last_states = self.cmd_encoder_gru.forward(cmds_embedding)  # 1 x cmds x hidden

        # Same observed state for all commands.
        cmd_selector_input = torch.stack([state_hidden] * nb_cmds, 2)  # 1 x batch x cmds x hidden

        # Same command choices for the whole batch.
        cmds_encoding_last_states = torch.stack([cmds_encoding_last_states] * batch_size, 1)  # 1 x batch x cmds x hidden

        # Concatenate the observed state and command encodings.
        cmd_selector_input = torch.cat([cmd_selector_input, cmds_encoding_last_states], dim=-1)

        # Compute one score per command.
        scores = F.relu(self.att_cmd(cmd_selector_input)).squeeze(-1)  # 1 x Batch x cmds

        probs = F.softmax(scores, dim=2)  # 1 x Batch x cmds
        index = probs[0].multinomial(num_samples=1).unsqueeze(0)  # 1 x batch x indx
        return scores, index, value


class NeuralAgent:
    """ Simple Neural Agent for playing TextWorld games. """
    MAX_VOCAB_SIZE = 1000
    UPDATE_FREQUENCY = 10
    LOG_FREQUENCY = 1000
    GAMMA = 0.9

    def __init__(self) -> None:
        # self._initialized = False
        # self._epsiode_has_started = False
        self.id2word = ["<PAD>", "<UNK>"]
        self.word2id = {w: i for i, w in enumerate(self.id2word)}

        self.model = CommandScorer(input_size=self.MAX_VOCAB_SIZE, hidden_size=128)
        self.optimizer = optim.Adam(self.model.parameters(), 0.00003)

        self.mode = "test"

    def train(self):
        self.mode = "train"
        self.stats = {"max": defaultdict(list), "mean": defaultdict(list)}
        self.transitions = []
        self.model.reset_hidden(1)
        self.last_score = 0
        self.no_train_step = 0

    def test(self):
        self.mode = "test"
        self.model.reset_hidden(1)

    @property
    def infos_to_request(self) -> EnvInfos:
        return EnvInfos(description=True, inventory=True, admissible_commands=True, has_won=True, has_lost=True)

    def act(self, obs: str, score: int, done: bool, infos: Mapping[str, Any]) -> Optional[str]:
        # Build agent's observation: feedback + look + inventory.
        input_ = "{}\n{}\n{}".format(obs, infos["description"], infos["inventory"])

        # Tokenize and pad the input and the commands to chose from.
        input_tensor = self._process([input_])
        commands_tensor = self._process(infos["admissible_commands"])

        # Get our next action and value prediction.
        outputs, indexes, values = self.model(input_tensor, commands_tensor)
        action = infos["admissible_commands"][indexes[0]]

        if self.mode == "test":
            if done:
                self.model.reset_hidden(1)
            return action

        self.no_train_step += 1

        if self.transitions:
            reward = score - self.last_score  # Reward is the gain/loss in score.
            self.last_score = score
            if infos["has_won"]:
                reward += 100
            if infos["has_lost"]:
                reward -= 100

            self.transitions[-1][0] = reward  # Update reward information.

        self.stats["max"]["score"].append(score)

        if self.no_train_step % self.UPDATE_FREQUENCY == 0:
            # Update model
            returns, advantages = self._discount_rewards(values)

            loss = 0
            for transition, ret, advantage in zip(self.transitions, returns, advantages):
                reward, indexes_, outputs_, values_ = transition

                advantage = advantage.detach()  # Block gradients flow here.
                probs = F.softmax(outputs_, dim=2)
                log_probs = torch.log(probs)
                log_action_probs = log_probs.gather(2, indexes_)
                policy_loss = (-log_action_probs * advantage).sum()
                value_loss = (.5 * (values_ - ret) ** 2.).sum()
                entropy = (-probs * log_probs).sum()
                loss += policy_loss + 0.5 * value_loss - 0.1 * entropy

                self.stats["mean"]["reward"].append(reward)
                self.stats["mean"]["policy"].append(policy_loss.item())
                self.stats["mean"]["value"].append(value_loss.item())
                self.stats["mean"]["entropy"].append(entropy.item())
                self.stats["mean"]["confidence"].append(torch.exp(log_action_probs).item())

            if self.no_train_step % self.LOG_FREQUENCY == 0:
                msg = "{}. ".format(self.no_train_step)
                msg += "  ".join("{}: {:.3f}".format(k, np.mean(v)) for k, v in self.stats["mean"].items())
                msg += "  " + "  ".join("{}: {}".format(k, np.max(v)) for k, v in self.stats["max"].items())
                msg += "  vocab: {}".format(len(self.id2word))
                print(msg)
                self.stats = {"max": defaultdict(list), "mean": defaultdict(list)}

            loss.backward()
            nn.utils.clip_grad_norm_(self.model.parameters(), 40)
            self.optimizer.step()
            self.optimizer.zero_grad()

            self.transitions = []
            self.model.reset_hidden(1)
        else:
            # Keep information about transitions for Truncated Backpropagation Through Time.
            self.transitions.append([None, indexes, outputs, values])  # Reward will be set on the next call

        if done:
            self.last_score = 0  # Will be starting a new episode. Reset the last score.

        return action

    def _process(self, texts):
        texts = list(map(self._tokenize, texts))
        max_len = max(len(l) for l in texts)
        padded = np.ones((len(texts), max_len)) * self.word2id["<PAD>"]

        for i, text in enumerate(texts):
            padded[i, :len(text)] = text

        padded_tensor = torch.from_numpy(padded).type(torch.long).to(device)
        padded_tensor = padded_tensor.permute(1, 0)  # Batch x Seq => Seq x Batch
        return padded_tensor

    def _tokenize(self, text):
        # Simple tokenizer: strip out all non-alphabetic characters.
        text = re.sub("[^a-zA-Z0-9\- ]", " ", text)
        word_ids = list(map(self._get_word_id, text.split()))
        return word_ids

    def _get_word_id(self, word):
        if word not in self.word2id:
            if len(self.word2id) >= self.MAX_VOCAB_SIZE:
                return self.word2id["<UNK>"]

            self.id2word.append(word)
            self.word2id[word] = len(self.word2id)

        return self.word2id[word]

    def _discount_rewards(self, last_values):
        returns, advantages = [], []
        R = last_values.data
        for t in reversed(range(len(self.transitions))):
            rewards, _, _, values = self.transitions[t]
            R = rewards + self.GAMMA * R
            adv = R - values
            returns.append(R)
            advantages.append(adv)

        return returns[::-1], advantages[::-1]


def play(agent, path, max_step=50, nb_episodes=10, verbose=True):
    """
    This code uses the cooking agent design in the spaceship game.

    :param agent: the obj of NeuralAgent, a sample object for the agent
    :param path: The path to the game (envo model)
    """
    infos_to_request = agent.infos_to_request
    infos_to_request.max_score = True  # Needed to normalize the scores.

    gamefiles = [path]
    if os.path.isdir(path):
        gamefiles = glob(os.path.join(path, "*.ulx"))

    env_id = textworld.gym.register_games(gamefiles,
                                          request_infos=infos_to_request,
                                          max_episode_steps=max_step)
    env = gym.make(env_id)  # Create a Gym environment to play the text game.

    if verbose:
        if os.path.isdir(path):
            print(os.path.dirname(path), end="")
        else:
            print(os.path.basename(path), end="")

    # Collect some statistics: nb_steps, final reward.
    avg_moves, avg_scores, avg_norm_scores, seed_h = [], [], [], 4567
    for no_episode in range(nb_episodes):
        obs, infos = env.reset()  # Start new episode.

        env.env.textworld_env._wrapped_env.seed(seed=seed_h)
        seed_h += 1

        score = 0
        done = False
        nb_moves = 0
        while not done:
            command = agent.act(obs, score, done, infos)
            obs, score, done, infos = env.step(command)
            nb_moves += 1

        agent.act(obs, score, done, infos)  # Let the agent know the game is done.

        if verbose:
            print(".", end="")
        avg_moves.append(nb_moves)
        avg_scores.append(score)
        avg_norm_scores.append(score / infos["max_score"])

    env.close()
    msg = "  \tavg. steps: {:5.1f}; avg. score: {:4.1f} / {}."
    if verbose:
        if os.path.isdir(path):
            print(msg.format(np.mean(avg_moves), np.mean(avg_norm_scores), 1))
        else:
            print(msg.format(np.mean(avg_moves), np.mean(avg_scores), infos["max_score"]))


agent = NeuralAgent()

print("Training")
agent.train()  # Tell the agent it should update its parameters.

starttime = time()
print(os.path.realpath("./games/levelMedium.ulx"))
play(agent, "./games/levelMedium.ulx", nb_episodes=25, verbose=False)  # Medium level game.
print("Trained in {:.2f} secs".format(time() - starttime))

print('==============   Time To Test   ============== ')

print("Testing")
agent.test()
play(agent, "./games/levelMedium.ulx")  # Medium level game.
