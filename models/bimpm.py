# -*- coding: utf-8 -*-
"""Model graph of Bilateral Multi-Perspective Matching.
References:
    Bilateral Multi-Perspective Matching for Natural Language Sentences
"""
import sys
import numpy as np
from keras.layers import Input
from keras.models import Model
from keras.layers.merge import concatenate
import keras.backend as K
sys.path.append('utils/')
from multi_perspective import MultiPerspective
from layers import (
    WordRepresLayer, CharRepresLayer, ContextLayer, PredictLayer
)
from keras.models import *
from keras.layers import *
from keras.optimizers import *

import config
np.random.seed(2018)
def create_pretrained_embedding(pretrained_weights_path, trainable=False, **kwargs):
    "Create embedding layer from a pretrained weights array"
    pretrained_weights = np.load(pretrained_weights_path)
    in_dim, out_dim = pretrained_weights.shape
    embedding = Embedding(in_dim, out_dim, weights=[
                          pretrained_weights], trainable=True, **kwargs)
    return embedding

def bimpm():
    print('--- Building model...')
 

    emb_layer = create_pretrained_embedding(
        config.word_embed_weight, mask_zero=False)
    sequence_length = config.word_maxlen
    nb_per_word = 5
    rnn_unit = 'gru'
  
    
    dropout = 0.5
    context_rnn_dim =128
    mp_dim = 64
    highway = True
    aggregate_rnn_dim = 128
    dense_dim = 256


    # Model words input
    w1 = Input(shape=(sequence_length,), dtype='int32')
    w2 = Input(shape=(sequence_length,), dtype='int32')
    
    # Build word representation layer
 
    w_res1 = emb_layer(w1)
    w_res2 = emb_layer(w2)

 
    sequence1 = w_res1
    sequence2 = w_res2

    # Build context representation layer
    context_layer = ContextLayer(
        context_rnn_dim, rnn_unit=rnn_unit, dropout=dropout, highway=highway,
        input_shape=(sequence_length, K.int_shape(sequence1)[-1],),
        return_sequences=True)
    context1 = context_layer(sequence1)
    context2 = context_layer(sequence2)

    # Build matching layer
    matching_layer = MultiPerspective(mp_dim)
    matching1 = matching_layer([context1, context2])
    matching2 = matching_layer([context2, context1])
    matching = concatenate([matching1, matching2])

    # Build aggregation layer
    aggregate_layer = ContextLayer(
        aggregate_rnn_dim, rnn_unit=rnn_unit, dropout=dropout, highway=highway,
        input_shape=(sequence_length, K.int_shape(matching)[-1],),
        return_sequences=False)
    aggregation = aggregate_layer(matching)

    # Build prediction layer
    pred = PredictLayer(dense_dim,
                        input_dim=K.int_shape(aggregation)[-1],
                        dropout=dropout)(aggregation)
    if config.feats==[]:
         # Model words input
        megic_feats = Input(shape=(1,), dtype='int32')
    else:
        megic_feats = Input(shape=(len(config.feats),), dtype='int32')

    # Build model graph
    model = Model(inputs=[w1,w2,megic_feats],
                  outputs=pred)

    # Compile model
    model.compile(loss='binary_crossentropy',
                  optimizer='adam',
                  metrics=['accuracy'])
    print(model.summary())
    return model