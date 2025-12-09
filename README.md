🔑 UOVapp : Système de Signature Post-Quantique UOV en Python

Ce projet implémente un système de signature numérique basé sur le schéma Unbalanced Oil and Vinegar (UOV), une des constructions de cryptographie asymétrique multivariée considérée comme résistante aux attaques par ordinateurs quantiques.

L'application est fournie avec une interface utilisateur graphique (GUI), développée avec PySide6 (Qt), pour démontrer visuellement la génération des clés, la signature des messages et la vérification des signatures.

🌟 Fonctionnalités Clés

Implémentation UOV Complète : Intègre les fonctions de génération de clés (KeyGen), de signature (Sign) et de vérification (Verify) du schéma UOV.

Résistance Post-Quantique : Utilisation de la cryptographie multivariée, candidate à la standardisation pour sa sécurité face aux algorithmes quantiques (comme l'algorithme de Shor).

Interface Utilisateur Fluide : Utilisation du multithreading (QThread) pour exécuter les calculs cryptographiques longs (notamment la génération des clés) en arrière-plan, garantissant que l'interface utilisateur reste toujours réactive et ne "gèle" jamais.

Paramétrage Flexible : Permet de configurer les paramètres de sécurité clés de UOV (v pour Vinegar et o pour Oil) via l'interface.

💻 Structure du Projet

Le projet est divisé en deux parties principales :

uov/uov.py (Cœur Cryptographique) : Contient toute la logique mathématique et cryptographique (manipulation des polynômes quadratiques, inversion de matrice, etc.).

gui/main_app.py (Interface Utilisateur) : Gère l'application graphique, les interactions utilisateur et le lancement des opérations cryptographiques dans des threads séparés.

🚀 Démarrage Rapide

Prérequis

Python 3.12

Les bibliothèques nécessaires : PySide6

Installation

Clonez le dépôt :

git clone [https://github.com/Chris-Manuelpipo/UOVapp.git](https://github.com/Chris-Manuelpipr/UOVapp.git)
cd UOV-PySig


Installez les dépendances Python (PySide6 est nécessaire pour l'interface graphique) :

pip install PySide6


Exécution

Lancez l'application GUI depuis le répertoire racine :

python gui/main_app.py


⚙️ Utilisation de l'Application GUI

Générer les Clés :

Dans l'onglet  Générer les clés, choisissez les paramètres v (Vinegar) et o (Oil). Assurez-vous que v > o.

Cliquez sur " Générer les clés". L'application démarre le calcul en arrière-plan et affiche un résumé structurel de la clé publique une fois terminé (évitant le gel de l'interface).

Signer :

Allez dans l'onglet  Signer un message.

Entrez le message et cliquez sur "Signer le message". La signature UOV (un long vecteur d'entiers) est affichée.

Vérifier :

Dans l'onglet " Vérifier une signature, entrez le message original et copiez/collez le vecteur de signature.

Cliquez sur " Vérifier" pour confirmer si la signature est valide pour le message donné avec la clé publique générée.

 Contribution

Les contributions sont les bienvenues ! Si vous souhaitez améliorer la performance des algorithmes cryptographiques, ajouter des fonctionnalités ou corriger des bugs, veuillez soumettre une Pull Request.
