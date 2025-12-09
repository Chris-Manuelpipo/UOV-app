import sys
import os
import json
import time
import hashlib
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QPushButton, QVBoxLayout,
    QHBoxLayout, QLabel, QSpinBox, QTextEdit, QMessageBox, QLineEdit,
    QProgressDialog, QGroupBox, QFileDialog
)
from PySide6.QtCore import Qt, QThread, Signal

# Assurez-vous que le chemin vers le module uov est correct
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# NOTE: Assurez-vous d'avoir le module uov disponible dans l'environnement d'exécution
try:
    from uov import KeyGen, Sign, Verify, q
except ImportError:
    # Fournir des stubs si uov n'est pas disponible pour la compilation (mais l'app ne fonctionnera pas réellement sans)
    print("ATTENTION: Le module 'uov' est introuvable. Les fonctions crypto ne seront pas disponibles.")
    q = 251 # Valeur par défaut
    def KeyGen(*args, **kwargs): return {"n": 156, "v": 112, "m": 44, "F": [], "T": []}
    def Sign(*args, **kwargs): return list(range(156))
    def Verify(*args, **kwargs): return True


BASE = Path(__file__).resolve().parent.parent

# ==============================================================================
# CLASSE DE TRAVAIL EN ARRIÈRE-PLAN POUR LA GÉNÉRATION DE CLÉS
# ==============================================================================

class KeyGenWorker(QThread):
    """Travailleur pour la génération de clés KeyGen"""
    finished = Signal(dict, str, str, float)
    
    def __init__(self, n, v, m):
        super().__init__()
        self.n = n
        self.v = v
        self.m = m

    def run(self):
        try:
            start_time = time.time()
            private_key = KeyGen(self.n, self.v, self.m)
            public_key = {k: private_key[k] for k in ["n", "v", "m", "F", "T"]}
            
            pub_digest = {
                "Paramètres": f"v={self.v} (vinegar), o={self.m} (oil)",
                "n": self.n,
                "Nombre de polynomes quadratiques": len(public_key["F"]),
                "Forme de T": f"{self.n}x{self.n}",
                "Modèle des coefficients": public_key["F"][0]["vv"][:5] if public_key["F"] else "N/A",
                "q": q
            }
            pub_text = json.dumps(pub_digest, indent=2)
            priv_text = "Clé privée (F, T) générée et stockée en mémoire. Non affichée pour raisons de sécurité."
            
            end_time = time.time()
            duration = end_time - start_time
            self.finished.emit(private_key, pub_text, priv_text, duration)
        except Exception as e:
            # En cas d'erreur, émettre un dictionnaire vide et le message d'erreur
            self.finished.emit({}, f"Erreur de génération : {e}", "", 0.0)

# ==============================================================================
# CLASSE DE TRAVAIL EN ARRIÈRE-PLAN POUR LA SIGNATURE
# ==============================================================================

class SignWorker(QThread):
    """Travailleur pour la signature asynchrone (message ou document)"""
    finished = Signal(bool, str, list, float, str) # Succès, message/hash signé, signature, durée, chemin du fichier (ou None)
    
    def __init__(self, private_key, data_to_sign, is_file_hash, file_path=None):
        super().__init__()
        self.private_key = private_key
        self.data_to_sign = data_to_sign
        self.is_file_hash = is_file_hash
        self.file_path = file_path

    def run(self):
        try:
            # Si c'est un fichier, le message à signer est d'abord le hash
            message = self.data_to_sign
            
            if self.is_file_hash and self.file_path:
                # Calculer le hash du fichier (peut être long)
                message = self._calculate_file_hash(self.file_path)

            start_time = time.time()
            sigma = Sign(self.private_key, message) 
            end_time = time.time()
            duration = end_time - start_time
            
            self.finished.emit(True, message, sigma, duration, self.file_path)
            
        except Exception as e:
            # Émettre l'échec
            self.finished.emit(False, str(e), [], 0.0, self.file_path)

    def _calculate_file_hash(self, file_path):
        """Calcule le hash SHA-256 d'un fichier (fonction utilitaire pour le worker)"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

# ==============================================================================
# CLASSE DE TRAVAIL EN ARRIÈRE-PLAN POUR LA VÉRIFICATION
# ==============================================================================

class VerifyWorker(QThread):
    """Travailleur pour la vérification asynchrone (message ou document)"""
    finished = Signal(bool, str, float, bool) # Résultat (Valide/Invalide), message/hash, durée, est_verification_fichier
    
    def __init__(self, public_key, data_to_verify, sigma, is_file_verification, stored_hash=None):
        super().__init__()
        self.public_key = public_key
        self.data_to_verify = data_to_verify # Message ou chemin du fichier
        self.sigma = sigma
        self.is_file_verification = is_file_verification
        self.stored_hash = stored_hash # Hash attendu si vérification de fichier

    def run(self):
        try:
            message_or_hash = self.data_to_verify
            
            if self.is_file_verification:
                # 1. Calculer le hash du fichier actuel
                current_hash = self._calculate_file_hash(self.data_to_verify)
                
                # 2. Vérifier que le hash correspond au hash stocké dans le .sig
                if current_hash != self.stored_hash:
                    # Le fichier a été modifié, la vérification échoue avant l'appel à Verify
                    self.finished.emit(False, "Le document a été modifié !", 0.0, True)
                    return
                
                message_or_hash = current_hash
            
            # 3. Vérifier la signature
            start_time = time.time()
            ok = Verify(self.public_key, message_or_hash, self.sigma)
            end_time = time.time()
            duration = end_time - start_time
            
            self.finished.emit(ok, message_or_hash, duration, self.is_file_verification)
            
        except Exception as e:
            # Émettre l'échec, le message d'erreur est la raison
            self.finished.emit(False, str(e), 0.0, self.is_file_verification)

    def _calculate_file_hash(self, file_path):
        """Calcule le hash SHA-256 d'un fichier (fonction utilitaire pour le worker)"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

# ==============================================================================
# FENÊTRE PRINCIPALE
# ==============================================================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Signature UOV")
        self.resize(900, 700)
        
        self.public_key = None  
        self.private_key = None 
        self.last_sigma = None
        self.keygen_worker = None
        self.sign_worker = None
        self.verify_worker = None 
        self.progress_dialog = None
        
        # Variables pour les fichiers
        self.selected_file_path = None
        self.verify_file_path = None
        self.verify_signature_path = None
        
        self.init_ui()

    def init_ui(self):
        tabs = QTabWidget()
        tabs.addTab(self.tab_keygen(), "Générer les clés")
        tabs.addTab(self.tab_sign(), " Signer un message ou un document")
        tabs.addTab(self.tab_verify(), "Vérifier une signature")
        self.setCentralWidget(tabs)
        
        self.setStyleSheet("""
    /* --- Global --- */
QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 16px;
}

/* --- Labels --- */
QLabel {
    color: #e0e0e0;
    font-weight: 500;
    font-size: 16px;
}

/* --- GroupBox --- */
QGroupBox {
    border: 1px solid #3c3c3c;
    border-radius: 6px;
    margin-top: 10px;
    padding: 10px;
    font-weight: bold;
    font-size: 17px;
    color: #c0c0c0;
}

QGroupBox:title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0px 4px;
}

/* --- LineEdits --- */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #2b2b2b;
    border: 1px solid #555;
    border-radius: 5px;
    padding: 6px;
    font-size: 15px;
    selection-background-color: #4a90e2;
}

/* --- Buttons --- */
QPushButton {
    background-color: #2d63c8;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 600;
    font-size: 16px;
}

QPushButton:hover {
    background-color: #3a74e8;
}

QPushButton:pressed {
    background-color: #244c96;
}

/* --- Secondary buttons --- */
QPushButton#secondary {
    background-color: #444;
    font-size: 16px;
}

QPushButton#secondary:hover {
    background-color: #555;
}

/* --- SpinBox --- */
QSpinBox {
    font-size: 15px;
}

/* --- ScrollBar --- */
QScrollBar:vertical {
    background: #2b2b2b;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #555;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #777;
}

/* --- MessageBox --- */
QMessageBox {
    background-color: #1e1e1e;
    font-size: 16px;
}

QMessageBox QLabel {
    color: #e0e0e0;
    font-size: 16px;
}

QMessageBox QPushButton {
    background-color: #2d63c8;
    border-radius: 5px;
    padding: 6px 12px;
    font-size: 16px;
}

/* --- Tabs --- */
QTabWidget::pane {
    border: 1px solid #333;
    background: #1e1e1e;
}

QTabBar::tab {
    background: #2b2b2b;
    padding: 8px 16px;
    border: 1px solid #444;
    border-bottom: none;
    font-size: 16px;
}

QTabBar::tab:selected {
    background: #3d3d3d;
    font-weight: bold;
    font-size: 16px;
}
""")

    # --- Tab KeyGen ---
    def tab_keygen(self):
        
        w = QWidget()
        layout = QVBoxLayout()
        
        param_group = QGroupBox("Paramètres UOV (v, o, q)")
        params_layout = QHBoxLayout()
        params_layout.addWidget(QLabel("Nombre de variables vinegar :"))
        self.spin_v = QSpinBox()
        self.spin_v.setRange(1, 500)
        self.spin_v.setValue(112)
        params_layout.addWidget(self.spin_v)

        params_layout.addWidget(QLabel("Nombre de variables huile:"))
        self.spin_o = QSpinBox()
        self.spin_o.setRange(1, 500)
        self.spin_o.setValue(44)
        params_layout.addWidget(self.spin_o)

        params_layout.addWidget(QLabel("q:"))
        self.input_q = QLineEdit(str(q))
        self.input_q.setReadOnly(True)
        params_layout.addWidget(self.input_q)
        param_group.setLayout(params_layout)
        layout.addWidget(param_group)

        btn_layout = QHBoxLayout()
        self.btn_gen = QPushButton("Générer les clés")
        self.btn_gen.clicked.connect(self.handle_generate)
        btn_layout.addWidget(self.btn_gen)
        layout.addLayout(btn_layout)
        
        layout.addWidget(QLabel("Clé Publique (F°T):"))
        self.text_pub = QTextEdit()
        self.text_pub.setReadOnly(True)
        layout.addWidget(self.text_pub)

        self.text_priv_label = QLabel("Clé Privée (F, T) :")
        layout.addWidget(self.text_priv_label)
        self.text_priv = QLineEdit("Non affichée. Stockée en mémoire.")
        self.text_priv.setReadOnly(True)
        layout.addWidget(self.text_priv)

        w.setLayout(layout)
        return w
        

    def handle_generate(self):
        
        v = int(self.spin_v.value())
        o = int(self.spin_o.value())
        if v <= o:
             QMessageBox.critical(self, "Erreur", "v (vinegar) doit être > o (oil).")
             return
        
        n = v + o
        m = o

        self.progress_dialog = QProgressDialog("Génération des clés ...", "Annuler", 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.show()
        self.btn_gen.setEnabled(False) # Désactiver le bouton pendant le travail
        
        self.keygen_worker = KeyGenWorker(n, v, m)
        self.keygen_worker.finished.connect(self.keygen_finished)
        self.keygen_worker.start()
        # ...

    def keygen_finished(self, private_key, pub_text, priv_text, duration):
        
        self.progress_dialog.close()
        self.btn_gen.setEnabled(True)
        
        if private_key:
            self.private_key = private_key
            self.public_key = {k: self.private_key[k] for k in ["n", "v", "m", "F", "T"]}
            
            self.text_pub.setPlainText(pub_text)
            self.text_priv.setText(priv_text) 
            
            QMessageBox.information(self, "Succès", f"Clés générées en {duration:.2f}s, vous pouvez signer un message ou un document.")
        else:
             self.text_pub.setPlainText(pub_text)
             QMessageBox.critical(self, "Erreur de génération", "Erreur lors de la génération des clés.")
      

    # --- Tab Signer (Fusionne Message et Document) ---
    def tab_sign(self):
        w = QWidget()
        layout = QVBoxLayout()
        
        # --- Signer un message texte ---
        msg_group = QGroupBox("Signer un message ")
        msg_layout = QVBoxLayout()
        
        msg_layout.addWidget(QLabel("Message à signer :"))
        self.text_message_sign = QTextEdit()
        msg_layout.addWidget(self.text_message_sign)

        self.btn_sign_msg = QPushButton(" Signer le message")
        self.btn_sign_msg.clicked.connect(self.handle_sign_message)
        msg_layout.addWidget(self.btn_sign_msg)

        msg_layout.addWidget(QLabel("Signature obtenue :"))
        self.text_signature = QTextEdit()
        self.text_signature.setReadOnly(True)
        msg_layout.addWidget(self.text_signature)
        
        msg_group.setLayout(msg_layout)
        layout.addWidget(msg_group)

        # --- Signer un document ---
        sign_file_group = QGroupBox(" Signer un document")
        sign_file_layout = QVBoxLayout()
        
        file_select_layout = QHBoxLayout()
        self.label_selected_file = QLabel("Aucun fichier sélectionné")
        self.label_selected_file.setStyleSheet("color: #888; font-style: italic;")
        file_select_layout.addWidget(self.label_selected_file)
        
        btn_select_file = QPushButton(" Choisir un document à signer")
        btn_select_file.clicked.connect(self.select_file_to_sign)
        file_select_layout.addWidget(btn_select_file)
        sign_file_layout.addLayout(file_select_layout)
        
        self.btn_sign_file = QPushButton(" Signer le document ")
        self.btn_sign_file.clicked.connect(self.handle_sign_file)
        self.btn_sign_file.setEnabled(False)
        sign_file_layout.addWidget(self.btn_sign_file)
        
        self.label_file_hash = QLabel("Hash (SHA-256) du document: ")
        self.label_file_hash.setStyleSheet("font-size: 14px; color: #4a90e2;")
        sign_file_layout.addWidget(self.label_file_hash)
        
        sign_file_group.setLayout(sign_file_layout)
        layout.addWidget(sign_file_group)
        
        layout.addStretch()
        w.setLayout(layout)
        return w

    def handle_sign_message(self):
        if not self.private_key:
            QMessageBox.warning(self, "Avertissement", "Génèrez d'abord les clés.")
            return
        message = self.text_message_sign.toPlainText()
        if not message:
            QMessageBox.warning(self, "Avertissement", "Message vide.")
            return
            
        self.progress_dialog = QProgressDialog("Calcul de la signature du message...", "Annuler", 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.show()
        
        self.btn_sign_msg.setEnabled(False)
        
        self.sign_worker = SignWorker(self.private_key, message, is_file_hash=False)
        self.sign_worker.finished.connect(self.sign_message_finished)
        self.sign_worker.start()

    def sign_message_finished(self, success, message_or_error, sigma, duration, file_path):
        self.progress_dialog.close()
        self.btn_sign_msg.setEnabled(True)
        
        if success:
            self.text_signature.setPlainText(str(sigma)) 
            self.last_sigma = sigma
            QMessageBox.information(self, "Succès", f"Signature calculée en {duration:.2f}s. Longueur: {len(sigma)} entiers.")
        else:
            QMessageBox.critical(self, "Erreur de signature", f"Échec de la signature : {message_or_error}")
    
    def handle_sign_file(self):
        if not self.private_key:
            QMessageBox.warning(self, "Avertissement", "Génèrez d'abord les clés.")
            return
        
        if not self.selected_file_path:
            QMessageBox.warning(self, "Avertissement", "Sélectionnez un fichier à signer.")
            return
        
        self.progress_dialog = QProgressDialog("Calcul du hash et signature du document...", "Annuler", 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.show()
        
        self.btn_sign_file.setEnabled(False)

        # On passe le chemin du fichier pour que le worker calcule le hash et signe
        self.sign_worker = SignWorker(self.private_key, None, is_file_hash=True, file_path=self.selected_file_path)
        self.sign_worker.finished.connect(self.sign_file_finished)
        self.sign_worker.start()
    
    def sign_file_finished(self, success, file_hash_or_error, sigma, duration, file_path):
        self.progress_dialog.close()
        self.btn_sign_file.setEnabled(True)

        if not success:
            QMessageBox.critical(self, "Erreur de signature", f"Échec de la signature : {file_hash_or_error}")
            return
        
        # Sauvegarder la signature
        try:
            sig_file_path = file_path + ".sig"
            
            save_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Sauvegarder la signature", 
                sig_file_path, 
                "Fichiers de signature (*.sig)"
            )

            if not save_path:
                QMessageBox.warning(self, "Annulation", "Sauvegarde de la signature annulée.")
                return

            signature_data = {
                "file_name": os.path.basename(file_path),
                "file_hash": file_hash_or_error, # Ici, c'est le hash du fichier
                "signature": sigma,
                "algorithm": "UOV",
                "hash_algorithm": "SHA-256"
            }
            
            with open(save_path, "w") as f:
                json.dump(signature_data, f, indent=2)
            
            QMessageBox.information(
                self, 
                "Succès", 
                f"Document signé en {duration:.2f}s.\n\n"
                f"Signature sauvegardée dans :\n{save_path}"
            )
            
            self.label_file_hash.setText(f"Signature créée : {os.path.basename(save_path)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur de sauvegarde", f"Erreur lors de la sauvegarde du fichier signature : {e}")

    # --- Tab Vérifier une signature (Fusionne Message et Document) ---
    def tab_verify(self):
        w = QWidget()
        layout = QVBoxLayout()
        
        # --- Section 1: Vérifier la signature d'un message texte ---
        msg_verify_group = QGroupBox(" Vérifier la signature d'un message texte")
        msg_verify_layout = QVBoxLayout()
        
        msg_verify_layout.addWidget(QLabel("Message à vérifier :"))
        self.text_message_verify = QTextEdit()
        msg_verify_layout.addWidget(self.text_message_verify)

        msg_verify_layout.addWidget(QLabel("Signature (collez une signature ou utilisez la dernière signature) :"))
        self.text_signature_input = QTextEdit()
        
        btn_load_sig = QPushButton("Charger la dernière signature")
        btn_load_sig.clicked.connect(lambda: self.text_signature_input.setPlainText(str(self.last_sigma)))
        msg_verify_layout.addWidget(btn_load_sig)
        
        msg_verify_layout.addWidget(self.text_signature_input)
        
        btn_layout = QHBoxLayout()
        self.btn_verify_msg = QPushButton("Vérifier le message")
        self.btn_verify_msg.clicked.connect(self.handle_verify_message)
        btn_layout.addWidget(self.btn_verify_msg)
        msg_verify_layout.addLayout(btn_layout)

        self.label_verify_result = QLabel("---")
        self.label_verify_result.setStyleSheet("font-size: 14pt; font-weight: bold;")
        msg_verify_layout.addWidget(self.label_verify_result)
        
        msg_verify_group.setLayout(msg_verify_layout)
        layout.addWidget(msg_verify_group)


        # --- Section 2: Vérifier la signature d'un document ---
        verify_file_group = QGroupBox(" Vérifier une signature de document")
        verify_layout = QVBoxLayout()
        
        # Sélection du fichier à vérifier
        file_verify_layout = QHBoxLayout()
        self.label_verify_file = QLabel("Aucun document sélectionné")
        self.label_verify_file.setStyleSheet("color: #888; font-style: italic;")
        file_verify_layout.addWidget(self.label_verify_file)
        
        btn_select_verify_file = QPushButton(" Choisir le document")
        btn_select_verify_file.clicked.connect(self.select_file_to_verify)
        file_verify_layout.addWidget(btn_select_verify_file)
        verify_layout.addLayout(file_verify_layout)
        
        # Sélection du fichier signature
        sig_verify_layout = QHBoxLayout()
        self.label_verify_sig = QLabel("Aucune signature (.sig) sélectionnée")
        self.label_verify_sig.setStyleSheet("color: #888; font-style: italic;")
        sig_verify_layout.addWidget(self.label_verify_sig)
        
        btn_select_verify_sig = QPushButton("Choisir la signature (.sig)")
        btn_select_verify_sig.clicked.connect(self.select_signature_to_verify)
        sig_verify_layout.addWidget(btn_select_verify_sig)
        verify_layout.addLayout(sig_verify_layout)
        
        self.btn_verify_file = QPushButton(" Vérifier la signature du document")
        self.btn_verify_file.clicked.connect(self.handle_verify_file)
        self.btn_verify_file.setEnabled(False)
        verify_layout.addWidget(self.btn_verify_file)
        
        self.label_file_verify_result = QLabel("---")
        self.label_file_verify_result.setStyleSheet("font-size: 16pt; font-weight: bold;")
        verify_layout.addWidget(self.label_file_verify_result)
        
        verify_file_group.setLayout(verify_layout)
        layout.addWidget(verify_file_group)
        
        layout.addStretch()
        w.setLayout(layout)
        return w

    def handle_verify_message(self):
        if not self.public_key:
            QMessageBox.warning(self, "Avertissement", "Générez d'abord les clés.")
            return
        
        message = self.text_message_verify.toPlainText()
        sig_text = self.text_signature_input.toPlainText().strip()
        
        if not message or not sig_text:
            QMessageBox.warning(self, "Avertissement", "Message ou signature manquante.")
            return
        
        try:
            sigma = eval(sig_text)
            if not isinstance(sigma, list) or not all(isinstance(x, int) for x in sigma):
                 raise ValueError("Non list of ints")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Format de signature invalide : {e}")
            return
            
        self.progress_dialog = QProgressDialog("Vérification du message en cours...", "Annuler", 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.show()
        
        self.btn_verify_msg.setEnabled(False)
        
        # Démarrer le thread de vérification
        self.verify_worker = VerifyWorker(self.public_key, message, sigma, is_file_verification=False)
        self.verify_worker.finished.connect(self.verify_message_finished)
        self.verify_worker.start()

    def verify_message_finished(self, is_valid, message_or_error, duration, is_file_verification):
        self.progress_dialog.close()
        self.btn_verify_msg.setEnabled(True)
        
        if is_valid:
            self.label_verify_result.setText(f" Signature valide ! ({duration:.2f}s)")
            self.label_verify_result.setStyleSheet("font-size: 14pt; font-weight: bold; color: green;")
        else:
            if "Erreur de vérification" in message_or_error:
                QMessageBox.critical(self, "Erreur de vérification", message_or_error)
            
            self.label_verify_result.setText(f"Signature invalide !")
            self.label_verify_result.setStyleSheet("font-size: 14pt; font-weight: bold; color: red;")
            
    # --- Méthodes pour la signature de fichiers (utilisent un worker) ---
    
    def select_file_to_sign(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Sélectionner un fichier à signer", 
            "", 
            "Tous les fichiers (*.*)"
        )
        if file_path:
            self.selected_file_path = file_path
            self.label_selected_file.setText(f" {os.path.basename(file_path)}")
            self.label_selected_file.setStyleSheet("color: #4a90e2; font-weight: bold;")
            self.btn_sign_file.setEnabled(True)
            
            # Calculer le hash du fichier (peut être fait dans le thread principal car c'est juste un affichage)
            try:
                file_hash = self.calculate_file_hash(file_path)
                self.label_file_hash.setText(f"Hash SHA-256: {file_hash[:64]}...")
            except Exception as e:
                self.label_file_hash.setText(f"Erreur calcul hash: {e}")
        else:
            self.selected_file_path = None
            self.label_selected_file.setText("Aucun fichier sélectionné")
            self.label_selected_file.setStyleSheet("color: #888; font-style: italic;")
            self.btn_sign_file.setEnabled(False)
            self.label_file_hash.setText("Hash (SHA-256) du document: ---")

    def calculate_file_hash(self, file_path):
        """Calcule le hash SHA-256 d'un fichier (synchrone, pour affichage immédiat)"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def select_file_to_verify(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Sélectionner le document à vérifier", 
            "", 
            "Tous les fichiers (*.*)"
        )
        if file_path:
            self.verify_file_path = file_path
            self.label_verify_file.setText(f"{os.path.basename(file_path)}")
            self.label_verify_file.setStyleSheet("color: #4a90e2; font-weight: bold;")
        else:
            self.verify_file_path = None
            self.label_verify_file.setText("Aucun document sélectionné")
            self.label_verify_file.setStyleSheet("color: #888; font-style: italic;")
            
        self.check_verify_ready()
    
    def select_signature_to_verify(self):
        sig_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Sélectionner le fichier de signature", 
            "", 
            "Fichiers de signature (*.sig);;Tous les fichiers (*.*)"
        )
        if sig_path:
            self.verify_signature_path = sig_path
            self.label_verify_sig.setText(f" {os.path.basename(sig_path)}")
            self.label_verify_sig.setStyleSheet("color: #4a90e2; font-weight: bold;")
        else:
            self.verify_signature_path = None
            self.label_verify_sig.setText("Aucune signature (.sig) sélectionnée")
            self.label_verify_sig.setStyleSheet("color: #888; font-style: italic;")
            
        self.check_verify_ready()
    
    def check_verify_ready(self):
        """Active le bouton de vérification si fichier et signature sont sélectionnés"""
        if self.verify_file_path and self.verify_signature_path:
            self.btn_verify_file.setEnabled(True)
        else:
            self.btn_verify_file.setEnabled(False)
    
    def handle_verify_file(self):
        if not self.public_key:
            QMessageBox.warning(self, "Avertissement", "Génèrez d'abord les clés.")
            return
        
        if not self.verify_file_path or not self.verify_signature_path:
            QMessageBox.warning(self, "Avertissement", "Sélectionnez le fichier et sa signature.")
            return

        # 1. Charger la signature (doit être fait dans le thread principal pour accéder au FS)
        try:
            with open(self.verify_signature_path, "r") as f:
                signature_data = json.load(f)
            
            stored_hash = signature_data.get("file_hash")
            sigma = signature_data.get("signature")
            
            if not stored_hash or not sigma:
                 QMessageBox.critical(self, "Erreur", "Fichier de signature invalide : hash ou signature manquante.")
                 return
            
            if not isinstance(sigma, list) or not all(isinstance(x, int) for x in sigma):
                 QMessageBox.critical(self, "Erreur", "La signature dans le fichier .sig n'est pas au format UOV attendu (liste d'entiers).")
                 return
                 
        except Exception as e:
             QMessageBox.critical(self, "Erreur de lecture", f"Erreur lors du chargement de la signature : {e}")
             return

        self.progress_dialog = QProgressDialog("Vérification du document en cours (Calcul hash + Vérification crypto)...", "Annuler", 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.show()
        
        self.btn_verify_file.setEnabled(False)

        # Démarrer le thread de vérification du fichier
        self.verify_worker = VerifyWorker(
            public_key=self.public_key, 
            data_to_verify=self.verify_file_path, 
            sigma=sigma, 
            is_file_verification=True,
            stored_hash=stored_hash
        )
        self.verify_worker.finished.connect(self.verify_file_finished)
        self.verify_worker.start()

    def verify_file_finished(self, is_valid, message_or_hash, duration, is_file_verification):
        self.progress_dialog.close()
        self.btn_verify_file.setEnabled(True)
        
        # Réinitialiser le résultat visuel
        self.label_file_verify_result.setText("---")
        self.label_file_verify_result.setStyleSheet("font-size: 16pt; font-weight: bold;")
        
        if is_valid:
            self.label_file_verify_result.setText(f" Signature valide ! ({duration:.2f}s)")
            self.label_file_verify_result.setStyleSheet("font-size: 16pt; font-weight: bold; color: green;")
            QMessageBox.information(
                self, 
                "Signature valide", 
                f" La signature est valide (Vérification en {duration:.2f}s) !"
            )
        else:
            if message_or_hash == "Le document a été modifié !":
                # Cas spécial où le hash du fichier ne correspond pas au hash stocké
                self.label_file_verify_result.setText(f" Le document a été modifié !")
                self.label_file_verify_result.setStyleSheet("font-size: 16pt; font-weight: bold; color: red;")
                QMessageBox.warning(self, "Document modifié", "Le fichier a été modifié depuis la signature.")
            else:
                # Échec de la vérification crypto ou autre erreur
                self.label_file_verify_result.setText(f"Signature invalide !")
                self.label_file_verify_result.setStyleSheet("font-size: 16pt; font-weight: bold; color: red;")
                QMessageBox.critical(
                    self, 
                    "Signature invalide", 
                    f" La signature n'est pas valide (Erreur: {message_or_hash}) !"
                )

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()