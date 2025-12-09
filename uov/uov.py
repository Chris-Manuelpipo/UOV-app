import random
import hashlib
import json
import sys

# --- PARAMÈTRES & OUTILS MATHÉMATIQUES GF(2^8) ---


# Corps fini: q=256 (GF(2^8))
q = 256
IRREDUCIBLE_256 = 0b100011101 # Polynôme: x^8 + x^4 + x^3 + x^2 + 1 


def gf_add(a, b):
    """Addition dans GF(2^k) = XOR."""
    return a ^ b

def gf_sub(a, b):
    """Soustraction dans GF(2^k) = XOR (identique à l'addition)."""
    return a ^ b

def gf_mul(a, b):
    """Multiplication dans GF(2^8) modulo x^8 + x^4 + x^3 + x^2 + 1."""
    res = 0
    a = int(a)
    b = int(b)
    
    for _ in range(8):
        if b & 1:
            res ^= a
        
        # Réduction si le bit de poids fort (bit 7) de 'a' est un 1
        a_high_bit = a & 0x80
        a <<= 1
        
        if a_high_bit:
            a ^= IRREDUCIBLE_256
            
        b >>= 1
        
    return res

def gf_inv(a):
    """Inverse multiplicatif de 'a' dans GF(2^8) via XGCD pour les polynômes."""
    if a == 0:
        raise ZeroDivisionError("Division par zéro dans GF(2^8).")
    
    # Algorithme d'Euclide étendu pour les polynômes
    # r0 = IRREDUCIBLE_256, r1 = a
    r0 = IRREDUCIBLE_256
    r1 = a
    x0 = 0
    x1 = 1
    
    while r1 != 0:
        # q = r0 / r1 (division polynomiale)
        q_poly = 0
        r_temp = r0
        
        # Trouver le degré de r0 et r1
        deg_r0 = r0.bit_length() - 1
        deg_r1 = r1.bit_length() - 1
        
        # Calculer le quotient q
        while deg_r0 >= deg_r1 and deg_r1 >= 0:
            shift = deg_r0 - deg_r1
            q_poly |= (1 << shift)
            r_temp ^= (r1 << shift)
            
            # Recalculer le degré de r_temp pour la prochaine itération
            if r_temp == 0:
                deg_r0 = -1
            else:
                deg_r0 = r_temp.bit_length() - 1

        # Mise à jour des variables de l'algorithme
        r = r_temp
        x = x0 ^ gf_mul(q_poly, x1) # Utilisation de gf_mul
        
        r0, r1 = r1, r
        x0, x1 = x1, x
        
        if r0 == 1:
            # L'inverse est x0
            return x0
    
    # Si on arrive ici, l'inverse n'existe pas (r0 != 1)
    if r0 == 1:
        return x0
    else:
        # Devrait être impossible si a != 0 et IRREDUCIBLE_256 est irréductible
        raise ValueError(f"Inverse de {a} n'existe pas dans GF(2^8).")


# --- FONCTIONS MATHÉMATIQUES UTILITAIRES ---

def rand_vec(n):
    """Génère un vecteur aléatoire sur F_q (256)."""
    return [random.randrange(q) for _ in range(n)]

def mat_vec_mul(M, v):
    """Multiplication Matrice x Vecteur sur F_q."""
    res = []
    for i in range(len(M)):
        sum_val = 0
        for j in range(len(v)):
            # Utilisation de gf_add et gf_mul
            sum_val = gf_add(sum_val, gf_mul(M[i][j], v[j]))
        res.append(sum_val)
    return res

def invert_matrix(M):
    """Inversion de matrice sur F_q."""
    n = len(M)
    A = [[int(x) for x in row] for row in M]
    I = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
    
    for col in range(n):
        pivot = None
        for row in range(col, n):
            if A[row][col] != 0:
                pivot = row
                break
        if pivot is None:
            raise ValueError("Matrice non inversible.")

        A[col], A[pivot] = A[pivot], A[col]
        I[col], I[pivot] = I[pivot], I[col]

        # Normaliser ligne
        inv_pivot = gf_inv(A[col][col]) # Utilisation de gf_inv
        A[col] = [gf_mul(x, inv_pivot) for x in A[col]] # Utilisation de gf_mul
        I[col] = [gf_mul(x, inv_pivot) for x in I[col]] # Utilisation de gf_mul

        # Eliminer autres lignes
        for row in range(n):
            if row != col:
                factor = A[row][col]
                # Utilisation de gf_sub et gf_mul
                A[row] = [gf_sub(A[row][i], gf_mul(factor, A[col][i])) for i in range(n)]
                I[row] = [gf_sub(I[row][i], gf_mul(factor, I[col][i])) for i in range(n)]
    return I

# --- FONCTIONS UOV (GENRATION ET EVALUATION POLYNOMIALE) ---

# Génère les polynomes quadratiques
def generate_uov_polynomials(n, m, v):
    o = n - v
    polys = [] 
    for _ in range(m):
        poly = {
            "vv": [[random.randrange(q) for _ in range(v)] for _ in range(v)],
            "vo": [[random.randrange(q) for _ in range(o)] for _ in range(v)],
            "lin": [random.randrange(q) for _ in range(n)],
            "const": random.randrange(q),
        }
        polys.append(poly)
    return polys

# Évalue un polynôme F_i sur le vecteur x dans F_q.
def eval_poly(poly, x, v):
    o = len(x) - v
    xv = [int(i) for i in x[:v]] # Variables Vinegar
    xo = [int(i) for i in x[v:]]  # Variables Oil
    res = poly["const"]
    
    # Terme quadratique Vinegar-Vinegar (xv_i * xv_j)
    for i in range(v):
        for j in range(v):
            term = gf_mul(poly["vv"][i][j], gf_mul(xv[i], xv[j])) # Utilisation de gf_mul
            res = gf_add(res, term) # Utilisation de gf_add
            
    # Terme quadratique Vinegar-Oil (xv_i * xo_j)
    for i in range(v):
        for j in range(o):
            term = gf_mul(poly["vo"][i][j], gf_mul(xv[i], xo[j])) # Utilisation de gf_mul
            res = gf_add(res, term) # Utilisation de gf_add
            
    # Terme linéaire
    x_full = xv + xo 
    for i in range(len(x_full)):
        term = gf_mul(poly["lin"][i], x_full[i]) # Utilisation de gf_mul
        res = gf_add(res, term) # Utilisation de gf_add
        
    # Le résultat est déjà réduit modulo q par les opérations gf_add/gf_mul
    return res

#Évalue tous les polynômes F sur le vecteur x.
def eval_polys(polys, x, v):
    
    return [eval_poly(p, x, v) for p in polys]

# --- FONCTIONS PRINCIPALES ---

#Génère les clés secrètes et publiques UOV.
def KeyGen(n, v, m):
    if n - v != m:
        raise ValueError("Erreur de dimension: n - v doit être égal à m (taille de l'huile o).")
        
    print(f"Génération de clés sur GF(2^{n.bit_length()-1}) avec q={q}...")
    
    # F (Polynômes centraux secrets)
    F = generate_uov_polynomials(n, m, v)

    # T (Transformation affine secrète)
    while True:
        T = [[random.randrange(q) for _ in range(n)] for _ in range(n)]
        try:
            T_inv = invert_matrix(T)
            print("Matrice de transformation T inversible trouvée.")
            break
        except Exception:
            continue

    return {
        "n": n, "v": v, "m": m,
        "F": F,
        "T": T,
        "T_inv": T_inv
    }

#Algorithme de signature UOV.
def Sign(keypair, message):
    F = keypair["F"]
    T_inv = keypair["T_inv"]
    n = keypair["n"]
    v = keypair["v"]
    m = keypair["m"]
    o = n - v
    
    # Hashage
    h = hashlib.sha256(message.encode()).digest()
    while len(h) < m: 
        h += hashlib.sha256(h).digest()
    t = [h[i] % q for i in range(m)] # Target vector

    max_tries = 1000
    for attempt in range(max_tries):
        # 1. Tirer les vinegar aléatoirement
        xv = rand_vec(v)

        # 2. Construire système linéaire Ax = b pour les huiles (xo)
        A = [[0]*o for _ in range(m)]
        b = [0]*m

        for p_idx, poly in enumerate(F):
            # Calculer la valeur connue C = F_i(xv, 0) - F_i(0, 0)
            val_known = poly["const"]
            
            # Terme VV
            vv_sum = 0
            for i in range(v):
                for j in range(v):
                    term = gf_mul(poly["vv"][i][j], gf_mul(xv[i], xv[j]))
                    vv_sum = gf_add(vv_sum, term)
            val_known = gf_add(val_known, vv_sum)
            
            # Terme Lin V
            lin_v_sum = 0
            for i in range(v):
                term = gf_mul(poly["lin"][i], xv[i])
                lin_v_sum = gf_add(lin_v_sum, term)
            val_known = gf_add(val_known, lin_v_sum)
            
            # b = target - known
            b[p_idx] = gf_sub(t[p_idx], val_known) # Utilisation de gf_sub

            # Matrice A (Coefficients des variables huile)
            for j in range(o):
                coeff = 0
                # Terme quadratique (vo)
                for i in range(v):
                    term = gf_mul(poly["vo"][i][j], xv[i])
                    coeff = gf_add(coeff, term)
                # Terme linéaire (lin)
                coeff = gf_add(coeff, poly["lin"][v + j])
                A[p_idx][j] = coeff

        # 3. Résolution
        try:
            A_inv = invert_matrix(A)
            xo = mat_vec_mul(A_inv, b)
            
            # 4. Reconstitution u = xv || xo
            u = xv + xo
            
            # 5. Signature sigma = T_inv(u)
            sigma = mat_vec_mul(T_inv, u)
            return sigma

        except ValueError:
            # Matrice singulière, on recommence
            continue

    raise Exception("Échec de signature : impossible de trouver une matrice inversible après 1000 essais.")

#Algorithme de vérification UOV.
def Verify(keypair, message, sigma):
    
    F = keypair["F"]
    T = keypair["T"]
    v = keypair["v"]
    m = keypair["m"]
    
    # 1. Hashing
    h = hashlib.sha256(message.encode()).digest()
    while len(h) < m: 
        h += hashlib.sha256(h).digest()
    target = [h[i] % q for i in range(m)]
    
    # 2. Calculer P(sigma) = F( T(sigma) )
    u = mat_vec_mul(T, sigma)
    y = eval_polys(F, u, v)
    
    # 3. Comparaison
    return y == target
