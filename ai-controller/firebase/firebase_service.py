"""
Firebase Admin SDK Service.
Handles secure token verification, authenticated user retrieval, and scoped Firestore queries.
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, auth as firebase_auth, firestore

from config import settings

logger = logging.getLogger("ai_controller.firebase")


class FirebaseService:
    """Service wrapping Firebase Admin Auth and Firestore with strict user isolation."""

    _app: Optional[firebase_admin.App] = None
    _db: Optional[firestore.Client] = None

    def __init__(self):
        self._ensure_initialized()

    def _ensure_initialized(self):
        """Initializes Firebase Admin SDK if not already active."""
        if FirebaseService._app is not None and FirebaseService._db is not None:
            return

        try:
            if not firebase_admin._apps:
                cred = None
                
                # 1. Try raw JSON environment variable (useful for cloud deploys like Render/Fly/Railway)
                if settings.FIREBASE_SERVICE_ACCOUNT_JSON:
                    try:
                        cert_dict = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
                        cred = credentials.Certificate(cert_dict)
                        logger.info("Using Firebase credentials from FIREBASE_SERVICE_ACCOUNT_JSON")
                    except Exception as e:
                        logger.warning(f"Failed parsing FIREBASE_SERVICE_ACCOUNT_JSON: {e}")

                # 2. Try file path
                if not cred and settings.FIREBASE_SERVICE_ACCOUNT_PATH:
                    path = os.path.expanduser(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
                    if not os.path.isabs(path):
                        path = str((Path(__file__).resolve().parent.parent / path).resolve())
                    if os.path.exists(path):
                        cred = credentials.Certificate(path)
                        logger.info(f"Using Firebase credentials file from {path}")
                    else:
                        logger.warning(f"Firebase credentials file not found at {path}")

                # 3. Auto-detect default service account file if present in ai-controller
                if not cred:
                    potential_paths = [
                        Path(__file__).resolve().parent.parent / "firebase-service-account.json",
                        Path(__file__).resolve().parent.parent / "service-account.json",
                        Path.cwd() / "firebase-service-account.json"
                    ]
                    for p in potential_paths:
                        if p.exists():
                            try:
                                cred = credentials.Certificate(str(p))
                                logger.info(f"Auto-detected and loaded Firebase service account from {p}")
                                break
                            except Exception as auto_err:
                                logger.warning(f"Failed loading auto-detected service account {p}: {auto_err}")

                # 3. Fallback to default application credentials or project ID
                if cred:
                    FirebaseService._app = firebase_admin.initialize_app(cred, {
                        'projectId': settings.FIREBASE_PROJECT_ID
                    })
                else:
                    logger.warning("No service account provided; attempting Application Default Credentials or unauthenticated mock mode.")
                    try:
                        FirebaseService._app = firebase_admin.initialize_app(options={
                            'projectId': settings.FIREBASE_PROJECT_ID
                        })
                    except Exception as fallback_err:
                        logger.warning(f"Default app initialization warning: {fallback_err}")
            else:
                FirebaseService._app = firebase_admin.get_app()

            try:
                FirebaseService._db = firestore.client()
            except Exception as db_err:
                logger.warning(f"Firestore client could not be created directly: {db_err}")

        except Exception as err:
            logger.error(f"Error initializing Firebase Admin SDK: {err}")

    @property
    def db(self) -> Optional[firestore.Client]:
        if FirebaseService._db is None:
            self._ensure_initialized()
        return FirebaseService._db

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verifies a Firebase ID token.
        Extracts and returns the decoded token containing authenticated uid and claims.
        Raises ValueError or Exception if invalid or expired.
        """
        if not token:
            raise ValueError("Token is required")
        
        # Strip 'Bearer ' prefix if present
        if token.startswith("Bearer "):
            token = token.split("Bearer ", 1)[1].strip()

        # In development or testing mode, support guest demo tokens
        if settings.ENVIRONMENT in ["development", "test"] and token.startswith("test-token-"):
            uid = token.replace("test-token-", "")
            return {
                "uid": uid,
                "email": "alex.rivera@techcorp.io" if uid == "guest_user" else f"{uid}@example.com",
                "name": "Alex Rivera" if uid == "guest_user" else f"Test User {uid}",
                "auth_time": int(datetime.utcnow().timestamp())
            }

        try:
            decoded_token = firebase_auth.verify_id_token(token)
            return decoded_token
        except Exception as e:
            logger.warning(f"Firebase token verification failed: {e}")
            raise ValueError(f"Invalid or expired Firebase ID token: {str(e)}")

    def get_user_profile(self, uid: str) -> Dict[str, Any]:
        """
        Retrieves user document from Firestore: users/{uid}
        Strictly scoped to the provided authenticated uid.
        """
        if not uid:
            raise ValueError("User ID cannot be empty")

        if uid == "guest_user":
            now = datetime.now()
            curr_y = now.year
            curr_m = now.month - 1
            salaries = {
                f"{curr_y}-{curr_m}": {"amount": 78000.0, "employer": "Microsoft / Tech Innovations", "payDay": 1},
                f"{curr_y}-{curr_m-1 if curr_m > 0 else 11}": {"amount": 78000.0, "employer": "Microsoft / Tech Innovations", "payDay": 1}
            }
            budgets = {
                f"{curr_y}-{curr_m}": 48000.0,
                f"{curr_y}-{curr_m-1 if curr_m > 0 else 11}": 48000.0
            }
            return {
                "uid": "guest_user",
                "displayName": "Alex Rivera",
                "email": "alex.rivera@techcorp.io",
                "employer": "Microsoft / Tech Innovations",
                "salaries": salaries,
                "budgets": budgets
            }

        if not self.db:
            return {"uid": uid, "budgets": {}, "salaries": {}, "employer": "Salaried Professional"}

        user_ref = self.db.collection("users").document(uid)
        doc = user_ref.get()
        if doc.exists:
            data = doc.to_dict() or {}
            data["uid"] = uid
            return data
        return {"uid": uid, "budgets": {}, "salaries": {}, "employer": "Salaried Professional"}

    def get_salary_for_month(self, uid: str, month: int, year: int) -> Tuple[float, str, int]:
        """
        Retrieves salary amount, employer, and payday for a specific month.
        Firestore stores salaries under users/{uid}.salaries with key 'YYYY-M' (0-indexed month).
        Returns: (amount, employer, payday)
        """
        profile = self.get_user_profile(uid)
        salaries = profile.get("salaries", {})
        default_employer = profile.get("employer", "Salaried Professional")
        
        month_key = f"{year}-{month}"
        salary_info = salaries.get(month_key)
        
        if salary_info is not None:
            if isinstance(salary_info, dict):
                amount = float(salary_info.get("amount", 0) or 0)
                emp = salary_info.get("employer") or default_employer
                pday = int(salary_info.get("payDay", 1) or 1)
                return amount, emp, pday
            try:
                return float(salary_info), default_employer, 1
            except (ValueError, TypeError):
                pass

        # Fallback to most recent salary if set
        if isinstance(salaries, dict) and salaries:
            keys = sorted(salaries.keys(), reverse=True)
            for k in keys:
                val = salaries[k]
                if isinstance(val, dict) and val.get("amount"):
                    return float(val.get("amount", 0)), val.get("employer", default_employer), int(val.get("payDay", 1))
                elif isinstance(val, (int, float)):
                    return float(val), default_employer, 1

        return 0.0, default_employer, 1

    def get_budget_for_month(self, uid: str, month: int, year: int) -> float:
        """
        Retrieves budget for a specific month.
        Firestore stores budgets under users/{uid}.budgets with key 'YYYY-M' (0-indexed month).
        """
        profile = self.get_user_profile(uid)
        budgets = profile.get("budgets", {})
        month_key = f"{year}-{month}"
        
        if isinstance(budgets, dict) and month_key in budgets:
            try:
                return float(budgets[month_key] or 0)
            except (ValueError, TypeError):
                pass
                
        # Check legacy single budget
        if "budget" in profile and profile["budget"] is not None:
            try:
                return float(profile["budget"])
            except (ValueError, TypeError):
                pass

        return 0.0

    def get_user_transactions(
        self, 
        uid: str, 
        month: Optional[int] = None, 
        year: Optional[int] = None,
        transaction_type: Optional[str] = None,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Retrieves transactions for the user from subcollection: users/{uid}/expenses
        Filters by month/year and type ('expense' or 'income') if provided.
        Returns list of transaction dicts sorted by date descending.
        """
        if not uid:
            raise ValueError("UID required")

        if uid == "guest_user":
            now = datetime.now()
            curr_y = now.year
            curr_m = now.month - 1
            
            def d_str(day_offset):
                day = max(1, now.day - day_offset)
                return f"{curr_y}-{curr_m+1:02d}-{day:02d}"

            demo_txs = [
                {"id": "tx_demo_1", "amount": 78000.0, "category": "Salary", "description": "Monthly In-Hand Salary Credited 💼", "date": d_str(now.day - 1), "type": "income", "splitWith": []},
                {"id": "tx_demo_2", "amount": 16500.0, "category": "Bills", "description": "Monthly Apartment Rent & Society Maintenance", "date": d_str(now.day - 2), "type": "expense", "splitWith": []},
                {"id": "tx_demo_3", "amount": 4800.0, "category": "Food", "description": "Monthly Grocery & Supermarket Haul", "date": d_str(3), "type": "expense", "splitWith": []},
                {"id": "tx_demo_4", "amount": 1450.0, "category": "Food", "description": "Team Lunch & Artisan Cafe", "date": d_str(1), "type": "expense", "splitWith": ["Rahul", "Priya"]},
                {"id": "tx_demo_5", "amount": 1850.0, "category": "Transport", "description": "Monthly Metro Card & Uber Commutes", "date": d_str(4), "type": "expense", "splitWith": []},
                {"id": "tx_demo_6", "amount": 2499.0, "category": "Shopping", "description": "Noise Cancelling Work Headphones", "date": d_str(5), "type": "expense", "splitWith": []},
                {"id": "tx_demo_7", "amount": 1200.0, "category": "Entertainment", "description": "Weekend Cinema & Popcorn", "date": d_str(6), "type": "expense", "splitWith": []}
            ]
            
            filtered = []
            for item in demo_txs:
                if transaction_type is not None and item.get("type") != transaction_type:
                    continue
                filtered.append(item)
            return filtered

        if not self.db:
            return []

        coll_ref = self.db.collection("users").document(uid).collection("expenses")
        query = coll_ref.limit(limit)

        docs = query.stream()
        results = []

        for doc in docs:
            item = doc.to_dict()
            item["id"] = doc.id
            tx_date_str = item.get("date")

            # Parse date and filter by month & year if requested
            if tx_date_str and (month is not None or year is not None):
                try:
                    # Date format is YYYY-MM-DD
                    dt = datetime.strptime(str(tx_date_str)[:10], "%Y-%m-%d")
                    # Python dt.month is 1-12, but our internal month index is 0-11
                    tx_month_idx = dt.month - 1
                    tx_year = dt.year
                    
                    if month is not None and tx_month_idx != month:
                        continue
                    if year is not None and tx_year != year:
                        continue
                except Exception:
                    continue

            # Filter by transaction type if requested ('expense' or 'income')
            if transaction_type is not None:
                item_type = item.get("type", "expense")
                if item_type != transaction_type:
                    continue

            results.append(item)

        # Sort descending by date
        results.sort(key=lambda x: str(x.get("date", "")), reverse=True)
        return results

    def get_all_user_transactions_for_indexing(self, uid: str) -> List[Dict[str, Any]]:
        """
        Retrieves all transactions for a user for vectorstore indexing.
        Strictly restricted to users/{uid}/expenses.
        """
        return self.get_user_transactions(uid=uid, limit=2000)


# Singleton
firebase_service = FirebaseService()
