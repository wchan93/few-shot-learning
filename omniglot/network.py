"""Helper class for building Siamese model for One-shot learning.

   @description
     For training, validating/evaluating & predictions with SiameseNetwork.

   @author
     Victor I. Afolabi
     Artificial Intelligence & Software Engineer.
     Email: javafolabi@gmail.com
     GitHub: https://github.com/victor-iyiola/

   @project
     File: network.py
     Package: omniglot
     Created on 1st August, 2018 @ 10:47 AM.

   @license
     MIT License
     Copyright (c) 2018. Victor I. Afolabi. All rights reserved.
"""
from omniglot import Dataset, BaseNetwork

import tensorflow as tf

from tensorflow import keras


class Network(BaseNetwork):
    """Light-weight implementation of the SiameseNetwork model."""

    def __init__(self, num_classes=1, **kwargs):
        super(Network, self).__init__(**kwargs)

    def build(self,  **kwargs):
        # Number of output classes.
        num_classes = kwargs.get('num_classes', 1)

        # Input pair inputs.
        pair_1st = keras.Input(shape=self._input_shape)
        pair_2nd = keras.Input(shape=self._input_shape)

        # Siamese Model.
        net = keras.models.Sequential()

        # 1st layer (64@10x10)
        net.add(keras.layers.Conv2D(filters=64, kernel_size=(10, 10),
                                    input_shape=self._input_shape,
                                    activation='relu'))
        net.add(keras.layers.MaxPool2D(pool_size=(2, 2)))

        # 2nd layer (128@7x7)
        net.add(keras.layers.Conv2D(filters=128, kernel_size=(7, 7),
                                    activation='relu'))
        net.add(keras.layers.MaxPool2D(pool_size=(2, 2)))

        # 3rd layer (128@4x4)
        net.add(keras.layers.Conv2D(filters=128, kernel_size=(4, 4),
                                    activation='relu'))
        net.add(keras.layers.MaxPool2D(pool_size=(2, 2)))

        # 4th layer (265@4x4)
        net.add(keras.layers.Conv2D(filters=256, kernel_size=(4, 4),
                                    activation='relu'))
        net.add(keras.layers.MaxPool2D(pool_size=(2, 2)))

        # 5th layer  (9216x4096)
        net.add(keras.layers.Flatten())
        net.add(keras.layers.Dense(units=4096, activation='sigmoid'))

        # Call the Sequential model on each input tensors with shared params.
        encoder_1st = net(pair_1st)
        encoder_2nd = net(pair_2nd)

        # Layer to merge two encoded inputs with the l1 distance between them.
        distance_layer = keras.layers.Lambda(self.dist_func)

        # Call this layer on list of two input tensors.
        distance = distance_layer([encoder_1st, encoder_2nd])

        # Model prediction: if image pairs are of same letter.
        output_layer = keras.layers.Dense(num_classes, activation='sigmoid')
        outputs = output_layer(distance)

        # Return a keras Model architecture.
        return keras.Model(inputs=[pair_1st, pair_2nd], outputs=outputs)

    def train(self, train_data: Dataset, valid_data: Dataset=None,
              batch_size: int=64, resume_training=True, **kwargs):

        # Set default keyword arguments.
        kwargs.setdefault('epochs', 1)
        kwargs.setdefault('steps_per_epoch', 128)
        kwargs.setdefault('verbose', self._verbose)

        # Get batch generators.
        train_gen = train_data.next_batch(batch_size=batch_size)

        # Resume training.
        if resume_training and tf.gfile.Exists(self._save_path):
            self.load_model()

        try:
            # Fit the network.
            if valid_data is None:
                # without validation set.
                self._model.fit_generator(train_gen, **kwargs)
            else:
                valid_gen = valid_data.next_batch(batch_size=batch_size)
                # with validation set.
                self._model.fit_generator(train_gen, validation_data=valid_gen,
                                          validation_steps=batch_size, **kwargs)
        except KeyboardInterrupt:
            # When training is unexpectedly stopped!
            self._log('\nTraining interrupted by user!')

        # Save learned weights after completed training or KeyboardInterrupt.
        self.save_model()
