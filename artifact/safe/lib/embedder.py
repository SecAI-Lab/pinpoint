"""
Load SAFE's published frozen graph and run it.

SAFE ships its own loader (neural_network/SAFEEmbedder.py), but it is written
against TensorFlow 1: it calls tf.gfile, tf.GraphDef and tf.Session at the top
level, all of which TensorFlow 2 moved behind tf.compat.v1. Colab has shipped
TensorFlow 2 for years, so that loader raises

    AttributeError: module 'tensorflow' has no attribute 'gfile'

Patching a checkout of someone else's repository during install is worse than
not depending on the part that broke, so the twenty lines that matter are here
instead. The graph, its tensor names and the L2 normalization are SAFE's; only
the API calls around them are the compat.v1 spellings.

SAFE's tokenizer and normalizer (asm_embedding/) need only json and numpy, and
are used from the clone unchanged.

The graph runs on the CPU unless SAFE_DEVICE=gpu is set. Its recurrent network
is unrolled one step at a time, and on a GPU every step pays a fixed launch
overhead. An artifact reviewer measured about 2.5 ms per step at ~1% GPU
utilization, and SAFE running about 13x slower on the GPU. The device changes
only the running time, not the results.
"""
import os

import numpy as np

# Tensor names baked into SAFE's published graph.
IN_TOKENS = 'import/x_1:0'
IN_LENGTHS = 'import/lengths_1:0'
OUT_EMBEDDING = 'import/Embedding1/dense/BiasAdd:0'


class FrozenSAFE:
    def __init__(self, model_file):
        import tensorflow as tf
        if hasattr(tf, 'compat') and hasattr(tf.compat, 'v1'):
            tf = tf.compat.v1
            tf.disable_v2_behavior()
        self._tf = tf

        with tf.gfile.GFile(str(model_file), 'rb') as f:
            graph_def = tf.GraphDef()
            graph_def.ParseFromString(f.read())
        with tf.Graph().as_default() as graph:
            tf.import_graph_def(graph_def)

        self.use_gpu = os.environ.get('SAFE_DEVICE', 'cpu').lower() == 'gpu'
        if self.use_gpu:
            config = tf.ConfigProto()
            # Colab hands the whole GPU to the process by default, which would
            # leave nothing for the BinShot half of a run sharing the session.
            config.gpu_options.allow_growth = True
        else:
            # Hide the GPU from this session only; see the module docstring.
            config = tf.ConfigProto(device_count={'GPU': 0})
        self.session = tf.Session(graph=graph, config=config)

        g = self.session.graph
        self.x = g.get_tensor_by_name(IN_TOKENS)
        self.lengths = g.get_tensor_by_name(IN_LENGTHS)
        # SAFE compares embeddings by cosine similarity, and normalizing here
        # makes that a dot product downstream.
        self.emb = tf.nn.l2_normalize(g.get_tensor_by_name(OUT_EMBEDDING), axis=1)

    def embed(self, token_ids, lengths):
        return self.session.run(self.emb, feed_dict={self.x: np.stack(token_ids),
                                                     self.lengths: np.array(lengths)})

    def device(self):
        """'GPU' or 'CPU', for the run banner."""
        if not self.use_gpu:
            return 'CPU (set SAFE_DEVICE=gpu to use the GPU)'
        try:
            gpus = self._tf.config.list_physical_devices('GPU')
        except AttributeError:
            gpus = self._tf.test.is_gpu_available()
            return 'GPU' if gpus else 'CPU'
        return 'GPU' if gpus else 'CPU'
