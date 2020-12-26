import random
import torch
import numpy as np
from collections import deque
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.autograd import Variable
from memory import ReplayMemory
from model import DQN
from utils import find_max_lives, check_live, get_frame, get_init_state
from config import *
import os

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

class Agent():
    def __init__(self, action_size):
        self.action_size = action_size

        # These are hyper parameters for the DQN
        self.discount_factor = 0.99
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.explore_step = 500000
        self.epsilon_decay = (self.epsilon - self.epsilon_min) / self.explore_step
        self.train_start = 100000
        self.update_target = 1000

        # Generate the memory
        self.memory = ReplayMemory()

        # Create the policy net
        self.policy_net = DQN(action_size)
        self.policy_net.to(device)

        self.optimizer = optim.Adam(params=self.policy_net.parameters(), lr=learning_rate)
        self.scheduler = optim.lr_scheduler.StepLR(self.optimizer, step_size=scheduler_step_size, gamma=scheduler_gamma)

    def load_policy_net(self, path):
        self.policy_net = torch.load(path)

    """Get action using policy net using epsilon-greedy policy"""
    def get_action(self, state):
        if np.random.rand() <= self.epsilon:
            ### CODE #### 
            # Choose a random action
            a = torch.tensor([[random.randrange(self.action_size)]], device=device, dtype=torch.long)

        else:
            ### CODE ####
            # Choose the best action
            with torch.no_grad():
                state = torch.from_numpy(state).reshape(1,4,84,84).to(device)
                a = self.policy_net(state).max(1)[1].view(1, 1)

        return a

    # pick samples randomly from replay memory (with batch_size)
    def train_policy_net(self, frame):
        if self.epsilon > self.epsilon_min:
            self.epsilon -= self.epsilon_decay

        mini_batch = self.memory.sample_mini_batch(frame)
        mini_batch = np.array(mini_batch).transpose()

        history = np.stack(mini_batch[0], axis=0)
        states = np.float32(history[:, :4, :, :]) / 255.
        states = torch.from_numpy(states).cuda()
        actions = list(mini_batch[1])
        actions = torch.LongTensor(actions).cuda()
        rewards = list(mini_batch[2])
        rewards = torch.FloatTensor(rewards).cuda()
        next_states = np.float32(history[:, 1:, :, :]) / 255.
        dones = mini_batch[3] # checks if the game is over
        musk = torch.tensor(list(map(int, dones==False)),dtype=torch.uint8)


        # Compute Q(s_t, a), the Q-value of the current state
        ### CODE ####
        curr_Q = self.policy_net(states).gather(1, actions.unsqueeze(1)).squeeze(1)

        # Compute Q function of next state
        ### CODE ####
        next_state_values = torch.zeros(32, device=device)
        next_states = torch.from_numpy(next_states).to(device)
        next_state_values[musk==1] = self.policy_net(next_states[musk==1]).max(1)[0].detach()

        # Find maximum Q-value of action at next state from target net
        ### CODE ####
        target_Q = next_state_values * self.discount_factor + rewards

        # Compute the Huber Loss
        ### CODE ####
        loss = F.smooth_l1_loss(curr_Q, target_Q)

        # Optimize the model, .step() both the optimizer and the scheduler!
        ### CODE ####
        self.optimizer.zero_grad()
        loss.backward()
        #torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 10)
        for param in self.policy_net.parameters():
            param.grad.data.clamp_(-1, 1)
        self.optimizer.step()



