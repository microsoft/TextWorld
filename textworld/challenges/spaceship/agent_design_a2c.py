from collections import defaultdict
from os.path import join as pjoin
from time import time
from glob import glob
from typing import Mapping, Any, Optional
import re
import numpy as np

import os
import gym

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import optim

from textworld import EnvInfos
import textworld.gym


PATH = pjoin(os.path.dirname(__file__), 'textworld_data')
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class ActorzCritic(nn.Module):

    eps = 0.01

    def __init__(self, input_size, hidden_size):
        super(ActorzCritic, self).__init__()
        torch.manual_seed(42)  # For reproducibility
        self.embedding = nn.Embedding(input_size, hidden_size)
        self.encoder_gru = nn.GRU(hidden_size, hidden_size)
        self.cmd_encoder_gru = nn.GRU(hidden_size, hidden_size)
        self.state_gru = nn.GRU(hidden_size, hidden_size)

        self.linear_1 = nn.Linear(2 * hidden_size, 2 * hidden_size)
        self.critic = nn.Linear(hidden_size, 1)
        self.actor = nn.Linear(hidden_size * 2, 1)

        # Parameters
        self.state_hidden = torch.zeros(1, 1, hidden_size, device=device)
        self.hidden_size = hidden_size

    def forward(self, obs, commands, mode, method):
        input_length, batch_size = obs.size(0), obs.size(1)
        nb_cmds = commands.size(1)

        embedded = self.embedding(obs)
        encoder_output, encoder_hidden = self.encoder_gru(embedded)

        state_output, state_hidden = self.state_gru(encoder_hidden, self.state_hidden)
        self.state_hidden = state_hidden
        state_value = self.critic(state_output)

        # Attention network over the commands.
        cmds_embedding = self.embedding.forward(commands)
        _, cmds_encoding_last_states = self.cmd_encoder_gru.forward(cmds_embedding)  # 1*cmds*hidden

        # Same observed state for all commands.
        cmd_selector_input = torch.stack([state_hidden] * nb_cmds, 2)  # 1*batch*cmds*hidden

        # Same command choices for the whole batch.
        cmds_encoding_last_states = torch.stack([cmds_encoding_last_states] * batch_size, 1)  # 1*batch*cmds*hidden

        # Concatenate the observed state and command encodings.
        input_ = torch.cat([cmd_selector_input, cmds_encoding_last_states], dim=-1)

        # One FC layer
        x = F.relu(self.linear_1(input_))

        # Compute state-action value (score) per command.
        action_state = F.relu(self.actor(x)).squeeze(-1)  # 1 x Batch x cmds
        # action_state = F.relu(self.actor(input_)).squeeze(-1)  # 1 x Batch x cmds

        probs = F.softmax(action_state, dim=2)  # 1 x Batch x cmds

        if mode == "train":
            action_index = probs[0].multinomial(num_samples=1).unsqueeze(0)  # 1 x batch x indx
        elif mode == "test":
            if method == 'random':
                action_index = probs[0].multinomial(num_samples=1).unsqueeze(0)  # 1 x batch x indx
            elif method == 'arg-max':
                action_index = probs[0].max(1).indices.unsqueeze(-1).unsqueeze(-1)  # 1 x batch x indx
            elif method == 'eps-soft':
                index = probs[0].max(1).indices.unsqueeze(-1).unsqueeze(-1)
                p = np.random.random()
                if p < (1 - self.eps + self.eps / nb_cmds):
                    action_index = index
                else:
                    while True:
                        tp = np.random.choice(probs[0][0].detach().numpy())
                        if (probs[0][0] == tp).nonzero().unsqueeze(-1) != index:
                            action_index = (probs[0][0] == tp).nonzero().unsqueeze(-1)
                            break

        return action_state, action_index, state_value

    def reset_hidden(self, batch_size):
        self.state_hidden = torch.zeros(1, batch_size, self.hidden_size, device=device)


class NeuralAgent:
    """ Simple Neural Agent for playing TextWorld games. """

    MAX_VOCAB_SIZE = 1000
    UPDATE_FREQUENCY = 10
    LOG_FREQUENCY = 1000
    GAMMA = 0.9

    def __init__(self) -> None:
        self.id2word = ["<PAD>", "<UNK>"]
        self.word2id = {w: i for i, w in enumerate(self.id2word)}

        self.model = ActorzCritic(input_size=self.MAX_VOCAB_SIZE, hidden_size=128)
        self.optimizer = optim.Adam(self.model.parameters(), 0.00003)

    def train(self):
        self.mode = "train"
        self.method = "random"
        self.transitions = []
        self.last_score = 0
        self.no_train_step = 0
        self.stats = {"max": defaultdict(list), "mean": defaultdict(list)}
        self.memo = {"max": defaultdict(list), "mean": defaultdict(list), "mem": defaultdict(list)}
        self.model.reset_hidden(1)

    def test(self, method):
        self.mode = "test"
        self.method = method
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
        outputs, indexes, values = self.model(input_tensor, commands_tensor, mode=self.mode, method=self.method)
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
        self.memo["max"]["score"].append(score)

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
                policy_loss = (log_action_probs * advantage).sum()
                value_loss = ((values_ - ret) ** 2.).sum()
                entropy = (-probs * log_probs).sum()
                loss += 0.5 * value_loss - policy_loss - 0.001 * entropy

                self.memo["mem"]["selected_action_index"].append(indexes_.item())
                self.memo["mem"]["state_val_func"].append(values_.item())
                self.memo["mem"]["advantage"].append(advantage.item())
                self.memo["mem"]["return"].append(ret.item())
                self.memo["mean"]["reward"].append(reward)
                self.memo["mean"]["policy_loss"].append(policy_loss.item())
                self.memo["mean"]["value_loss"].append(value_loss.item())

                self.stats["mean"]["reward"].append(reward)
                self.stats["mean"]["policy_loss"].append(policy_loss.item())
                self.stats["mean"]["value_loss"].append(value_loss.item())
                self.stats["mean"]["entropy"].append(entropy.item())
                self.stats["mean"]["confidence"].append(torch.exp(log_action_probs).item())

            if self.no_train_step % self.LOG_FREQUENCY == 0:
                msg = "{}. ".format(self.no_train_step)
                msg += "  ".join("{}: {:.3f}".format(k, np.mean(v)) for k, v in self.stats["mean"].items())
                msg += "  " + "  ".join("{}: {}".format(k, np.max(v)) for k, v in self.stats["max"].items())
                msg += "  vocab: {}".format(len(self.id2word))
                print(msg)
                self.stats = {"max": defaultdict(list), "mean": defaultdict(list)}

            self.optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm(self.model.parameters(), 40)
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
        This code uses the agent design in the spaceship game.

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
            print(command, "....", end="")
            obs, score, done, infos = env.step(command)
            nb_moves += 1
        agent.act(obs, score, done, infos)  # Let the agent know the game is done.
        print(score)
        print(obs)
        print('-------------------------------------')

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
            print(avg_scores)
            print(msg.format(np.mean(avg_moves), np.mean(avg_scores), infos["max_score"]))


agent = NeuralAgent()
step_size = 750

print(" =====  Training  ===================================================== ")
agent.train()  # Tell the agent it should update its parameters.
start_time = time()
print(os.path.realpath("./games/levelMedium_v1.ulx"))
play(agent, "./games/levelMedium_v1.ulx", max_step=step_size, nb_episodes=2000, verbose=False)
print("Trained in {:.2f} secs".format(time() - start_time))

print(' =====  Test  ========================================================= ')
agent.test(method='random')
play(agent, "./games/levelMedium_v1.ulx", max_step=step_size)  # Medium level game.

save_path = "./model/levelMedium_v1_random.npy"
if not os.path.exists(os.path.dirname(save_path)):
    os.mkdir(os.path.dirname(save_path))

np.save(save_path, agent)
