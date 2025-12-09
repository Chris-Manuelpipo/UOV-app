import numpy as np
from hashlib import sha256

# --- Fonctions utilitaires ---
def hash_message(message: bytes, q: int, n_oil: int):
    h = sha256(message).digest()
    return np.array([b % q for b in h[:n_oil]], dtype=np.int64)

class QuadraticPolynomial:
    def __init__(self, n, q):
        self.A = np.random.randint(0, q, (n, n))

    def evaluate(self, x, q):
        return int(np.dot(x, np.dot(self.A, x)) % q)

# --- Génération clés ---
def generate_keys(n_oil, n_vin, q):
    n = n_oil + n_vin
    private_polys = [QuadraticPolynomial(n, q) for _ in range(n_oil)]
    # Ici la clé publique est juste un placeholder
    public_polys = private_polys
    return private_polys, public_polys

# --- Signature simplifiée ---
def sign(message, private_polys, q, n_oil, n_vin):
    n = n_oil + n_vin
    h = hash_message(message.encode(), q, n_oil)

    while True:
        # Tirage Vinegar
        x_v = np.random.randint(0, q, n_vin)
        # Pour l’instant, on simule les Oil comme un vecteur aléatoire
        x_o = np.random.randint(0, q, n_oil)
        x = np.concatenate([x_o, x_v])
        result = np.array([f.evaluate(x, q) for f in private_polys]) % q
        if np.array_equal(result, h):
            return x

# --- Vérification ---
def verify(message, signature, public_polys, q):
    n_oil = len(public_polys)
    h = hash_message(message.encode(), q, n_oil)
    result = np.array([f.evaluate(signature, q) for f in public_polys]) % q
    return np.array_equal(result, h)

# --- Programme principal ---
def main():
    print("=== UOV Prototype en Python ===")
    message = input("Entrez le message à signer : ")
    n_oil = int(input("Nombre de variables Oil : "))
    n_vin = int(input("Nombre de variables Vinegar : "))
    q = 31  # corps fini petit pour test rapide

    print("[+] Génération des clés…")
    priv, pub = generate_keys(n_oil, n_vin, q)
    print("[OK] Clés générées")
    print(priv)
    print (pub)

    print("[+] Signature du message…")
    signature = sign(message, priv, q, n_oil, n_vin)
    print("[OK] Signature effectuée")
    print("Signature :", signature)

    print("[+] Vérification…")
    valid = verify(message, signature, pub, q)
    print("Signature valide ?", valid)

if __name__ == "__main__":
    main()





# import numpy as np
# from sympy import symbols, Poly

# # Paramètres UOV
# n = 4  # Nombre total de variables (oil + vinegar)
# o = 2  # Nombre de variables "oil"
# v = n - o  # Nombre de variables "vinegar"

# # Génération aléatoire des matrices pour la clé privée
# A = np.random.randint(0, 2, size=(o, v))
# B = np.random.randint(0, 2, size=(o, o))
# C = np.random.randint(0, 2, size=(o, v))

# # Variables symboliques pour les équations
# oil_vars = symbols(f'x0:{o}')
# vinegar_vars = symbols(f'y0:{v}')
# all_vars = oil_vars + vinegar_vars

# # Construction des équations quadratiques (simplifiée)
# equations = []
# for i in range(o):
#     # Exemple d'équation quadratique : x_i + sum(A[i,j]*y_j) + sum(B[i,j]*x_i*x_j) + sum(C[i,j]*y_j*y_k) = 0
#     eq = oil_vars[i] + sum(A[i,j] * vinegar_vars[j] for j in range(v))
#     equations.append(eq)

# print("Équations quadratiques (clé publique) :")
# for eq in equations:
#     print(eq)

# # Exemple de signature (simplifié)
# def sign(message, private_key):
#     # Ici, tu devrais résoudre le système d'équations pour générer la signature.
#     # Cela nécessite une implémentation plus avancée.
#     return np.random.randint(0, 2, size=n)  # Signature fictive

# # Exemple de vérification
# def verify(message, signature, public_key):
#     # Vérifie si la signature satisfait les équations quadratiques.
#     # Retourne True ou False.
#     return True  # Vérification fictive

# # Test
# message = "Bonjour"
# signature = sign(message, (A, B, C))
# is_valid = verify(message, signature, equations)
# print(f"Signature valide ? {is_valid}")




# class UOVApp:
#     def __init__(self):
#         self.private_key = None
#         self.public_key = None

#     def generate_keys(self, o, v):
#         # Génère les clés publique et privée
#         pass

#     def sign_message(self, message):
#         # Signe un message avec la clé privée
#         pass

#     def verify_signature(self, message, signature):
#         # Vérifie une signature avec la clé publique
#         pass

#     def save_keys(self, private_key_path, public_key_path):
#         # Sauvegarde les clés dans des fichiers
#         pass

#     def load_keys(self, private_key_path, public_key_path):
#         # Charge les clés depuis des fichiers
#         pass

# def main():
#     app = UOVApp()
#     while True:
#         print("\nMenu principal :")
#         print("1. Générer une nouvelle paire de clés")
#         print("2. Signer un message")
#         print("3. Vérifier une signature")
#         print("4. Quitter")
#         choice = input("Choisissez une option : ")
#         if choice == "1":
#             o = int(input("Nombre de variables 'oil' : "))
#             v = int(input("Nombre de variables 'vinegar' : "))
#             app.generate_keys(o, v)
#         elif choice == "2":
#             message = input("Entrez le message à signer : ")
#             signature = app.sign_message(message)
#             print(f"Signature : {signature}")
#         elif choice == "3":
#             message = input("Entrez le message : ")
#             signature = input("Entrez la signature : ")
#             is_valid = app.verify_signature(message, signature)
#             print(f"Signature valide ? {is_valid}")
#         elif choice == "4":
#             break

# if __name__ == "__main__":
#     main()
