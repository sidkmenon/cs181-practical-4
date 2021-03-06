import numpy as np
import numpy.random as npr
import scipy.linalg
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

        self.epsilon = 0

        dims = self.basis_dimensions()
        self.N = np.ones(dims + (2,))
        self.R = np.zeros(dims + (2,))
        self.Np = np.zeros(dims + (2,) + dims)

        self.Pi = np.zeros(dims)
        self.V = np.zeros(dims)

        self.Q = np.zeros(dims + (2,))

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

        if (random.random() < self.epsilon):
            new_action = random.choice((0,1))
        else:
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
            # self.tree_bot_bins, \
            self.tree_top_bins, \
            self.tree_dist_bins, \
            # self.monkey_vel_bins, \
            # self.monkey_bot_bins, \
            self.monkey_top_bins)

    def basis(self, state):
        return (\
                # self.bin(state["tree"]["bot"],self.tree_bot_range,self.tree_bot_bins),    \
                self.bin(state["tree"]["top"],self.tree_top_range,self.tree_top_bins),    \
                self.bin(state["tree"]["dist"],self.tree_dist_range,self.tree_dist_bins), \

                # self.bin(state["monkey"]["vel"],self.monkey_vel_range,self.monkey_vel_bins), \
                # self.bin(state["monkey"]["bot"],self.monkey_bot_range,self.monkey_bot_bins), \
                self.bin(state["monkey"]["top"],self.monkey_top_range,self.monkey_top_bins))

    def solve_V(self, pi):
        '''
        returns: vector of length S for self.V

        ex. S = 2

        solve for A * x = B, where

            [ 1     0     0  ]
            |                |
        A = [ r_1   t_1   t_2]
            |                |
            [ r_2   t_3   t_4]

            [ 1 ] 
        x = [v_1]
            [v_2]


            [ 1 ] 
        B = [v_1]
            [v_2]

        '''
        reward = np.array([1])
        for s in np.ndindex(np.shape(self.Pi)):
            np.append(reward, self.R[s + (self.Pi[s],)])

        A = np.insert(np.insert(self.transition_matrix(),0,0,axis=0),0,reward,axis=1)
        B = np.insert(self.V,0,1)
        self.V = np.linalg.solve(A,B)[1:]

    def transition_matrix(self):
        '''
        returns: S x S transition matrix with probabilities from all states s given action a to all states s'

        ex. S = 2

        T = [ t_1 t_2 ]
            [ t_3 t_4 ]

        '''
        transition = []
        for s in np.ndindex(np.shape(self.Pi)):
            transition.append([(self.Np[s + (self.Pi[s],) + (Ellipsis,)] / self.N[(Ellipsis,) + (self.Pi[s],)]).flatten()])
        transition = np.concatenate(tuple(transition),axis=0)
        return transition


    def policy_iteration(self):
        # Update policy iteration
        while True:
            Pi_copy = np.copy(self.Pi)

            self.solve_V(Pi_copy)

            for s in np.ndindex(np.shape(self.Pi)):
                for a in [(0,),(1,)]:
                    self.Q[s + a] = self.R[s + a] + self.gamma * np.dot((self.Np[s + a + (Ellipsis,)] / self.N[(Ellipsis,) + a]).flat, self.V.flat)
                self.Pi[s] = np.argmax(self.Q[s])
                print "test"

            if np.array_equal(self.Pi, Pi_copy):
                break

    def value_iteration(self):
        while True:
            V_copy = np.copy(self.V)

            for s in np.ndindex(np.shape(self.Pi)):
                expected_values = np.array([ np.dot( (self.Np[ s + a + (Ellipsis,) ] / self.N[(Ellipsis,) + a]).flat, V_copy.flat ) for a in [(0,), (1,)] ])
                self.Pi[s] = np.argmax(self.R[s + (Ellipsis,)] + self.gamma * expected_values)
                self.V[s] = np.max(self.R[s + (Ellipsis,)] + self.gamma * expected_values)

            print np.count_nonzero(self.Pi)

            if np.isclose(self.V, V_copy, atol=0.1, rtol=0.0).all():
                break

def evaluate(gamma=0.4, iters=100, chatter=True):

    learner = ModelBasedLearner()
    learner.gamma = gamma

    highscore = 0
    avgscore = 0.0

    if chatter:
        print "epoch", "\t", "score", "\t", "high", "\t", "avg"

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
            print ii, "\t", score, "\t", highscore, "\t", avgscore

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