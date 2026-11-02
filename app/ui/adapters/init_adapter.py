"""Initialisation de l'application : création du premier administrateur et de l'exercice courant."""
from __future__ import annotations

import sqlite3
from datetime import date

from app.database.connection import get_connection, transaction
from app.repositories import utilisateurs, exercices, parametres
from app.security.session import Role
from app.security.passwords import hash_password
from app.security.audit import Action
from app.security import audit
from app.services.auth_service import has_admin, create_first_admin, AuthError
from app.services.exercice_service import create_exercice, set_funeral_tarifs


def ensure_first_admin() -> bool:
    """Crée le premier administrateur si aucun n'existe.
    
    Returns:
        True si un admin a été créé, False si un admin existait déjà.
    """
    conn = get_connection()
    try:
        if has_admin(conn):
            conn.close()
            return False
        
        # Créer l'administrateur par défaut
        with transaction(conn):
            user_id = create_first_admin(
                conn,
                identifiant="admin",
                nom_complet="Administrateur",
                password="Admin2026"
            )
        conn.close()
        return True
    except AuthError:
        conn.close()
        return False
    except Exception:
        conn.close()
        return False


def ensure_current_exercise() -> bool:
    """Crée l'exercice courant s'il n'existe pas.
    
    Returns:
        True si un exercice a été créé, False si un exercice existait déjà.
    """
    conn = get_connection()
    try:
        # Vérifier si un exercice existe déjà
        existing = conn.execute(
            "SELECT id FROM exercices ORDER BY id DESC LIMIT 1"
        ).fetchone()
        
        if existing:
            conn.close()
            return False
        
        # Créer l'exercice 2025-2026 (septembre à août)
        today = date.today()
        year = today.year
        if today.month < 9:
            year -= 1
        
        with transaction(conn):
            exercice_id = create_exercice(
                conn,
                f"{year}-{year + 1}",
                date(year, 9, 1),
                date(year + 1, 8, 31)
            )
            
            # Définir les tarifs funéraires par défaut
            set_funeral_tarifs(conn, exercice_id, 5000, 3000)
            
            # Définir les tarifs mensuels par défaut
            conn.execute(
                "INSERT INTO tarifs_mensuels (exercice_id, sexe, montant) VALUES (?, 'M', 5000)",
                (exercice_id,)
            )
            conn.execute(
                "INSERT INTO tarifs_mensuels (exercice_id, sexe, montant) VALUES (?, 'F', 3000)",
                (exercice_id,)
            )
        
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur création exercice: {e}")
        conn.close()
        return False


def initialize_application() -> None:
    """Initialise l'application complète (admin + exercice)."""
    ensure_first_admin()
    ensure_current_exercise()
