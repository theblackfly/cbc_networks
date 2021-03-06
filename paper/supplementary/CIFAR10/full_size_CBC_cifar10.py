# -*- coding: utf-8 -*-
"""Implementation of the full size CBC on CIFAR-10 from the paper.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import os

from keras.layers import *
from keras.models import Model
from keras.datasets import cifar10
from keras import callbacks
from keras.optimizers import Adam
from keras.utils import to_categorical
from keras.preprocessing.image import ImageDataGenerator
from keras import backend as K
from keras.losses import MSE

from keras_cbc.layers.component_input import \
    ConstantInput, AddComponents
from keras_cbc.layers.detection_probability_functions import \
    CosineSimilarity2D
from keras_cbc.layers.reasoning_layers import Reasoning
from keras_cbc.utils.constraints import \
    euclidean_normalization, clip
from keras_cbc.utils.losses import MarginLoss
from keras_cbc.utils.activations import swish
from keras_cbc.visualizations.basic_visualizations import \
    plot_components, plot_simple_reasoning
from keras_cbc.utils.callbacks import LossScheduler
from keras_cbc.utils.evaluation import statistics


def get_data():
    (x_train, y_train), (x_test, y_test) = cifar10.load_data()

    x_train = x_train.reshape(-1, 32, 32, 3).astype('float32') / 255
    x_test = x_test.reshape(-1, 32, 32, 3).astype('float32') / 255
    y_train = to_categorical(y_train.astype('float32'))
    y_test = to_categorical(y_test.astype('float32'))

    return (x_train, y_train), (x_test, y_test)


class Backbone(object):
    """Feature extractor of a CBC with support of the special Siamese
    training procedure.

    We use this class to realize our special training setting where the
    gradient back flow to feature extractor weights is just realized over the
    Siamese network path where input images are preprocessed. For the
    component processing Siamese path no gradient back flow to feature
    extractor layer weights is realized and the gradient is only pushed to
    the components. Via this implementation we can train the components in
    the input space.

    If a 'dependent_backbone' is given, then it is assumed that they share
    the same architecture. In this case the layers are initialized as non-
    trainable and as dependent on the weights of the given backbone. The
    dependency is realized by copying all the weights at the beginning of
    each batch from the 'dependent_backbone' to the own weights. The method
    'copy_weights' is used for that in combination with a custom callback.

    Keep care if you use batch normalization as it requires a special
    treatment.

    We know that the copying of weights is not efficient in terms of
    computational overhead. But we see now other workaround to realize that
    in Keras.
    """

    def __init__(self, dependent_backbone=None):

        self.dependent_backbone = dependent_backbone
        if dependent_backbone is not None:
            self.trainable = False
        else:
            self.trainable = True

        self.layers = [
            Conv2D(filters=32,
                   kernel_size=(3, 3),
                   activation=swish,
                   kernel_constraint=euclidean_normalization,
                   use_bias=True,
                   padding='valid',
                   trainable=self.trainable),
            Conv2D(filters=64,
                   kernel_size=(3, 3),
                   activation=swish,
                   kernel_constraint=euclidean_normalization,
                   use_bias=True,
                   padding='valid',
                   trainable=self.trainable),
            MaxPool2D(pool_size=(2, 2)),
            Conv2D(filters=64,
                   kernel_size=(3, 3),
                   activation=swish,
                   kernel_constraint=euclidean_normalization,
                   use_bias=True,
                   padding='valid',
                   trainable=self.trainable),
            Conv2D(filters=128,
                   kernel_size=(3, 3),
                   activation=swish,
                   kernel_constraint=euclidean_normalization,
                   use_bias=True,
                   padding='valid',
                   trainable=self.trainable),
            MaxPool2D(pool_size=(2, 2))]

    def __call__(self, inputs, *args, **kwargs):
        x = inputs
        for i, layer in enumerate(self.layers):
            x = layer(x)
        return x

    def copy_weights(self):
        for i, layer in enumerate(self.dependent_backbone.layers):
            self.layers[i].set_weights(layer.get_weights())


def model(input_shape,
          n_classes,
          n_components,
          component_shape,
          components_initializer,
          reasoning_initializer):
    """Defines the CBC model in the Siamese setting.

    # Arguments:
        input_shape: List/tuple of three integers, specifying the shape of
            the input data (rows, cols, channels).
        n_classes: Integer, specifying the number of classes.
        n_components: Integer, specifying the number of trainable components
            in the input space.
        component_shape: List/tuple of three integers, specifying the shape
            of a component (rows, cols, channels).
        components_initializer: Numpy array, that is used as
            initialization for the components.
        reasoning_initializer: Numpy array, that is used as
            initialization for the reasoning matrix.

    # Returns:
        A list of two objects:
            [0]: keras CBC model
            [1] backbone with non trainable weights which must be passed
                to the callback.
    """
    # initialize the two paths of the Siamese network
    backbone = Backbone()
    backbone_fix = Backbone(dependent_backbone=backbone)

    # initialize the two input sources for the Siamese network
    data_input = Input(shape=input_shape, name='model_input')
    components_input = ConstantInput(np.zeros((1,)), name='components')()

    # call input data processing path of the Siamese network
    data_output = backbone(data_input)

    # call component processing path of the Siamese network
    add_components = AddComponents(shape=(n_components,) + component_shape,
                                   trainable=True,
                                   initializer=(lambda x:
                                                components_initializer),
                                   constraint=clip,
                                   name='add_components_1')
    components = add_components(components_input)
    components_output = backbone_fix(components)

    # CBC layers: detection followed by reasoning
    detection = CosineSimilarity2D(
        padding='valid', activation='relu')([data_output, components_output])
    # Squeeze one dimensions
    detection = Lambda(lambda x: K.squeeze(K.squeeze(x, 1), 1))(detection)

    reasoning = Reasoning(n_classes=n_classes,
                          reasoning_initializer=(lambda x:
                                                 reasoning_initializer),
                          name='reasoning_1')

    probabilities = reasoning(detection)

    return Model([data_input, components_input], probabilities), backbone_fix


def eval_plots(eval_model, save_dir):
    """Create the component and reasoning matrix plots.

    # Arguments:
        eval_model: Keras CBC model which should be evaluated.
        save_dir: String, specifying the output path.
    """
    save_dir = save_dir + '/eval/'

    # get weights
    components = eval_model.get_layer('add_components_1').get_weights()[0]
    reasoning_weights = eval_model.get_layer('reasoning_1').get_weights()[0]

    # plots
    plot_components(components, save_dir + '/components/')
    plot_simple_reasoning(reasoning_weights, save_dir + '/reasoning_matrices/')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights",
                        help="Load h5 model trained weights")
    parser.add_argument('--save_dir', default='./output')
    parser.add_argument('--epochs', default=475, type=int)
    parser.add_argument('--lr', default=0.001, type=float,
                        help="Initial learning rate of Adam.")
    parser.add_argument('--batch_size', default=128, type=int)
    parser.add_argument('--gpu', default=0, type=int,
                        help="Select the GPU used for training.")
    parser.add_argument('--eval', action='store_true',
                        help="Evaluation mode: visualizing the trained model.")
    args = parser.parse_args()

    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    os.environ["CUDA_VISIBLE_DEVICES"] = str(args.gpu)

    if not os.path.exists(args.save_dir):
        os.makedirs(args.save_dir)

    (x_train, y_train), (x_test, y_test) = get_data()

    # reasoning and components initializer by class means
    tmp = []
    reasoning_initializer = np.zeros((2, 1, 10, 10))
    for i in range(10):
        tmp.append(np.expand_dims(np.mean(x_train[np.argmax(y_train, -1) == i],
                                          axis=0), 0))
        reasoning_initializer[0, 0, i, i] = 1
    components_initializer = np.concatenate(tmp, axis=0)

    train_model, backbone_fix = model(
        input_shape=x_test.shape[1:],
        n_classes=10,
        n_components=10,
        component_shape=x_test.shape[1:],
        components_initializer=components_initializer,
        reasoning_initializer=reasoning_initializer)

    train_model.summary()

    if args.weights:
        train_model.load_weights(args.weights)

    train_datagen = ImageDataGenerator(width_shift_range=2,
                                       height_shift_range=2,
                                       rotation_range=15)

    generator = train_datagen.flow(x_train,
                                   y_train,
                                   batch_size=args.batch_size)

    train_model.compile(optimizer=Adam(lr=args.lr),
                        loss=MSE,
                        metrics=['accuracy'])

    if not args.eval:
        # Callbacks
        checkpoint = callbacks.ModelCheckpoint(
            args.save_dir + '/weights-{epoch:02d}.h5', save_best_only=True,
            save_weights_only=True, verbose=1)
        csv_logger = callbacks.CSVLogger(args.save_dir + '/log.csv')
        lr_reduce = callbacks.ReduceLROnPlateau(factor=0.9,
                                                monitor='val_loss',
                                                mode='min',
                                                verbose=1,
                                                patience=5)
        copy_weights = callbacks.LambdaCallback(
            on_batch_begin=lambda batch, logs: backbone_fix.copy_weights())
        loss_scheduler = LossScheduler(losses=[MarginLoss(0.1),
                                               MarginLoss(0.2),
                                               MarginLoss(0.3)],
                                       epochs=[25, 175, 325],
                                       optimizer=Adam(lr=args.lr),
                                       metrics=['accuracy'],
                                       reduce_lr_on_plateau=lr_reduce)

        callbacks = [checkpoint, lr_reduce, csv_logger,
                     copy_weights, loss_scheduler]

        train_model.fit_generator(
            generator=generator,
            steps_per_epoch=int(y_train.shape[0] / args.batch_size),
            epochs=args.epochs,
            validation_data=[x_test, y_test],
            callbacks=callbacks,
            verbose=1)

        train_model.save_weights(args.save_dir + '/trained_model.h5')

    # --- evaluation
    # compute statistics on the test dataset
    path = args.save_dir + '/statistics.txt'
    statistics(x_train, y_train, x_test, y_test, train_model, path)

    # plot reasoning process
    eval_plots(train_model, save_dir=args.save_dir)
