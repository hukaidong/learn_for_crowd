#!/usr/bin/env python
# encoding: utf-8

import model
import tensorflow as tf

from graph import Graph
from params import params
from params import dump
from path import Path

class Train(object):
    def __init__(self, x, y_):
        cut = int(x.shape[0] * params.test_partial)
        x_tr, y_tr = x[:cut, :], y_[:cut, :]
        x_te, y_te = x[cut:, :], y_[cut:, :]
        self.x_tr = x_tr
        self.y_tr = y_tr
        self.x_te = x_te
        self.y_te = y_te
        pardim = x.shape[1]
        if params.add_noise:
            pardim += 1
        tardim = y_.shape[1]
        self.graph = Graph(pardim, tardim)

    def train(self, steps = params.train_steps):
        outpd = Path(params.outp_dir)
        with tf.Session() as sess:
            init = tf.global_variables_initializer()
            sess.run(init)
            saver = tf.train.Saver()
            writer = tf.summary.FileWriter(
                outpd, sess.graph)
            ckpt = tf.train.get_checkpoint_state(outpd)
            if ckpt:
                saver.restore(sess, ckpt.model_checkpoint_path)
            for step in range(steps):
                self._trainer(sess)
                if step % 100 == 0:
                    R, g, s= self._analysiser(sess)
                    print("Steps", g,": RMSE", R)
                    saver.save(sess, outpd/"model",
                               global_step=g)
                    writer.add_summary(s, g)

    def _trainer(self, sess):
        x, y_ = self.sample(test=False)
        sess.run([self.graph.train_op],
                 feed_dict=self.graph.feed_dict(x, y_, False))

    def _analysiser(self, sess):
        x, y_ = self.sample(test=True)
        (R,A,Z,logZ), g, sum = sess.run([self.graph.sum, self.graph.g, self.graph.analysis],
                        feed_dict=self.graph.feed_dict(x, y_, True))
        dump(Path(params.outp_dir)/"RAZ.txt",
             {
                 "R": R,
                 "A": A,
                 "Z": Z,
                 "logZ": logZ,
                 "global_steps": g
             })
        return R,g, sum

    def sample(self, test=False):
        if not test:
            xs, ys = model.sampling(
                self.x_tr, self.y_tr, params.batch_size)
            nxs = model.add_noise(xs ) if params.add_noise else xs
        else:
            xs, ys = self.x_te, self.y_te
            nxs = model.add_noise(xs, zeros=True) if params.add_noise else xs
        return nxs, ys

if __name__ == "__main__":
    from loader import load
    t = Train(*load())
    t.train()







