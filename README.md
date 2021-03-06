# Classification-by-Components: Probabilistic Modeling of Reasoning over a Set of Components

[![License](https://img.shields.io/pypi/l/Django.svg)](https://github.com/saralajew/cbc_networks/blob/master/LICENSE)

This repository contains both the scripts required to reproduce the 
experiments presented in the corresponding paper as well as the package 
developed to create CBCs in Keras.

The full paper is available in the [online proceedings of NeurIPS2019.](https://papers.nips.cc/paper/8546-classification-by-components-probabilistic-modeling-of-reasoning-over-a-set-of-components)

## Abstract
Neural networks are state-of-the-art classification approaches but are generally difficult to interpret. This issue can be partly alleviated by constructing a precise decision process within the neural network. In this work, a network architecture, denoted as Classification-By-Components network (CBC), is proposed. It is restricted to follow an intuitive reasoning based decision process inspired by Biederman's recognition-by-components theory from cognitive psychology. The network is trained to learn and detect generic components that characterize objects. In parallel, a class-wise reasoning strategy based on these components is learned to solve the classification problem. In contrast to other work on reasoning, we propose three different types of reasoning: positive, negative and indefinite. These three types together form a probability space to provide a probabilistic classifier. The decomposition of objects into generic components combined with the probabilistic reasoning provides by design a clear interpretation of the classification decision process. The evaluation of the approach on MNIST shows that CBCs are viable classifiers. Additionally, we demonstrate that the inherent interpretability offers a profound understanding of the classification behavior such that we can explain the success of an adversarial attack. The method's scalability is successfully tested using the ImageNet dataset.

## CBC Keras package installation
The Keras package for CBCs is divided into three submodules, layers, utils 
and visualizations. The layer module contains all layers required to handle 
the components, the detection probability functions and the reasoning. The 
visualization module contains methods for creating the visualizations, most 
of which are presented in Sec. 4.1.2. Lastly, the utils module contains 
additional activation functions, callbacks, constraints and loss functions 
such as the euclidean normalization and margin loss function. 

### Keras installation

The package requires a working installation of the latest Keras version with
a **backend of your choice**. Please, make sure that you **installed Keras 
properly** before you proceed with the installation of this package.
See [here](https://github.com/keras-team/keras) for the installation 
instructions of Keras.

**If you use Tensorflow as backend, then please use Tensorflow 1. We observed
 problems with Tensorflow 2!**

### CBC package installation

We recommend using Python 3, as no other version has been tested 
yet. Additionally, the ImageNet experiment requires tensorflow-gpu as 
backend (see `extras_require` in `setup.py`).

Clone this repository by calling

```
git clone https://github.com/saralajew/cbc_networks.git
cd cbc_networks
```

Install the package with pip after cloning. In the 
root directory (where `setup.cfg` and `setup.py` are) call

```
pip install -e .
```

## Paper experiments
The scripts that can be used to replicate the results in the paper are 
organized by section. The script for each experiment is accompanied with 
a short README that explains how the script can be used. 
