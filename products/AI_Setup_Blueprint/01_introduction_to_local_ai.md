# 01 INTRODUCTION TO LOCAL AI.MD

# Module Title: Introduction to Local AI

Welcome to the first module of our comprehensive course on setting up an artificial intelligence environment. In this initial session focused entirely upon local setups for Artificial Intelligence (AI), we'll explore foundational concepts and practical implementations.

## Objectives
- Understand key components in a locally installed, self-contained machine learning system.
- Configure Python programming essentials tailored specifically toward AI development within your own computer setup without relying on cloud services or external APIs. 
- Gain familiarity with essential tools like Jupyter Notebooks for data exploration combined with Pandas and Matplotlib libraries to visualize results.

## Prerequisites
To follow through this module seamlessly, please ensure you have the following installed:
1. Python 3.x (Preferably via Anaconda distribution)
2. Basic knowledge of programming in python 
3. Familiarity using command line interface.
4. Installed Jupyter Notebook and a text editor for coding.

## Setup Instructions

### Step 1: Install Required Packages
Open your terminal or command prompt, navigate to the project directory you want as per below:

```bash
cd /path/to/your/project/directory/
```

Then run these commands:
- To install Python packages via pip (Python package manager):

    ```bash 
    pip3.7 install pandas matplotlib jupyter notebook scikit-learn tensorflow numpy seaborn tqdm scipy psutil joblib torch requests yfinance urllib library
    ```

  Or use Anaconda to create a virtual environment for our project.

- To do this, run: 

   `conda env list` 
   
If no conda environments exist or you want an isolated Python setup:
  
```bash
conda create --name ai_local python=3.7 -y; source activate ai_local;
```

### Step 2: Verify Installation

- To check if all packages are correctly installed, run:

 ```python
 import pandas as pd 
 import matplotlib.pyplot as plt 

 print(pd.__version__)
 print(plt.__version__)
 ```
 If you see versions of the libraries listed above without errors in your terminal output then you're good to proceed.

### Step 3: Launch Jupyter Notebook

Run this command from within project directory:

 ```bash
 jupyter notebook --no-browser
 ```

This will launch a web browser pointing directly at `localhost` and listening for connections on port number (8888) of the IP address you are currently using. 

From here, we'll jump straight into building our first simple AI model with Jupyter Notebook by writing Python code.

## Hands-On Tasks

1. **Data Exploration**
- Load a sample dataset: Pandas DataFrame
  ```python 
  import pandas as pd 
  
  # load the iris dataset from seaborn's online repository.
  data = pd.read_csv("https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv")
  
  print(data.head()) 
  ```

2. **Data Visualization**
- Visualize distributions of features in a sample dataset using Pandas and Matplotlib
 ```python
  
 import pandas as pd 
  
 # load the iris dataset from seaborn's online repository.
 data = pd.read_csv("https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv")
 
 sns.set_style({"color_codes": True})
 ax =  sns.catplot(x="species", hue="species",
                 kind="count", data=data)
 ```

3. **Simple AI Model using Tensorflow**
- Build and train a simple neural network to classify iris species.
 ```python
 import tensorflow as tf
 
 # Load the Iris dataset from seaborn's online repository in CSV format.
 df = pd.read_csv("https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv")

 X_train, y_train, X_test, y_test = train_test_split(df.drop('species', axis=1),df['species'], random_state=0)
 

 model=tensorflow.keras.models.Sequential([ 
   tensorflow.keras.layers.Dense(10,input_shape=(4,), activation='relu'), #  Input Layer (X Train shape) -> Dense Neuron with ReLU Activations
   tensorflow.keras.layers.Dense(8,activation="relu"),# Second dense layer of neurons-> Activation Function
   tensorflow.keras.layers.Dense(3,batch_norm=True), # Third Dense Neural Network output node(s)-> Batch Normalization --> Softmax activation function for multi-class classification problem.
 ])

 model.compile(loss='sparse_categorical_crossentropy',optimizer=tf.keras.optimizers.Adam(lr=0.01),
               metrics=['accuracy'])

 history=model.fit(X_train,y_train,epochs = 10000,batch_size=3)
 ```

### Summary
In this session we have:
- Installed required packages for building AI locally.
- Checked installation status of python dependencies using pip and conda virtual environments respectively to avoid conflicts with existing Python installations in your system. 
- Launched Jupyter Notebook as an interactive development environment (IDE) which allows us to easily develop, test code snippets interactively within the browser without leaving our machine setup.

Congratulations! You now have a strong foundation for building locally installed AI systems using advanced techniques and concepts that will be explored throughout this course!

## Next Steps
In subsequent sessions we'll dive deeper into more complex architectures involving deep learning models such as CNNs (Convolutional Neural Networks) and RNNs (Recurrent neural networks), exploring libraries like PyTorch, Keras etc. We'll also explore the nuances of training AI systems locally using distributed computing techniques to maximize efficiency while minimizing resource costs.

Stay tuned for our next session where we'll focus on more complex scenarios involving time-series data analysis in a local setup. Happy learning!