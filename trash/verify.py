# # uov_core/verify.py
# import hashlib
# from .keygen import mat_vec_mul, eval_polys_with_T, q

# def Verify(keypair, message, sigma):
#     """
#     keypair: dict (F,T,...)
#     sigma: vecteur signé (liste) => sigma = s = T_inv * u
#     pour vérifier, on calcule u' = T * sigma et on évalue F(u') et compare à H(m)
#     """
#     F = keypair["F"]
#     T = keypair["T"]
#     v = keypair["v"]
#     m = keypair["m"]

#     h = hashlib.sha256(message.encode()).digest()
#     t = [h[i] % q for i in range(m)]

#     # calcule u' = T * sigma
#     u_prime = mat_vec_mul(T, sigma)
#     # évaluer F sur u_prime : on a implémenté eval_polys_with_T pour faire la transformation si besoin,
#     # mais ici F attend directement des variables (ici u_prime)
#     # On recalcule F(u_prime)
#     def eval_poly(poly, x, v_local):
#         o = len(x) - v_local
#         xv = x[:v_local]
#         xo = x[v_local:]
#         res = poly["const"]
#         for i in range(v_local):
#             for j in range(v_local):
#                 res += poly["vv"][i][j] * xv[i] * xv[j]
#         for i in range(v_local):
#             for j in range(o):
#                 res += poly["vo"][i][j] * xv[i] * xo[j]
#         for i in range(len(x)):
#             res += poly["lin"][i] * x[i]
#         return res % q

#     evals = [eval_poly(poly, u_prime, v) for poly in F]
#     return evals == t
