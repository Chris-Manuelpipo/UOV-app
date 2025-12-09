# # uov_core/keygen.py
# import random

# q = 257  # corps fini (garde la valeur de ton prototype)

# def rand_vec(n):
#     return [random.randrange(q) for _ in range(n)]

# def mat_vec_mul(M, v):
#     return [(sum(M[i][j] * v[j] for j in range(len(v))) % q) for i in range(len(M))]

# def invert_matrix(M):
#     n = len(M)
#     A = [row[:] for row in M]
#     I = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
#     for col in range(n):
#         pivot = None
#         for row in range(col, n):
#             if A[row][col] % q != 0:
#                 pivot = row
#                 break
#         if pivot is None:
#             raise Exception("Matrice non inversible.")
#         A[col], A[pivot] = A[pivot], A[col]
#         I[col], I[pivot] = I[pivot], I[col]
#         inv_pivot = pow(A[col][col], -1, q)
#         A[col] = [(x * inv_pivot) % q for x in A[col]]
#         I[col] = [(x * inv_pivot) % q for x in I[col]]
#         for row in range(n):
#             if row != col:
#                 factor = A[row][col]
#                 A[row] = [(A[row][i] - factor * A[col][i]) % q for i in range(n)]
#                 I[row] = [(I[row][i] - factor * I[col][i]) % q for i in range(n)]
#     return I

# def generate_uov_polynomials(n, m, v):
#     o = n - v
#     polys = []
#     for _ in range(m):
#         poly = {
#             "vv": [[random.randrange(q) for _ in range(v)] for _ in range(v)],
#             "vo": [[random.randrange(q) for _ in range(o)] for _ in range(v)],
#             "lin": [random.randrange(q) for _ in range(n)],
#             "const": random.randrange(q),
#         }
#         polys.append(poly)
#     return polys

# def build_public_P(F, T):
#     # Retourne une fonction P(x) qui applique T puis évalue les polynômes F
#     def eval_poly(poly, x, v):
#         o = len(x) - v
#         xv = x[:v]
#         xo = x[v:]
#         res = poly["const"]
#         for i in range(v):
#             for j in range(v):
#                 res += poly["vv"][i][j] * xv[i] * xv[j]
#         for i in range(v):
#             for j in range(o):
#                 res += poly["vo"][i][j] * xv[i] * xo[j]
#         for i in range(len(x)):
#             res += poly["lin"][i] * x[i]
#         return res % q

#     def P(x):
#         # Tx = T * x
#         Tx = mat_vec_mul(T, x)
#         m = len(F)
#         return [eval_poly(F[i], Tx, sum(len(F[0]['lin']) for __ in [0]) - (len(T) - 0)) for i in range(m)]
#     # Note: on reconstruira correctement la version de P dans le GUI (voir utilisation)
#     return P

# def KeyGen(n, v, m):
#     F = generate_uov_polynomials(n, m, v)
#     # choisir T inversible
#     while True:
#         T = [[random.randrange(q) for _ in range(n)] for _ in range(n)]
#         try:
#             T_inv = invert_matrix(T)
#             break
#         except Exception:
#             continue
#     # note: on ne sérialise pas la closure P ; on stocke F, T, T_inv
#     return {
#         "F": F,
#         "T": T,
#         "T_inv": T_inv,
#         "n": n,
#         "v": v,
#         "m": m,
#     }

# # helper: évaluer F(T*x)
# def eval_polys_with_T(F, T, x, v):
#     Tx = mat_vec_mul(T, x)
#     # évaluation simple en reprenant le code d'éval
#     def eval_poly(poly, x, v):
#         o = len(x) - v
#         xv = x[:v]
#         xo = x[v:]
#         res = poly["const"]
#         for i in range(v):
#             for j in range(v):
#                 res += poly["vv"][i][j] * xv[i] * xv[j]
#         for i in range(v):
#             for j in range(o):
#                 res += poly["vo"][i][j] * xv[i] * xo[j]
#         for i in range(len(x)):
#             res += poly["lin"][i] * x[i]
#         return res % q
#     return [eval_poly(poly, Tx, v) for poly in F]
