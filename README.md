# 🔑 UOV-app — Implémentation Python du Schéma de Signature Post-Quantique UOV

UOV-app est une implémentation fonctionnelle du schéma de signature **Unbalanced Oil and Vinegar (UOV)**, une construction de cryptographie multivariée reconnue pour sa résistance aux attaques quantiques.

Le projet inclut une **interface graphique (GUI)** développée avec **PySide6**, permettant de générer des clés, signer des messages et vérifier des signatures de manière intuitive.

---

## 🌟 Fonctionnalités Principales

- **Implémentation UOV complète (KeyGen, Sign, Verify)**  
  Code mathématique développé **à la main**, sans bibliothèque externe de corps finis.

- **Cryptographie Post-Quantique**  
  Utilisation d'un corps fini **GF(256)** (champ binaire étendu), conforme aux constructions UOV classiques.  
  Paramètres par défaut : **v = 112**, **o = 44** (jeu recommandé UOV-IP du NIST).

- **Interface graphique réactive (PySide6)**  
  L'application repose sur **QThread** pour exécuter les opérations lourdes (notamment KeyGen) en arrière-plan.  
  La GUI reste fluide et affiche une **barre de progression** pendant les calculs.

- **Paramétrage configurable**  
  L'utilisateur peut choisir les valeurs de *v* (Vinegar) et *o* (Oil) avant la génération des clés.

- **Signatures sérialisées en JSON**  
  Lisibles, exportables et facilement manipulables.

---

## 🧩 Architecture du Projet

```
UOV-app/
│
├── uov/
│   └── uov.py          # Cœur cryptographique (polynômes, GF(256), KeyGen, Sign, Verify)
│
└── interface/
    └── main_app.py     # Point d'entrée de l'interface graphique PySide6
```

### Composants principaux

- **uov/uov.py**  
  Implémente l'intégralité de la logique cryptographique :
  - Manipulations dans GF(256)
  - Inversion et opérations matricielles
  - Polynômes quadratiques
  - KeyGen, Sign, Verify du schéma UOV classique

- **interface/main_app.py**  
  Interface graphique Qt/PySide6, gestion des threads, interactions utilisateur, affichage des coefficients de la clé publique et de la signature.

---

## 🚀 Installation

### Prérequis

- Python **3.12** (fonctionne également sur Python 3.x récents)
- Système compatible PySide6 (Linux, Windows, macOS)

### Cloner le dépôt

```bash
git clone https://github.com/Chris-Manuelpipo/UOV-app.git
cd UOV-app
```

### Installer les dépendances

```bash
pip install PySide6
```

Aucune autre bibliothèque externe n'est nécessaire.

---

## ▶️ Exécution de l'application

Depuis la racine du projet :

```bash
python interface/main_app.py
```

L'interface se lance immédiatement.

---

## ⚙️ Utilisation

### 1. Génération des clés

1. Choisir les valeurs **v** et **o** (par défaut : 112/44)
   - ⚠️ **Attention** : la règle de sécurité UOV impose **v > o**
2. Cliquer sur **Générer les clés**
3. L'application affiche une barre de progression, puis un résumé des coefficients de la clé publique

### 2. Signature

1. Aller dans **Signer un message**
2. Entrer un message texte (sans limite particulière)
3. Le message est automatiquement haché SHA-256, puis signé
4. La signature (liste d'entiers) est affichée et sérialisée en JSON

### 3. Vérification

1. Aller dans **Vérifier une signature**
2. Fournir :
   - Le message original
   - La signature au format JSON
3. Cliquer sur **Vérifier** : la GUI confirme ou rejette la signature

> ℹ️ **Note** : L'interface ne propose pas encore l'export des clés en fichier.

---

## 🔐 Notes de Sécurité

⚠️ **Ce projet est académique.**  
Il ne doit pas être utilisé en production, ni pour des données sensibles.

**Limitations :**
- Pas d'audit cryptographique
- Pas de protections contre les attaques par canaux cachés (timing, side-channel)
- Pas d'implémentation certifiée du standard UOV-IP
- Paramètres recommandés mais non garantis contre les attaques avancées

---

## 🛠️ Contribution

Les contributions sont encouragées :

- Optimisation des opérations dans GF(256)
- Réorganisation du cœur cryptographique
- Ajout de tests unitaires
- Améliorations GUI (visualisation, export, feedback)

Aucune convention de commit spécifique n'est imposée.

### Pour contribuer :

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Commit vos changements (`git commit -m 'Ajout de fonctionnalité'`)
4. Push vers la branche (`git push origin feature/amelioration`)
5. Ouvrir une Pull Request

---

## 📄 Licence

Ce projet est distribué sous licence MIT. 

---

## 👤 Auteur

**Chris-Manuelpipo et toute l'équipe**  Pour le projet de science de l'information sur le schéma UOV.
GitHub: [@Chris-Manuelpipo](https://github.com/Chris-Manuelpipo)