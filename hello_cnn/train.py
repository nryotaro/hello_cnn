# -*- coding: utf-8 -*-
import tensorflow as tf
import os
import time
import datetime


# Training parameters
tf.flags.DEFINE_integer("batch_size", 64, "Batch Size (default: 64)")
tf.flags.DEFINE_integer(
    "evaluate_every", 100,
    "Evaluate model on dev set after this many steps (default: 100)")
tf.flags.DEFINE_integer(
    "num_checkpoints", 5,
    "Number of checkpoints to store (default: 5)")
tf.flags.DEFINE_integer(
    "checkpoint_every", 100,
    "Save model after this many steps (default: 100)")
# Misc Parameters
tf.flags.DEFINE_boolean(
    "allow_soft_placement", True,
    "Allow device soft device placement")
tf.flags.DEFINE_boolean(
    "log_device_placement", False,
    "Log placement of ops on devices")

FLAGS = tf.flags.FLAGS
FLAGS._parse_flags()


class Cnn(object):
    """
    TODO:
        summary
        checkpoint

    Properties:
        loss
        accuracy
    """
    def __init__(self):

        pass


def train():
    with tf.Graph().as_default():

        session_conf = tf.ConfigProto(
            # Allow device soft device placement
            # If you would like TensorFlow to automatically choose an existing
            # and supported device to run the operations
            # in case the specified one doesn't exist,
            # you can set allow_soft_placement
            allow_soft_placement=FLAGS.allow_soft_placement,
            # Log placement of ops on devices
            # To find out which devices your operations and
            # tensors are assigned to,
            # create the session with log_device_placement configuration
            # option set to True.
            log_device_placement=FLAGS.log_device_placement)
        sess = tf.Session(config=session_conf)

        with sess.as_default():
            cnn = Cnn()
            # Define Training procedure
            # global_step refer to the number of batches seen by the graph.
            # Everytime a batch is provided,
            # the weights are updated in the direction that minimizes the loss.
            # global_step just keeps track of the number of batches seen so far
            global_step = tf.Variable(0, name="global_step", trainable=False)

            # minimize simply combine
            # calls compute_gradients() and apply_gradients()
            optimizer = tf.train.AdamOptimizer(1e-3)
            # List of (gradient, variable) pairs
            grads_and_vars = optimizer.compute_gradients(cnn.loss)
            train_op = optimizer.apply_gradients(
                grads_and_vars, global_step=global_step)

            # Keep track of gradient values and sparsity (optional)
            grad_summaries = []
            for g, v in grads_and_vars:
                if g is not None:
                    grad_hist_summary = tf.summary.histogram(
                        "{}/grad/hist".format(v.name), g)

                    # tf.nn.zero_fraction
                    # Returns the fraction of zeros in value.
                    # If value is empty, the result is nan.
                    # This is useful in summaries to
                    # measure and report sparsity.
                    sparsity_summary = tf.summary.scalar(
                        "{}/grad/sparsity".format(v.name),
                        tf.nn.zero_fraction(g))
                    grad_summaries.append(grad_hist_summary)
                    grad_summaries.append(sparsity_summary)
            grad_summaries_merged = tf.summary.merge(grad_summaries)

            # Output directory for models and summaries
            timestamp = str(int(time.time()))
            out_dir = os.path.abspath(
                os.path.join(os.path.curdir, "runs", timestamp))
            print("Writing to {}\n".format(out_dir))

            # Summaries for loss and accuracy
            loss_summary = tf.summary.scalar("loss", cnn.loss)
            acc_summary = tf.summary.scalar("accuracy", cnn.accuracy)

            # Train Summaries
            train_summary_op = tf.summary.merge(
                [loss_summary, acc_summary, grad_summaries_merged])
            train_summary_dir = os.path.join(out_dir, "summaries", "train")
            train_summary_writer = tf.summary.FileWriter(
                train_summary_dir, sess.graph)

            # Dev summaries
            dev_summary_op = tf.summary.merge([loss_summary, acc_summary])
            dev_summary_dir = os.path.join(out_dir, "summaries", "dev")
            dev_summary_writer = tf.summary.FileWriter(
                dev_summary_dir, sess.graph)

            # Checkpoint directory. Tensorflow assumes
            # this directory already exists so we need to create it
            checkpoint_dir = os.path.abspath(
                os.path.join(out_dir, "checkpoints"))
            checkpoint_prefix = os.path.join(checkpoint_dir, "model")
            if not os.path.exists(checkpoint_dir):
                os.makedirs(checkpoint_dir)
            saver = tf.train.Saver(
                tf.global_variables(), max_to_keep=FLAGS.num_checkpoints)

            # Initialize all variables
            sess.run(tf.global_variables_initializer())

            def train_step(x_batch, y_batch):
                """
                A single training step
                """
                feed_dict = {
                    cnn.input_x: x_batch,
                    cnn.input_y: y_batch,
                    cnn.dropout_keep_prob: 0.5
                }
                _, step, summaries, loss, accuracy = sess.run(
                    [train_op, global_step, train_summary_op,
                     cnn.loss, cnn.accuracy], feed_dict)

                time_str = datetime.datetime.now().isoformat()
                print("{}: step {}, loss {:g}, acc {:g}".format(
                    time_str, step, loss, accuracy))
                train_summary_writer.add_summary(summaries, step)

            def dev_step(x_batch, y_batch, writer=None):
                """
                Evaluates model on a dev set
                """
                feed_dict = {
                    cnn.input_x: x_batch,
                    cnn.input_y: y_batch,
                    cnn.dropout_keep_prob: 1.0
                }
                step, summaries, loss, accuracy = sess.run(
                    [global_step, dev_summary_op, cnn.loss, cnn.accuracy],
                    feed_dict)
                time_str = datetime.datetime.now().isoformat()
                print("{}: step {}, loss {:g}, acc {:g}".format(
                    time_str, step, loss, accuracy))

                if writer:
                    writer.add_summary(summaries, step)

            # Generate batches
            batches = data_helpers.batch_iter(
                list(zip(x_train, y_train)),
                FLAGS.batch_size, FLAGS.num_epochs)
            # Training loop. For each batch...
            for batch in batches:
                x_batch, y_batch = zip(*batch)
                train_step(x_batch, y_batch)
                current_step = tf.train.global_step(sess, global_step)
                if current_step % FLAGS.evaluate_every == 0:
                    print("\nEvaluation:")
                    dev_step(x_dev, y_dev, writer=dev_summary_writer)
                    print("")
                    if current_step % FLAGS.checkpoint_every == 0:
                        # checkpoint_prefix: save destination
                        path = saver.save(
                            sess, checkpoint_prefix, global_step=current_step)
                        print("Saved model checkpoint to {}\n".format(path))
