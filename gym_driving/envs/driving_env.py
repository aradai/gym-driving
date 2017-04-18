from gym_driving.envs.environment import *
from gym_driving.envs.car import *
from gym_driving.envs.terrain import *

import logging
import math
import gym
from gym import spaces
from gym.utils import seeding
import numpy as np
import IPython
import pickle
import json

logger = logging.getLogger(__name__)

class DrivingEnv(gym.Env):
    """
    Generic wrapper class for simulating
    environments.
    """
    # metadata = {
    #     'render.modes': ['human', 'rgb_array'],
    #     'video.frames_per_second' : 50
    # }
    # def __init__(self, param_dict=None):
    def __init__(self, graphics_mode=True, screen=None, config_filepath=None):
        if config_filepath is None:
            param_dict = {
                'num_cpu_cars': 10, 
                'main_car_starting_angles': np.linspace(-30, 30, 5), 
                'cpu_cars_bounding_box': [[100.0, 1000.0], [-90.0, 90.0]],
                'screen_size': (512, 512),
                'logging_dir': None,
                'logging_rate': 10,
                'time_horizon': 100,
                'terrain_params': [[0, -2000, 20000, 38000, 'grass'], [0, 0, 20000, 200, 'road'], [0, 2000, 20000, 3800, 'grass']],
            }
        else:
            param_dict = json.load(open(config_filepath, 'r'))
        print(config_filepath)
        print(param_dict)

        self.num_cpu_cars = param_dict['num_cpu_cars']
        self.main_car_starting_angles = param_dict['main_car_starting_angles']
        self.cpu_cars_bounding_box = param_dict['cpu_cars_bounding_box']
        self.screen_size = param_dict['screen_size']
        self.logging_dir = param_dict['logging_dir']
        self.logging_rate = param_dict['logging_rate']
        self.time_horizon = param_dict['time_horizon']
        self.terrain_params = param_dict['terrain_params']
        self.state_space = param_dict['state_space']
        self.control_space = param_dict['control_space']
        self.param_dict = param_dict

        # Default options for PyGame screen, terrain
        if screen is None:
            screen = pygame.display.set_mode(self.screen_size)
            # pygame.display.set_caption('Driving Simulator')

        if self.logging_dir is not None and not os.path.exists(self.logging_dir):
            os.makedirs(self.logging_dir)
        self.screen = screen
        self.environment = Environment(graphics_mode=graphics_mode, screen_size=self.screen_size, \
                screen=self.screen, param_dict=self.param_dict)
        self.graphics_mode = graphics_mode

        low, high, step = param_dict['steer_action']
        if self.control_space == 'discrete':
            # 0, 1, 2 = Steer left, center, right
            action_space = np.linspace(low, high, step)
            self.action_space = spaces.Discrete(len(action_space) - 1)
        elif self.control_space == 'continuous':
            self.action_space = spaces.Box(low=low, high=high, shape=(1,))

        # TODO: Handle observation space for images
        # Limits on x, y, angle
        if self.state_space == 'positions':
            low = np.tile(np.array([-10000.0, -10000.0, 0.0]), self.num_cpu_cars + 1)
            high = np.tile(np.array([10000.0, 10000.0, 360.0]), self.num_cpu_cars + 1)
            self.observation_space = spaces.Box(low, high)
        elif self.state_space == 'image':
            w, h = param_dict['screen_size']
            self.observation_space = spaces.Box(low=0, high=255, shape=(w, h))
        self.exp_count = self.iter_count = 0
        
        # self._seed()
        # self.reset()
        # self.viewer = None

        # self.steps_beyond_done = None

        # # Just need to initialize the relevant attributes
        # self._configure()

    # def _configure(self, display=None):
    #     self.display = display

    # def _seed(self, seed=None):
    #     self.np_random, seed = seeding.np_random(seed)
    #     return [seed]

    def _render(self, mode='human', close=False):
        pass

    def _step(self, action):
        self.iter_count += 1
        action = np.array([action, 2])
        state, reward, done, info_dict = self.environment.step(action)
        # print(state, reward, done, info_dict)
        if self.logging_dir is not None and self.iter_count % self.logging_rate == 0:
            self.log_state(state)
        if self.iter_count >= self.time_horizon:
            done = True
        return state, reward, done, info_dict
        
    def _reset(self):
        self.exp_count += 1
        self.iter_count = 0
        self.screen = pygame.display.set_mode(self.screen_size)
        state = self.environment.reset(self.screen)
        # state = pygame.surfarray.array2d(self.screen).astype(np.uint8)
        return state

    def _render(self, mode='human', close=False):
        return None

    def log_state(self, state):
        if self.state_space == 'positions':
            file_name = 'log.txt'
            with open(file_name, 'a') as outfile:
                outfile.write(state)
        elif self.state_space == 'image':
            image_name = 'exp_{}_iter_{}.png'.format(self.exp_count, self.iter_count)
            image_path = os.path.join(self.logging_dir, image_name)
            pygame.image.save(self.screen, image_path)

    def simulate_actions(self, actions, noise=0.0, state=None):
        return self.environment.simulate_actions(actions, noise, state)

    def __deepcopy__(self, memo):
        env = DrivingEnv(graphics_mode=self.graphics_mode, \
            screen_size=self.screen_size, screen=None, terrain=None, \
            logging_dir=self.logging_dir, logging_rate=self.logging_rate, \
            param_dict=self.param_dict)
        return env