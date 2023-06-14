from numba import jit
import numpy as np
from sklearn.cluster import Birch


@jit(nopython=True)
def cw(C, n_iters, initialized_classes=None):
    nodes = np.array(list(range(C.shape[0])))
    if initialized_classes is None:
        # ith element is the class node i belongs to
        node_classes = nodes.copy()
    else:
        node_classes = initialized_classes

    for _ in range(n_iters):
        np.random.shuffle(nodes)
        for i in nodes:
            neighbors = C[i].nonzero()[0]
            if len(neighbors) != 0:
                class_sums = np.zeros(len(nodes))
                for j in neighbors:
                    class_sums[node_classes[j]] += C[i, j]
                node_classes[i] = class_sums.argmax()

    return node_classes




class ChineseWhispers:
    def __init__(self, iterations=20, threshold=0.75):
        self.iterations = iterations
        self.threshold = threshold

    def fit_predict(self, embeddings, frames=None, initialized_classes=None):
        """
        Parameters
        ----------
        embeddings : np.ndarray
            array of shape [N, d_emb] of N embeddings of dimension d_emb
        frames : arraylike
            list of length N giving the frame number for every embedding

        Returns
        -------
        np.ndarray
            array of shape [N] giving the clustering assignments
        """
        C = (1 + embeddings @ (embeddings.T)) / 2
        C[C <= self.threshold] = 0

        if frames is not None:
            assert len(frames) == C.shape[0]
            # set faces that appear in the same frame to have zero similarity
            m = np.ones_like(C)
            _, counts = np.unique(frames, return_counts=True)
            i = 0
            for c in counts:
                m[i : i + c, i : i + c] = 0
                i += c
            C = C * m
        else:
            np.fill_diagonal(C, 0)

        return cw(C, self.iterations, initialized_classes)


# class BIRCH:
#     def __init__(self):
#         self.n_clusters = None
#         self.threshold = 0.2

#     def fit_predict(self, embeddings, frames=None):
#         brc = Birch(n_clusters=self.n_clusters, threshold=self.threshold)
#         return brc.fit_predict(embeddings)
