"""
This code was modified on top of Google tensorflow
(https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/using_your_own_dataset.md)

This code works similar to `label-maker package` when used with Label Maker and Tensor Flow object detection API.
To create a correct training data set for Tensor Flow Object Detection, we recommend you:

1. After running `label-maker images`, do `git clone https://github.com/tensorflow/models.git`
2. Install TensorFlow object detection by following this: https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/installation.md
3. From your Label Maker, copy `tiles` folder, this code `tf_records_generation.py` and `labels.py` to Tensorflow object detecrtion directory
4. From directory `tensorflow/models/research/` run:

python tf_records_generation.py --label_input=labels.npz \
             --train_rd_path=data/train_buildings.record \
             --test_rd_path=data/test_buildings.record
"""
#cansat tags for a while 
tags = ["buildings", "highway", "aerodrom", "apron", "runway", "taxiway", "grassland", "heath", "scrub", "water", "wood", "farmland", "grass", "residential", "ditch", "river"]

import os
import io
import numpy as np
from os import makedirs, path as op
import shutil

import pandas as pd
import tensorflow as tf

from PIL import Image
from utils import dataset_util
from collections import namedtuple

flags = tf.app.flags
flags.DEFINE_string('label_input', '', 'Path to the labels.npz input')
flags.DEFINE_string('tiles_input', '', 'Path to the tiles input')
flags.DEFINE_string('train_tf_path', '', 'Path to the train input')
flags.DEFINE_string('test_tf_path', '', 'Path to the test input')
flags.DEFINE_string('train_rd_path', '', 'Path to output TFRecord')
flags.DEFINE_string('test_rd_path', '', 'Path to output TFRecord')
FLAGS = flags.FLAGS

def class_text_to_int(row_label):
    return tags[row_label]

def split(df, group):
    data = namedtuple('data', ['filename', 'object'])
    gb = df.groupby(group)
    return [data(filename, gb.get_group(x)) for filename, x in zip(gb.groups.keys(), gb.groups)]

def create_tf_example(group, path):
    """Creates a tf.Example proto from sample buillding image tile.

    Args:
     encoded_building_image_data: The jpg encoded data of the building image.

    Returns:
     example: The created tf.Example.
    """
    with tf.gfile.GFile(op.join(path, '{}'.format(group.filename)), 'rb') as fid:
        encoded_jpg = fid.read()
    encoded_jpg_io = io.BytesIO(encoded_jpg)
    image = Image.open(encoded_jpg_io)
    width, height = image.size
    filename = group.filename.encode('utf8')
    image_format = b'jpg'
    xmins = []
    xmaxs = []
    ymins = []
    ymaxs = []
    classes_text = []
    classes = []

    for _, row in group.object.iterrows():
        xmins.append(row['xmin'] / width)
        xmaxs.append(row['xmax'] / width)
        ymins.append(row['ymin'] / height)
        ymaxs.append(row['ymax'] / height)
        classes_text.append(tags[row['class_num']].encode('utf8'))
        classes.append(row['class_num'])

    tf_example = tf.train.Example(features=tf.train.Features(feature={
        'image/height': dataset_util.int64_feature(height),
        'image/width': dataset_util.int64_feature(width),
        'image/filename': dataset_util.bytes_feature(filename),
        'image/source_id': dataset_util.bytes_feature(filename),
        'image/encoded': dataset_util.bytes_feature(encoded_jpg),
        'image/format': dataset_util.bytes_feature(image_format),
        'image/object/bbox/xmin': dataset_util.float_list_feature(xmins),
        'image/object/bbox/xmax': dataset_util.float_list_feature(xmaxs),
        'image/object/bbox/ymin': dataset_util.float_list_feature(ymins),
        'image/object/bbox/ymax': dataset_util.float_list_feature(ymaxs),
        'image/object/class/text': dataset_util.bytes_list_feature(classes_text),
        'image/object/class/label': dataset_util.int64_list_feature(classes),
    }))
    return tf_example


def main(_):
    labels = np.load(op.join(os.getcwd(), FLAGS.label_input))
    tile_names = [tile for tile in labels.files]
    tile_names.sort()
    tiles = np.array(tile_names)

    tf_tiles_info = []

    for tile in tiles:
        bboxes = labels[tile].tolist()
        width = 256
        height = 256
        if bboxes:
            for bbox in bboxes:
                    class_num = bbox[4]
                    bbox = [max(0, min(255, x)) for x in bbox[0:4]]
                    y = ["{}.jpg".format(tile), width, height, class_num, bbox[0], bbox[1], bbox[2], bbox[3]]
                    tf_tiles_info.append(y)
    split_index = int(len(tf_tiles_info) * 0.8)
    column_name = ['filename', 'width', 'height', 'class_num', 'xmin', 'ymin', 'xmax', 'ymax']
    df = pd.DataFrame(tf_tiles_info, columns=column_name)
    # shuffle the dataframe
    df = df.sample(frac=1)
    train_df = df[:split_index]
    test_df = df[split_index:]
    print("You have {} training tiles and {} test tiles ready".format(
        len(set(train_df['filename'])), len(set(test_df['filename']))))

    tiles_dir = op.join(os.getcwd(), FLAGS.tiles_input)
    train_dir = op.join(os.getcwd(), FLAGS.train_tf_path)
    test_dir = op.join(os.getcwd(), FLAGS.test_tf_path)
    print(train_dir)
    print(test_dir)

    if not op.isdir(train_dir):
        makedirs(train_dir)
    if not op.isdir(test_dir):
        makedirs(test_dir)

    for tile in train_df['filename']:
        tile_dir = op.join(tiles_dir, tile)
        shutil.copy(tile_dir, train_dir)

    for tile in test_df['filename']:
        tile_dir = op.join(tiles_dir, tile)
        shutil.copy(tile_dir, test_dir)
    ### for train
    writer = tf.python_io.TFRecordWriter(FLAGS.train_rd_path)
    grouped = split(train_df, 'filename')
    print("train_group 0", grouped[0])
    for group in grouped:
        tf_example = create_tf_example(group, train_dir)
        writer.write(tf_example.SerializeToString())
    writer.close()
    output_train = op.join(os.getcwd(), FLAGS.train_rd_path)
    print('Successfully created the TFRecords: {}'.format(output_train))

    ### for test
    writer = tf.python_io.TFRecordWriter(FLAGS.test_rd_path)
    grouped = split(test_df, 'filename')
    print("test_group 0", grouped[0])
    for group in grouped:
        tf_example = create_tf_example(group, test_dir)
        writer.write(tf_example.SerializeToString())

    writer.close()
    output_test = op.join(os.getcwd(), FLAGS.test_rd_path)
    print('Successfully created the TFRecords: {}'.format(output_test))

def _score_converter_fn_with_logit_scale(tf_score_converter_fn, logit_scale):
    def score_converter_fn(logits):
        cr = logit_scale
        cr = tf.constant([[cr]], tf.float32)
        print(logit_scale)
        print(logits)
        scaled_logits = tf.divide(logits, cr, name='scale_logits') #change logit_scale
        return tf_score_converter_fn(scaled_logits, name='convert_scores')
    score_converter_fn.__name__ = '%s_with_logit_scale' % (tf_score_converter_fn.__name__)
    return score_converter_fn

if __name__ == '__main__':
    tf.app.run()