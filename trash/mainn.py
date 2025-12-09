import random
import hashlib

# Opérations dans le corps fini

q = 257  # petit corps fini

def rand_vec(n):
    return [random.randrange(q) for _ in range(n)]

# Multiplication d'une matrice par un vecteur
def mat_vec_mul(M, v):
    return [(sum(M[i][j] * v[j] for j in range(len(v))) % q) for i in range(len(M))]

#
def invert_matrix(M):
    # Inversion d'une matrice M mod q (méthode Gauss-Jordan)
    n = len(M)
    A = [row[:] for row in M]
    I = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
    for col in range(n):
        # Trouver pivot
        pivot = None
        for row in range(col, n):
            if A[row][col] % q != 0:
                pivot = row
                break
        if pivot is None:
            raise Exception("Matrice non inversible.")

        # Swap
        A[col], A[pivot] = A[pivot], A[col]
        I[col], I[pivot] = I[pivot], I[col]

        # Normaliser ligne
        inv_pivot = pow(A[col][col], -1, q)
        A[col] = [(x * inv_pivot) % q for x in A[col]]
        I[col] = [(x * inv_pivot) % q for x in I[col]]

        # Eliminer autres lignes
        for row in range(n):
            if row != col:
                factor = A[row][col]
                A[row] = [(A[row][i] - factor * A[col][i]) % q for i in range(n)]
                I[row] = [(I[row][i] - factor * I[col][i]) % q for i in range(n)]

    return I

# Génération de polynômes UOV
def generate_uov_polynomials(n, m, v):
    """
    structure UOV  :
    - Variables vinaigres : v
    - Variables huiles : o = n - v
    """
    o = n - v

    polys = [] # Liste des polynomes quadratiques
    for _ in range(m):
        # Construction d'un polynôme UOV :
        # f(x) = formule quadratique du modèle mathématique
        poly = {
            "vv": [[random.randrange(q) for _ in range(v)] for _ in range(v)], # Partie quadratique
            "vo": [[random.randrange(q) for _ in range(o)] for _ in range(v)], # Partie huile vinaigre
            "lin": [random.randrange(q) for _ in range(n)], # Partie linéaire
            "const": random.randrange(q), # Partie constante
        }
        polys.append(poly)
    return polys


def eval_poly(poly, x, v):
    """Évalue un polynôme UOV structuré."""
    o = len(x) - v
    xv = x[:v]
    xo = x[v:]

    res = poly["const"]

    # Terme vinegar-vinegar
    for i in range(v):
        for j in range(v):
            res += poly["vv"][i][j] * xv[i] * xv[j]

    # Terme vinegar-oil
    for i in range(v):
        for j in range(o):
            res += poly["vo"][i][j] * xv[i] * xo[j]

    # Terme linéaire
    for i in range(len(x)):
        res += poly["lin"][i] * x[i]

    return res % q # Resultat module q


def eval_polys(polys, x, v):
    return [eval_poly(p, x, v) for p in polys]


# --- Remplacer KeyGen pour garantir T inversible ---
def KeyGen(n, v, m):
    F = generate_uov_polynomials(n, m, v)

    # Choisir T non singulière
    while True:
        T = [[random.randrange(q) for _ in range(n)] for _ in range(n)]
        try:
            T_inv = invert_matrix(T)
            break
        except Exception:
            continue

    def P(x):
        Tx = mat_vec_mul(T, x)
        return eval_polys(F, Tx, v)

    return (P, F, T, T_inv)

# --- Nouvelle implémentation Sign utilisant la résolution linéaire pour les oil ---
def Sign(F, T_inv, message, n, v, max_tries=1000):
    h = hashlib.sha256(message.encode()).digest()
    m = len(F)
    t = [h[i] % q for i in range(m)]
    o = n - v

    if o <= 0:
        raise ValueError("Nombre d'oil doit être >= 1")
    if v <= o:
        # règle pratique : v doit être strictement supérieur à o dans beaucoup d'instanciations
        pass

    for attempt in range(max_tries):
        # 1) tirer les vinegar
        xv = [random.randrange(q) for _ in range(v)]

        # Construire A (m x o) et b (m)
        A = [[0]*o for _ in range(m)]
        b = [0]*m

        for p_idx, poly in enumerate(F):
            # calculer la partie constante donnée xv
            const_part = poly["const"] % q

            # terme vv (dépend uniquement de xv)
            vv_sum = 0
            for i in range(v):
                for j in range(v):
                    vv_sum = (vv_sum + poly["vv"][i][j] * xv[i] * xv[j]) % q

            # terme linéaire sur les vinegar
            lin_v_sum = 0
            for i in range(v):
                lin_v_sum = (lin_v_sum + poly["lin"][i] * xv[i]) % q

            # Pour chaque colonne j (variable oil_j), coefficient A[p_idx][j] =
            # sum_i vo[i][j] * xv[i]  + lin[v + j]
            for j in range(o):
                s = 0
                for i in range(v):
                    s = (s + poly["vo"][i][j] * xv[i]) % q
                s = (s + poly["lin"][v + j]) % q
                A[p_idx][j] = s

            # RHS b = t[p] - (const + vv_sum + lin_v_sum)  (mod q)
            b[p_idx] = (t[p_idx] - (const_part + vv_sum + lin_v_sum)) % q

        # Tenter d'inverser A (A est m x o avec m == o normalement)
        try:
            # A should be square (m == o). If not, skip.
            if len(A) != len(A[0]):
                continue

            A_inv = invert_matrix(A)  # peut lever Exception si singulier
            # xo = A_inv * b
            xo = mat_vec_mul(A_inv, b)
            # construire u
            u = xv + [x % q for x in xo]
            # vérifier (sécurité)
            if eval_polys(F, u, v) == t:
                s = mat_vec_mul(T_inv, u)
                return s
            else:
                # improbable si calcul correct, sinon continuer
                continue
        except Exception:
            # matrice singulière, retenter avec d'autres xv
            continue

    raise Exception("Echec de la signature après {} essais - matrice A souvent singulière".format(max_tries))


# Vérification
def Verify(P, message, sigma):
    h = hashlib.sha256(message.encode()).digest()
    m = len(P(rand_vec(len(sigma))))  # astuce pour connaître m
    t = [h[i] % q for i in range(m)]
    return P(sigma) == t


# Interface utilisateur
if __name__ == "__main__":
    print("=== UOV Signature Demo ===")

    msg = input("Message à signer : ")
    v = int(input("Nombre de variables vinegar : "))
    o = int(input("Nombre de variables oil : "))
    n = v + o
    m = o  # m = nombre d'équations = nombre de variables oil

    print("\n[+] Génération des clés...")
    P, F, T, T_inv = KeyGen(n, v, m)
    print("[+] Signature en cours...")
    sigma = Sign(F, T_inv, msg, n, v)
    print("\nMessage : ", msg)
    print("\nSignature :", sigma)


    print("\n[+] Vérification...")
    if Verify(P, msg, sigma):
        print(" Signature valide !")
    else:
        print(" Signature invalide.")