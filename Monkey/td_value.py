# Implements model-free learning (Q-learning)

import numpy as np
import numpy.random as npr
import sys
import math
import random

from SwingyMonkey import SwingyMonkey


class TDValueLearner:

    def __init__(self):
        bin_count = 5

        # self.tree_bot_range = (0, 400)
        # self.tree_bot_bins = 10
        self.tree_top_range = (0, 400)
        self.tree_top_bins = bin_count
        self.tree_dist_range = (0, 600)
        self.tree_dist_bins = bin_count
        self.monkey_vel_range = (-50,50)
        self.monkey_vel_bins = bin_count
        # self.monkey_bot_range = (0, 450)
        # self.monkey_bot_bins = 10
        self.monkey_top_range = (0, 450)
        self.monkey_top_bins = bin_count

        self.alpha = 0.5
        self.gamma = 0.5
        self.epsilon = 0.1

        self.current_state  = None
        self.last_state  = None
        self.last_action = None
        self.last_reward = None

        # dimensions of s
        dims = self.basis_dimensions()
        self.V = np.zeros(dims)
        self.R = np.zeros(dims + (2,))

        # self.N[s + a] = number of times we've taken action a from state s
        self.N = np.ones(dims + (2,))

        # self.Np[s + a + sp] = number of times we've transitioned to state sp
        # after taking action a in state s
        self.Np = np.zeros(dims + (2,) + dims)

        # note that P(sp | s,a) = self.Np[ s + a + (Ellipsis,) ] / self.N[(Ellipsis,) + a]

        'Number of times taken action a from each state s'
        self.k = np.ones(dims + (2,))

    def reset(self):
        self.current_state  = None
        self.last_state  = None
        self.last_action = None
        self.last_reward = None

    def action_callback(self, state):
        '''Implement this function to learn things and take actions.
        Return 0 if you don't want to jump and 1 if you do.'''


        # store state, last state for learning in reward_callback
        self.last_state  = self.current_state
        self.current_state = state
        s  = self.basis(state)

        # plan 
        if (random.random() < self.epsilon):
            new_action = random.choice((0,1))
        else:


            expected_values = np.array([ np.dot( (self.Np[ s + a + (Ellipsis,) ] / self.N[(Ellipsis,) + a]).flat, self.V.flat ) for a in [(0,), (1,)] ])
            new_action =  np.argmax(self.R[s + (Ellipsis,)] + )

        # store last action, record exploration
        self.last_action = new_action
        a  = (self.last_action,)
        self.k[s + a] += 1

        # learn the transition model
        if (self.last_state != None):
            s  = self.basis(self.last_state)
            sp = self.basis(self.current_state)
            a  = (self.last_action,)

            self.N[s + a] += 1
            self.Np[s + a + sp] += 1

        return self.last_action

    def reward_callback(self, reward):
        '''This gets called so you can see what reward you get.'''

        if (self.last_state != None) and (self.current_state != None) and (self.last_action != None):
            s  = self.basis(self.last_state)
            sp = self.basis(self.current_state)
            a  = (self.last_action,)


            alpha = 1.0 / self.k[s + a]

            # update V
            self.V[s] = self.V[s] + alpha * ( (reward + self.gamma * self.V[sp]) - self.V[s] )
            
            # update R
            self.R[s + a] = (self.R[s + a] * self.k[s + a] + reward) / (self.R[s + a] + 1)


        self.last_reward = reward


    def bin(self, value, range, bins):
        bin_size = (range[1] - range[0]) / bins
        return math.floor((value - range[0]) / bin_size)

    def basis_dimensions(self):
        return (\
            # self.tree_bot_bins, \
            self.tree_top_bins, self.tree_dist_bins, \
            self.monkey_vel_bins, \
            # self.monkey_bot_bins, \
            self.monkey_top_bins)

    def basis(self, state):
        return (\
                # self.bin(state["tree"]["bot"],self.tree_bot_range,self.tree_bot_bins),    \
                self.bin(state["tree"]["top"],self.tree_top_range,self.tree_top_bins),    \
                self.bin(state["tree"]["dist"],self.tree_dist_range,self.tree_dist_bins), \

                self.bin(state["monkey"]["vel"],self.monkey_vel_range,self.monkey_vel_bins), \
                # self.bin(state["monkey"]["bot"],self.monkey_bot_range,self.monkey_bot_bins), \
                self.bin(state["monkey"]["top"],self.monkey_top_range,self.monkey_top_bins))



def evaluate(gamma=0.4, iters=100, chatter=True):

    learner = TDValueLearner()
    learner.gamma = gamma

    highscore = 0
    avgscore = 0.0

    for ii in xrange(iters):

        learner.epsilon = 1/(ii+1)

        # Make a new monkey object.
        swing = SwingyMonkey(sound=False,            # Don't play sounds.
                             text="Epoch %d" % (ii), # Display the epoch on screen.
                             tick_length=1,          # Make game ticks super fast.
                             action_callback=learner.action_callback,
                             reward_callback=learner.reward_callback)

        # Loop until you hit something.
        while swing.game_loop():
            pass

        score = swing.get_state()['score']
        highscore = max([highscore, score])
        avgscore = (ii*avgscore+score)/(ii+1)

        if chatter:
            print ii, score, highscore, avgscore

        # Reset the state of the learner.
        learner.reset()

    return -avgscore


def find_hyperparameters():

    # find the best value for hyperparameters
    best_parameters = (0,0)
    best_value = 0
    for gamma in np.arange(0.1,1,0.1):
        parameters = {"gamma": gamma}
        value = evaluate(**parameters)
        if value < best_value:
            best_parameters = parameters
            print "Best: ",parameters, " : ", value


    print best_parameters
    return best_parameters

evaluate(iters=1000,gamma=0.4)
