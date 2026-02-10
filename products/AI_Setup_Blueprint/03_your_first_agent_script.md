# 03 YOUR FIRST AGENT SCRIPT.MD

```markdown
# Your First Agent Script

Welcome to the third module of our *AI Setup Blueprint* course. In today's session, we'll dive into creating your very first agent script using Python and a popular AI framework like OpenAI Gym.

## Prerequisites:

- Basic knowledge in programming (Python recommended)
- Familiarity with concepts related to machine learning or artificial intelligence
- An installed version of an appropriate environment for running the code snippets

Let's get straight to action!

### Step 1: Setting Up Your Environment

First, make sure you have Python and necessary libraries installed. Create a virtual environment if you're not familiar:

```bash
python -m venv env
source env/bin/activate # On Windows use `.\env\Scripts\Activate`
```

Install the required packages by running these commands in your terminal or command prompt.

```bash
pip install gym torch numpy
```

### Step 2: Importing Libraries

Create a Python script file and import all essential libraries:

```python
import os
import random
from pathlib import Path
import time
import datetime as dt
import pandas as pd
import numpy as np

# For OpenAI Gym environments
import gym
import torch

# Set the device to GPU if available, else CPU.
device = "cuda" if torch.cuda.is_available() else "cpu"
```

### Step 3: Initializing Your Agent Environment and Model Skeletons

Set up a basic environment using an existing one from OpenAI Gym:

```python
env_name = 'CartPole-v1'
env = gym.make(env_name)
state_space_size, action_space_size = env.observation_space.shape[0], env.action_space.n

# Initialize your agent's model skeleton here (if applicable).
class Agent:
    def __init__(self):
        pass  # Define the initialization logic for future extensions.
```

### Step 4: Writing Your First Action Functionality Script

Implement a basic function to perform an action and receive feedback:

```python
def sample_action(env, agent_state_dict=None):  
    if random.uniform(0,1) < epsilon:
        env.action_space.sample() # Explore with any randomly chosen number.
    else:
        selected_action = ...  # Add your model's logic here for choosing actions based on states

# Placeholder to show action is executed and state received
next_state, reward, done, _=env.step(sampled_action)
```

### Step 5: Collecting Experiences & Learning (Skeleton)

Set up a loop structure that collects experiences until certain conditions are met:

```python
for i in range(50000):
    next_state, rewards, dones, info = env.step(actions[i])
    
# Here you can define your logic for learning from each experience.
```

### Step 6: Saving and Loading Your Agent's Experiences (Skeleton)

Implement saving experiences to a file or database:

```python
def save_experience(experiences):
    with open('agent_data.pkl', 'wb') as f:
        pickle.dump(experiences, f)
    
# Load function would be similarly defined.
```

### Final Thoughts

This is just the foundation of your agent script. There are endless possibilities for improving its architecture and performance by integrating neural networks or leveraging reinforcement learning techniques.

Remember to always save progress periodically with functions like `save_experience`.

Happy scripting! Get back on day 04, where we will explore complex environments.
```

Note: The above module is a skeleton that you can build upon. Flesh out the agent model's logic based on your preferred machine learning strategy (Q-Learning, DQN, etc.). Remember to replace placeholders with actual code as necessary.