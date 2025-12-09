# gui/main_app.py - VERSION FINALE AVEC AFFICHAGE "DIGEST"
import sys
import os
import json
import time
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QPushButton, QVBoxLayout,
    QHBoxLayout, QLabel, QSpinBox, QTextEdit, QMessageBox, QLineEdit,
    QProgressDialog, QGroupBox
)
from PySide6.QtCore import Qt, QThread, Signal
# Assurez-vous que le chemin vers le module uov est correct
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from uov import KeyGen, Sign, Verify, q

BASE = Path(__file__).resolve().parent.parent

# ==============================================================================
# CLASSE DE TRAVAIL EN ARRIÈRE-PLAN (QThread Worker)
# Effectue la génération et la sérialisation des clés pour éviter de geler l'interface.
# ==============================================================================

class KeyGenWorker(QThread):
    # Signal émis lorsque le travail est terminé
    finished = Signal(dict, str, str, float)
    
    def __init__(self, n, v, m):
        super().__init__()
        self.n = n
        self.v = v
        self.m = m

    def run(self):
        try:
            start_time = time.time()
            
            # 1. GÉNÉRATION DES CLÉS (Long calcul)
            private_key = KeyGen(self.n, self.v, self.m)
            
            # 2. PRÉPARATION DES CLÉS PUBLIQUES ET PRIVÉES
            public_key = {k: private_key[k] for k in ["n", "v", "m", "F", "T"]}
            
            # --- NOUVEAU : Création du digest de la Clé Publique ---
            pub_digest = {
                "Parameters": f"v={self.v} (vinegar), o={self.m} (oil)",
                "Total_N": self.n,
                "F_Polynomes_Count": len(public_key["F"]),
                "T_Matrice_Shape": f"{self.n}x{self.n}",
                "F_Sample_Coefficients": public_key["F"][0]["vv"][:5], # Afficher juste 5 coefficients du premier polynôme pour l'aperçu
                "Q_Modulus": q
            }
            # Sérialisation rapide du digest (petit dictionnaire)
            pub_text = json.dumps(pub_digest, indent=2)
            
            # --- NOUVEAU : Message pour la Clé Privée (non affichée) ---
            priv_text = "Clé privée (F, T_inv) générée et stockée en mémoire. Non affichée pour raisons de sécurité."
            
            end_time = time.time()
            duration = end_time - start_time

            # Émet le signal avec les données
            self.finished.emit(private_key, pub_text, priv_text, duration)

        except Exception as e:
            # En cas d'erreur, on peut émettre un signal d'erreur
            print(f"Erreur dans le thread KeyGen: {e}")
            
# ==============================================================================
# FENÊTRE PRINCIPALE
# ==============================================================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Application de signature UOV (Chris)")
        self.resize(900, 700)
        
        self.public_key = None  
        self.private_key = None 
        self.last_sigma = None
        self.keygen_worker = None
        self.progress_dialog = None
        
        self.init_ui()

    def init_ui(self):
        tabs = QTabWidget()
        tabs.addTab(self.tab_keygen(), " Générer les clés")
        tabs.addTab(self.tab_sign(), " Signer un message")
        tabs.addTab(self.tab_verify(), " Vérifier une signature")
        self.setCentralWidget(tabs)
        
        self.setStyleSheet("""
            /* --- Global --- */
QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 14px;
}

/* --- Labels --- */
QLabel {
    color: #e0e0e0;
    font-weight: 500;
}

/* --- GroupBox --- */
QGroupBox {
    border: 1px solid #3c3c3c;
    border-radius: 6px;
    margin-top: 10px;
    padding: 10px;
    font-weight: bold;
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
}

QPushButton:hover {
    background-color: #3a74e8;
}

QPushButton:pressed {
    background-color: #244c96;
}

/* --- Secondary buttons (ex: clear, reset) --- */
QPushButton#secondary {
    background-color: #444;
}

QPushButton#secondary:hover {
    background-color: #555;
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

/* --- TableViews (si tu en utilises) --- */
QTableWidget, QTableView {
    background-color: #262626;
    gridline-color: #3c3c3c;
    selection-background-color: #3e7be6;
    selection-color: white;
}

QHeaderView::section {
    background: #333;
    color: #e0e0e0;
    padding: 6px;
    border: 1px solid #3c3c3c;
}

/* --- ComboBox --- */
QComboBox {
    background-color: #2b2b2b;
    border: 1px solid #555;
    border-radius: 5px;
    padding: 6px;
}

QComboBox QAbstractItemView {
    background-color: #2b2b2b;
    border: 1px solid #555;
    selection-background-color: #4a90e2;
}

/* --- MessageBox --- */
QMessageBox {
    background-color: #1e1e1e;
}

QMessageBox QLabel {
    color: #e0e0e0;
}

QMessageBox QPushButton {
    background-color: #2d63c8;
    border-radius: 5px;
    padding: 6px 12px;
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
}

QTabBar::tab:selected {
    background: #3d3d3d;
    font-weight: bold;
}

        """)

    # --- Tab KeyGen ---
    def tab_keygen(self):
        w = QWidget()
        layout = QVBoxLayout()
        
        param_group = QGroupBox("Paramètres UOV (v, o, q)")
        params_layout = QHBoxLayout()
        params_layout.addWidget(QLabel("v (vinegar) :"));
        self.spin_v = QSpinBox(); self.spin_v.setRange(1, 500); self.spin_v.setValue(112)
        params_layout.addWidget(self.spin_v)

        params_layout.addWidget(QLabel("o (oil) :"));
        self.spin_o = QSpinBox(); self.spin_o.setRange(1, 500); self.spin_o.setValue(44)
        params_layout.addWidget(self.spin_o)

        params_layout.addWidget(QLabel("q (mod) :"));
        self.input_q = QLineEdit(str(q)); self.input_q.setReadOnly(True)
        params_layout.addWidget(self.input_q)
        param_group.setLayout(params_layout)
        layout.addWidget(param_group)

        btn_layout = QHBoxLayout()
        self.btn_gen = QPushButton("Générer les clés")
        self.btn_gen.clicked.connect(self.handle_generate)
        btn_layout.addWidget(self.btn_gen)
        layout.addLayout(btn_layout)
        
        # Affichage du résumé de la Clé Publique (Digest)
        layout.addWidget(QLabel("Clé Publique (F°T) - Résumé de Structure :"))
        self.text_pub = QTextEdit(); self.text_pub.setReadOnly(True); 
        layout.addWidget(self.text_pub)

        # La Clé Privée est maintenant affichée dans un champ QLineEdit, sans son contenu
        self.text_priv_label = QLabel("Clé Privée (F, T) :")
        layout.addWidget(self.text_priv_label)
        self.text_priv = QLineEdit("Non affichée. Stockée en mémoire."); self.text_priv.setReadOnly(True); 
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

        self.progress_dialog = QProgressDialog("Génération des clés en arrière-plan...", "Annuler", 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.show()
        
        self.keygen_worker = KeyGenWorker(n, v, m)
        self.keygen_worker.finished.connect(self.keygen_finished)
        self.keygen_worker.start()
        
        self.btn_gen.setEnabled(False)

    def keygen_finished(self, private_key, pub_text, priv_text, duration):
        # Cette méthode s'exécute sur le thread principal (UI)
        
        self.progress_dialog.close()
        self.btn_gen.setEnabled(True)
        
        self.private_key = private_key
        # La clé publique est extraite du dictionnaire privé pour la vérification
        self.public_key = {k: self.private_key[k] for k in ["n", "v", "m", "F", "T"]}
        
        # Affichage du digest rapide
        self.text_pub.setPlainText(pub_text)
        # Mise à jour du message de la clé privée
        self.text_priv.setText(priv_text) 
        
        QMessageBox.information(self, "Succès", f"Clés générées vous pouvez signer un message.")


    # --- Tab Sign ---
    def tab_sign(self):
        w = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Message à signer :"))
        self.text_message_sign = QTextEdit()
        layout.addWidget(self.text_message_sign)

        btn_layout = QHBoxLayout()
        self.btn_sign = QPushButton(" Signer le message")
        self.btn_sign.clicked.connect(self.handle_sign)
        btn_layout.addWidget(self.btn_sign)
        layout.addLayout(btn_layout)

        layout.addWidget(QLabel("Signature obtenue :"))
        self.text_signature = QTextEdit(); self.text_signature.setReadOnly(True)
        layout.addWidget(self.text_signature)

        w.setLayout(layout)
        return w

    def handle_sign(self):
        if not self.private_key:
            QMessageBox.warning(self, "Avertissement", "Génèrez d'abord les clés.")
            return
        message = self.text_message_sign.toPlainText()
        if not message:
            QMessageBox.warning(self, "Avertissement", "Message vide.")
            return
            
        progress = QProgressDialog("Calcul de la signature ...", "Annuler", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        QApplication.processEvents()
        
        try:
            start_time = time.time()
            sigma = Sign(self.private_key, message) 
            end_time = time.time()
            
            self.text_signature.setPlainText(str(sigma)) 
            self.last_sigma = sigma
            
            progress.close()
            QMessageBox.information(self, "Succès", f"Signature calculée . Longueur: {len(sigma)} entiers.")
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Erreur", f"Echec signature : {e}")
            
    # --- Tab Verify ---
    def tab_verify(self):
        w = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Message :"))
        self.text_message_verify = QTextEdit()
        layout.addWidget(self.text_message_verify)

        layout.addWidget(QLabel("Signature (collez une signature ou utilisez la derniere signature) :"))
        self.text_signature_input = QTextEdit()
        
        btn_load_sig = QPushButton("Charger la dernière signature")
        btn_load_sig.clicked.connect(lambda: self.text_signature_input.setPlainText(str(self.last_sigma)))
        layout.addWidget(btn_load_sig)
        
        layout.addWidget(self.text_signature_input)
        
        btn_layout = QHBoxLayout()
        self.btn_verify = QPushButton("Vérifier")
        self.btn_verify.clicked.connect(self.handle_verify)
        btn_layout.addWidget(self.btn_verify)
        layout.addLayout(btn_layout)

        self.label_verify_result = QLabel("---")
        self.label_verify_result.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(self.label_verify_result)
        w.setLayout(layout)
        return w

    def handle_verify(self):
        if not self.public_key:
            QMessageBox.warning(self, "Avertissement", "Génèrez d'abord  les clés.")
            return
        
        message = self.text_message_verify.toPlainText()
        sig_text = self.text_signature_input.toPlainText().strip()
        
        if not message or not sig_text:
            QMessageBox.warning(self, "Avertissement", "Message ou signature manquante.")
            return
        
        progress = QProgressDialog("Vérification en cours...", "Annuler", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        QApplication.processEvents()
        
        sigma = None
        try:
            if self.last_sigma is not None and sig_text == str(self.last_sigma):
                sigma = self.last_sigma
            elif sig_text.startswith('[') and sig_text.endswith(']'):
                sigma = eval(sig_text)
            else:
                 QMessageBox.critical(self, "Erreur", "Format de signature invalide (doit être un vecteur Python entre crochets).")
                 return
            
            start_time = time.time()
            ok = Verify(self.public_key, message, sigma)
            end_time = time.time()
            
            progress.close() 
            
            if ok:
                self.label_verify_result.setText(f" Signature valide ! ")
                self.label_verify_result.setStyleSheet("font-size: 14pt; font-weight: bold; color: green;")
            else:
                self.label_verify_result.setText(f" Signature invalide ! ")
                self.label_verify_result.setStyleSheet("font-size: 14pt; font-weight: bold; color: red;")
                
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Erreur", f"Erreur de vérification: {e}")

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()