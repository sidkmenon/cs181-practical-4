import numpy as np
import numpy.random as npr
import sys
import math
import random

from SwingyMonkey import SwingyMonkey

class ModelBasedLearner:

    def __init__(self):
        self.tree_bot_range = (0, 400)
        self.tree_bot_bins = 10
        self.tree_top_range = (0, 400)
        self.tree_top_bins = 10
        self.tree_dist_range = (0, 600)
        self.tree_dist_bins = 10
        self.monkey_vel_range = (-50,50)
        self.monkey_vel_bins = 10
        self.monkey_bot_range = (0, 450)
        self.monkey_bot_bins = 10
        self.monkey_top_range = (0, 450)
        self.monkey_top_bins = 10

        self.gamma = 0.5

        dims = self.basis_dimensions()
        self.N = np.ones(dims + (2,))
        self.R = np.zeros(dims + (2,))
        self.Np = np.zeros(dims + (2,) + dims)

        self.Pi = np.zeros(dims)
        self.V = np.zeros(dims)

        self.current_state  = None
        self.last_state  = None
        self.last_action = None
        self.last_reward = None

    def reset(self):
        self.current_state  = None
        self.last_state  = None
        self.last_action = None
        self.last_reward = None

    def action_callback(self, state):
        '''Implement this function to learn things and take actions.
        Return 0 if you don't want to jump and 1 if you do.'''

        # You might do some learning here based on the current state and the last state.

        # You'll need to take an action, too, and return it.
        # Return 0 to swing and 1 to jump.

        new_action = self.Pi[self.basis(state)]

        # if self.N[self.basis(state)].any() == 0:
        #     new_action = np.argmax(self.R[self.basis(state)])
        # else:
        #     new_action = np.argmax(self.R[self.basis(state)]/self.N[self.basis(state)])

        new_state  = state

        self.last_action = new_action
        self.last_state  = self.current_state
        self.current_state = new_state

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
            a  = (self.last_action,)

            self.R[s + a] += self.last_reward
        
        self.last_reward = reward

    def bin(self, value, range, bins):
        bin_size = (range[1] - range[0]) / bins
        return math.floor((value - range[0]) / bin_size)

    def basis_dimensions(self):
        return (\
            self.tree_bot_bins, self.tree_top_bins, self.tree_dist_bins, \
            self.monkey_vel_bins, self.monkey_bot_bins, self.monkey_top_bins)

    def basis(self, state):
        return (self.bin(state["tree"]["bot"],self.tree_bot_range,self.tree_bot_bins),    \
                self.bin(state["tree"]["top"],self.tree_top_range,self.tree_top_bins),    \
                self.bin(state["tree"]["dist"],self.tree_dist_range,self.tree_dist_bins), \

                self.bin(state["monkey"]["vel"],self.monkey_vel_range,self.monkey_vel_bins), \
                self.bin(state["monkey"]["bot"],self.monkey_bot_range,self.monkey_bot_bins), \
                self.bin(state["monkey"]["top"],self.monkey_top_range,self.monkey_top_bins))

    def policy_iteration(self):
        # Update value function
        V_ = np.copy(self.V)

        for s, v in np.ndenumerate(self.V):
            a = (self.Pi[s],)
            # Here is the problem with the shapes of the matrices
            v = self.R[s + a] + self.gamma * np.dot(self.Np[s + a]/self.N[s + a], V_)
            self.V[s] = v

        # Update policy
        for s, v in np.ndenumerate(self.Pi):
            # Here is the problem with the shapes of the matrices
            v = np.argmax(self.R[s] + self.gamma * np.dot(self.Np[s]/self.N[s].reshape((2,1)), V_))
            self.Pi[s] = v

def evaluate(x, iters=50):

    learner = ModelBasedLearner()
    learner.gamma = x

    highscore = 0
    avgscore = 0.0

    for ii in xrange(iters):

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
        # print avgscore

        # Reset the state of the learner.
        learner.reset()
        # Try to work in a planning calculation for the policy iteration
        # learner.policy_iteration()

    print x, " : ", avgscore, highscore
    return -avgscore

best_parameters = 0
best_value = 0
for gamma in np.arange(0.4,0.5,0.02):
    parameters = gamma
    value = evaluate(parameters)
    if value < best_value:
        best_parameters = parameters
        print "Best: ", parameters, " : ", value

print best_parameters

'''
iters = 100
learner = ModelBasedLearner()

for ii in xrange(iters):

    # Make a new monkey object.
    swing = SwingyMonkey(sound=False,            # Don't play sounds.
                         text="Epoch %d" % (ii), # Display the epoch on screen.
                         tick_length=1,          # Make game ticks super fast.
                         action_callback=learner.action_callback,
                         reward_callback=learner.reward_callback)

    # Loop until you hit something.
    while swing.game_loop():
        pass

    # Reset the state of the learner.
    learner.reset()
'''