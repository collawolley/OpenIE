__author__ = 'hadyelsahar'

import os
import re
from os import path
import sys
import numpy as np

# get to upper directory to append vectorizers
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from Vectorizers.wordvectorizer import *
from nltk.tokenize import TreebankWordTokenizer

_DATA_PATH = __file__.replace("preprocessor.py", "") + "data/"

class Preprocessor:
    """
    preprocessor class is the class responsible of converting the brat annotation
    files into standard outputs of input feature vectors and and
    save them into a pickle file in the 'data' folder
    """
    def __init__(self, inputdir, datadir="./data/", ner=True, pos=True, dependency=False, embeddings="word2vec",
                 seg_only=True, otag="out"):
        """
        :param inputdir:
        :param datadir:
        :param ner:
        :param pos:
        :param dependency:
        :param embeddings:
        :param seg_only: True create y labels without tag names B-seg I-seg will be the only labels
        :param otag: what to call the out tag "seg" or "OUT"  (naming out tag as OUT will make the seq learner learn
        the auxilary words in addition to phrase extraction, but naming as default seg will just do phrase extraction.
        :return:
        """

        self.inputdir = inputdir
        self.datadir = datadir
        self.seg = seg_only
        self.otag = otag
        self.tokenize = TreebankWordTokenizer().tokenize

        # S     :   the raw sentences                            - shape: nx1   (n is the number of sentences)
        # Xid   :   the tokens in order, also the features ids   - shape: nx1
        # X     :   the features vectors for every token         - shape: nxm   (m is the feature vector size)
        # Y     :   the correct labels                           - shape: nx1
        self.S, self.Xid, self.Y = self.read_data_dir(inputdir)

        self.vectorizer = None
        self.X = self.vectorize(self.S, self.Xid, ner=ner, pos=pos, dependency=dependency, embeddings=embeddings)


    def read_data_dir(self, inputdir):
        """
        :param inputdir: directory contains brat annotation files
        Two files per sentence ending with ".txt" or ".ann"

        .txt : text file contains one sentence per files
        .ann : annotation file contains one Tag or relation per line
        for the scope of phrase extraction we wil concentrate only on lines starting with T
        which are the labeling for TAGS

        :return: (S,X,y)
         S:  array containing all sentences in all the .txt files, in order
         X:  array containing all words tokenized in all .txt files in order i.e. training set labels
         y:  array containing all labels for X in order
        """

        files = os.listdir(inputdir)

        # select only files with annotation existing
        # get the basename without the file type
        # add .txt or .ann later
        file_names = [x.replace(".ann", "") for x in files if ".ann" in x]
        file_names = ["0020"]
        # capital letters for corpus #small letters per sentence
        S = []
        Xid = []
        Y = []
        # for every training example
        for f in file_names:
            try:
                # collect text sentences tokens
                fo = file("%s/%s.txt" % (inputdir, f), 'r')
                s = fo.read()
                x = self.tokenize(s)

                fa = file("%s/%s.ann" % (inputdir, f), 'r')  # filling annotations with labels

                # collect tags in the annotation
                # select lines only that contain tags
                tags = fa.read().split("\n")
                tags = [i for i in tags if re.match('^T', i)]
                tags = [t.split("\t") for t in tags]

                # split "Subject 00 45 into  ["subject", "00", "45"]
                tags = [[t[0]] + t[1].split(" ") + t[2:] for t in tags]
                tags = [t[0:2] + [int(t[2]), int(t[3])] + t[4:] for t in tags]
                # sort tags by start position
                tags = sorted(tags, key=lambda l: l[2])

                y = []
                tagged_tokens = []
                tagged_labels = []

                for tag in tags:
                    tokens = self.tokenize(tag[-1])

                    tagged_tokens += tokens
                    label = "seg" if self.seg else tag[1]
                    tagged_labels.append("B-%s" % label)
                    tagged_labels += ["I-%s" % label for i in tokens[1:]]

                for word in x:
                    if word in tagged_tokens:
                        id = tagged_tokens.index(word)
                        y.append(tagged_labels[id])
                        del tagged_tokens[id]
                        del tagged_labels[id]

                    else:
                        # differentiate between tagged and non-tagged out (when self.otag is "seg"),
                        # change Bo -> B later in code
                        # if the previous label is out add I-out else add B-out
                        if len(y) > 0 and ("Io-%s" % self.otag == y[-1] or "Bo-%s" % self.otag == y[-1]):
                            y.append("Io-%s" % self.otag)
                        else:
                            y.append("Bo-%s" % self.otag)

                # convert Bo  -> B and Io -> o
                y = [re.sub(r"(.)(o)(-%s)" % self.otag, r"\1\3", i) for i in y]

                if len(y) != len(x) or len(tagged_tokens) > 0 or len(tagged_labels) > 0:
                    raise RuntimeError

                else:
                    Xid.append(x)
                    S.append(s)
                    Y.append(y)

            except Exception as e:
                print "Error extraction of file %s" % f
                pass

        return np.array(S), np.array(Xid), np.array(Y)

    def vectorize(self, S, Xid, ner=False, pos=False, dependency=False, embeddings="word2vec"):
        """
        vectorizer is a method given standard options which features to include and X ( all tokens)
        and S (all sentences) it does the following

        - loads a vectorizer as set it in self.vectorizer
        - run the vectorizers and extract feature vector per word,
        -
        :param S: (usually self.S) array of Raw Sentences. used to get
        :param Xid: (feature indices) usually not neaded, as we will
        :return:
        """

        if self.vectorizer is not None:
            self.vectorizer = WordVectorizer(ner=False, pos=False, dependency=False, embeddings="word2vec")

        X = []

        return X

    def save_data(self, outputdir):
        raise NotImplementedError






