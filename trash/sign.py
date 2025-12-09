# # uov_core/sign.py
# import random
# import hashlib
# from .keygen import eval_polys_with_T, q

# def Sign(keypair, message, max_tries=1000):
#     """
#     keypair: dict retourné par KeyGen (contient F, T, T_inv, n, v, m)
#     renvoie sigma (liste d'entiers) représentant la signature (s = T_inv * u)
#     """
#     F = keypair["F"]
#     T_inv = keypair["T_inv"]
#     n = keypair["n"]
#     v = keypair["v"]
#     m = keypair["m"]
#     o = n - v

#     h = hashlib.sha256(message.encode()).digest()
#     t = [h[i] % q for i in range(m)]

#     if o <= 0:
#         raise ValueError("Nombre d'oil doit être >= 1")

#     # fonctions utilitaires
#     def invert_matrix_local(M):
#         # on suppose que la méthode d'inversion se trouve dans keygen
#         from .keygen import invert_matrix
#         return invert_matrix(M)

#     def mat_vec_mul_local(M, vvec):
#         return [(sum(M[i][j] * vvec[j] for j in range(len(vvec))) % q) for i in range(len(M))]

#     for attempt in range(max_tries):
#         xv = [random.randrange(q) for _ in range(v)]
#         A = [[0]*o for _ in range(m)]
#         b = [0]*m

#         for p_idx, poly in enumerate(F):
#             const_part = poly["const"] % q
#             vv_sum = 0
#             for i in range(v):
#                 for j in range(v):
#                     vv_sum = (vv_sum + poly["vv"][i][j] * xv[i] * xv[j]) % q
#             lin_v_sum = 0
#             for i in range(v):
#                 lin_v_sum = (lin_v_sum + poly["lin"][i] * xv[i]) % q
#             for j in range(o):
#                 s = 0
#                 for i in range(v):
#                     s = (s + poly["vo"][i][j] * xv[i]) % q
#                 s = (s + poly["lin"][v + j]) % q
#                 A[p_idx][j] = s
#             b[p_idx] = (t[p_idx] - (const_part + vv_sum + lin_v_sum)) % q

#         # A devrait être carré (m == o)
#         if len(A) != len(A[0]):
#             continue
#         try:
#             A_inv = invert_matrix_local(A)
#             xo = mat_vec_mul_local(A_inv, b)
#             u = xv + [x % q for x in xo]
#             # vérifier F(u) == t mais attention : F est défini sur Tx, dans ton modèle tu utilisais Tx = T * u
#             # Ici on suppose F attend u déjà transformé si KeyGen/Sign sont cohérents.
#             # On vérifie en procédant via eval_polys_with_T si besoin (vérifie usage en GUI).
#             # calculer s = T_inv * u
#             s = mat_vec_mul_local(T_inv, u)
#             # renvoi sigma (s)
#             return s
#         except Exception:
#             continue
#     raise Exception(f"Echec de la signature après {max_tries} essais.")
