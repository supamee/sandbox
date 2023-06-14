
import numpy as np
import scipy as sp
from scipy.spatial import ConvexHull
from sklearn.decomposition import PCA
from sklearn.neighbors import KDTree

# from foundation.utils.dists import cosine_distance

__all__ = [
    "AggregateData",
    "EmbeddingVolume",
    "EmbeddingPolytope",
    "SparseEmbeddingCloud",
]



class AggregateData:
    def __init__(self, ambient_dim: int = 128, pca_dim: int = 20, **kwargs) -> None:
        self.num_embeddings = 0
        self.new_emb_counter = 0
        self.ambient_dim = ambient_dim
        self.pca_dim = pca_dim
        self.embeddings = np.empty((0, ambient_dim), np.float32)
        self.low_d_embeddings = np.empty((0, pca_dim), np.float32)
        self.rep_idx = []
        self.avg_emb = np.empty((ambient_dim))
        self.avg_emb[:] = None
        self.updated_pca = False
        self.pca = None

    def dim_reduce(self, temporal: bool = False) -> None:
        temp_spread = 0.001
        working_embs = np.copy(self.embeddings)
        if temporal:
            working_embs = np.array(
                [
                    np.append(working_embs[i], i * temp_spread)
                    for i in range(len(working_embs))
                ]
            )
        pca = None
        if self.pca_dim < self.ambient_dim:
            if self.num_embeddings > self.pca_dim:
                pca = PCA()
                long_embeddings = pca.fit_transform(working_embs)
                self.low_d_embeddings = long_embeddings[:, : self.pca_dim]
            self.pca = pca
        else:
            self.low_d_embeddings = np.copy(working_embs)
        self.updated_pca = True

    def add_vector(self, emb: np.ndarray) -> None:
        emb_c = np.copy(emb)
        if np.isnan(sum(self.avg_emb)).all():
            s = emb_c
        else:
            s = self.avg_emb * self.new_emb_counter
            s += emb_c
        self.new_emb_counter += 1
        self.avg_emb = s / (self.new_emb_counter)
        self.embeddings = np.append(self.embeddings, [emb_c.flatten()], axis=0)
        self.num_embeddings = len(self.embeddings)
        self.updated_pca = False

    def brute_force_neighbor_search(self, q: np.ndarray) -> float:
        if len(self.embeddings) == 0:
            return 0.0
        ix = -1
        base = 0.0
        for i, e in enumerate(self.embeddings):
            val = 1 - utils.cosine_distance(q, e)
            if val > base:
                base = val
                ix = i
        return 1 - utils.cosine_distance(self.embeddings[ix], q)

    def pack(self):
        rep_embeddings = self.embeddings[self.rep_idx]
        return {
            str(self.rep_idx[i]): rep_embeddings[i].tolist()
            for i in range(len(self.rep_idx))
        }


class EmbeddingVolume(AggregateData):
    def __init__(
        self,
        ball_radius: float = 0.5,
        new_volume_thresh: float = 0.25,
        ambient_dim: int = 128,
        pca_dim: int = None,
        **kwargs,
    ) -> None:
        super().__init__(ambient_dim, ambient_dim, **kwargs)
        self.ball_radius = ball_radius
        self.new_volume_thresh = new_volume_thresh
        self.updated_tree = False
        self.tree = None
        self.add_vec_count = 0
        self.keep_only_reps = True

    def add_vector(self, emb: np.array) -> None:
        if self.tree is None:
            super().add_vector(emb)
            self.rep_idx += [self.add_vec_count]
            self.update_tree()
            self.peak_density = self.tree.kernel_density(
                self.embeddings, self.ball_radius, kernel="gaussian"
            )[0]
        else:
            if not self.keep_only_reps:
                super().add_vector(emb)
            query_density = self.tree.kernel_density(
                np.expand_dims(emb.flatten(), axis=0),
                self.ball_radius,
                kernel="gaussian",
            )[0]
            if query_density < self.new_volume_thresh * self.peak_density:
                if self.keep_only_reps:
                    super().add_vector(emb)
                self.rep_idx += [self.add_vec_count]
                self.update_tree()
        self.add_vec_count += 1

    def update_tree(self) -> None:
        if self.keep_only_reps:
            self.tree = KDTree(self.embeddings, leaf_size=2)
        else:
            self.tree = KDTree(self.embeddings[self.rep_idx], leaf_size=2)
        self.updated_tree = True

    def get_reps(self) -> list:
        if not self.updated_tree:
            self.update_tree()
        if self.keep_only_reps:
            return list(range(len(self.embeddings)))
        else:
            return self.rep_idx

    def query(self, q: np.ndarray) -> int:
        query_density = self.tree.kernel_density(
            np.expand_dims(q, axis=0), self.ball_radius, kernel="gaussian"
        )[0]
        if query_density > self.new_volume_thresh * self.peak_density:
            return 1
        return 0

    def nearest_neighbor_similarity(self, q: np.ndarray) -> float:
        if self.tree is not None:
            if not self.updated_tree:
                self.update_tree()
            q = q.reshape(1, -1)
            _, ind = self.tree.query(q, k=1)
            similarity = 1 - utils.cosine_distance(self.embeddings[int(ind)], q)
            return similarity
        else:
            return self.brute_force_neighbor_search(q)


class EmbeddingPolytope(AggregateData):
    def __init__(self, ambient_dim: int = 128, pca_dim: int = 3, **kwargs) -> None:
        super().__init__(ambient_dim=ambient_dim, pca_dim=pca_dim, **kwargs)
        self.hull = None
        self.vertices = np.empty((0, pca_dim), np.float32)
        self.vertices_idx = []
        self.updated_hull = False
        self.update_freq = 5
        self.keep_only_reps = False

    def add_vector(self, emb: np.array) -> None:
        super().add_vector(emb)
        self.updated_hull = False
        if self.keep_only_reps and self.new_emb_counter % self.update_freq == (
            self.update_freq - 1
        ):
            if len(self.embeddings) > self.pca_dim + 1:
                self.update_hull()
                self.embeddings = self.embeddings[self.vertices_idx]
                self.num_embeddings = len(self.embeddings)
                self.updated_pca = False

    def update_hull(self, temporal: bool = False) -> None:
        if not self.updated_pca:
            self.dim_reduce(temporal=temporal)
        if self.num_embeddings >= self.pca_dim + 1:
            self.hull = ConvexHull(self.low_d_embeddings)
            self.vertices = self.low_d_embeddings[self.hull.vertices]
            self.vertices_idx = self.hull.vertices
            self.updated_hull = True

    def temporal_slicing(self, vertices: list, temporal_time: int = 3) -> list:
        reps = set()
        vertices = sorted(vertices)
        i = 0
        while i < len(vertices) - 1:
            pointer = i + 1
            if vertices[pointer] - vertices[i] >= temporal_time:
                reps.add(vertices[i])
                reps.add(vertices[pointer])
            else:
                dsum = 0
                while dsum <= temporal_time:
                    if pointer < len(vertices):
                        dsum += vertices[pointer] - vertices[i]
                        if dsum <= temporal_time:
                            pointer += 1
                    else:
                        break
                if pointer < len(vertices):
                    reps.add(vertices[i])
                    reps.add(vertices[pointer])
            i = pointer
        return list(reps)

    def get_reps(self, temp_thresh: int = 2) -> list:
        if not self.updated_hull:
            self.update_hull()
        if self.updated_hull:
            if temp_thresh == 0:
                self.rep_idx = [i for i in self.vertices_idx]
            else:
                self.rep_idx = self.temporal_slicing(
                    self.vertices_idx, temporal_time=temp_thresh
                )
        return self.rep_idx

    def in_hull(self, q: np.ndarray, tolerance: float = 1e-10) -> bool:
        return all(
            (np.dot(eq[:-1], q) + eq[-1] <= tolerance) for eq in self.hull.equations
        )

    def query(self, q: np.ndarray) -> bool:
        return self.in_hull(q)

    def nearest_neighbor_similarity(self, q: np.ndarray) -> float:
        q = q.reshape(1, -1)
        closest = 0.0
        for v in range(len(self.embeddings)):
            d = 1 - utils.cosine_distance(self.embeddings[v], q)
            if d > closest:
                closest = d
        return closest


class SparseEmbeddingCloud:
    def __init__(
        self,
        ambient_dim: int = 128,
        pca_dim: int = 15,
        membership_thresh: int = 1,
        cloud_method: str = "cloud",
        entity_type: str = "person",
        representative_method: str = "polytope",
        **kwargs,
    ) -> None:
        self.membership_thresh = membership_thresh
        self.cov_matrix_inv = np.zeros((pca_dim, pca_dim))
        self.updated_cov = False
        assert cloud_method in [
            "cloud",
            "cloud_normalized",
            "avg_euc",
            "avg_cos",
            "avg_gauss",
            "avg_gauss_normalized",
        ], "Invalid cloud method"
        self.cloud_method = cloud_method
        assert entity_type in ["face", "person"], "Invalid entity type"
        self.entity_type = entity_type
        self.set_parameters()
        self.representative_method = representative_method
        self.updated_tree = False
        representative_methods = {
            "polytope": EmbeddingPolytope,
            "volume": EmbeddingVolume,
        }
        assert representative_method in list(
            representative_methods.keys()
        ), "Invalid representative method"
        self.reductor = representative_methods.get(representative_method)(
            ambient_dim=ambient_dim, **kwargs
        )
        self.reductor.keep_only_reps = True

    def set_parameters(self) -> None:
        cloud_method_radii_4persons = {
            "cloud": 7.5,
            "cloud_normalized": 0.4,
            "avg_euc": 10.1,
            "avg_cos": 0.58,
            "avg_gauss": 5.45,
            "avg_gauss_normalized": 3,
        }
        cloud_method_radii_4faces = {
            "cloud": 0.93,
            "cloud_normalized": 0.93,
            "avg_euc": 1,
            "avg_cos": 1,
            "avg_gauss": 4.5,
            "avg_gauss_normalized": 4.5,
        }
        if self.entity_type == "person":
            self.cloud_radius = cloud_method_radii_4persons[self.cloud_method]
        elif self.entity_type == "face":
            self.cloud_radius = cloud_method_radii_4faces[self.cloud_method]
        else:
            self.cloud_radius = None

    def add_vector(self, emb: np.ndarray) -> None:
        self.reductor.add_vector(emb)
        self.updated_cov = False
        self.updated_tree = False

    def update_tree(self, normalize: bool = False) -> None:
        E = np.copy(self.reductor.embeddings)
        if E.size == 0:
            self.update_tree = False
        else:
            if normalize:
                for e in E:
                    e /= np.linalg.norm(e)
            self.tree = KDTree(E, leaf_size=40)
            self.updated_tree = True

    def update_cov(self) -> None:
        self.reductor.dim_reduce()
        if self.reductor.num_embeddings > self.reductor.pca_dim:
            cov_matrix = np.cov(self.reductor.low_d_embeddings.T)
            self.cov_matrix_inv = sp.linalg.inv(cov_matrix)
            self.updated_cov = True

    def euc_dist(self, p: np.ndarray, q: np.ndarray) -> float:
        return np.linalg.norm(p - q)

    def gauss_dist(self, p, avg) -> float:
        if self.reductor.num_embeddings < self.reductor.pca_dim:
            return np.inf
        if not self.reductor.updated_pca:
            self.reductor.dim_reduce()
        if not self.updated_cov:
            self.update_cov()
        if self.reductor.pca is not None:
            p_small = self.reductor.pca.transform(np.array([p]))[0][
                : self.reductor.pca_dim
            ]
            avg_small = self.reductor.pca.transform(np.array([avg]))[0][
                : self.reductor.pca_dim
            ]
        else:
            p_small = np.copy(p)
            avg_small = np.copy(avg)
        mahal = sp.spatial.distance.mahalanobis(p_small, avg_small, self.cov_matrix_inv)
        return mahal

    def avg_query(
        self, q: np.ndarray, metric, thresh: float, normalize: bool = False
    ) -> int:
        if normalize:
            normalized_avg = self.reductor.avg_emb / np.linalg.norm(
                self.reductor.avg_emb
            )
            normalized_q = q / np.linalg.norm(q)
        else:
            normalized_avg = self.reductor.avg_emb
            normalized_q = q
        if metric(normalized_avg, normalized_q) < thresh:
            return 1
        return 0

    def query(self, q: np.ndarray, UNIT_TEST_METHOD: str = None) -> int:
        q = q.reshape(1, -1)
        if UNIT_TEST_METHOD is not None:
            method = UNIT_TEST_METHOD
        else:
            method = self.cloud_method
            self.set_parameters()

        rval = 0
        if method == "cloud":
            if not self.updated_tree:
                self.update_tree(normalize=False)
            in_cloud_count = self.tree.query_radius(
                q, self.cloud_radius, count_only=True
            )
            if in_cloud_count >= self.membership_thresh:
                rval = 1
        elif method == "cloud_normalized":
            if not self.updated_tree:
                self.update_tree(normalize=True)
            in_cloud_count = self.tree.query_radius(
                q, self.cloud_radius, count_only=True
            )
            if in_cloud_count >= self.membership_thresh:
                rval = 1
        elif method == "avg_euc":
            rval = self.avg_query(q, self.euc_dist, self.cloud_radius, normalize=False)
        elif method == "avg_cos":
            rval = self.avg_query(q, self.euc_dist, self.cloud_radius, normalize=True)
        elif method == "avg_gauss":
            rval = self.avg_query(
                q, self.gauss_dist, self.cloud_radius, normalize=False
            )
        elif method == "avg_gauss_normalized":
            rval = self.avg_query(q, self.gauss_dist, self.cloud_radius, normalize=True)
        else:
            rval = None
        return rval

    def multi_query(self, Q: np.ndarray) -> int:
        total = 0
        for q in Q:
            total += self.query(q)
        percentage = total / len(Q)
        return percentage
 
    def query_wc(self, q: np.ndarray):
        self.set_parameters()
        q = q.reshape(1, -1)
        rval = (None, None)
        if self.cloud_method == "cloud":
            if not self.updated_tree:
                self.update_tree(normalize=False)
            in_cloud_count = self.tree.query_radius(
                q, self.cloud_radius, count_only=True
            )
            if in_cloud_count >= self.membership_thresh:
                rval = (1, in_cloud_count[0])
            else:
                rval = (0, in_cloud_count[0])
        elif self.cloud_method == "cloud_normalized":
            if not self.updated_tree:
                self.update_tree(normalize=True)
            in_cloud_count = self.tree.query_radius(
                q, self.cloud_radius, count_only=True
            )
            if in_cloud_count >= self.membership_thresh:
                rval = (1, in_cloud_count[0])
            else:
                rval = (0, in_cloud_count[0])
        else:
            rval = (None, None)
        return rval

    def nearest_neighbor_similarity(self, q: np.ndarray) -> float:
        return self.reductor.nearest_neighbor_similarity(q)
